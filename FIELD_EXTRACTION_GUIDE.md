# PyEDI Field Extraction Quick Reference

## Enhanced Segments - What's Extracted

### 835 Payment Segments

#### BPR - Financial Information
```python
{
  "transaction_handling": "Remittance Information Only",  # Decoded from "I"
  "total_payment_amount": 132.0,                         # Float conversion
  "credit_debit": "Credit",                              # Decoded from "C"
  "payment_method": "Check",                             # Decoded from "CHK"
  "payment_date": "2019-03-31"                          # Formatted date
}
```

#### CLP - Claim Payment
```python
{
  "patient_control_number": "7722337",
  "claim_status": "Processed as Primary",               # Decoded from "1"
  "total_charge_amount": 226.0,
  "total_payment_amount": 132.0,
  "patient_responsibility_amount": 10.0,
  "claim_filing": "Preferred Provider Organization (PPO)",  # Decoded from "12"
  "facility_type": "Office",                            # Decoded from "11"
  "drg_code": "025",
  "drg_weight": 0.5
}
```

#### CAS - Claim Adjustments
```python
{
  "adjustment_group_code": "CO",
  "adjustment_group": "Contractual Obligations",
  "adjustments": [
    {
      "reason_code": "197",
      "reason": "Precertification/authorization/notification absent",
      "amount": 2000.0,
      "quantity": 1
    },
    {
      "reason_code": "45",
      "reason": "Charge exceeds fee schedule/maximum allowable",
      "amount": 30000.0
    }
  ]
}
```

#### SVC - Service Payment
```python
{
  "procedure_qualifier": "HC",
  "procedure_code": "99213",
  "procedure_modifiers": ["26", "27"],                   # Unpacked from composite
  "line_charge_amount": 100.0,
  "line_payment_amount": 80.0,
  "revenue_code": "0022",
  "revenue_description": "Skilled nursing facility prospective payment system (HIPPS)",
  "units_paid": 1.0
}
```

#### AMT - Amount (Qualifier-Based)
```python
# AMT*AU*132~ becomes:
{
  "amount_qualifier": "AU",
  "amount_type": "Coverage Amount",                      # Smart naming
  "amount": 132.0
}

# AMT*D8*100~ becomes:
{
  "amount_qualifier": "D8",
  "amount_type": "Discount Amount",                      # Smart naming
  "amount": 100.0
}
```

#### QTY - Quantity (Qualifier-Based)
```python
# QTY*CA*4~ becomes:
{
  "quantity_qualifier": "CA",
  "quantity_type": "Covered - Actual",                   # Smart naming
  "quantity": 4.0
}
```

### 837 Claim Segments

#### CLM - Claim Information
```python
{
  "patient_control_number": "26463774",
  "total_charge_amount": 100.0,
  "facility_code": "11",                                 # Unpacked from CLM05
  "place_of_service": "Office",                          # Decoded
  "frequency_code": "1",                                 # Unpacked from CLM05
  "claim_type_code": "B",                                # Unpacked from CLM05
  "provider_signature_indicator": "Y",
  "assignment_participation_code": "A",
  "release_of_information_code": "Y"
}
```

#### PWK - Paperwork/Attachments
```python
{
  "report_type_code": "OZ",
  "report_transmission_code": "BM",
  "attachment_control_number": "DMN0012"
}
```

## Code Lookups

### Place of Service Codes
- `11` → "Office"
- `12` → "Home"
- `21` → "Inpatient Hospital"
- `22` → "On Campus-Outpatient Hospital"
- `23` → "Emergency Room – Hospital"
- `31` → "Skilled Nursing Facility"
- `81` → "Independent Laboratory"

### Claim Status Codes
- `1` → "Processed as Primary"
- `2` → "Processed as Secondary"
- `3` → "Processed as Tertiary"
- `4` → "Denied"
- `5` → "Pended"

### Claim Filing Indicator Codes
- `12` → "Preferred Provider Organization (PPO)"
- `13` → "Point of Service (POS)"
- `14` → "Exclusive Provider Organization (EPO)"
- `15` → "Indemnity Insurance"
- `16` → "Health Maintenance Organization (HMO) Medicare Risk"
- `MB` → "Medicare Part B"
- `MC` → "Medicaid"
- `CI` → "Commercial Insurance Co."

### Adjustment Group Codes
- `CO` → "Contractual Obligations"
- `CR` → "Correction and Reversals"
- `OA` → "Other Adjustments"
- `PI` → "Payor Initiated Reductions"
- `PR` → "Patient Responsibility"

### Common Adjustment Reason Codes
- `1` → "Deductible"
- `2` → "Coinsurance"
- `3` → "Co-payment"
- `45` → "Charge exceeds fee schedule/maximum allowable"
- `97` → "Benefit for this service is included in payment/allowance"
- `131` → "Claim specific negotiated discount"
- `197` → "Precertification/authorization/notification absent"

## Usage Examples

### Extract Payment Information
```python
from pyedi import X12Parser, StructuredFormatter

# Parse 835 payment file
parser = X12Parser()
formatter = StructuredFormatter()

generic = parser.parse("payment_835.edi")
structured = formatter.format(generic)

# Access payment details
payment_info = structured['heading']['financial_information_loop']['financial_information_BPR']
print(f"Payment Amount: ${payment_info['total_payment_amount']}")
print(f"Payment Method: {payment_info['payment_method']}")
print(f"Payment Date: {payment_info['payment_date']}")
```

### Extract Claim Adjustments
```python
# Find all claim adjustments
for segment in structured['detail'].values():
    if isinstance(segment, dict) and 'adjustment_group' in segment:
        print(f"Adjustment Group: {segment['adjustment_group']}")
        for adj in segment.get('adjustments', []):
            print(f"  Reason: {adj['reason']}")
            print(f"  Amount: ${adj['amount']}")
```

### Extract Service Line Details
```python
# Find service payment information
for key, value in structured['detail'].items():
    if 'svc' in key.lower() and isinstance(value, dict):
        if 'procedure_code' in value:
            print(f"Procedure: {value['procedure_code']}")
            print(f"Charge: ${value['line_charge_amount']}")
            print(f"Paid: ${value['line_payment_amount']}")
            if 'procedure_modifiers' in value:
                print(f"Modifiers: {value['procedure_modifiers']}")
```

### Map to Target Schema with JSONata
```python
from pyedi import SchemaMapper

# Define mapping for your target schema
mapping = {
    "name": "Payment Mapping",
    "mapping_type": "only_mapped",
    "expressions": {
        "paymentAmount": "$.heading.financial_information_loop.financial_information_BPR.total_payment_amount",
        "paymentMethod": "$.heading.financial_information_loop.financial_information_BPR.payment_method",
        "paymentDate": "$.heading.financial_information_loop.financial_information_BPR.payment_date",
        "claims": "$.detail.clp.{
            'patientControlNumber': patient_control_number,
            'status': claim_status,
            'chargeAmount': total_charge_amount,
            'paidAmount': total_payment_amount,
            'facilityType': facility_type
        }"
    }
}

mapper = SchemaMapper(mapping)
target_json = mapper.map(structured)
```

## Testing Your Extraction

Run the test suite to verify all fields are extracted:

```bash
python3 tests/test_enhanced_extraction.py
```

Expected output:
```
✅ 837P Extraction: PASSED
✅ 835 Extraction: PASSED
✅ All tests passed!
```

## Debugging Tools

Use the debugging tools to inspect extraction:

```bash
# Visual EDI structure inspector
python3 debug_tools/edi_inspector.py your_file.edi -v

# Step-through pipeline debugger
python3 debug_tools/pipeline_debugger.py your_file.edi --save

# Test JSONata expressions
python3 debug_tools/jsonata_tester.py structured.json

# Look up segment/code meanings
python3 debug_tools/segment_lookup.py NM1
python3 debug_tools/segment_lookup.py --interactive

# Profile performance
python3 debug_tools/performance_profiler.py your_file.edi
```

## Key Takeaways

1. **All segments are extracted** - Parser captures everything
2. **Enhanced formatting** - Complex segments get special handling
3. **Human-readable codes** - Codes are decoded to descriptions
4. **Composite unpacking** - Multi-part fields are separated
5. **Smart naming** - Fields named based on qualifiers/context
6. **Type conversion** - Amounts are floats, dates are formatted
7. **Complete testing** - Verified with official test files

PyEDI now provides complete, production-ready extraction of all fields from 837 and 835 EDI transactions!