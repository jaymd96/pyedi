#!/usr/bin/env python3
"""
EDI Segment Lookup Tool

Quick reference tool for EDI segments, elements, and code values.
Provides descriptions and meanings for X12 EDI components.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import textwrap
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyedi.code_sets import edi_codes


class SegmentLookup:
    """EDI segment and code lookup tool"""

    # Common segment descriptions
    SEGMENT_DESCRIPTIONS = {
        # Interchange/Functional Group
        'ISA': 'Interchange Control Header - Defines sender, receiver, and control information',
        'IEA': 'Interchange Control Trailer - Closes the interchange',
        'GS': 'Functional Group Header - Groups related transaction sets',
        'GE': 'Functional Group Trailer - Closes the functional group',
        'ST': 'Transaction Set Header - Begins a transaction set',
        'SE': 'Transaction Set Trailer - Ends a transaction set',

        # Common Healthcare Segments
        'BHT': 'Beginning of Hierarchical Transaction - Transaction purpose and reference',
        'HL': 'Hierarchical Level - Defines hierarchical relationships',
        'NM1': 'Individual or Organizational Name - Name and identification',
        'N3': 'Address Information - Street address',
        'N4': 'Geographic Location - City, State, ZIP',
        'PER': 'Administrative Communications Contact - Contact information',
        'REF': 'Reference Information - Various reference numbers',
        'DTM': 'Date or Time or Period - Date/time information',
        'DTP': 'Date or Time Period - Specific date/time qualifiers',

        # Claim Specific
        'CLM': 'Health Claim - Main claim information',
        'HI': 'Health Care Information Codes - Diagnosis/procedure codes',
        'SV1': 'Professional Service - Service line details',
        'SV2': 'Institutional Service Line - Hospital service details',
        'SBR': 'Subscriber Information - Insurance subscriber details',
        'CAS': 'Claims Adjustment - Adjustment reason codes',
        'AMT': 'Monetary Amount - Various amount types',
        'QTY': 'Quantity - Various quantity measurements',
        'LX': 'Transaction Set Line Number - Service line counter',

        # Payment/Remittance
        'CLP': 'Claim Payment Information - Payment details for a claim',
        'SVC': 'Service Payment Information - Payment for specific services',
        'PLB': 'Provider Level Adjustment - Provider adjustments',
        'TRN': 'Reassociation Trace Number - Check/EFT trace number',
        'BPR': 'Beginning Segment for Payment Order/Remittance - Payment method and amount',

        # Loop Headers
        'PRV': 'Provider Information - Provider specialty/taxonomy',
        'CUR': 'Currency - Currency information',
        'PAT': 'Patient Information - Patient demographic details',
        'DMG': 'Demographic Information - Additional demographics',
        'INS': 'Insured Benefit - Insurance coverage details',
        'DX': 'Diagnosis - Diagnosis information',
        'EQ': 'Eligibility or Benefit Inquiry - Eligibility request details',
    }

    # Element type mappings
    ELEMENT_TYPES = {
        'ID': 'Identifier/Code',
        'AN': 'Alphanumeric String',
        'DT': 'Date (CCYYMMDD)',
        'TM': 'Time (HHMM or HHMMSS)',
        'N': 'Numeric',
        'N0': 'Integer',
        'N2': 'Decimal with 2 places',
        'R': 'Real Number',
    }

    def __init__(self):
        self.codes = edi_codes

    def lookup(self, query: str, detailed: bool = False) -> None:
        """
        Lookup EDI segment, element, or code

        Args:
            query: Segment ID, element ID, or code to lookup
            detailed: Show detailed information
        """
        query = query.upper().strip()

        # Check if it's a segment
        if self._is_segment(query):
            self._lookup_segment(query, detailed)
        # Check if it's an element reference (e.g., NM101)
        elif self._is_element(query):
            self._lookup_element(query, detailed)
        # Check if it's a qualifier code
        elif self._is_code(query):
            self._lookup_code(query, detailed)
        else:
            # Try to search for partial matches
            self._search(query)

    def _is_segment(self, query: str) -> bool:
        """Check if query is a segment ID"""
        return len(query) <= 3 and query.isalpha()

    def _is_element(self, query: str) -> bool:
        """Check if query is an element ID (e.g., NM101)"""
        return re.match(r'^[A-Z]{2,3}\d{2}$', query) is not None

    def _is_code(self, query: str) -> bool:
        """Check if query might be a code value"""
        return len(query) <= 5

    def _lookup_segment(self, segment_id: str, detailed: bool) -> None:
        """Lookup segment information"""
        print(f"\n📋 SEGMENT: {segment_id}")
        print("="*60)

        # Get description
        if segment_id in self.SEGMENT_DESCRIPTIONS:
            print(f"Description: {self.SEGMENT_DESCRIPTIONS[segment_id]}")
        else:
            print("Description: (Custom or less common segment)")

        # Show common elements for known segments
        elements = self._get_segment_elements(segment_id)
        if elements:
            print("\nCommon Elements:")
            for elem_id, elem_desc in elements.items():
                print(f"  {elem_id}: {elem_desc}")

        # Show usage examples
        if detailed:
            examples = self._get_segment_examples(segment_id)
            if examples:
                print("\nExamples:")
                for example in examples:
                    print(f"  {example}")

    def _lookup_element(self, element_id: str, detailed: bool) -> None:
        """Lookup element information"""
        segment_id = element_id[:-2]
        element_num = element_id[-2:]

        print(f"\n🔍 ELEMENT: {element_id}")
        print("="*60)
        print(f"Segment: {segment_id}")
        print(f"Position: {element_num}")

        # Get element description based on segment and position
        element_desc = self._get_element_description(segment_id, element_num)
        if element_desc:
            print(f"Description: {element_desc['description']}")
            if 'type' in element_desc:
                print(f"Data Type: {self.ELEMENT_TYPES.get(element_desc['type'], element_desc['type'])}")
            if 'codes' in element_desc:
                print("\nValid Codes:")
                for code, desc in element_desc['codes'].items():
                    print(f"  {code}: {desc}")

    def _lookup_code(self, code: str, detailed: bool) -> None:
        """Lookup code value"""
        print(f"\n🏷️ CODE: {code}")
        print("="*60)

        found = False

        # Search in various code categories
        code_categories = {
            'claim_status': 'Claim Status',
            'claim_filing': 'Claim Filing Indicator',
            'place_of_service': 'Place of Service',
            'claim_frequency': 'Claim Frequency',
            'entity_type': 'Entity Type',
            'entity_id': 'Entity Identifier',
            'reference_id': 'Reference Identifier',
            'date_qualifier': 'Date/Time Qualifier',
            'amount_qualifier': 'Amount Qualifier Code',
            'adjustment_reason': 'Adjustment Reason',
            'adjustment_group': 'Adjustment Group',
            'remark_code': 'Remark Code',
            'service_type': 'Service Type',
        }

        for category, category_name in code_categories.items():
            if hasattr(self.codes, f'get_{category}_description'):
                desc_func = getattr(self.codes, f'get_{category}_description')
                description = desc_func(code)
                if description and description != code:
                    print(f"{category_name}: {description}")
                    found = True

        if not found:
            print("Code not found in standard code sets")
            print("\nTip: This might be a custom code or specific to your trading partner")

    def _search(self, query: str) -> None:
        """Search for partial matches"""
        print(f"\n🔎 SEARCHING: {query}")
        print("="*60)

        results = []

        # Search segment descriptions
        for seg_id, desc in self.SEGMENT_DESCRIPTIONS.items():
            if query in seg_id or query.lower() in desc.lower():
                results.append(f"Segment {seg_id}: {desc}")

        if results:
            print("\nMatching Segments:")
            for result in results[:10]:
                print(f"  {result}")

        # Search code descriptions
        print("\nSearching code sets...")
        self._search_codes(query)

    def _search_codes(self, query: str) -> None:
        """Search through code sets"""
        # This would search through all code mappings
        # For brevity, showing a simplified version
        print("  (Code search would check all code categories)")

    def _get_segment_elements(self, segment_id: str) -> Dict[str, str]:
        """Get common elements for a segment"""
        elements = {
            'NM1': {
                'NM101': 'Entity Identifier Code (e.g., IL=Insured, 1=Person)',
                'NM102': 'Entity Type Qualifier (1=Person, 2=Non-Person)',
                'NM103': 'Name Last or Organization Name',
                'NM104': 'Name First',
                'NM105': 'Name Middle',
                'NM108': 'Identification Code Qualifier',
                'NM109': 'Identification Code',
            },
            'CLM': {
                'CLM01': 'Claim Submitter Identifier',
                'CLM02': 'Total Claim Charge Amount',
                'CLM05': 'Facility Code + Frequency Code + Claim Type',
                'CLM06': 'Provider Signature on File (Y/N)',
                'CLM07': 'Medicare Assignment Code',
                'CLM08': 'Benefits Assignment Certification',
                'CLM09': 'Release of Information Code',
            },
            'SVC': {
                'SVC01': 'Composite Medical Procedure Identifier',
                'SVC02': 'Monetary Amount (Charge)',
                'SVC03': 'Monetary Amount (Payment)',
                'SVC04': 'National Uniform Billing Committee Revenue Code',
                'SVC05': 'Units of Service Paid Count',
            },
            'CAS': {
                'CAS01': 'Claim Adjustment Group Code',
                'CAS02': 'Claim Adjustment Reason Code',
                'CAS03': 'Monetary Amount',
                'CAS04': 'Quantity',
            },
            'REF': {
                'REF01': 'Reference Identification Qualifier',
                'REF02': 'Reference Identification',
                'REF03': 'Description',
            },
            'DTP': {
                'DTP01': 'Date/Time Qualifier',
                'DTP02': 'Date Time Period Format Qualifier',
                'DTP03': 'Date Time Period',
            },
        }
        return elements.get(segment_id, {})

    def _get_element_description(self, segment_id: str, element_num: str) -> Optional[Dict[str, Any]]:
        """Get detailed element description"""
        # This would normally query a comprehensive element database
        # For demonstration, returning common examples
        common_elements = {
            'NM101': {
                'description': 'Entity Identifier Code',
                'type': 'ID',
                'codes': {
                    'IL': 'Insured or Subscriber',
                    'PR': 'Payer',
                    '1': 'Person',
                    '2': 'Non-Person Entity',
                    '40': 'Receiver',
                    '41': 'Submitter',
                    '85': 'Billing Provider',
                    'PE': 'Payee',
                    'DN': 'Referring Provider',
                }
            },
            'CLM05-1': {
                'description': 'Facility Code Value',
                'type': 'ID',
                'codes': {
                    '11': 'Office',
                    '12': 'Home',
                    '21': 'Inpatient Hospital',
                    '22': 'Outpatient Hospital',
                    '23': 'Emergency Room',
                    '81': 'Independent Laboratory',
                }
            }
        }

        element_key = f"{segment_id}{element_num}"
        return common_elements.get(element_key)

    def _get_segment_examples(self, segment_id: str) -> List[str]:
        """Get usage examples for a segment"""
        examples = {
            'NM1': [
                'NM1*IL*1*SMITH*JOHN****MI*123456789~',
                'NM1*PR*2*UNITED HEALTHCARE*****PI*87726~',
                'NM1*85*2*FAMILY MEDICAL CENTER*****XX*1234567890~',
            ],
            'CLM': [
                'CLM*26463774*100***11:B:1*Y*A*Y*Y~',
                'CLM*PATIENT123*5000***22:B:1*Y*A*Y*Y~',
            ],
            'SVC': [
                'SVC*HC:99213*100*80**1~',
                'SVC*HC:93000*500*400**1~',
            ],
        }
        return examples.get(segment_id, [])

    def interactive_mode(self) -> None:
        """Start interactive lookup mode"""
        print("\n" + "="*80)
        print("📚 EDI SEGMENT & CODE LOOKUP")
        print("="*80)
        print("\nType segment IDs (e.g., NM1), element IDs (e.g., NM101),")
        print("or codes to lookup. Type 'help' for more info, 'quit' to exit.\n")

        while True:
            try:
                query = input("lookup> ").strip()

                if not query:
                    continue

                if query.lower() in ['quit', 'exit', 'q']:
                    break
                elif query.lower() in ['help', 'h', '?']:
                    self._show_help()
                elif query.lower() == 'segments':
                    self._list_segments()
                elif query.lower() == 'codes':
                    self._list_code_categories()
                else:
                    self.lookup(query, detailed=True)

            except (EOFError, KeyboardInterrupt):
                print("\n")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        print("\n👋 Goodbye!")

    def _show_help(self) -> None:
        """Show help information"""
        print("""
📚 LOOKUP COMMANDS:

Lookups:
  <segment>   - Lookup segment (e.g., NM1, CLM, SVC)
  <element>   - Lookup element (e.g., NM101, CLM02)
  <code>      - Lookup code value (e.g., IL, PR, 22)

Commands:
  segments    - List common segments
  codes       - List code categories
  help        - Show this help
  quit        - Exit lookup tool

Examples:
  NM1         - Show NM1 segment details
  NM101       - Show NM1 element 01 details
  IL          - Lookup code "IL"
  claim       - Search for "claim" related items
        """)

    def _list_segments(self) -> None:
        """List common segments"""
        print("\n📋 COMMON EDI SEGMENTS:")
        print("-"*60)

        categories = {
            'Control': ['ISA', 'IEA', 'GS', 'GE', 'ST', 'SE'],
            'Heading': ['BHT', 'REF', 'DTP'],
            'Party': ['NM1', 'N3', 'N4', 'PER', 'DMG'],
            'Claim': ['CLM', 'HI', 'SV1', 'SV2', 'DTP', 'REF'],
            'Payment': ['CLP', 'CAS', 'SVC', 'DTM', 'AMT'],
        }

        for category, segments in categories.items():
            print(f"\n{category}:")
            for seg in segments:
                desc = self.SEGMENT_DESCRIPTIONS.get(seg, "")
                if desc:
                    # Truncate long descriptions
                    desc = desc[:50] + "..." if len(desc) > 50 else desc
                    print(f"  {seg:4} - {desc}")

    def _list_code_categories(self) -> None:
        """List code categories"""
        print("\n🏷️ CODE CATEGORIES:")
        print("-"*60)

        categories = [
            ('Entity Identifiers', 'NM101 codes like IL, PR, 85'),
            ('Date Qualifiers', 'DTP01 codes for date types'),
            ('Reference Qualifiers', 'REF01 codes for reference types'),
            ('Adjustment Groups', 'CAS01 codes like CO, PR, OA'),
            ('Adjustment Reasons', 'CAS02 reason codes'),
            ('Place of Service', 'CLM05-1 facility codes'),
            ('Claim Status', 'CLP02 status codes'),
        ]

        for name, description in categories:
            print(f"  {name:20} - {description}")


def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(
        description='EDI Segment Lookup - Quick reference for EDI segments and codes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
        Examples:
          %(prog)s NM1            # Lookup NM1 segment
          %(prog)s NM101          # Lookup NM1 element 01
          %(prog)s IL             # Lookup code "IL"
          %(prog)s --interactive  # Start interactive mode

        Interactive Commands:
          NM1       - Show segment details
          NM101     - Show element details
          IL        - Lookup code value
          segments  - List common segments
          codes     - List code categories
          help      - Show help
          quit      - Exit
        ''')
    )

    parser.add_argument('query', nargs='?',
                       help='Segment, element, or code to lookup')
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Start interactive lookup mode')
    parser.add_argument('-d', '--detailed', action='store_true',
                       help='Show detailed information')

    args = parser.parse_args()

    # Create lookup tool
    lookup = SegmentLookup()

    if args.interactive or not args.query:
        # Start interactive mode
        lookup.interactive_mode()
    else:
        # Single lookup
        lookup.lookup(args.query, detailed=args.detailed)


if __name__ == '__main__':
    main()