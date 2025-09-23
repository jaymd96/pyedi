#!/usr/bin/env python3
"""Test the new StructuredFormatter output format"""

import sys
import os
import json
import tempfile

# Add parent directory to path
sys.path.insert(0, '/Users/james/Projects/HarmonyHealth/x12_edi_converter')

from pyedi import X12Parser, StructuredFormatter

# Sample 835 EDI
edi_835 = """ISA*00*          *00*          *ZZ*UNITEDHC       *ZZ*FAMILYHEALTH   *250925*0800*^*00501*835000001*0*P*:~
GS*HP*UNITEDHC*FAMILYHEALTH*20250925*0800*1*X*005010X221A1~
ST*835*0001*005010X221A1~
BPR*I*1500.00*C*CHK*CCP*01*123456789*DA*987654321*1234567890**01*555666777*DA*777888999~
TRN*1*123456789*1555666777*987654321~
DTM*405*20250924~
N1*PR*UNITED HEALTHCARE~
N3*123 INSURANCE WAY~
N4*MINNEAPOLIS*MN*55401~
N1*PE*FAMILY HEALTH CLINIC*XX*1234567890~
LX*1~
CLP*CLM001*1*800*600*200*MC*CLAIM123456*21**41~
NM1*QC*1*SMITH*JOHN*A***MI*MEM001~
DTM*232*20250920~
DTM*233*20250920~
AMT*AU*800~
SE*16*0001~
GE*1*1~
IEA*1*835000001~"""

# Sample 837 EDI
edi_837 = """ISA*00*          *00*          *ZZ*FAMILYHEALTH   *ZZ*BCBSIL         *250925*0800*^*00501*837000001*0*P*:~
GS*HC*FAMILYHEALTH*BCBSIL*20250925*0800*1*X*005010X222A1~
ST*837*0001*005010X222A1~
BHT*0019*00*123456*20250925*0800*CH~
NM1*41*2*FAMILY HEALTH CLINIC*****46*1234567890~
PER*IC*BILLING DEPT*TE*5555551234~
NM1*40*2*BLUE CROSS BLUE SHIELD IL*****46*BCBSIL~
HL*1**20*1~
NM1*85*2*FAMILY HEALTH CLINIC*****XX*1234567890~
N3*456 MEDICAL CENTER DR~
N4*CHICAGO*IL*60601~
REF*EI*987654321~
HL*2*1*22*1~
SBR*P********CI~
NM1*IL*1*DOE*JANE****MI*SUB123456~
N3*789 PATIENT ST~
N4*CHICAGO*IL*60602~
DMG*D8*19800515*F~
HL*3*2*23*0~
PAT*19~
NM1*QC*1*DOE*JANE~
N3*789 PATIENT ST~
N4*CHICAGO*IL*60602~
CLM*CLAIM789*350***11:B:1*Y*A*Y*Y~
DTP*434*RD8*20250920-20250920~
HI*ABK:I10~
LX*1~
SV1*HC:99213*150*UN*1***1~
DTP*472*D8*20250920~
LX*2~
SV1*HC:85025*50*UN*1***1~
DTP*472*D8*20250920~
SE*31*0001~
GE*1*1~
IEA*1*837000001~"""

def test_formatter(edi_content, transaction_type):
    """Test the formatter with the given EDI content"""
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edi', delete=False) as temp_file:
        temp_file.write(edi_content)
        temp_file_path = temp_file.name
    
    try:
        # Parse the EDI
        parser = X12Parser()
        generic_json = parser.parse(temp_file_path)
        
        print(f"\n{'='*60}")
        print(f"Testing {transaction_type} Transaction")
        print(f"{'='*60}")
        
        # Check what's in generic_json
        print("\nGeneric JSON keys:", list(generic_json.keys()))
        print("Transaction type:", generic_json.get('transaction_type'))
        print("Map file:", generic_json.get('map_file'))
        
        # Format to structured
        formatter = StructuredFormatter()
        structured_json = formatter.format(generic_json)
        
        print("\nStructured JSON keys:", list(structured_json.keys()))
        
        # Show sample of the output structure
        if 'heading' in structured_json:
            print("\nHeading section keys:", list(structured_json['heading'].keys())[:5])
            
            # Show a sample segment
            for key, value in list(structured_json['heading'].items())[:2]:
                print(f"\n{key}:")
                if isinstance(value, dict):
                    for field, field_value in list(value.items())[:3]:
                        print(f"  {field}: {field_value}")
                elif isinstance(value, list) and len(value) > 0:
                    print(f"  (List with {len(value)} items)")
                    if isinstance(value[0], dict):
                        for field, field_value in list(value[0].items())[:3]:
                            print(f"    {field}: {field_value}")
        
        if 'detail' in structured_json:
            print("\nDetail section keys:", list(structured_json['detail'].keys())[:5])
            
            # Show a sample from detail
            for key, value in list(structured_json['detail'].items())[:1]:
                print(f"\n{key}:")
                if isinstance(value, dict):
                    for field, field_value in list(value.items())[:3]:
                        print(f"  {field}: {field_value}")
                elif isinstance(value, list) and len(value) > 0:
                    print(f"  (List with {len(value)} items)")
                    if isinstance(value[0], dict):
                        for field, field_value in list(value[0].items())[:3]:
                            print(f"    {field}: {field_value}")
        
        # Save to file for inspection
        output_file = f"test_output_{transaction_type.lower()}_structured.json"
        with open(output_file, 'w') as f:
            json.dump(structured_json, f, indent=2)
        print(f"\nFull output saved to: {output_file}")
        
        return structured_json
        
    finally:
        # Clean up
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# Test both transaction types
result_835 = test_formatter(edi_835, "835")
result_837 = test_formatter(edi_837, "837")

print("\n" + "="*60)
print("Key observations:")
print("="*60)
print("1. Field names should now be descriptive (e.g., 'transaction_set_purpose_code_01')")
print("2. Position numbers are preserved in field names")
print("3. Fallback to raw field names when mapping not found")
