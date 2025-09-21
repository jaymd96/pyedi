#!/usr/bin/env python3
"""
Structured EDI Formatter Module

Transforms generic X12 JSON output into a structured format similar to Stedi's Guide JSON,
preserving X12 structure while adding meaningful field names with position numbers.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from collections import OrderedDict
from datetime import datetime
import re

from ..code_sets import edi_codes as codes
from .map_loader import MapElementLoader


class StructuredFormatter:
    """Transform generic X12 JSON to structured format preserving X12 organization"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.map_loader = MapElementLoader()

    def format(self, generic_json: Dict[str, Any], include_technical: bool = True) -> Dict[str, Any]:
        """
        Format generic JSON to structured format with meaningful field names

        Args:
            generic_json: Output from X12Parser
            include_technical: Include original codes alongside descriptions (for compatibility)

        Returns:
            Structured JSON in Guide JSON format with descriptive field names and position numbers
        """
        try:
            # Store transaction type and map file for element name lookups
            self._current_transaction_type = generic_json.get('transaction_type')
            self._current_map_file = generic_json.get('map_file')

            # Get the first transaction
            transactions = generic_json.get('transactions', [])
            if not transactions:
                return generic_json

            transaction = transactions[0]
            segments = transaction.get('segments', [])

            # Build the structured output
            result = OrderedDict()

            # Add interchange and functional group metadata
            result['interchange'] = self._format_interchange(generic_json)
            result['functional_group'] = self._format_functional_group(generic_json)

            # Group segments into heading and detail sections
            heading_segments, detail_segments = self._partition_segments(segments)

            # Process heading section
            if heading_segments:
                result['heading'] = self._process_segment_group(heading_segments)

            # Process detail section
            if detail_segments:
                result['detail'] = self._process_segment_group(detail_segments)

            # Add transaction type for convenience
            result['transaction_type'] = self._current_transaction_type

            return result

        except Exception as e:
            self.logger.error(f"Error transforming to structured format: {e}", exc_info=True)
            return generic_json

    def _format_interchange(self, generic_json: Dict[str, Any]) -> Dict[str, Any]:
        """Format interchange information"""
        interchange = generic_json.get('interchange', {})
        return {
            'sender_id': interchange.get('sender_id'),
            'sender_qualifier': interchange.get('sender_qualifier'),
            'receiver_id': interchange.get('receiver_id'),
            'receiver_qualifier': interchange.get('receiver_qualifier'),
            'date': interchange.get('date'),
            'time': interchange.get('time'),
            'control_number': interchange.get('control_number'),
            'version': interchange.get('version'),
            'test_indicator': interchange.get('test_indicator')
        }

    def _format_functional_group(self, generic_json: Dict[str, Any]) -> Dict[str, Any]:
        """Format functional group information"""
        groups = generic_json.get('functional_groups', [])
        if not groups:
            return {}

        group = groups[0]
        return {
            'functional_id': group.get('functional_id'),
            'sender_code': group.get('sender_code'),
            'receiver_code': group.get('receiver_code'),
            'date': group.get('date'),
            'time': group.get('time'),
            'control_number': group.get('control_number'),
            'version': group.get('version')
        }

    def _partition_segments(self, segments: List[Dict[str, Any]]) -> tuple:
        """
        Partition segments into heading and detail sections.
        Heading typically includes setup segments like ST, BGN/BHT, N1 loops, etc.
        Detail includes the main content like claims, members, service lines, etc.
        """
        heading_segments = []
        detail_segments = []

        # Common heading loop IDs and segment IDs
        heading_loops = {'1000A', '1000B', '1000C'}  # Submitter, Receiver, etc.
        heading_segment_ids = {'ST', 'BHT', 'BGN', 'BPR', 'TRN', 'CUR', 'REF', 'DTM', 'BGN'}

        # Segments that typically start the detail section
        detail_start_segments = {'CLP', 'CLM', 'INS', 'HL', 'LX'}

        in_detail = False

        for segment in segments:
            seg_id = segment.get('segment_id')
            loop_id = segment.get('loop_id', '')

            # Check if we've entered the detail section
            if seg_id in detail_start_segments:
                in_detail = True

            # Classify segment
            if not in_detail:
                # Check if it's a heading segment
                if seg_id in heading_segment_ids or loop_id in heading_loops:
                    heading_segments.append(segment)
                elif seg_id == 'N1':
                    # N1 segments in the beginning are usually heading
                    heading_segments.append(segment)
                else:
                    detail_segments.append(segment)
            else:
                detail_segments.append(segment)

        return heading_segments, detail_segments

    def _process_segment_group(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a group of segments into structured format"""
        result = OrderedDict()

        # Group segments by loop
        loops = self._group_segments_by_loop(segments)

        for loop_key, loop_segments in loops.items():
            if loop_key == 'no_loop':
                # Process segments not in a loop
                for segment in loop_segments:
                    seg_key = self._create_segment_key(segment)
                    seg_data = self._format_segment(segment)

                    # Handle multiple occurrences of the same segment
                    if seg_key in result:
                        # Convert to list if not already
                        if not isinstance(result[seg_key], list):
                            result[seg_key] = [result[seg_key]]
                        result[seg_key].append(seg_data)
                    else:
                        result[seg_key] = seg_data
            else:
                # Process loop
                loop_name = self._format_loop_name(loop_key, loop_segments)
                loop_data = self._process_loop(loop_segments)

                # Handle repeating loops
                if loop_name in result:
                    # Convert to list if not already
                    if not isinstance(result[loop_name], list):
                        result[loop_name] = [result[loop_name]]
                    result[loop_name].append(loop_data)
                else:
                    # Check if this loop typically repeats
                    if self._is_repeating_loop(loop_key, loop_segments):
                        result[loop_name] = [loop_data]
                    else:
                        result[loop_name] = loop_data

        return result

    def _group_segments_by_loop(self, segments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group segments by their loop ID and instance"""
        loops = OrderedDict()

        for segment in segments:
            loop_id = segment.get('loop_id')
            loop_instance = segment.get('loop_instance', 0)

            if loop_id:
                # Create a unique key for this loop instance
                loop_key = f"{loop_id}_{loop_instance}"
            else:
                loop_key = 'no_loop'

            if loop_key not in loops:
                loops[loop_key] = []
            loops[loop_key].append(segment)

        return loops

    def _process_loop(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process segments within a loop"""
        result = OrderedDict()

        # Group segments by type within the loop
        segment_groups = OrderedDict()
        for segment in segments:
            seg_id = segment.get('segment_id')
            if seg_id not in segment_groups:
                segment_groups[seg_id] = []
            segment_groups[seg_id].append(segment)

        # Process each segment type
        for seg_id, seg_list in segment_groups.items():
            seg_key = self._create_segment_key(seg_list[0])

            if len(seg_list) == 1:
                result[seg_key] = self._format_segment(seg_list[0])
            else:
                # Multiple segments of the same type in the loop
                result[seg_key] = [self._format_segment(seg) for seg in seg_list]

        return result

    def _format_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single segment with descriptive field names and position numbers"""
        result = OrderedDict()
        elements = segment.get('elements', {})
        seg_id = segment.get('segment_id', '')
        loop_id = segment.get('loop_id', '')
        loop_type = self._get_loop_type(loop_id, segment)

        # Build context for naming
        context = {
            'segment_id': seg_id,
            'loop_id': loop_id,
            'loop_type': loop_type
        }

        # Extract entity code for NM1/N1 segments to provide context
        if seg_id == 'NM1' and 'NM101' in elements:
            entity_code = self._get_element_value_raw(elements.get('NM101'))
            context['entity_code'] = entity_code
            # Also store entity type (1=person, 2=org)
            if 'NM102' in elements:
                context['entity_type'] = self._get_element_value_raw(elements.get('NM102'))
            # Store for use by subsequent segments in same loop
            self._current_entity_code = entity_code
        elif seg_id == 'N1' and 'N101' in elements:
            entity_code = self._get_element_value_raw(elements.get('N101'))
            context['entity_code'] = entity_code
            self._current_entity_code = entity_code
        elif hasattr(self, '_current_entity_code'):
            # Use stored entity code for other segments in same loop
            context['entity_code'] = self._current_entity_code

        # Extract qualifiers for REF and DTP/DTM segments
        if seg_id == 'REF' and 'REF01' in elements:
            context['ref_qualifier'] = self._get_element_value_raw(elements.get('REF01'))
        elif seg_id in ['DTP', 'DTM'] and f'{seg_id}01' in elements:
            context['date_qualifier'] = self._get_element_value_raw(elements.get(f'{seg_id}01'))

        # Get transaction type from the root context if available
        transaction_type = getattr(self, '_current_transaction_type', None)

        for elem_id, elem_data in elements.items():
            # Extract position number from element ID (e.g., 'BGN01' -> '01')
            position = re.search(r'\d+$', elem_id)
            if position:
                position_num = position.group()
            else:
                position_num = elem_id

            # Get element name and value
            if isinstance(elem_data, dict):
                # First try to use the name from the parser if available
                elem_name = elem_data.get('name')
                elem_value = elem_data.get('value')

                # Handle composite elements
                if elem_data.get('composite'):
                    elem_value = elem_data.get('components', [])
            else:
                elem_name = None
                elem_value = elem_data

            # If no name from parser, try to get it from the map loader
            if not elem_name and self._current_map_file:
                elem_name = self.map_loader.get_element_name(self._current_map_file, seg_id, elem_id)

            # If still no name, use the element ID
            if not elem_name or elem_name == elem_id:
                elem_name = elem_id
                # Use simple format for fallback
                field_name = self._format_field_name(elem_name, position_num)
            else:
                # Format the field name in Stedi style with context
                field_name = self.map_loader.format_element_name_for_json(elem_name, elem_id, context)

            # Apply any data type conversions
            if elem_value is not None:
                elem_value = self._convert_value(elem_value, elem_name, elem_id)

            result[field_name] = elem_value

        return result

    def _get_element_value_raw(self, element: Any) -> str:
        """Get raw element value without conversion"""
        if isinstance(element, dict):
            return element.get('value', '')
        return str(element) if element else ''

    def _get_loop_type(self, loop_id: str, segment: Dict[str, Any]) -> str:
        """Determine loop type from loop ID and context"""
        # Common healthcare loop patterns
        if 'payer' in loop_id.lower() or loop_id in ['1000A', '1000']:
            return 'payer'
        elif 'payee' in loop_id.lower() or loop_id in ['1000B']:
            return 'payee'
        elif 'subscriber' in loop_id.lower() or loop_id in ['2000B', '2010BA']:
            return 'subscriber'
        elif 'patient' in loop_id.lower() or loop_id in ['2000C', '2010CA']:
            return 'patient'
        elif 'billing' in loop_id.lower() or loop_id in ['2010AA']:
            return 'billing_provider'
        elif 'rendering' in loop_id.lower() or loop_id in ['2310B', '2420A']:
            return 'rendering_provider'
        elif 'referring' in loop_id.lower() or loop_id in ['2310A', '2420B']:
            return 'referring_provider'
        elif 'receiver' in loop_id.lower() or loop_id in ['1000B']:
            return 'receiver'
        elif 'submitter' in loop_id.lower() or loop_id in ['1000A']:
            return 'submitter'

        # Check segment name hints
        seg_name = segment.get('segment_name', '').lower()
        if 'payer' in seg_name:
            return 'payer'
        elif 'payee' in seg_name:
            return 'payee'
        elif 'patient' in seg_name:
            return 'patient'
        elif 'subscriber' in seg_name or 'insured' in seg_name:
            return 'subscriber'
        elif 'provider' in seg_name:
            return 'provider'

        return ''

    def _format_field_name(self, name: str, position: str) -> str:
        """Format field name with position number in snake_case"""
        # Convert name to snake_case
        name = re.sub(r'[^\w\s]', '', name)  # Remove special characters
        name = re.sub(r'\s+', '_', name)  # Replace spaces with underscores
        name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)  # Handle acronyms
        name = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', name)  # Handle camelCase
        name = name.lower()

        # Remove redundant words
        name = re.sub(r'_code_code', '_code', name)
        name = re.sub(r'_id_id', '_id', name)
        name = re.sub(r'_number_number', '_number', name)

        # Add position number
        return f"{name}_{position.zfill(2)}"

    def _create_segment_key(self, segment: Dict[str, Any]) -> str:
        """Create a descriptive key for a segment"""
        seg_id = segment.get('segment_id')
        seg_name = segment.get('segment_name', seg_id)

        # Convert to snake_case
        key = re.sub(r'[^\w\s]', '', seg_name)
        key = re.sub(r'\s+', '_', key)
        key = key.lower()

        # Add segment ID if not already included
        if seg_id and seg_id.lower() not in key:
            key = f"{key}_{seg_id}"

        return key

    def _format_loop_name(self, loop_key: str, segments: List[Dict[str, Any]]) -> str:
        """Create a descriptive name for a loop"""
        # Extract loop ID from key (format: "loopid_instance")
        parts = loop_key.rsplit('_', 1)
        loop_id = parts[0] if parts else loop_key

        # Get the first segment to help identify the loop
        first_segment = segments[0] if segments else None
        if first_segment:
            seg_id = first_segment.get('segment_id')
            seg_name = first_segment.get('segment_name', seg_id)

            # Try to get a descriptive name from the segment
            if seg_id == 'N1' or seg_id == 'NM1':
                # Entity loops - try to get entity type
                entity_code = self._get_element_value(first_segment, f'{seg_id}01')
                entity_desc = codes.get_entity_description(entity_code) if entity_code else seg_name

                # Format the name
                name = re.sub(r'[^\w\s]', '', entity_desc)
                name = re.sub(r'\s+', '_', name)
                name = name.lower()

                return f"{name}_{seg_id}_loop"
            else:
                # Generic loop name
                seg_key = re.sub(r'[^\w\s]', '', seg_name)
                seg_key = re.sub(r'\s+', '_', seg_key)
                seg_key = seg_key.lower()

                return f"{seg_key}_loop"

        # Fallback to loop ID
        return f"{loop_id}_loop"

    def _is_repeating_loop(self, loop_key: str, segments: List[Dict[str, Any]] = None) -> bool:
        """Check if a loop can repeat based on metadata from parser"""
        # Check the loop_max_use metadata from segments
        if segments:
            for segment in segments:
                max_use = segment.get('loop_max_use')
                if max_use:
                    # Check if max_use indicates it can repeat
                    if max_use == 'unbounded':
                        return True
                    try:
                        # If it's a number > 1, it can repeat
                        if int(max_use) > 1:
                            return True
                    except (ValueError, TypeError):
                        pass
                    # If max_use is '1' or any other value, it doesn't repeat
                    return False

        # Default to False if no metadata available
        return False

    def _get_element_value(self, segment: Dict[str, Any], element_id: str) -> Any:
        """Get element value from segment"""
        elements = segment.get('elements', {})
        element = elements.get(element_id)

        if isinstance(element, dict):
            if 'value' in element:
                return element['value']
            elif element.get('composite'):
                return element.get('components', [])

        return element

    def _convert_value(self, value: Any, name: str, elem_id: str) -> Any:
        """Convert value based on its type or name"""
        if value is None or value == '':
            return None

        # Check for date patterns
        if any(word in name.lower() for word in ['date', 'datetime']):
            return self._format_date(value)

        # Check for time patterns
        if 'time' in name.lower() and 'datetime' not in name.lower():
            return self._format_time(value)

        # Check for amount/money patterns - but exclude method/format codes
        name_lower = name.lower()
        if ('method' not in name_lower and 'format' not in name_lower and 'code' not in name_lower):
            if any(word in name_lower for word in ['amount', 'charge', 'paid', 'payment', 'price', 'cost', 'fee']):
                return self._safe_float(value)

        # Check for quantity/count patterns
        if any(word in name.lower() for word in ['quantity', 'count', 'units', 'number_of']):
            try:
                # Try integer first for counts
                return int(value)
            except (ValueError, TypeError):
                return self._safe_float(value)

        # Check for control numbers (should remain as strings even if numeric)
        if 'control_number' in name.lower() or 'reference_number' in name.lower():
            return str(value)

        return value

    def _format_date(self, date_str: str) -> str:
        """Format date from CCYYMMDD or YYMMDD to YYYY-MM-DD"""
        if not date_str or not isinstance(date_str, str):
            return date_str

        try:
            if len(date_str) == 8:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            elif len(date_str) == 6:
                year_prefix = "20" if int(date_str[:2]) <= 50 else "19"
                return f"{year_prefix}{date_str[:2]}-{date_str[2:4]}-{date_str[4:]}"
            else:
                return date_str
        except:
            return date_str

    def _format_time(self, time_str: str) -> str:
        """Format time from HHMM or HHMMSS to HH:MM or HH:MM:SS"""
        if not time_str or not isinstance(time_str, str):
            return time_str

        try:
            if len(time_str) == 4:
                return f"{time_str[:2]}:{time_str[2:]}"
            elif len(time_str) == 6:
                return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
            else:
                return time_str
        except:
            return time_str

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


# Convenience function for backwards compatibility and ease of use
def format_structured(generic_json: Dict[str, Any], include_technical: bool = True) -> Dict[str, Any]:
    """
    Format generic X12 JSON to structured format

    Args:
        generic_json: Output from X12Parser
        include_technical: Include original codes alongside descriptions (for compatibility)

    Returns:
        Structured JSON in Guide JSON format
    """
    formatter = StructuredFormatter()
    return formatter.format(generic_json, include_technical)