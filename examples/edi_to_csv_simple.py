#!/usr/bin/env python3
"""
Simple EDI to CSV converter using PyEDI v1.0.7
Extracts key fields into a clean CSV format
"""

import csv
import sys
from io import StringIO
from pathlib import Path

from pyedi import X12Parser, StructuredFormatter


def extract_key_fields(transaction: dict) -> dict:
    """Extract key fields from a parsed EDI transaction into a flat structure"""

    fields = {
        'transaction_type': transaction.get('transaction_type', ''),
        'transaction_set_control': '',
        'sender_id': '',
        'receiver_id': '',
        'date': '',
        'time': '',
        'reference_id': '',
        'claim_id': '',
        'claim_amount': '',
        'patient_name': '',
        'provider_name': '',
        'payer_name': '',
        'service_codes': '',
        'diagnosis_codes': '',
    }

    # Extract interchange info
    if 'interchange' in transaction:
        interchange = transaction['interchange']
        fields['sender_id'] = str(interchange.get('sender_id', '')).strip()
        fields['receiver_id'] = str(interchange.get('receiver_id', '')).strip()
        fields['date'] = interchange.get('date', '')
        fields['time'] = interchange.get('time', '')

    # Extract heading info
    if 'heading' in transaction:
        heading = transaction['heading']

        # Transaction set header
        if 'transaction_set_header_loop' in heading:
            tsh_loop = heading['transaction_set_header_loop']
            if 'transaction_set_header_ST' in tsh_loop:
                tsh = tsh_loop['transaction_set_header_ST']
                fields['transaction_set_control'] = tsh.get('transaction_set_control_number_02', '')

        # Beginning segment
        if 'beginning_of_hierarchical_transaction_loop' in heading:
            bht_loop = heading['beginning_of_hierarchical_transaction_loop']
            if 'beginning_of_hierarchical_transaction_BHT' in bht_loop:
                bht = bht_loop['beginning_of_hierarchical_transaction_BHT']
                fields['reference_id'] = bht.get('originator_application_transaction_identifier', '')

        # Extract names from various name segments
        # Submitter (Payer)
        if 'submitter_NM1_loop' in heading:
            submitter_loops = heading['submitter_NM1_loop']
            if isinstance(submitter_loops, list) and submitter_loops:
                submitter_loop = submitter_loops[0]
                if 'submitter_name_NM1' in submitter_loop:
                    submitter_names = submitter_loop['submitter_name_NM1']
                    if isinstance(submitter_names, list) and submitter_names:
                        fields['payer_name'] = submitter_names[0].get('submitter_name', '')

        # Receiver
        if 'receiver_NM1_loop' in heading:
            receiver_loops = heading['receiver_NM1_loop']
            if isinstance(receiver_loops, list) and receiver_loops:
                receiver_loop = receiver_loops[0]
                if 'receiver_name_NM1' in receiver_loop:
                    receiver_names = receiver_loop['receiver_name_NM1']
                    if isinstance(receiver_names, list) and receiver_names:
                        # Store receiver name (could be provider)
                        pass

    # Extract detail info
    if 'detail' in transaction:
        detail = transaction['detail']

        # Provider Name from billing provider
        if 'billing_provider_NM1_loop' in detail:
            provider_loops = detail['billing_provider_NM1_loop']
            if isinstance(provider_loops, list) and provider_loops:
                provider_loop = provider_loops[0]
                if 'billing_provider_name_NM1' in provider_loop:
                    provider_names = provider_loop['billing_provider_name_NM1']
                    if isinstance(provider_names, list) and provider_names:
                        fields['provider_name'] = provider_names[0].get('billing_provider_name', '')

        # Patient/Subscriber info
        if 'insured_or_subscriber_NM1_loop' in detail:
            subscriber_loops = detail['insured_or_subscriber_NM1_loop']
            if isinstance(subscriber_loops, list) and subscriber_loops:
                subscriber_loop = subscriber_loops[0]
                if 'insured_party_name_NM1' in subscriber_loop:
                    insured_names = subscriber_loop['insured_party_name_NM1']
                    if isinstance(insured_names, list) and insured_names:
                        insured = insured_names[0]
                        last_name = insured.get('insured_party_name', '')
                        first_name = insured.get('first_name', '')
                        if first_name:
                            fields['patient_name'] = f"{last_name} {first_name}"
                        else:
                            fields['patient_name'] = last_name

        # Claims
        if 'claim_information_loop' in detail:
            claim_loops = detail['claim_information_loop']
            if isinstance(claim_loops, list) and claim_loops:
                claim_loop = claim_loops[0]
                if 'claim_information_CLM' in claim_loop:
                    claim = claim_loop['claim_information_CLM']
                    fields['claim_id'] = claim.get('claim_submitters_identifier', '')
                    fields['claim_amount'] = claim.get('total_claim_charge_amount_02', '')

        # Service lines - look for SV1 segments
        service_codes = []
        if 'sv1' in detail:
            sv1_segments = detail['sv1']
            if not isinstance(sv1_segments, list):
                sv1_segments = [sv1_segments]

            for sv1 in sv1_segments:
                # The procedure code is typically in the first composite element
                if 'sv101' in sv1:
                    proc_info = sv1['sv101']
                    if isinstance(proc_info, dict):
                        proc_code = proc_info.get('procedure_code', '')
                    elif isinstance(proc_info, str):
                        # Sometimes it's just a string with HC:code format
                        if ':' in proc_info:
                            proc_code = proc_info.split(':')[1]
                        else:
                            proc_code = proc_info
                    else:
                        proc_code = str(proc_info)

                    if proc_code:
                        service_codes.append(proc_code)

        fields['service_codes'] = ', '.join(service_codes)

        # Diagnosis codes - look for HI segment
        diagnosis_codes = []
        if 'hi' in detail:
            hi_segments = detail['hi']
            if not isinstance(hi_segments, list):
                hi_segments = [hi_segments]

            for hi in hi_segments:
                # HI segment contains diagnosis codes in various fields
                for key in hi:
                    if key.startswith('hi') and isinstance(hi[key], dict):
                        # Look for diagnosis code within the composite
                        diag_code = hi[key].get('diagnosis_code', '')
                        if not diag_code:
                            # Sometimes it's in a different format
                            diag_code = hi[key].get('code', '')
                        if diag_code:
                            diagnosis_codes.append(diag_code)

        fields['diagnosis_codes'] = ', '.join(diagnosis_codes)

    return fields


def convert_edi_to_csv(source, output_file: str = None):
    """
    Convert EDI (file or string) to CSV using PyEDI v1.0.7

    Args:
        source: EDI file path (str) or EDI content (str)
        output_file: Optional output CSV file path

    Returns:
        CSV content as string
    """
    # Initialize parser and formatter
    parser = X12Parser()
    formatter = StructuredFormatter()

    # Determine if source is a file or content
    if isinstance(source, str) and (source.startswith('ISA') or '\n' in source):
        # It's EDI content - use StringIO (v1.0.7 feature)
        print("Parsing EDI content using StringIO...")
        edi_stream = StringIO(source)
        generic_json = parser.parse(edi_stream)
    else:
        # It's a file path
        print(f"Parsing EDI file: {source}")
        generic_json = parser.parse(source)

    # Format to structured output
    parsed_data = formatter.format(generic_json)

    # Handle both single and multiple transactions (v1.0.7 improvement)
    if isinstance(parsed_data, list):
        transactions = parsed_data
    else:
        transactions = [parsed_data]

    # Extract key fields from each transaction
    rows = []
    for i, transaction in enumerate(transactions, 1):
        row = extract_key_fields(transaction)
        row['transaction_number'] = i
        rows.append(row)

    # Define field order for CSV
    fieldnames = [
        'transaction_number',
        'transaction_type',
        'transaction_set_control',
        'sender_id',
        'receiver_id',
        'date',
        'time',
        'reference_id',
        'claim_id',
        'claim_amount',
        'patient_name',
        'provider_name',
        'payer_name',
        'service_codes',
        'diagnosis_codes',
    ]

    # Create CSV
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    csv_content = csv_buffer.getvalue()

    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write(csv_content)
        print(f"✓ CSV saved to: {output_file}")
        print(f"  Processed {len(rows)} transaction(s)")

    return csv_content


def main():
    """Main entry point for command-line usage"""

    if len(sys.argv) < 2:
        print("Usage: python edi_to_csv_simple.py <input.edi> [output.csv]")
        print("\nExample EDI to test with:")
        print("-" * 60)

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

        print(sample_edi)
        print("-" * 60)
        print("\nTesting with sample EDI...")
        csv_output = convert_edi_to_csv(sample_edi, "sample_output.csv")
        print("\n✓ Sample output saved to: sample_output.csv")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.edi', '.csv').replace('.txt', '.csv')

    if not Path(input_file).exists():
        print(f"Error: File {input_file} not found")
        sys.exit(1)

    try:
        convert_edi_to_csv(input_file, output_file)
    except Exception as e:
        print(f"Error processing EDI file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()