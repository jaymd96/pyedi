#!/usr/bin/env python3
"""
X12 EDI Parser Module

Parses X12 EDI files into generic JSON format while preserving full context
including paths, loop structure, and metadata. Uses pyx12 library for
proper X12 parsing and validation.
"""

import sys
import os
import json
import logging
from collections import OrderedDict
from typing import Dict, Any, List, Optional, Union
from io import StringIO, BytesIO
import tempfile

import pyx12
import pyx12.error_handler
import pyx12.errors
import pyx12.map_index
import pyx12.map_if
import pyx12.params
import pyx12.x12file
from pyx12.map_walker import walk_tree


class X12Parser:
    """
    Parse X12 EDI messages to JSON while preserving full context and structure
    """

    def __init__(self, map_path: Optional[str] = None):
        # Use pyx12 package's installed map files by default
        if map_path is None:
            # Find pyx12's installed map directory
            pyx12_dir = os.path.dirname(pyx12.__file__)
            self.map_path = os.path.join(pyx12_dir, 'map')
            if not os.path.exists(self.map_path):
                # Fallback to local pyx12 if installed package doesn't have maps
                local_pyx12_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pyx12', 'pyx12', 'map'))
                if os.path.exists(local_pyx12_path):
                    self.map_path = local_pyx12_path
                else:
                    raise RuntimeError(f"pyx12 map directory not found. Tried {self.map_path} and {local_pyx12_path}")
        else:
            self.map_path = map_path

        self.logger = logging.getLogger('x12_to_json')
        self.logger.info(f"Using pyx12 map directory: {self.map_path}")

        self.param = pyx12.params.params()
        if self.map_path:
            self.param.set('map_path', self.map_path)

        # Initialize loop tracking state
        self.loop_instance_stack = []  # Stack of (loop_id, instance_num) tuples
        self.loop_counters = {}  # {loop_id: count} for tracking instances
        self.hl_tree = {}  # Hierarchical tree structure
        self.current_hl_id = None  # Current HL segment ID
        self.current_hl_parent = None  # Current HL parent ID
        self.current_hl_level = None  # Current HL level code
        self.segment_index = 0  # Track segment position

    def parse(self, source: Union[str, StringIO, BytesIO]) -> Dict[str, Any]:
        """
        Parse an X12 source to JSON structure

        Args:
            source: X12 EDI content as:
                - File path (str starting with '/' or containing path separators)
                - EDI string content
                - StringIO/BytesIO file-like object

        Returns:
            Dictionary containing parsed EDI data in generic JSON format
        """
        # Determine source type and get file path
        source_file = self._prepare_source(source)
        self.logger.info(f"Converting source: {source_file if isinstance(source_file, str) else 'stream'}")

        # Reset state for new file
        self.loop_instance_stack = []
        self.loop_counters = {}
        self.hl_tree = {}
        self.current_hl_id = None
        self.current_hl_parent = None
        self.current_hl_level = None
        self.segment_index = 0

        # Initialize error handler
        errh = pyx12.error_handler.errh_null()

        # Open X12 source
        try:
            src = pyx12.x12file.X12Reader(source_file)
        except pyx12.errors.X12Error as e:
            self.logger.error(f"Failed to read X12 source: {e}")
            raise
        finally:
            # Clean up temporary file if created
            if hasattr(self, '_temp_file') and self._temp_file:
                try:
                    os.unlink(self._temp_file)
                    self._temp_file = None
                except:
                    pass

        # Load control map based on version
        control_map_file = 'x12.control.00501.xml' if src.icvn == '00501' else 'x12.control.00401.xml'
        control_map = pyx12.map_if.load_map_file(control_map_file, self.param, self.map_path)

        # Initialize map index
        map_index = pyx12.map_index.map_index(self.map_path)

        # Initialize walker and state
        walker = walk_tree()
        node = control_map.getnodebypath('/ISA_LOOP/ISA')

        # Result structure
        result = {
            "x12_version": None,
            "transaction_type": None,
            "functional_group": None,
            "interchange": {},
            "functional_groups": [],
            "transactions": [],
            "map_file": None  # Store the map file for element name lookups
        }

        # Current context
        current_interchange = None
        current_functional_group = None
        current_transaction = None
        current_map = None

        # Transaction type info
        icvn = None
        fic = None
        vriic = None
        tspc = None

        # Process segments
        segment_count = 0
        for seg in src:
            segment_count += 1
            seg_id = seg.get_seg_id()
            orig_node = node

            # Handle control segments
            if seg_id == 'ISA':
                # Start new interchange
                icvn = seg.get_value('ISA12')
                result['x12_version'] = icvn
                current_interchange = self._create_interchange_json(seg)
                result['interchange'] = current_interchange
                node = control_map.getnodebypath('/ISA_LOOP/ISA')
                walker.forceWalkCounterToLoopStart('/ISA_LOOP', '/ISA_LOOP/ISA')

            elif seg_id == 'GS':
                # Start new functional group
                fic = seg.get_value('GS01')
                vriic = seg.get_value('GS08')
                result['functional_group'] = fic

                # Load appropriate map
                map_file = map_index.get_filename(icvn, vriic, fic)
                if map_file:
                    current_map = pyx12.map_if.load_map_file(map_file, self.param, self.map_path)
                    src.check_837_lx = True if current_map.id == '837' else False
                    node = current_map.getnodebypath('/ISA_LOOP/GS_LOOP/GS')
                    result['map_file'] = map_file  # Store the map file name

                current_functional_group = self._create_functional_group_json(seg)
                result['functional_groups'].append(current_functional_group)
                walker.forceWalkCounterToLoopStart('/ISA_LOOP/GS_LOOP', '/ISA_LOOP/GS_LOOP/GS')

            elif seg_id == 'ST':
                # Start new transaction
                trans_id = seg.get_value('ST01')
                trans_control = seg.get_value('ST02')
                result['transaction_type'] = trans_id

                current_transaction = {
                    "transaction_type": trans_id,
                    "control_number": trans_control,
                    "implementation": vriic,
                    "segments": [],
                    "loops": OrderedDict()
                }
                result['transactions'].append(current_transaction)

                # Update node to ST segment path if we have a loaded map
                if current_map:
                    try:
                        node = current_map.getnodebypath('/ISA_LOOP/GS_LOOP/ST_LOOP/ST')
                    except:
                        self.logger.warning("Could not get ST node from map")

            elif seg_id == 'SE':
                # End transaction
                current_transaction = None

            elif seg_id == 'GE':
                # End functional group
                current_functional_group = None

            elif seg_id == 'IEA':
                # End interchange
                current_interchange = None

            else:
                # Walk to find proper node
                if node is not None:
                    try:
                        (node, pop_loops, push_loops) = walker.walk(
                            node, seg, errh, src.get_seg_count(),
                            src.get_cur_line(), src.get_ls_id()
                        )

                        # CRITICAL FIX: Process loop changes from walker
                        if pop_loops:
                            for loop in pop_loops:
                                self._handle_loop_exit(loop)

                        if push_loops:
                            for loop in push_loops:
                                self._handle_loop_entry(loop)

                    except (pyx12.errors.EngineError, AttributeError) as e:
                        self.logger.error(f"Error at line {src.get_cur_line()}: {e}")
                        node = orig_node
                else:
                    self.logger.warning(f"Node is None for segment {seg_id}, using original")
                    node = orig_node

            # Special handling for HL segments
            if seg_id == 'HL':
                self._handle_hl_segment(seg)

            # Add segment to current transaction
            if current_transaction and seg_id not in ['ISA', 'GS', 'GE', 'IEA']:
                segment_json = self._create_segment_json(seg, node)
                self.segment_index += 1
                current_transaction['segments'].append(segment_json)

                # Organize into loops
                if node:
                    loop_path = self._get_loop_path(node)
                    if loop_path:
                        self._add_to_loop_structure(
                            current_transaction['loops'],
                            loop_path,
                            segment_json
                        )

        # Add hierarchical tree to each transaction
        for transaction in result['transactions']:
            transaction['hierarchical_tree'] = self.hl_tree

        return result

    def _handle_loop_exit(self, loop):
        """Handle exiting a loop"""
        if self.loop_instance_stack:
            # Remove loops from stack that are being exited
            loop_id = loop.id if hasattr(loop, 'id') else str(loop)
            self.loop_instance_stack = [
                (lid, inst) for lid, inst in self.loop_instance_stack
                if lid != loop_id
            ]

    def _handle_loop_entry(self, loop):
        """Handle entering a loop"""
        loop_id = loop.id if hasattr(loop, 'id') else str(loop)

        # Increment counter for this loop type
        if loop_id not in self.loop_counters:
            self.loop_counters[loop_id] = 0
        else:
            self.loop_counters[loop_id] += 1

        # Add to stack with instance number
        self.loop_instance_stack.append((loop_id, self.loop_counters[loop_id]))

    def _handle_hl_segment(self, seg):
        """Special handling for HL segments to build hierarchical tree"""
        hl_id = seg.get_value('HL01')
        hl_parent = seg.get_value('HL02')
        hl_level = seg.get_value('HL03')
        hl_child = seg.get_value('HL04')

        self.current_hl_id = hl_id
        self.current_hl_parent = hl_parent
        self.current_hl_level = hl_level

        # Build hierarchical tree
        self.hl_tree[hl_id] = {
            'parent': hl_parent,
            'level': hl_level,
            'level_name': self._get_level_name(hl_level),
            'has_child': hl_child == '1',
            'children': [],
            'segment_start': self.segment_index
        }

        # Link to parent
        if hl_parent and hl_parent in self.hl_tree:
            self.hl_tree[hl_parent]['children'].append(hl_id)

    def _get_level_name(self, level_code):
        """Get human-readable name for HL level code"""
        level_names = {
            '20': 'Information Source',
            '21': 'Information Receiver',
            '22': 'Subscriber',
            '23': 'Dependent',
            'PT': 'Party',
            '19': 'Provider',
            'PR': 'Payer',
            '41': 'Submitter',
            '40': 'Receiver',
            '85': 'Billing Provider',
            'IL': 'Insured',
            'QC': 'Patient'
        }
        return level_names.get(level_code, f'Level {level_code}')

    def _get_current_loop_instance(self):
        """Get the current loop instance context"""
        loop_instances = {}
        for loop_id, instance in self.loop_instance_stack:
            loop_instances[loop_id] = instance
        return loop_instances

    def _get_hierarchical_context(self):
        """Get the current hierarchical context"""
        if not self.current_hl_id:
            return {}

        # Build HL path from root to current
        hl_path = []
        current = self.current_hl_id
        while current:
            hl_path.insert(0, current)
            if current in self.hl_tree:
                current = self.hl_tree[current].get('parent')
            else:
                break

        return {
            'hl_id': self.current_hl_id,
            'hl_parent': self.current_hl_parent,
            'hl_level': self.current_hl_level,
            'hl_level_name': self._get_level_name(self.current_hl_level),
            'hl_path': hl_path
        }

    def _create_interchange_json(self, seg) -> Dict[str, Any]:
        """Create JSON for ISA segment"""
        return {
            "sender_id": seg.get_value('ISA06').strip(),
            "sender_qualifier": seg.get_value('ISA05'),
            "receiver_id": seg.get_value('ISA08').strip(),
            "receiver_qualifier": seg.get_value('ISA07'),
            "date": seg.get_value('ISA09'),
            "time": seg.get_value('ISA10'),
            "control_number": seg.get_value('ISA13'),
            "version": seg.get_value('ISA12'),
            "test_indicator": seg.get_value('ISA15')
        }

    def _create_functional_group_json(self, seg) -> Dict[str, Any]:
        """Create JSON for GS segment"""
        return {
            "functional_id": seg.get_value('GS01'),
            "sender_code": seg.get_value('GS02'),
            "receiver_code": seg.get_value('GS03'),
            "date": seg.get_value('GS04'),
            "time": seg.get_value('GS05'),
            "control_number": seg.get_value('GS06'),
            "version": seg.get_value('GS08')
        }

    def _create_segment_json(self, seg, node) -> Dict[str, Any]:
        """Create JSON for a segment with full context and element names"""
        segment_json = {
            "segment_id": seg.get_seg_id(),
            "x12_path": node.get_path() if node else "unknown",
            "elements": OrderedDict()
        }

        # Add segment name from pyx12 node if available
        if node and hasattr(node, 'name'):
            segment_json['segment_name'] = node.name

        # Add loop information if available
        loop_id = None
        if node:
            parent = node.parent
            while parent and parent.id != 'transaction':
                if parent.base_name == 'loop':
                    loop_id = parent.id
                    segment_json['loop_id'] = parent.id
                    segment_json['loop_name'] = parent.name

                    # Add loop metadata for determining if it can repeat
                    if hasattr(parent, 'max_use'):
                        segment_json['loop_max_use'] = parent.max_use
                    if hasattr(parent, 'usage'):
                        segment_json['loop_usage'] = parent.usage

                    break
                parent = parent.parent

        # Add loop instance number
        if loop_id:
            loop_instances = self._get_current_loop_instance()
            if loop_id in loop_instances:
                segment_json['loop_instance'] = loop_instances[loop_id]

        # Add hierarchical context for transaction segments
        hierarchical_context = self._get_hierarchical_context()
        if hierarchical_context:
            segment_json['hierarchical_context'] = hierarchical_context

        # Add all element values with names from pyx12 nodes
        if hasattr(seg, 'elements'):
            for idx, ele in enumerate(seg.elements):
                ele_id = f"{seg.get_seg_id()}{str(idx+1).zfill(2)}"

                # Try to get element node for name and metadata
                elem_node = None
                if node and hasattr(node, 'get_child_node_by_idx'):
                    try:
                        # Use idx directly as get_child_node_by_idx expects 0-based index
                        elem_node = node.get_child_node_by_idx(idx)
                        if elem_node and hasattr(elem_node, 'name'):
                            self.logger.debug(f"Found element name for {ele_id}: {elem_node.name}")
                    except Exception as e:
                        self.logger.debug(f"Could not get element node for {ele_id}: {e}")

                # Handle composite elements
                if hasattr(ele, 'elements') and len(ele.elements) > 1:
                    # This is a composite with multiple sub-elements
                    segment_json['elements'][ele_id] = {
                        "components": [str(sub.get_value()) if sub else "" for sub in ele.elements],
                        "composite": True
                    }
                    # Add element name if available
                    if elem_node and hasattr(elem_node, 'name'):
                        segment_json['elements'][ele_id]['name'] = elem_node.name
                elif hasattr(ele, 'get_value'):
                    # Simple element or composite with single element
                    value = str(ele.get_value()) if ele.get_value() else ""

                    # If we have element metadata from pyx12, include it
                    if elem_node and hasattr(elem_node, 'name'):
                        segment_json['elements'][ele_id] = {
                            "value": value,
                            "name": elem_node.name
                        }
                        # Add additional metadata if available
                        if hasattr(elem_node, 'data_ele'):
                            segment_json['elements'][ele_id]['data_ele'] = elem_node.data_ele
                        if hasattr(elem_node, 'data_type'):
                            segment_json['elements'][ele_id]['data_type'] = elem_node.data_type
                        if hasattr(elem_node, 'usage'):
                            segment_json['elements'][ele_id]['usage'] = elem_node.usage
                    else:
                        # No metadata available, just store value
                        segment_json['elements'][ele_id] = value

        return segment_json

    def _get_loop_path(self, node) -> List[str]:
        """Get the loop hierarchy for a node"""
        path = []
        current = node.parent

        while current:
            if current.base_name == 'loop':
                path.insert(0, current.id)
            current = current.parent

        return path

    def _prepare_source(self, source: Union[str, StringIO, BytesIO]) -> str:
        """
        Prepare the source for pyx12 processing.

        Args:
            source: EDI content as file path, string, or file-like object

        Returns:
            File path that pyx12 can read
        """
        self._temp_file = None

        # Check if it's a file-like object
        if isinstance(source, (StringIO, BytesIO)):
            # Read content from the file-like object
            content = source.read()
            if isinstance(source, StringIO):
                content = content.encode('utf-8')
            elif isinstance(content, str):
                content = content.encode('utf-8')

            # Reset the stream position
            source.seek(0)

            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.edi', delete=False) as tmp:
                tmp.write(content)
                self._temp_file = tmp.name
                return tmp.name

        # Check if it's a string
        elif isinstance(source, str):
            # Determine if it's a file path or EDI content
            source_stripped = source.strip()

            # Check for file path indicators
            is_file_path = (
                source_stripped.startswith('/') or
                source_stripped.startswith('./') or
                source_stripped.startswith('../') or
                '\\' in source or  # Windows path
                ':' in source[:10] or  # Windows drive letter
                os.path.exists(source)  # File exists
            )

            if is_file_path:
                return source
            else:
                # It's EDI content as a string
                # Create temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.edi', delete=False) as tmp:
                    tmp.write(source)
                    self._temp_file = tmp.name
                    return tmp.name
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

    def _add_to_loop_structure(self, loops: Dict, path: List[str], segment: Dict):
        """Add segment to nested loop structure"""
        current = loops

        for loop_id in path:
            if loop_id not in current:
                current[loop_id] = {
                    "loop_id": loop_id,
                    "segments": [],
                    "loops": OrderedDict()
                }
            current = current[loop_id]["loops"]

        # Add segment to the deepest loop
        if path:
            parent = loops
            for loop_id in path[:-1]:
                parent = parent[loop_id]["loops"]
            parent[path[-1]]["segments"].append(segment)


def main():
    """Main entry point for CLI usage"""
    import argparse

    arg_parser = argparse.ArgumentParser(description='Parse X12 EDI to JSON')
    arg_parser.add_argument('input_file', help='Input X12 file')
    arg_parser.add_argument('-o', '--output', help='Output JSON file',
                            default=None)
    arg_parser.add_argument('-m', '--map-path', help='Path to X12 maps',
                            default=None)
    arg_parser.add_argument('-p', '--pretty', action='store_true',
                            help='Pretty print JSON')
    arg_parser.add_argument('-v', '--verbose', action='store_true',
                            help='Verbose output')

    args = arg_parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level,
                       format='%(asctime)s - %(levelname)s - %(message)s')

    # Parse file
    parser = X12Parser(map_path=args.map_path)
    result = parser.parse(args.input_file)

    # Output
    json_str = json.dumps(result, indent=2 if args.pretty else None)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(json_str)
        print(f"JSON written to {args.output}")
    else:
        print(json_str)

    return 0


if __name__ == '__main__':
    sys.exit(main())