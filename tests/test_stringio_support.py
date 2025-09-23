#!/usr/bin/env python3
"""
Test script for StringIO/string support in pyedi package
"""

import json
from io import StringIO
from pyedi import X12Pipeline
from pyedi.core.parser import X12Parser
from pyedi.core.mapper import SchemaMapper

# Sample EDI content (835 remittance advice)
edi_content = """ISA*00*          *00*          *ZZ*CLEARINGHOUSE  *ZZ*123456789      *220101*1200*^*00501*000000001*0*P*:~
GS*HP*CLEARINGHOUSE*123456789*20220101*1200*1*X*005010X221A1~
ST*835*0001*005010X221A1~
BPR*I*40.00*C*CHK*CTX*01*123456789*DA*987654321*1234567890**01*987654321*DA*20250925*CHK123456~
TRN*1*CHK123456*1234567890~
N1*PR*UNITED HEALTHCARE~
N3*PO BOX 12345~
N4*ATLANTA*GA*30348~
N1*PE*FAMILY HEALTH ASSOCIATES*XX*1234567890~
LX*1~
CLP*FHA20250920001*1*190.00*40.00*150.00*MC*CLAIMNUMBER123*11*1~
NM1*QC*1*MARTINEZ*JENNIFER****MI*UHC123456789~
NM1*82*2*FAMILY HEALTH ASSOCIATES*****XX*1234567890~
DTM*232*20250920~
DTM*233*20250920~
SVC*HC:99213*190.00*40.00**1~
DTM*472*20250920~
CAS*PR*1*150.00~
SE*18*0001~
GE*1*1~
IEA*1*000000001~"""

# Sample mapping definition
mapping_def = {
    "name": "835_to_custom",
    "mapping_type": "only_mapped",
    "expressions": {
        "transaction_type": "transaction_type",
        "payment_amount": "payment_information.amount",
        "payment_method": "payment_information.method_code",
        "check_number": "payment_information.check_number",
        "payment_date": "payment_information.date",
        "payer_name": "payer_identification.name",
        "payee_name": "payee_identification.name",
        "claim_number": "claims[0].claim_id",
        "claim_status": "claims[0].status_code_description",
        "patient_name": "claims[0].patient.name_formatted",
        "total_charge": "claims[0].charge_amount",
        "total_paid": "claims[0].payment_amount"
    }
}

def test_string_input():
    """Test EDI content as string input"""
    print("=" * 60)
    print("Testing EDI content as string input...")
    print("=" * 60)

    pipeline = X12Pipeline()

    # Test with EDI as string and mapping as dict
    result = pipeline.transform(
        edi_file=edi_content,  # String EDI content
        mapping=mapping_def     # Dict mapping
    )

    print("Result from string input:")
    print(json.dumps(result, indent=2))
    print("\nSuccess: String input processed correctly\n")

    return result

def test_stringio_input():
    """Test EDI content as StringIO input"""
    print("=" * 60)
    print("Testing EDI content as StringIO input...")
    print("=" * 60)

    pipeline = X12Pipeline()

    # Create StringIO objects
    edi_io = StringIO(edi_content)
    mapping_json = json.dumps(mapping_def)
    mapping_io = StringIO(mapping_json)

    # Test with both EDI and mapping as StringIO
    result = pipeline.transform(
        edi_file=edi_io,      # StringIO EDI content
        mapping=mapping_io     # StringIO mapping
    )

    print("Result from StringIO input:")
    print(json.dumps(result, indent=2))
    print("\nSuccess: StringIO input processed correctly\n")

    return result

def test_parser_direct():
    """Test X12Parser directly with string and StringIO"""
    print("=" * 60)
    print("Testing X12Parser directly...")
    print("=" * 60)

    parser = X12Parser()

    # Test with string
    print("Parsing from string...")
    result1 = parser.parse(edi_content)
    print(f"Parsed {len(result1['transactions'])} transaction(s) from string")

    # Test with StringIO
    print("Parsing from StringIO...")
    edi_io = StringIO(edi_content)
    result2 = parser.parse(edi_io)
    print(f"Parsed {len(result2['transactions'])} transaction(s) from StringIO")

    print("\nSuccess: Parser handles both string and StringIO\n")

    return result1, result2

def test_mapper_direct():
    """Test SchemaMapper directly with string and StringIO"""
    print("=" * 60)
    print("Testing SchemaMapper directly...")
    print("=" * 60)

    # Test mapping initialization with string
    mapping_json = json.dumps(mapping_def)
    mapper1 = SchemaMapper(mapping_json)
    print(f"Mapper created from JSON string: {mapper1.name}")

    # Test mapping initialization with StringIO
    mapping_io = StringIO(mapping_json)
    mapper2 = SchemaMapper(mapping_io)
    print(f"Mapper created from StringIO: {mapper2.name}")

    # Test mapping with source as StringIO
    source_data = {"test": "data", "value": 123}
    source_json = json.dumps(source_data)
    source_io = StringIO(source_json)

    result = mapper2.map(source_io)
    print(f"Mapped from StringIO source: {result}")

    print("\nSuccess: Mapper handles string and StringIO\n")

    return mapper1, mapper2

def test_mixed_inputs():
    """Test various combinations of input types"""
    print("=" * 60)
    print("Testing mixed input types...")
    print("=" * 60)

    pipeline = X12Pipeline()

    # Test 1: String EDI, JSON string mapping
    mapping_json = json.dumps(mapping_def)
    result1 = pipeline.transform(edi_content, mapping_json)
    print("✓ String EDI + JSON string mapping")

    # Test 2: StringIO EDI, dict mapping
    edi_io = StringIO(edi_content)
    result2 = pipeline.transform(edi_io, mapping_def)
    print("✓ StringIO EDI + dict mapping")

    # Test 3: String EDI, StringIO mapping
    mapping_io = StringIO(mapping_json)
    result3 = pipeline.transform(edi_content, mapping_io)
    print("✓ String EDI + StringIO mapping")

    # Test 4: No mapping (structured output only)
    result4 = pipeline.transform(edi_content, mapping=None)
    print("✓ String EDI + no mapping (structured only)")

    print("\nSuccess: All mixed input combinations work\n")

    return result1, result2, result3, result4

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("TESTING STRINGIO/STRING SUPPORT IN PYEDI")
    print("=" * 60 + "\n")

    try:
        # Run all tests
        test_parser_direct()
        test_mapper_direct()
        test_string_input()
        test_stringio_input()
        test_mixed_inputs()

        print("=" * 60)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())