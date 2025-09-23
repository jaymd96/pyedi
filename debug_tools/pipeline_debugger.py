#!/usr/bin/env python3
"""
Pipeline Debugger Tool

Step-through debugger for the X12 transformation pipeline.
Allows inspection at each transformation stage with diffs and validation.
"""

import json
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from io import StringIO
import difflib
import textwrap
from datetime import datetime
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyedi import X12Parser, StructuredFormatter, SchemaMapper
from pyedi.pipelines import X12Pipeline


class PipelineDebugger:
    """Interactive debugger for X12 transformation pipeline"""

    def __init__(self, save_intermediate: bool = False, output_dir: str = "debug_output"):
        self.save_intermediate = save_intermediate
        self.output_dir = Path(output_dir)
        self.parser = X12Parser()
        self.formatter = StructuredFormatter()
        self.mapper = None

        # Debugging state
        self.stages = []
        self.current_stage = 0
        self.breakpoints = set()

        if save_intermediate:
            self.output_dir.mkdir(exist_ok=True)

    def debug(self,
             edi_source: Union[str, StringIO],
             mapping_file: Optional[str] = None,
             step_mode: bool = True) -> Dict[str, Any]:
        """
        Debug EDI transformation pipeline

        Args:
            edi_source: EDI file path or StringIO content
            mapping_file: Optional mapping definition file
            step_mode: If True, pause after each stage

        Returns:
            Final transformation result
        """
        print("\n" + "="*80)
        print("🔍 PIPELINE DEBUGGER - X12 Transformation Debugger")
        print("="*80 + "\n")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"debug_{timestamp}"

        if self.save_intermediate:
            self.session_dir.mkdir(exist_ok=True)
            print(f"📁 Debug output directory: {self.session_dir}\n")

        # Stage 1: Parse EDI to Generic JSON
        print("="*80)
        print("STAGE 1: EDI → Generic JSON")
        print("="*80)

        start_time = time.time()
        try:
            generic_json = self.parser.parse(edi_source)
            parse_time = time.time() - start_time

            self.stages.append({
                'name': 'Parse',
                'input_type': 'EDI',
                'output_type': 'Generic JSON',
                'data': generic_json,
                'time': parse_time,
                'status': 'success'
            })

            self._display_stage_summary(generic_json, parse_time, 'Parse')

            if self.save_intermediate:
                self._save_intermediate('01_generic.json', generic_json)

            if step_mode:
                self._pause_for_inspection(generic_json, 'Generic JSON')

        except Exception as e:
            print(f"❌ Parse Error: {e}")
            self.stages.append({
                'name': 'Parse',
                'status': 'error',
                'error': str(e)
            })
            return {}

        # Stage 2: Format to Structured JSON
        print("\n" + "="*80)
        print("STAGE 2: Generic JSON → Structured JSON")
        print("="*80)

        start_time = time.time()
        try:
            structured_json = self.formatter.format(generic_json)
            format_time = time.time() - start_time

            self.stages.append({
                'name': 'Format',
                'input_type': 'Generic JSON',
                'output_type': 'Structured JSON',
                'data': structured_json,
                'time': format_time,
                'status': 'success'
            })

            self._display_stage_summary(structured_json, format_time, 'Format')

            if self.save_intermediate:
                self._save_intermediate('02_structured.json', structured_json)

            if step_mode:
                self._pause_for_inspection(structured_json, 'Structured JSON')
                self._show_diff(generic_json, structured_json, 'Generic → Structured')

        except Exception as e:
            print(f"❌ Format Error: {e}")
            self.stages.append({
                'name': 'Format',
                'status': 'error',
                'error': str(e)
            })
            return generic_json

        # Stage 3: Map to Target Schema (if mapping provided)
        if mapping_file:
            print("\n" + "="*80)
            print("STAGE 3: Structured JSON → Target Schema")
            print("="*80)

            start_time = time.time()
            try:
                # Load mapping
                with open(mapping_file, 'r') as f:
                    mapping_def = json.load(f)

                self.mapper = SchemaMapper(mapping_def)
                mapped_json = self.mapper.map(structured_json)
                map_time = time.time() - start_time

                self.stages.append({
                    'name': 'Map',
                    'input_type': 'Structured JSON',
                    'output_type': 'Target Schema',
                    'data': mapped_json,
                    'time': map_time,
                    'status': 'success'
                })

                self._display_stage_summary(mapped_json, map_time, 'Map')

                if self.save_intermediate:
                    self._save_intermediate('03_mapped.json', mapped_json)

                if step_mode:
                    self._pause_for_inspection(mapped_json, 'Mapped JSON')
                    self._show_diff(structured_json, mapped_json, 'Structured → Mapped')

                final_result = mapped_json

            except Exception as e:
                print(f"❌ Mapping Error: {e}")
                self.stages.append({
                    'name': 'Map',
                    'status': 'error',
                    'error': str(e)
                })
                final_result = structured_json
        else:
            final_result = structured_json

        # Final Summary
        self._display_final_summary()

        return final_result

    def _display_stage_summary(self, data: Any, time_taken: float, stage: str) -> None:
        """Display summary of stage results"""
        print(f"\n✅ {stage} Complete ({time_taken:.3f}s)")

        if isinstance(data, dict):
            print(f"   Keys: {list(data.keys())[:5]}{'...' if len(data.keys()) > 5 else ''}")
            if 'transactions' in data:
                print(f"   Transactions: {len(data['transactions'])}")
        elif isinstance(data, list):
            print(f"   Items: {len(data)}")
            if data and isinstance(data[0], dict):
                print(f"   First item keys: {list(data[0].keys())[:5]}{'...' if len(data[0].keys()) > 5 else ''}")

    def _pause_for_inspection(self, data: Any, stage_name: str) -> None:
        """Pause for user inspection"""
        print(f"\n🔍 Inspecting {stage_name}")
        print("-" * 40)

        while True:
            command = input("\nDebugger> ").strip().lower()

            if command == 'continue' or command == 'c':
                break
            elif command == 'quit' or command == 'q':
                print("Exiting debugger")
                sys.exit(0)
            elif command == 'help' or command == 'h':
                self._show_debug_help()
            elif command.startswith('inspect '):
                path = command[8:].strip()
                self._inspect_path(data, path)
            elif command == 'keys':
                self._show_keys(data)
            elif command == 'dump':
                self._dump_current(data, stage_name)
            elif command == 'validate':
                self._validate_structure(data, stage_name)
            elif command == 'stats':
                self._show_stats(data)
            else:
                print("Unknown command. Type 'help' for options.")

    def _show_debug_help(self) -> None:
        """Show debugger help"""
        print("\n📚 DEBUGGER COMMANDS:")
        print("  continue/c      - Continue to next stage")
        print("  quit/q          - Exit debugger")
        print("  help/h          - Show this help")
        print("  inspect <path>  - Inspect value at path (e.g., 'transactions.0.heading')")
        print("  keys            - Show top-level keys")
        print("  dump            - Save current data to file")
        print("  validate        - Validate structure")
        print("  stats           - Show data statistics")

    def _inspect_path(self, data: Any, path: str) -> None:
        """Inspect data at specific path"""
        try:
            current = data
            parts = path.split('.')

            for part in parts:
                if part.isdigit():
                    current = current[int(part)]
                else:
                    current = current[part]

            print(f"\n📍 Value at '{path}':")
            if isinstance(current, (dict, list)):
                print(json.dumps(current, indent=2)[:1000])
                if len(json.dumps(current)) > 1000:
                    print("... (truncated)")
            else:
                print(current)

        except (KeyError, IndexError, TypeError) as e:
            print(f"❌ Cannot access path '{path}': {e}")

    def _show_keys(self, data: Any) -> None:
        """Show available keys"""
        if isinstance(data, dict):
            print("\n🔑 Available keys:")
            for key in data.keys():
                value_type = type(data[key]).__name__
                if isinstance(data[key], list):
                    print(f"  {key}: {value_type} ({len(data[key])} items)")
                elif isinstance(data[key], dict):
                    print(f"  {key}: {value_type} ({len(data[key])} keys)")
                else:
                    print(f"  {key}: {value_type}")
        elif isinstance(data, list):
            print(f"\n📋 List with {len(data)} items")
            if data and isinstance(data[0], dict):
                print("First item keys:", list(data[0].keys()))

    def _dump_current(self, data: Any, stage_name: str) -> None:
        """Dump current data to file"""
        filename = f"debug_dump_{stage_name.lower().replace(' ', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Data saved to {filename}")

    def _validate_structure(self, data: Any, stage_name: str) -> None:
        """Validate data structure"""
        print(f"\n🔍 Validating {stage_name} structure...")

        issues = []

        if isinstance(data, dict):
            # Check for expected keys based on stage
            if 'Generic' in stage_name:
                expected = ['x12_version', 'transactions', 'interchange']
                for key in expected:
                    if key not in data:
                        issues.append(f"Missing expected key: {key}")

            elif 'Structured' in stage_name:
                if isinstance(data, list):
                    if data and 'transaction_type' not in data[0]:
                        issues.append("Missing transaction_type in first transaction")
                elif 'transaction_type' not in data:
                    issues.append("Missing transaction_type")

        if issues:
            print("⚠️  Validation issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ Structure validation passed")

    def _show_stats(self, data: Any) -> None:
        """Show data statistics"""
        print("\n📊 DATA STATISTICS:")

        def count_elements(obj, depth=0):
            if depth > 10:  # Prevent infinite recursion
                return {'keys': 0, 'lists': 0, 'values': 0}

            stats = {'keys': 0, 'lists': 0, 'values': 0}

            if isinstance(obj, dict):
                stats['keys'] += len(obj)
                for value in obj.values():
                    child_stats = count_elements(value, depth + 1)
                    for key in stats:
                        stats[key] += child_stats[key]
            elif isinstance(obj, list):
                stats['lists'] += 1
                for item in obj:
                    child_stats = count_elements(item, depth + 1)
                    for key in stats:
                        stats[key] += child_stats[key]
            else:
                stats['values'] += 1

            return stats

        stats = count_elements(data)
        print(f"  Total keys:   {stats['keys']}")
        print(f"  Total lists:  {stats['lists']}")
        print(f"  Total values: {stats['values']}")

        # Calculate size
        json_str = json.dumps(data)
        print(f"  JSON size:    {len(json_str):,} bytes")

    def _show_diff(self, before: Any, after: Any, transformation: str) -> None:
        """Show difference between transformation stages"""
        print(f"\n🔄 DIFF: {transformation}")
        print("-" * 40)

        before_str = json.dumps(before, indent=2, sort_keys=True)[:2000]
        after_str = json.dumps(after, indent=2, sort_keys=True)[:2000]

        diff = difflib.unified_diff(
            before_str.splitlines(keepends=True),
            after_str.splitlines(keepends=True),
            fromfile='before',
            tofile='after',
            n=3
        )

        diff_lines = list(diff)[:50]  # Limit diff output

        if diff_lines:
            for line in diff_lines:
                if line.startswith('+'):
                    print(f"+ {line.rstrip()}")
                elif line.startswith('-'):
                    print(f"- {line.rstrip()}")
                elif line.startswith('@'):
                    print(f"@ {line.rstrip()}")

            if len(diff_lines) == 50:
                print("... (diff truncated)")
        else:
            print("No significant differences found")

    def _save_intermediate(self, filename: str, data: Any) -> None:
        """Save intermediate result to file"""
        filepath = self.session_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved intermediate: {filepath}")

    def _display_final_summary(self) -> None:
        """Display final pipeline summary"""
        print("\n" + "="*80)
        print("📊 PIPELINE SUMMARY")
        print("="*80)

        total_time = sum(s.get('time', 0) for s in self.stages)

        print(f"\nTotal stages:     {len(self.stages)}")
        print(f"Total time:       {total_time:.3f}s")
        print(f"Successful:       {sum(1 for s in self.stages if s.get('status') == 'success')}")
        print(f"Failed:           {sum(1 for s in self.stages if s.get('status') == 'error')}")

        print("\nStage Performance:")
        for stage in self.stages:
            status = "✅" if stage.get('status') == 'success' else "❌"
            time_str = f"{stage.get('time', 0):.3f}s" if 'time' in stage else 'N/A'
            print(f"  {status} {stage['name']:<10} {time_str:>8}")

        if self.save_intermediate:
            print(f"\n📁 Debug output saved to: {self.session_dir}")


def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(
        description='Pipeline Debugger - X12 Transformation Step-Through Debugger',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
        Examples:
          %(prog)s sample.edi                     # Debug EDI transformation
          %(prog)s sample.edi -m mapping.json     # Debug with mapping
          %(prog)s sample.edi --save              # Save intermediate files
          %(prog)s sample.edi --no-step           # Run without pausing

        Debugger Commands:
          continue/c      - Continue to next stage
          inspect <path>  - Inspect value at path
          keys            - Show available keys
          dump            - Save current data
          validate        - Validate structure
          stats           - Show statistics
          help            - Show commands
          quit            - Exit debugger
        ''')
    )

    parser.add_argument('edi_file', help='EDI file to debug')
    parser.add_argument('-m', '--mapping', help='Mapping definition file')
    parser.add_argument('--save', action='store_true',
                       help='Save intermediate files')
    parser.add_argument('--no-step', action='store_true',
                       help='Run without pausing between stages')
    parser.add_argument('-o', '--output-dir', default='debug_output',
                       help='Directory for debug output (default: debug_output)')

    args = parser.parse_args()

    # Create debugger
    debugger = PipelineDebugger(
        save_intermediate=args.save,
        output_dir=args.output_dir
    )

    # Debug pipeline
    result = debugger.debug(
        args.edi_file,
        mapping_file=args.mapping,
        step_mode=not args.no_step
    )

    if result:
        print("\n✅ Pipeline debugging complete")


if __name__ == '__main__':
    main()