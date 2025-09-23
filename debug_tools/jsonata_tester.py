#!/usr/bin/env python3
"""
JSONata Expression Tester

Interactive tool for testing and debugging JSONata mapping expressions.
Allows real-time testing of expressions against sample data.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import textwrap
from jsonata.jsonata import Jsonata

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyedi import X12Parser, StructuredFormatter


class JSONataTester:
    """Interactive JSONata expression tester and debugger"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.parser = X12Parser()
        self.formatter = StructuredFormatter()
        self.history = []
        self.sample_data = None
        self.expressions = {}

    def test_interactive(self, data_source: Optional[str] = None) -> None:
        """
        Start interactive JSONata testing session

        Args:
            data_source: Optional EDI file or JSON file to use as test data
        """
        print("\n" + "="*80)
        print("🧪 JSONATA EXPRESSION TESTER")
        print("="*80 + "\n")

        # Load test data if provided
        if data_source:
            self.sample_data = self._load_test_data(data_source)
            if self.sample_data:
                print(f"✅ Loaded test data from {data_source}")
                self._show_data_preview()
        else:
            print("ℹ️  No test data loaded. Use 'load' command to load data.")

        print("\nType 'help' for available commands, 'quit' to exit")
        print("-" * 80)

        # Interactive loop
        while True:
            try:
                command = input("\njsonata> ").strip()

                if not command:
                    continue

                if command.lower() in ['quit', 'exit', 'q']:
                    break
                elif command.lower() in ['help', 'h', '?']:
                    self._show_help()
                elif command.lower().startswith('load '):
                    filename = command[5:].strip()
                    self._load_command(filename)
                elif command.lower() == 'data':
                    self._show_full_data()
                elif command.lower() == 'preview':
                    self._show_data_preview()
                elif command.lower() == 'history':
                    self._show_history()
                elif command.lower().startswith('save '):
                    parts = command[5:].strip().split(maxsplit=1)
                    if len(parts) == 2:
                        self._save_expression(parts[0], parts[1])
                    else:
                        print("Usage: save <name> <expression>")
                elif command.lower() == 'list':
                    self._list_saved_expressions()
                elif command.lower().startswith('run '):
                    name = command[4:].strip()
                    self._run_saved_expression(name)
                elif command.lower() == 'examples':
                    self._show_examples()
                elif command.lower().startswith('export'):
                    parts = command.split()
                    filename = parts[1] if len(parts) > 1 else 'expressions.json'
                    self._export_expressions(filename)
                elif command.lower().startswith('import'):
                    parts = command.split()
                    if len(parts) > 1:
                        self._import_expressions(parts[1])
                    else:
                        print("Usage: import <filename>")
                else:
                    # Treat as JSONata expression
                    self._evaluate_expression(command)

            except (EOFError, KeyboardInterrupt):
                print("\n")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        print("\n👋 Goodbye!")

    def _show_help(self) -> None:
        """Show help information"""
        print("""
📚 AVAILABLE COMMANDS:

Data Management:
  load <file>      - Load EDI or JSON file as test data
  data             - Show full test data
  preview          - Show data structure preview

Expression Testing:
  <expression>     - Evaluate JSONata expression against test data
  save <name> <expr> - Save expression with a name
  run <name>       - Run saved expression
  list             - List saved expressions

Utilities:
  history          - Show expression history
  examples         - Show example expressions
  export [file]    - Export saved expressions
  import <file>    - Import expressions from file
  help             - Show this help
  quit             - Exit tester

💡 Tips:
  - Expressions are evaluated against the loaded test data
  - Use $ to refer to the root of the data
  - Use . to navigate object properties
  - Use [] to filter arrays
        """)

    def _load_test_data(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load test data from file"""
        try:
            path = Path(filename)

            if not path.exists():
                print(f"❌ File not found: {filename}")
                return None

            # Check if it's JSON or EDI
            if path.suffix.lower() == '.json':
                with open(path, 'r') as f:
                    return json.load(f)
            elif path.suffix.lower() in ['.edi', '.x12', '.txt']:
                # Parse EDI and format to structured
                print("  Parsing EDI file...")
                generic = self.parser.parse(str(path))
                print("  Formatting to structured JSON...")
                structured = self.formatter.format(generic)
                return structured if isinstance(structured, dict) else structured[0]
            else:
                print(f"❌ Unsupported file type: {path.suffix}")
                return None

        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return None

    def _load_command(self, filename: str) -> None:
        """Handle load command"""
        data = self._load_test_data(filename)
        if data:
            self.sample_data = data
            print(f"✅ Loaded test data from {filename}")
            self._show_data_preview()

    def _show_data_preview(self) -> None:
        """Show preview of loaded data"""
        if not self.sample_data:
            print("ℹ️  No data loaded")
            return

        print("\n📋 DATA PREVIEW:")
        print("-" * 40)

        def show_structure(obj, indent=0, max_depth=3):
            if indent >= max_depth:
                return

            if isinstance(obj, dict):
                for key in list(obj.keys())[:5]:
                    value = obj[key]
                    prefix = "  " * indent + "├─ "

                    if isinstance(value, dict):
                        print(f"{prefix}{key}: object ({len(value)} keys)")
                        show_structure(value, indent + 1, max_depth)
                    elif isinstance(value, list):
                        print(f"{prefix}{key}: array ({len(value)} items)")
                        if value and indent < max_depth - 1:
                            show_structure(value[0], indent + 1, max_depth)
                    else:
                        value_str = str(value)[:50]
                        if len(str(value)) > 50:
                            value_str += "..."
                        print(f"{prefix}{key}: {value_str}")

                if len(obj.keys()) > 5:
                    print("  " * indent + f"├─ ... and {len(obj.keys()) - 5} more keys")

            elif isinstance(obj, list) and obj:
                print("  " * indent + f"[0]: {type(obj[0]).__name__}")
                if isinstance(obj[0], dict):
                    show_structure(obj[0], indent + 1, max_depth)

        show_structure(self.sample_data)

    def _show_full_data(self) -> None:
        """Show full test data"""
        if not self.sample_data:
            print("ℹ️  No data loaded")
            return

        print("\n📄 FULL DATA:")
        print("-" * 40)
        json_str = json.dumps(self.sample_data, indent=2)

        # Limit output for large data
        if len(json_str) > 5000:
            print(json_str[:5000])
            print(f"\n... (truncated, showing 5000/{len(json_str)} chars)")
            print("\nSave to file for full data:")
            print("  with open('data.json', 'w') as f:")
            print("    json.dump(sample_data, f, indent=2)")
        else:
            print(json_str)

    def _evaluate_expression(self, expression: str) -> None:
        """Evaluate JSONata expression against test data"""
        if not self.sample_data:
            print("❌ No test data loaded. Use 'load' command first.")
            return

        try:
            # Create JSONata expression
            jsonata_expr = Jsonata(expression)

            # Evaluate against sample data
            result = jsonata_expr.evaluate(self.sample_data)

            # Add to history
            self.history.append({
                'expression': expression,
                'result': result,
                'success': True
            })

            # Display result
            print("\n✅ RESULT:")
            print("-" * 40)

            if result is None:
                print("null (no match)")
            elif isinstance(result, (dict, list)):
                result_str = json.dumps(result, indent=2)
                if len(result_str) > 2000:
                    print(result_str[:2000])
                    print(f"... (truncated, {len(result_str)} total chars)")
                else:
                    print(result_str)
            else:
                print(result)

            # Show type and size
            print("\n📊 Result Info:")
            print(f"  Type: {type(result).__name__}")
            if isinstance(result, list):
                print(f"  Length: {len(result)}")
            elif isinstance(result, dict):
                print(f"  Keys: {len(result)}")

        except Exception as e:
            print(f"\n❌ Expression Error: {e}")
            self.history.append({
                'expression': expression,
                'error': str(e),
                'success': False
            })

    def _save_expression(self, name: str, expression: str) -> None:
        """Save expression with a name"""
        self.expressions[name] = expression
        print(f"✅ Saved expression '{name}'")

    def _list_saved_expressions(self) -> None:
        """List all saved expressions"""
        if not self.expressions:
            print("ℹ️  No saved expressions")
            return

        print("\n💾 SAVED EXPRESSIONS:")
        print("-" * 40)
        for name, expr in self.expressions.items():
            print(f"  {name}: {expr}")

    def _run_saved_expression(self, name: str) -> None:
        """Run a saved expression"""
        if name not in self.expressions:
            print(f"❌ Expression '{name}' not found")
            return

        expression = self.expressions[name]
        print(f"🏃 Running: {expression}")
        self._evaluate_expression(expression)

    def _show_history(self) -> None:
        """Show expression history"""
        if not self.history:
            print("ℹ️  No expression history")
            return

        print("\n📜 EXPRESSION HISTORY:")
        print("-" * 40)

        for i, item in enumerate(self.history[-10:], 1):
            status = "✅" if item['success'] else "❌"
            print(f"{i}. {status} {item['expression']}")
            if 'result' in item and item['result'] is not None:
                result_str = str(item['result'])[:100]
                if len(str(item['result'])) > 100:
                    result_str += "..."
                print(f"   → {result_str}")
            elif 'error' in item:
                print(f"   → Error: {item['error']}")

    def _show_examples(self) -> None:
        """Show example JSONata expressions"""
        print("""
📝 EXAMPLE JSONATA EXPRESSIONS:

Basic Navigation:
  $                           # Root object
  $.transaction_type          # Get transaction_type field
  $.heading.name_loop         # Navigate nested objects
  $.detail.claim[0]           # Get first claim

Array Operations:
  $.detail.claim              # Get all claims
  $.detail.claim[0..2]        # Get first 3 claims
  $.detail.claim[-1]          # Get last claim
  $.detail.claim[amount > 100]  # Filter claims by amount

Transformations:
  $.detail.claim.amount       # Extract all amounts
  $sum($.detail.claim.amount) # Sum all amounts
  $count($.detail.claim)      # Count claims

Object Construction:
  {
    "type": $.transaction_type,
    "total": $sum($.detail.claim.amount),
    "count": $count($.detail.claim)
  }

String Operations:
  $uppercase($.heading.name)  # Convert to uppercase
  $substring($.control_number, 0, 5)  # Get substring

Conditional Logic:
  $.amount > 1000 ? "high" : "low"
  $.status = "A" ? "Active" : "Inactive"
        """)

    def _export_expressions(self, filename: str) -> None:
        """Export saved expressions to file"""
        if not self.expressions:
            print("ℹ️  No expressions to export")
            return

        try:
            with open(filename, 'w') as f:
                json.dump(self.expressions, f, indent=2)
            print(f"✅ Exported {len(self.expressions)} expressions to {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    def _import_expressions(self, filename: str) -> None:
        """Import expressions from file"""
        try:
            with open(filename, 'r') as f:
                imported = json.load(f)

            if not isinstance(imported, dict):
                print("❌ Invalid expression file format")
                return

            self.expressions.update(imported)
            print(f"✅ Imported {len(imported)} expressions from {filename}")

        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in file: {filename}")
        except Exception as e:
            print(f"❌ Import failed: {e}")


def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(
        description='JSONata Expression Tester - Test and debug JSONata mapping expressions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
        Examples:
          %(prog)s                           # Start interactive tester
          %(prog)s sample.edi                # Load EDI file and start tester
          %(prog)s structured.json           # Load JSON file and start tester

        Interactive Commands:
          $.transaction_type                 # Evaluate expression
          save getName $.heading.name        # Save expression
          run getName                        # Run saved expression
          load sample.json                   # Load test data
          help                              # Show all commands
        ''')
    )

    parser.add_argument('data_file', nargs='?',
                       help='Optional EDI or JSON file to use as test data')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')

    args = parser.parse_args()

    # Create tester
    tester = JSONataTester(verbose=args.verbose)

    # Start interactive session
    tester.test_interactive(args.data_file)


if __name__ == '__main__':
    main()