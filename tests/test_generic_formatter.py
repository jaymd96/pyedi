#!/usr/bin/env python3
"""Test the generic StructuredFormatter with sample EDI messages"""

import json
import sys
import os

# Add the project to the path
sys.path.insert(0, os.path.dirname(__file__))

from pyedi import X12Parser, format_structured

# Test with 834 message matching the example
edi_834 = """ISA*00*          *00*          *ZZ*SENDERNAME     *ZZ*RECEIVERNAME   *041227*1324*^*00501*000000103*0*P*>~
GS*BE*SENDERNAME*RECEIVERNAME*20041227*1324*000000103*X*005010X220A1~
ST*834*12345*005010X220A1~
BGN*00*12456*19980520*1200****2~
REF*38*ABCD012354~
N1*P5**FI*999888777~
N1*IN**FI*654456654~
INS*N*19*024*07*A~
REF*0F*123456789~
REF*1L*123456001~
DTP*357*D8*19960801~
NM1*IL*1*DOE*JAMES*E***34*103229876~
DMG*D8*19770816*M~
SE*12*12345~
GE*1*000000103~
IEA*1*000000103~"""

# Test with 835 message
edi_835 = """ISA*00*          *00*          *ZZ*AETNA          *ZZ*WECARE         *240102*1200*^*00501*000000001*0*P*:~
GS*HP*AETNA*WECARE*20240102*1200*1*X*005010X221A1~
ST*835*0001~
BPR*C*12500.00*C*CHK************20240102~
TRN*1*123456789*1234567890~
N1*PR*AETNA INSURANCE~
N3*123 PAYER STREET~
N4*HARTFORD*CT*06101~
N1*PE*WECARE CLINIC*XX*1234567890~
CLP*PATIENT123*1*15000.00*12500.00*2500.00*MC*987654321*11~
NM1*QC*1*DOE*JANE****MI*ABC123456~
SVC*HC:99213*150.00*120.00**1~
CAS*PR*1*30.00~
SE*13*0001~
GE*1*1~
IEA*1*000000001~"""

def test_formatter(edi_message, label):
    print(f"\n{'='*60}")
    print(f"Testing {label}")
    print('='*60)

    try:
        # Parse the EDI - write to temp file since parser expects a file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.edi', delete=False) as f:
            f.write(edi_message)
            temp_file = f.name

        parser = X12Parser()
        parsed = parser.parse(temp_file)

        # Clean up temp file
        os.unlink(temp_file)

        # Format with the new generic formatter
        structured = format_structured(parsed)

        # Print the result
        print(json.dumps(structured, indent=2))

        # Check specific fields for validation
        if label == "834":
            print("\n✓ Key fields extracted:")
            heading = structured.get('heading', {})
            bgn = heading.get('beginning_segment_bgn', {})
            print(f"  - Transaction purpose: {bgn.get('transaction_set_purpose_code_01')}")
            print(f"  - Reference number: {bgn.get('transaction_set_reference_number_02')}")
            print(f"  - Creation date: {bgn.get('transaction_set_creation_date_03')}")

            detail = structured.get('detail', {})
            if 'member_level_detail_ins_loop' in detail:
                member_loop = detail['member_level_detail_ins_loop']
                if isinstance(member_loop, list) and member_loop:
                    member = member_loop[0].get('member_name_nm1', {})
                    print(f"  - Member name: {member.get('member_last_name_03')} {member.get('member_first_name_04')}")

        elif label == "835":
            print("\n✓ Key fields extracted:")
            heading = structured.get('heading', {})
            bpr = heading.get('financial_information_bpr', {})
            print(f"  - Payment amount: {bpr.get('monetary_amount_02')}")
            print(f"  - Payment date: {bpr.get('date_16') or bpr.get('date_17')}")

            trn = heading.get('trace_trn', {})
            print(f"  - Check/EFT number: {trn.get('reference_identification_02')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Run tests
test_formatter(edi_834, "834")
test_formatter(edi_835, "835")