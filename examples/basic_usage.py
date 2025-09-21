#!/usr/bin/env python3
"""
Basic Usage Examples for PyEDI

This file demonstrates the basic usage patterns for the pyedi package.
"""

from pyedi import X12Pipeline, X12Parser, StructuredFormatter, SchemaMapper
from pyedi import MappingBuilder, load_mapping_definition
import json


def example_1_simple_pipeline():
    """Example 1: Simplest usage with the pipeline"""
    print("=" * 60)
    print("Example 1: Simple Pipeline Usage")
    print("=" * 60)

    # Create pipeline
    pipeline = X12Pipeline()

    # Transform EDI file with a mapping
    result = pipeline.transform(
        edi_file="sample_835.edi",
        mapping="mapping_definitions/835_to_payment_system.json"
    )

    # Print result
    print(json.dumps(result, indent=2)[:500])  # Print first 500 chars


def example_2_pipeline_with_options():
    """Example 2: Pipeline with configuration options"""
    print("\n" + "=" * 60)
    print("Example 2: Pipeline with Options")
    print("=" * 60)

    # Create pipeline with options
    pipeline = X12Pipeline(
        verbose=True,                # Enable logging
        save_intermediate=True,       # Save intermediate files
        include_technical=True        # Include technical codes
    )

    # Transform and save output
    result = pipeline.transform(
        edi_file="sample_837.edi",
        mapping="mapping_definitions/837_to_claims_system.json",
        output="output/claim_result.json"
    )

    # Get processing statistics
    stats = pipeline.get_statistics()
    print(f"Processing statistics: {stats}")


def example_3_step_by_step():
    """Example 3: Step-by-step transformation for full control"""
    print("\n" + "=" * 60)
    print("Example 3: Step-by-Step Processing")
    print("=" * 60)

    # Step 1: Parse EDI to generic JSON
    parser = X12Parser()
    generic_json = parser.parse("sample_835.edi")
    print(f"Step 1 - Parsed EDI: {len(generic_json.get('transactions', []))} transactions found")

    # Step 2: Format to structured JSON
    formatter = StructuredFormatter()
    structured_json = formatter.format(generic_json, include_technical=True)
    print(f"Step 2 - Formatted: Transaction type {structured_json.get('transaction_type')}")

    # Step 3: Map to target schema
    mapping = load_mapping_definition("mapping_definitions/835_to_payment_system.json")
    mapper = SchemaMapper(mapping)
    target_json = mapper.map(structured_json)
    print(f"Step 3 - Mapped: {len(target_json.keys())} fields in target schema")

    # Save result
    with open("output/step_by_step_result.json", "w") as f:
        json.dump(target_json, f, indent=2)


def example_4_custom_inline_mapping():
    """Example 4: Using custom inline mapping definition"""
    print("\n" + "=" * 60)
    print("Example 4: Custom Inline Mapping")
    print("=" * 60)

    # Define custom mapping inline
    custom_mapping = {
        "name": "simple_835_extract",
        "mapping_type": "only_mapped",
        "expressions": {
            "payment_id": "trace_information.check_or_eft_number",
            "payment_date": "payment_information.payment_date",
            "payment_amount": "payment_information.total_payment_amount",
            "payer_name": "payer.name",
            "payee_name": "payee.name",
            "total_claims": "$count(claims)",
            "claim_numbers": "claims ~> |$| patient_control_number |"
        }
    }

    # Use pipeline with custom mapping
    pipeline = X12Pipeline()
    result = pipeline.transform(
        edi_file="sample_835.edi",
        mapping=custom_mapping
    )

    print("Custom mapping result:")
    print(json.dumps(result, indent=2))


def example_5_mapping_builder():
    """Example 5: Build mapping programmatically with MappingBuilder"""
    print("\n" + "=" * 60)
    print("Example 5: Using MappingBuilder")
    print("=" * 60)

    # Create mapping using builder pattern
    builder = MappingBuilder("custom_837_mapping", mapping_type="only_mapped")

    # Add simple field mappings
    builder.add_field_mapping("claim_id", "claims[0].claim_number")
    builder.add_field_mapping("total_charge", "claims[0].total_charge_amount")
    builder.add_field_mapping("provider_name", "billing_provider.name")

    # Add object mapping
    builder.add_object_mapping("patient_info", {
        "first_name": "claims[0].subscriber.first_name",
        "last_name": "claims[0].subscriber.last_name",
        "member_id": "claims[0].subscriber.member_id"
    })

    # Add list mapping with transformation
    builder.add_list_mapping(
        "service_lines",
        "claims[0].service_lines",
        {
            "code": "procedure_code",
            "charge": "charge_amount",
            "units": "units"
        }
    )

    # Build and use the mapping
    mapping_def = builder.build()

    # Save mapping for reuse
    builder.export_to_file("custom_mapping.json")

    # Use with pipeline
    pipeline = X12Pipeline()
    result = pipeline.transform("sample_837.edi", mapping=mapping_def)
    print(f"Result with {len(result.keys())} mapped fields")


def example_6_batch_processing():
    """Example 6: Process multiple EDI files in batch"""
    print("\n" + "=" * 60)
    print("Example 6: Batch Processing")
    print("=" * 60)

    # List of EDI files to process
    edi_files = [
        "batch/835_file1.edi",
        "batch/835_file2.edi",
        "batch/835_file3.edi"
    ]

    # Create pipeline
    pipeline = X12Pipeline(verbose=True)

    # Process batch
    batch_results = pipeline.transform_batch(
        edi_files=edi_files,
        mapping="mapping_definitions/835_to_payment_system.json",
        output_dir="output/batch_results"
    )

    # Print summary
    print(f"Processed: {batch_results['statistics']['files_processed']} files")
    print(f"Succeeded: {batch_results['statistics']['files_succeeded']} files")
    print(f"Failed: {batch_results['statistics']['files_failed']} files")

    if batch_results['errors']:
        print("\nErrors:")
        for file, error in batch_results['errors'].items():
            print(f"  {file}: {error}")


def example_7_return_intermediate():
    """Example 7: Get all intermediate transformations for debugging"""
    print("\n" + "=" * 60)
    print("Example 7: Return Intermediate Transformations")
    print("=" * 60)

    pipeline = X12Pipeline()

    # Get all intermediate transformations
    all_stages = pipeline.transform(
        edi_file="sample_835.edi",
        mapping="mapping_definitions/835_to_payment_system.json",
        return_intermediate=True
    )

    # Access each stage
    print(f"Generic JSON keys: {list(all_stages['generic'].keys())}")
    print(f"Structured JSON keys: {list(all_stages['structured'].keys())}")
    print(f"Mapped JSON keys: {list(all_stages['mapped'].keys())}")

    # Save each stage for analysis
    for stage_name, stage_data in all_stages.items():
        with open(f"output/{stage_name}_stage.json", "w") as f:
            json.dump(stage_data, f, indent=2)
        print(f"Saved {stage_name} stage to output/{stage_name}_stage.json")


def example_8_validate_mapping():
    """Example 8: Validate mapping before using it"""
    print("\n" + "=" * 60)
    print("Example 8: Mapping Validation")
    print("=" * 60)

    pipeline = X12Pipeline()

    # Validate a mapping file
    validation_result = pipeline.validate_mapping(
        mapping="mapping_definitions/835_to_payment_system.json",
        sample_edi="sample_835.edi"  # Optional: test with actual EDI
    )

    print(f"Mapping valid: {validation_result['valid']}")
    if validation_result['errors']:
        print("Errors:", validation_result['errors'])
    if validation_result['warnings']:
        print("Warnings:", validation_result['warnings'])
    if 'sample_test' in validation_result:
        print(f"Sample test: {validation_result['sample_test']}")


if __name__ == "__main__":
    # Note: These examples assume you have sample EDI files and mapping definitions
    # in the appropriate directories. Adjust paths as needed.

    print("\nPyEDI - Usage Examples\n")

    # Uncomment the examples you want to run:

    # example_1_simple_pipeline()
    # example_2_pipeline_with_options()
    # example_3_step_by_step()
    # example_4_custom_inline_mapping()
    # example_5_mapping_builder()
    # example_6_batch_processing()
    # example_7_return_intermediate()
    # example_8_validate_mapping()

    print("\n" + "=" * 60)
    print("Examples complete! Uncomment the examples you want to run.")
    print("=" * 60)