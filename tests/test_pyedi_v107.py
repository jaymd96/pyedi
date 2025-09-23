#!/usr/bin/env python3
"""
Test PyEDI v1.0.7 features
"""

import json
from io import StringIO
from pyedi import X12Parser, StructuredFormatter

# Sample EDI
sample_edi = """ISA*00*          *00*          *ZZ*HEALTHPLAN123  *ZZ*PROVIDER456    *210901*1200*U*00501*000000001*0*P*:~
GS*HC*HEALTHPLAN123*PROVIDER456*20210901*1200*1*X*005010X222A1~
ST*837*0001*005010X222A1~
BHT*0019*00*REF123456*20210901*1200*CH~
NM1*41*2*UNITED HEALTHCARE*****46*87726~
NM1*40*2*PROVIDER CORP*****46*12345~
HL*1**20*1~
NM1*85*2*FAMILY MEDICAL CENTER*****XX*1234567890~
HL*2*1*22*0~
SBR*P*18*******CI~
NM1*IL*1*SMITH*JOHN****MI*987654321~
CLM*CLM789123*450.50***11:B:1*Y*A*Y*Y~
DTP*472*D8*20210901~
HI*ABK:J449~
LX*1~
SV1*HC:99213*150.50*UN*1***1~
LX*2~
SV1*HC:93000*300.00*UN*1***2~
SE*18*0001~
GE*1*1~
IEA*1*000000001~"""

print("Testing PyEDI v1.0.7...")
print("-" * 60)

# Test StringIO support
print("1. Testing StringIO input support (new in v1.0.7)...")
parser = X12Parser()
formatter = StructuredFormatter()

edi_stream = StringIO(sample_edi)
generic_json = parser.parse(edi_stream)

print(f"✓ Successfully parsed from StringIO")
print(f"  Transaction type: {generic_json.get('transaction_type')}")
print(f"  Number of transactions: {len(generic_json.get('transactions', []))}")

# Format to structured
print("\n2. Testing StructuredFormatter...")
structured = formatter.format(generic_json)

# Save for inspection
with open('test_structured_output.json', 'w') as f:
    json.dump(structured, f, indent=2)

print(f"✓ Structured output saved to test_structured_output.json")

# Check structure
if isinstance(structured, list):
    print(f"  Returned list with {len(structured)} transactions (multi-transaction support)")
    structured = structured[0]
else:
    print(f"  Returned single transaction")

# Print key fields
print("\n3. Checking key fields in structured output:")
print(f"  Transaction type: {structured.get('transaction_type')}")

if 'interchange' in structured:
    print(f"  Sender ID: {structured['interchange'].get('interchange_sender_id')}")
    print(f"  Receiver ID: {structured['interchange'].get('interchange_receiver_id')}")

if 'heading' in structured:
    heading = structured['heading']
    for key in heading:
        if 'name' in key.lower():
            print(f"  Found heading segment: {key}")

if 'detail' in structured:
    detail = structured['detail']
    for key in detail:
        print(f"  Found detail segment: {key}")

print("\n✓ Test complete!")