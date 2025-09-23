#!/usr/bin/env python3
"""
Demo script for generating CSV from EDI files using PyEDI v1.0.7
Demonstrates the new StringIO/BytesIO support and improved parser features
"""

import csv
import json
import sys
from io import StringIO
from pathlib import Path
from typing import Dict, Any, List

from pyedi import X12Parser, StructuredFormatter


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Flatten nested dictionary into flat key-value pairs"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # For lists, we'll just take the first item or convert to string
            if v and isinstance(v[0], dict):
                items.extend(flatten_dict(v[0], new_key, sep=sep).items())
            else:
                items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def edi_to_csv_from_string(edi_content: str, output_file: str = None) -> str:
    """
    Convert EDI content string to CSV using new PyEDI v1.0.7 StringIO support

    Args:
        edi_content: EDI content as a string
        output_file: Optional output CSV file path

    Returns:
        CSV content as string
    """
    print("Using PyEDI v1.0.7 with StringIO support...")

    # Parse EDI using StringIO (new v1.0.7 feature!)
    edi_stream = StringIO(edi_content)
    parser = X12Parser()
    formatter = StructuredFormatter()

    # Parse and format the data
    generic_json = parser.parse(edi_stream)
    parsed_data = formatter.format(generic_json)

    # Handle both single and multiple transactions (v1.0.7 fix)
    if isinstance(parsed_data, list):
        transactions = parsed_data
    else:
        transactions = [parsed_data]

    # Collect all rows for CSV
    all_rows = []
    all_keys = set()

    for i, transaction in enumerate(transactions):
        print(f"Processing transaction {i + 1}...")

        # Flatten the transaction data
        flat_data = flatten_dict(transaction)

        # Add transaction number
        flat_data['transaction_number'] = i + 1

        # Collect keys and data
        all_keys.update(flat_data.keys())
        all_rows.append(flat_data)

    # Create CSV
    csv_buffer = StringIO()
    fieldnames = sorted(all_keys)

    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_rows)

    csv_content = csv_buffer.getvalue()

    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write(csv_content)
        print(f"CSV saved to: {output_file}")

    return csv_content


def edi_file_to_csv(edi_file: str, output_file: str = None) -> str:
    """
    Convert EDI file to CSV using PyEDI v1.0.7

    Args:
        edi_file: Path to EDI file
        output_file: Optional output CSV file path

    Returns:
        CSV content as string
    """
    print(f"Reading EDI file: {edi_file}")

    # Parse EDI file directly
    parser = X12Parser()
    formatter = StructuredFormatter()

    # Parse and format the data
    generic_json = parser.parse(edi_file)
    parsed_data = formatter.format(generic_json)

    # Handle both single and multiple transactions
    if isinstance(parsed_data, list):
        transactions = parsed_data
    else:
        transactions = [parsed_data]

    # Collect all rows for CSV
    all_rows = []
    all_keys = set()

    for i, transaction in enumerate(transactions):
        print(f"Processing transaction {i + 1}...")

        # Extract key information based on transaction type
        transaction_type = transaction.get('transaction_type', 'Unknown')

        # Create a simplified row with key fields
        row_data = {
            'transaction_number': i + 1,
            'transaction_type': transaction_type,
        }

        # Extract interchange info
        if 'interchange' in transaction:
            row_data.update({
                'sender_id': transaction['interchange'].get('interchange_sender_id'),
                'receiver_id': transaction['interchange'].get('interchange_receiver_id'),
                'control_number': transaction['interchange'].get('interchange_control_number'),
                'date': transaction['interchange'].get('interchange_date'),
                'time': transaction['interchange'].get('interchange_time'),
            })

        # Extract functional group info
        if 'functional_group' in transaction:
            row_data.update({
                'functional_code': transaction['functional_group'].get('functional_identifier_code'),
                'group_control_number': transaction['functional_group'].get('group_control_number'),
            })

        # Extract heading info (varies by transaction type)
        if 'heading' in transaction:
            heading = transaction['heading']

            # Transaction set header
            if 'transaction_set_header' in heading:
                tsh = heading['transaction_set_header']
                if isinstance(tsh, list):
                    tsh = tsh[0]
                row_data['transaction_set_control'] = tsh.get('st02_329_transaction_set_control_number')

            # Beginning segment (varies by type)
            if 'beginning_of_hierarchical_transaction' in heading:
                bht = heading['beginning_of_hierarchical_transaction']
                if isinstance(bht, list):
                    bht = bht[0]
                row_data['purpose'] = bht.get('bht02_353_hierarchical_structure_code')
                row_data['reference_id'] = bht.get('bht03_127_reference_identification')
                row_data['creation_date'] = bht.get('bht04_373_date')
                row_data['creation_time'] = bht.get('bht05_337_time')

            # Names (submitter, receiver, etc.)
            for key in heading:
                if 'name' in key.lower():
                    name_data = heading[key]
                    if isinstance(name_data, list):
                        name_data = name_data[0]
                    if isinstance(name_data, dict) and 'party_name' in name_data:
                        party = name_data['party_name']
                        if isinstance(party, list):
                            party = party[0]
                        entity_type = party.get('nm101_98_entity_identifier_code', '')
                        name = party.get('nm103_1035_name_last_or_organization_name', '')
                        row_data[f'{entity_type}_name'] = name

        # Add row to collection
        all_keys.update(row_data.keys())
        all_rows.append(row_data)

    # Create CSV
    csv_buffer = StringIO()
    fieldnames = sorted(all_keys)

    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_rows)

    csv_content = csv_buffer.getvalue()

    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write(csv_content)
        print(f"CSV saved to: {output_file}")

    return csv_content


def demo_new_features():
    """Demonstrate the new PyEDI v1.0.7 features"""

    print("=" * 60)
    print("PyEDI v1.0.7 Demo - New Features Showcase")
    print("=" * 60)

    # Demo 1: StringIO support (new in v1.0.7)
    print("\n1. Testing new StringIO support...")
    sample_edi = """ISA*00*          *00*          *ZZ*SENDER123      *ZZ*RECEIVER456    *210901*1200*U*00501*000000001*0*P*:~
GS*HC*SENDER123*RECEIVER456*20210901*1200*1*X*005010X222A1~
ST*837*0001*005010X222A1~
BHT*0019*00*123456*20210901*1200*CH~
NM1*41*2*DEMO HEALTH PLAN*****46*123456789~
NM1*40*2*RECEIVER CORP*****46*987654321~
HL*1**20*1~
NM1*85*2*PROVIDER CLINIC*****XX*1234567890~
HL*2*1*22*0~
SBR*P*18*******CI~
NM1*IL*1*DOE*JOHN****MI*123456789~
CLM*CLAIM123*500***11:B:1*Y*A*Y*Y~
DTP*472*D8*20210901~
HI*ABK:M7989~
LX*1~
SV1*HC:99213*250*UN*1***1~
LX*2~
SV1*HC:99214*250*UN*1***2~
SE*18*0001~
GE*1*1~
IEA*1*000000001~"""

    csv_output = edi_to_csv_from_string(sample_edi, "demo_output_stringio.csv")
    print("✓ Successfully parsed EDI from string using StringIO")
    print(f"  Generated {len(csv_output.splitlines())} CSV lines")

    # Demo 2: Multi-transaction support (fixed in v1.0.7)
    print("\n2. Testing improved multi-transaction handling...")
    multi_transaction_edi = """ISA*00*          *00*          *ZZ*SENDER123      *ZZ*RECEIVER456    *210901*1200*U*00501*000000001*0*P*:~
GS*HC*SENDER123*RECEIVER456*20210901*1200*1*X*005010X222A1~
ST*837*0001*005010X222A1~
BHT*0019*00*TXN001*20210901*1200*CH~
NM1*41*2*PAYER ONE*****46*111111111~
CLM*CLAIM001*100***11:B:1*Y*A*Y*Y~
SE*6*0001~
ST*837*0002*005010X222A1~
BHT*0019*00*TXN002*20210901*1300*CH~
NM1*41*2*PAYER TWO*****46*222222222~
CLM*CLAIM002*200***11:B:1*Y*A*Y*Y~
SE*6*0002~
GE*2*1~
IEA*1*000000001~"""

    csv_output = edi_to_csv_from_string(multi_transaction_edi, "demo_output_multi_transaction.csv")
    print("✓ Successfully handled multiple transactions")
    print(f"  Generated {len(csv_output.splitlines())} CSV lines")

    # Demo 3: Load from file
    print("\n3. Testing file parsing with sample data...")

    # Create a sample EDI file
    sample_file = "sample_837.edi"
    with open(sample_file, 'w') as f:
        f.write(sample_edi)

    csv_output = edi_file_to_csv(sample_file, "demo_output_file.csv")
    print("✓ Successfully parsed EDI from file")
    print(f"  Generated {len(csv_output.splitlines())} CSV lines")

    print("\n" + "=" * 60)
    print("Demo complete! Check the generated CSV files:")
    print("  - demo_output_stringio.csv")
    print("  - demo_output_multi_transaction.csv")
    print("  - demo_output_file.csv")
    print("=" * 60)


if __name__ == "__main__":
    # Check if file argument provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.edi', '.csv')

        if Path(input_file).exists():
            print(f"Converting {input_file} to CSV...")
            edi_file_to_csv(input_file, output_file)
        else:
            print(f"Error: File {input_file} not found")
    else:
        # Run demo
        demo_new_features()