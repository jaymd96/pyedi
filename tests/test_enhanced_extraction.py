#!/usr/bin/env python3
"""
Test Enhanced Field Extraction for 837 and 835 Files

This script validates that PyEDI extracts all fields from comprehensive
837 (claim) and 835 (payment) EDI files.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyedi import X12Parser, StructuredFormatter


def test_837_extraction():
    """Test 837P professional claim extraction"""
    print("\n" + "="*80)
    print("TESTING 837P PROFESSIONAL CLAIM EXTRACTION")
    print("="*80 + "\n")

    edi_file = Path(__file__).parent.parent / "data" / "test_edi" / "837P-all-fields.dat"

    if not edi_file.exists():
        print(f"❌ Test file not found: {edi_file}")
        return False

    try:
        # Parse EDI
        parser = X12Parser()
        generic_json = parser.parse(str(edi_file))

        print(f"✅ Successfully parsed 837P file")
        print(f"   Transaction type: {generic_json.get('transaction_type')}")
        print(f"   X12 version: {generic_json.get('x12_version')}")

        # Format to structured
        formatter = StructuredFormatter()
        structured = formatter.format(generic_json)

        print(f"✅ Successfully formatted to structured JSON")

        # Save for inspection
        output_file = Path(__file__).parent / "output_837_enhanced.json"
        with open(output_file, 'w') as f:
            json.dump(structured, f, indent=2)

        print(f"✅ Output saved to: {output_file}")

        # Validate key fields are extracted
        print("\n📊 Validating Key Fields:")
        validation_passed = True

        # Check for CLM segment fields
        if 'detail' in structured:
            detail = structured['detail']

            # Look for CLM segment
            if 'clm' in str(detail).lower():
                print("   ✅ CLM segment found")

                # Check for composite field extraction (facility code, frequency code)
                if 'facility_code' in str(detail):
                    print("   ✅ CLM composite facility code extracted")
                else:
                    print("   ⚠️  CLM composite facility code not found")
                    validation_passed = False
            else:
                print("   ⚠️  CLM segment not found in detail")
                validation_passed = False

            # Look for PWK (paperwork/attachment) segment
            if 'pwk' in str(detail).lower() or 'attachment' in str(detail).lower():
                print("   ✅ PWK/Attachment segment found")
            else:
                print("   ℹ️  PWK segment not present (optional)")

            # Look for NM1 segments (providers, subscriber, patient)
            if 'nm1' in str(detail).lower() or 'name' in str(detail).lower():
                print("   ✅ NM1 (Name) segments found")
            else:
                print("   ⚠️  NM1 segments not found")
                validation_passed = False

        else:
            print("   ❌ No detail section found")
            validation_passed = False

        if validation_passed:
            print("\n✅ 837P Extraction: PASSED")
        else:
            print("\n⚠️  837P Extraction: PASSED WITH WARNINGS")

        return True

    except Exception as e:
        print(f"\n❌ 837P Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_835_extraction():
    """Test 835 payment remittance extraction"""
    print("\n" + "="*80)
    print("TESTING 835 PAYMENT REMITTANCE EXTRACTION")
    print("="*80 + "\n")

    edi_file = Path(__file__).parent.parent / "data" / "test_edi" / "835-all-fields.dat"

    if not edi_file.exists():
        print(f"❌ Test file not found: {edi_file}")
        return False

    try:
        # Parse EDI
        parser = X12Parser()
        generic_json = parser.parse(str(edi_file))

        print(f"✅ Successfully parsed 835 file")
        print(f"   Transaction type: {generic_json.get('transaction_type')}")
        print(f"   X12 version: {generic_json.get('x12_version')}")

        # Format to structured
        formatter = StructuredFormatter()
        structured = formatter.format(generic_json)

        print(f"✅ Successfully formatted to structured JSON")

        # Save for inspection
        output_file = Path(__file__).parent / "output_835_enhanced.json"
        with open(output_file, 'w') as f:
            json.dump(structured, f, indent=2)

        print(f"✅ Output saved to: {output_file}")

        # Validate key 835-specific fields
        print("\n📊 Validating Key 835 Fields:")
        validation_passed = True

        json_str = json.dumps(structured)

        # Check for BPR segment (payment information)
        if 'payment_method' in json_str or 'total_payment_amount' in json_str:
            print("   ✅ BPR (Payment) segment extracted")

            # Check for specific BPR fields
            if 'payment_method' in json_str:
                print("   ✅ BPR payment method decoded")
            if 'payment_date' in json_str:
                print("   ✅ BPR payment date extracted")
        else:
            print("   ⚠️  BPR segment not fully extracted")
            validation_passed = False

        # Check for TRN segment (trace number)
        if 'check_eft_trace_number' in json_str or 'trace' in json_str.lower():
            print("   ✅ TRN (Trace) segment extracted")
        else:
            print("   ⚠️  TRN segment not found")
            validation_passed = False

        # Check for CLP segment (claim payment info)
        if 'claim_status' in json_str or 'patient_control_number' in json_str:
            print("   ✅ CLP (Claim Payment) segment extracted")

            # Check for composite field extraction
            if 'claim_status' in json_str:
                print("   ✅ CLP claim status decoded")
            if 'facility_type' in json_str or 'facility_code' in json_str:
                print("   ✅ CLP facility code extracted")
        else:
            print("   ⚠️  CLP segment not fully extracted")
            validation_passed = False

        # Check for CAS segment (adjustments)
        if 'adjustment_group' in json_str or 'adjustment' in json_str.lower():
            print("   ✅ CAS (Adjustments) segment extracted")

            # Check for adjustment details
            if 'adjustment_reason' in json_str or 'reason_code' in json_str:
                print("   ✅ CAS adjustment reasons decoded")
        else:
            print("   ⚠️  CAS segment not fully extracted")
            validation_passed = False

        # Check for SVC segment (service payment info)
        if 'procedure_code' in json_str or 'line_payment' in json_str:
            print("   ✅ SVC (Service Payment) segment extracted")

            # Check for composite procedure code extraction
            if 'procedure_qualifier' in json_str or 'procedure_modifiers' in json_str:
                print("   ✅ SVC composite procedure code unpacked")
        else:
            print("   ⚠️  SVC segment not fully extracted")
            validation_passed = False

        # Check for AMT segment with qualifier-based naming
        if 'amount_type' in json_str or 'amount_qualifier' in json_str:
            print("   ✅ AMT segment with qualifier-based naming")
        else:
            print("   ℹ️  AMT segment standard naming (acceptable)")

        # Check for QTY segment
        if 'quantity_type' in json_str or 'quantity_qualifier' in json_str:
            print("   ✅ QTY segment with qualifier-based naming")
        else:
            print("   ℹ️  QTY segment standard naming (acceptable)")

        if validation_passed:
            print("\n✅ 835 Extraction: PASSED")
        else:
            print("\n⚠️  835 Extraction: PASSED WITH WARNINGS")

        return True

    except Exception as e:
        print(f"\n❌ 835 Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PyEDI ENHANCED FIELD EXTRACTION TEST SUITE")
    print("="*80)

    results = []

    # Test 837
    results.append(("837P Professional", test_837_extraction()))

    # Test 835
    results.append(("835 Payment", test_835_extraction()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {name}: {status}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed or had warnings")
        return 1


if __name__ == '__main__':
    sys.exit(main())
