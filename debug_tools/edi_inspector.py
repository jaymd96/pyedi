#!/usr/bin/env python3
"""
EDI Inspector Tool

Interactive tool for visualizing EDI structure, loop hierarchy, and segment details.
Provides a tree view of EDI transactions with detailed element information.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from io import StringIO
import textwrap

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyedi import X12Parser, StructuredFormatter
from pyedi.code_sets import edi_codes


class EDIInspector:
    """Interactive EDI structure inspector and visualizer"""

    def __init__(self, verbose: bool = False):
        self.parser = X12Parser()
        self.formatter = StructuredFormatter()
        self.verbose = verbose
        self.codes = edi_codes

    def inspect(self, source: Union[str, StringIO]) -> None:
        """
        Inspect an EDI source and display its structure

        Args:
            source: EDI file path or StringIO content
        """
        print("\n" + "="*80)
        print("EDI INSPECTOR - Interactive EDI Structure Visualizer")
        print("="*80 + "\n")

        # Parse EDI
        print("📄 Parsing EDI source...")
        try:
            generic_json = self.parser.parse(source)
        except Exception as e:
            print(f"❌ Error parsing EDI: {e}")
            return

        # Display overview
        self._display_overview(generic_json)

        # Display interchange info
        self._display_interchange(generic_json.get('interchange', {}))

        # Display transactions
        transactions = generic_json.get('transactions', [])
        for idx, trans in enumerate(transactions):
            self._display_transaction(trans, idx + 1)

        # Interactive mode
        if self.verbose:
            self._interactive_mode(generic_json)

    def _display_overview(self, data: Dict[str, Any]) -> None:
        """Display EDI file overview"""
        print("\n📊 OVERVIEW")
        print("-" * 40)
        print(f"X12 Version:        {data.get('x12_version')}")
        print(f"Transaction Type:   {data.get('transaction_type')}")
        print(f"Functional Group:   {data.get('functional_group')}")
        print(f"Map File:          {data.get('map_file')}")
        print(f"Total Transactions: {len(data.get('transactions', []))}")

    def _display_interchange(self, interchange: Dict[str, Any]) -> None:
        """Display interchange information"""
        if not interchange:
            return

        print("\n🔄 INTERCHANGE")
        print("-" * 40)
        print(f"Sender:   {interchange.get('sender_qualifier')}:{interchange.get('sender_id')}")
        print(f"Receiver: {interchange.get('receiver_qualifier')}:{interchange.get('receiver_id')}")
        print(f"Date:     {interchange.get('date')}")
        print(f"Time:     {interchange.get('time')}")
        print(f"Control:  {interchange.get('control_number')}")

    def _display_transaction(self, trans: Dict[str, Any], num: int) -> None:
        """Display transaction structure"""
        print(f"\n📋 TRANSACTION #{num}")
        print("-" * 40)
        print(f"Type:           {trans.get('transaction_type')}")
        print(f"Control Number: {trans.get('control_number')}")
        print(f"Total Segments: {len(trans.get('segments', []))}")

        # Display loop hierarchy
        print("\n🔀 LOOP STRUCTURE:")
        self._display_loop_tree(trans.get('loops', {}), indent=2)

        # Display hierarchical levels if present
        if trans.get('hierarchical_tree'):
            print("\n🎯 HIERARCHICAL LEVELS:")
            self._display_hl_tree(trans.get('hierarchical_tree', {}))

        # Display segment summary
        self._display_segment_summary(trans.get('segments', []))

    def _display_loop_tree(self, loops: Dict, indent: int = 0) -> None:
        """Display loop hierarchy as a tree"""
        for loop_id, loop_data in loops.items():
            prefix = "  " * indent + "├─ "
            segment_count = len(loop_data.get('segments', []))
            print(f"{prefix}{loop_id} ({segment_count} segments)")

            # Show first few segments
            if segment_count > 0:
                for seg in loop_data.get('segments', [])[:3]:
                    seg_prefix = "  " * (indent + 1) + "│  "
                    print(f"{seg_prefix}{seg.get('segment_id')} - {seg.get('segment_name', '')}")
                if segment_count > 3:
                    seg_prefix = "  " * (indent + 1) + "│  "
                    print(f"{seg_prefix}... and {segment_count - 3} more")

            # Recursively display nested loops
            if loop_data.get('loops'):
                self._display_loop_tree(loop_data.get('loops', {}), indent + 1)

    def _display_hl_tree(self, hl_tree: Dict) -> None:
        """Display hierarchical level tree"""
        for hl_id, hl_data in hl_tree.items():
            level_name = hl_data.get('level_name', hl_data.get('level'))
            parent = hl_data.get('parent', 'None')
            children = len(hl_data.get('children', []))

            indent = self._get_hl_depth(hl_id, hl_tree) * 2
            prefix = " " * indent + "└─ "

            print(f"{prefix}HL{hl_id}: {level_name} (Parent: {parent}, Children: {children})")

    def _get_hl_depth(self, hl_id: str, hl_tree: Dict) -> int:
        """Get depth of HL in hierarchy"""
        depth = 0
        current = hl_id
        while current in hl_tree and hl_tree[current].get('parent'):
            current = hl_tree[current].get('parent')
            depth += 1
        return depth

    def _display_segment_summary(self, segments: List[Dict]) -> None:
        """Display summary of segments"""
        segment_counts = {}
        for seg in segments:
            seg_id = seg.get('segment_id')
            segment_counts[seg_id] = segment_counts.get(seg_id, 0) + 1

        print("\n📝 SEGMENT SUMMARY:")
        for seg_id, count in sorted(segment_counts.items()):
            print(f"  {seg_id}: {count} occurrence(s)")

    def _interactive_mode(self, data: Dict[str, Any]) -> None:
        """Interactive mode for exploring specific segments"""
        print("\n" + "="*80)
        print("INTERACTIVE MODE - Type 'help' for commands, 'quit' to exit")
        print("="*80)

        while True:
            try:
                command = input("\n> ").strip().lower()

                if command == 'quit' or command == 'exit':
                    break
                elif command == 'help':
                    self._show_help()
                elif command.startswith('segment '):
                    seg_id = command.split(' ', 1)[1].upper()
                    self._show_segment_details(data, seg_id)
                elif command.startswith('loop '):
                    loop_id = command.split(' ', 1)[1]
                    self._show_loop_details(data, loop_id)
                elif command == 'tree':
                    self._show_full_tree(data)
                elif command == 'export':
                    self._export_analysis(data)
                else:
                    print("Unknown command. Type 'help' for available commands.")

            except (EOFError, KeyboardInterrupt):
                break

        print("\n👋 Exiting EDI Inspector")

    def _show_help(self) -> None:
        """Show help for interactive commands"""
        print("\n📚 AVAILABLE COMMANDS:")
        print("  segment <ID>  - Show details for specific segment type (e.g., 'segment NM1')")
        print("  loop <ID>     - Show details for specific loop (e.g., 'loop 2000A')")
        print("  tree          - Show complete EDI structure tree")
        print("  export        - Export analysis to JSON file")
        print("  help          - Show this help message")
        print("  quit/exit     - Exit interactive mode")

    def _show_segment_details(self, data: Dict[str, Any], seg_id: str) -> None:
        """Show details for specific segment type"""
        print(f"\n🔍 SEGMENT DETAILS: {seg_id}")
        print("-" * 40)

        found = False
        for trans in data.get('transactions', []):
            for seg in trans.get('segments', []):
                if seg.get('segment_id') == seg_id:
                    found = True
                    print(f"\n📍 Instance at path: {seg.get('x12_path')}")
                    if seg.get('loop_id'):
                        print(f"   Loop: {seg.get('loop_id')} ({seg.get('loop_name', '')})")

                    print("   Elements:")
                    for elem_id, elem_data in seg.get('elements', {}).items():
                        if isinstance(elem_data, dict):
                            name = elem_data.get('name', '')
                            value = elem_data.get('value', '')
                            print(f"     {elem_id}: {value} ({name})")
                        else:
                            print(f"     {elem_id}: {elem_data}")
                    break
            if found:
                break

        if not found:
            print(f"  No segments with ID '{seg_id}' found")

    def _show_loop_details(self, data: Dict[str, Any], loop_id: str) -> None:
        """Show details for specific loop"""
        print(f"\n🔍 LOOP DETAILS: {loop_id}")
        print("-" * 40)

        for trans in data.get('transactions', []):
            loop = self._find_loop(trans.get('loops', {}), loop_id)
            if loop:
                print(f"  Segments in loop: {len(loop.get('segments', []))}")
                for seg in loop.get('segments', []):
                    print(f"    - {seg.get('segment_id')}: {seg.get('segment_name', '')}")

                if loop.get('loops'):
                    print(f"  Nested loops: {list(loop.get('loops', {}).keys())}")
                break
        else:
            print(f"  Loop '{loop_id}' not found")

    def _find_loop(self, loops: Dict, loop_id: str) -> Optional[Dict]:
        """Find loop by ID recursively"""
        if loop_id in loops:
            return loops[loop_id]

        for loop_data in loops.values():
            nested = self._find_loop(loop_data.get('loops', {}), loop_id)
            if nested:
                return nested
        return None

    def _show_full_tree(self, data: Dict[str, Any]) -> None:
        """Show complete EDI structure tree"""
        print("\n🌳 COMPLETE EDI STRUCTURE TREE")
        print("=" * 80)

        for idx, trans in enumerate(data.get('transactions', [])):
            print(f"\n📁 Transaction #{idx + 1} ({trans.get('transaction_type')})")
            self._print_detailed_tree(trans.get('loops', {}), indent=1)

    def _print_detailed_tree(self, loops: Dict, indent: int = 0) -> None:
        """Print detailed tree structure"""
        for loop_id, loop_data in loops.items():
            prefix = "│  " * indent + "├─ "
            print(f"{prefix}📂 {loop_id}")

            # Show all segments in loop
            for seg in loop_data.get('segments', []):
                seg_prefix = "│  " * (indent + 1) + "├─ "
                print(f"{seg_prefix}📄 {seg.get('segment_id')}: {seg.get('segment_name', '')}")

            # Recursively show nested loops
            if loop_data.get('loops'):
                self._print_detailed_tree(loop_data.get('loops', {}), indent + 1)

    def _export_analysis(self, data: Dict[str, Any]) -> None:
        """Export analysis to JSON file"""
        output_file = "edi_inspection_report.json"

        analysis = {
            "overview": {
                "x12_version": data.get('x12_version'),
                "transaction_type": data.get('transaction_type'),
                "functional_group": data.get('functional_group'),
                "total_transactions": len(data.get('transactions', []))
            },
            "transactions": []
        }

        for trans in data.get('transactions', []):
            trans_analysis = {
                "type": trans.get('transaction_type'),
                "control_number": trans.get('control_number'),
                "segment_count": len(trans.get('segments', [])),
                "loop_structure": self._extract_loop_structure(trans.get('loops', {})),
                "segment_summary": self._get_segment_counts(trans.get('segments', []))
            }
            analysis['transactions'].append(trans_analysis)

        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)

        print(f"✅ Analysis exported to {output_file}")

    def _extract_loop_structure(self, loops: Dict) -> Dict:
        """Extract loop structure for export"""
        structure = {}
        for loop_id, loop_data in loops.items():
            structure[loop_id] = {
                "segment_count": len(loop_data.get('segments', [])),
                "nested_loops": self._extract_loop_structure(loop_data.get('loops', {}))
            }
        return structure

    def _get_segment_counts(self, segments: List[Dict]) -> Dict:
        """Get segment counts for export"""
        counts = {}
        for seg in segments:
            seg_id = seg.get('segment_id')
            counts[seg_id] = counts.get(seg_id, 0) + 1
        return counts


def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(
        description='EDI Inspector - Interactive EDI Structure Visualizer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
        Examples:
          %(prog)s sample.edi                    # Inspect EDI file
          %(prog)s sample.edi -v                 # Verbose mode with interactive exploration
          %(prog)s sample.edi --export           # Export analysis to JSON

        Interactive Commands (in verbose mode):
          segment NM1     - Show details for NM1 segments
          loop 2000A      - Show details for loop 2000A
          tree            - Show complete structure tree
          export          - Export analysis to JSON
          help            - Show available commands
          quit            - Exit interactive mode
        ''')
    )

    parser.add_argument('edi_file', help='EDI file to inspect')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose mode with interactive exploration')
    parser.add_argument('--export', action='store_true',
                       help='Export analysis to JSON file')

    args = parser.parse_args()

    # Create inspector
    inspector = EDIInspector(verbose=args.verbose)

    # Inspect EDI
    inspector.inspect(args.edi_file)

    # Export if requested
    if args.export:
        with open(args.edi_file, 'r') as f:
            edi_content = f.read()
        edi_stream = StringIO(edi_content)
        generic = inspector.parser.parse(edi_stream)
        inspector._export_analysis(generic)


if __name__ == '__main__':
    main()