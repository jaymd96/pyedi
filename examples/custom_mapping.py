#!/usr/bin/env python3
"""
Custom Mapping Examples for X12 EDI Converter

This file demonstrates how to create custom mappings for different use cases.
"""

from x12_edi_converter import MappingBuilder, X12Pipeline
import json


def create_835_payment_summary_mapping():
    """Create a simple 835 payment summary mapping"""
    builder = MappingBuilder("835_payment_summary", mapping_type="only_mapped")

    # Add basic payment information
    builder.add_field_mapping("payment_id", "trace_information.check_or_eft_number")
    builder.add_field_mapping("payment_date", "payment_information.payment_date")
    builder.add_field_mapping("total_payment", "payment_information.total_payment_amount")
    builder.add_field_mapping("payment_method", "payment_information.payment_method.description")

    # Add payer information as nested object
    builder.add_object_mapping("payer", {
        "name": "payer.name",
        "id": "payer.identification.value",
        "contact_name": "payer.contact.name",
        "contact_phone": "payer.contact.telephone"
    })

    # Add summary calculations using JSONata
    builder.add_field_mapping("total_claims_count", "$count(claims)")
    builder.add_field_mapping("total_charged", "$sum(claims.total_charge_amount)")
    builder.add_field_mapping("total_paid", "$sum(claims.total_paid_amount)")
    builder.add_field_mapping("total_patient_responsibility", "$sum(claims.patient_responsibility)")

    # Add claim status breakdown
    builder.add_field_mapping(
        "claim_status_breakdown",
        """claims ~> $group(claim_status.description) ~>
        $each(function($v, $k) { {"status": $k, "count": $count($v)} })"""
    )

    return builder.build()


def create_837_claim_extract_mapping():
    """Create an 837 claim data extraction mapping"""
    builder = MappingBuilder("837_claim_extract", mapping_type="only_mapped")

    # Transaction information
    builder.add_field_mapping("claim_id", "transaction_header.reference_number")
    builder.add_field_mapping("created_date", "transaction_header.creation_date")
    builder.add_field_mapping("transaction_type", "transaction_type")

    # Billing provider
    builder.add_object_mapping("billing_provider", {
        "name": "billing_provider.name",
        "npi": "billing_provider.identification.value",
        "tax_id": "billing_provider.references[0].value",
        "address": {
            "street": "billing_provider.address.street_1",
            "city": "billing_provider.address.city",
            "state": "billing_provider.address.state",
            "zip": "billing_provider.address.postal_code"
        }
    })

    # Claims with service lines
    builder.add_field_mapping(
        "claims",
        """claims ~> |$| {
            "claim_number": claim_number,
            "total_charge": total_charge_amount,
            "patient": {
                "first_name": subscriber.first_name,
                "last_name": subscriber.last_name,
                "member_id": subscriber.member_id
            },
            "service_lines": service_lines ~> |$| {
                "procedure_code": procedure_code,
                "charge": charge_amount,
                "units": units,
                "place_of_service": place_of_service
            } |
        } |"""
    )

    return builder.build()


def create_834_enrollment_mapping():
    """Create an 834 benefit enrollment mapping"""
    builder = MappingBuilder("834_enrollment_extract", mapping_type="only_mapped")

    # Transaction header
    builder.add_field_mapping("reference_number", "transaction_header.reference_number")
    builder.add_field_mapping("creation_date", "transaction_header.creation_date")

    # Plan sponsor
    builder.add_object_mapping("plan_sponsor", {
        "name": "plan_sponsor.name",
        "identifier": "plan_sponsor.identifier"
    })

    # Payer
    builder.add_object_mapping("payer", {
        "name": "payer.name",
        "identifier": "payer.identifier"
    })

    # Member enrollments with demographics
    builder.add_field_mapping(
        "enrollments",
        """members ~> |$| {
            "member_id": name.member_id,
            "full_name": name.first_name & " " & name.last_name,
            "relationship": relationship.description,
            "maintenance_type": maintenance_type,
            "benefit_status": benefit_status,
            "birth_date": demographics.birth_date,
            "gender": demographics.gender.description
        } |"""
    )

    # Summary statistics
    builder.add_field_mapping("total_members", "$count(members)")
    builder.add_field_mapping(
        "members_by_relationship",
        """members ~> $group(relationship.description) ~>
        $each(function($v, $k) { {"relationship": $k, "count": $count($v)} })"""
    )

    return builder.build()


def create_mapping_with_lookup_tables():
    """Create a mapping that uses lookup tables for code conversions"""
    builder = MappingBuilder("mapping_with_lookups", mapping_type="only_mapped")

    # Add lookup table for claim status codes
    builder.add_lookup_table("claim_status_lookup", [
        {"code": "1", "description": "Processed as Primary", "category": "paid"},
        {"code": "2", "description": "Processed as Secondary", "category": "paid"},
        {"code": "3", "description": "Processed as Tertiary", "category": "paid"},
        {"code": "4", "description": "Denied", "category": "denied"},
        {"code": "19", "description": "Processed as Primary, Forwarded", "category": "paid"},
        {"code": "20", "description": "Processed as Secondary, Forwarded", "category": "paid"},
        {"code": "22", "description": "Reversal of Previous Payment", "category": "reversed"}
    ])

    # Add lookup table for adjustment reason codes
    builder.add_lookup_table("adjustment_reason_lookup", [
        {"code": "1", "description": "Deductible", "type": "patient_responsibility"},
        {"code": "2", "description": "Coinsurance", "type": "patient_responsibility"},
        {"code": "3", "description": "Copayment", "type": "patient_responsibility"},
        {"code": "45", "description": "Charges exceed maximum", "type": "contractual"},
        {"code": "96", "description": "Non-covered charges", "type": "non_covered"},
        {"code": "97", "description": "Payment included in allowance", "type": "bundled"}
    ])

    # Use lookups in mappings
    builder.add_field_mapping(
        "claims_with_categories",
        """claims ~> |$| {
            "claim_id": patient_control_number,
            "status": claim_status.code,
            "status_category": $lookupTable("claim_status_lookup", "code", claim_status.code).category,
            "total_charge": total_charge_amount,
            "paid_amount": total_paid_amount,
            "adjustments": claim_adjustments ~> |$| {
                "group": adjustment_group.code,
                "reasons": reasons ~> |$| {
                    "code": code.code,
                    "description": $lookupTable("adjustment_reason_lookup", "code", code.code).description,
                    "type": $lookupTable("adjustment_reason_lookup", "code", code.code).type,
                    "amount": amount
                } |
            } |
        } |"""
    )

    return builder.build()


def create_conditional_mapping():
    """Create a mapping with conditional logic"""
    builder = MappingBuilder("conditional_mapping", mapping_type="only_mapped")

    # Basic fields
    builder.add_field_mapping("transaction_type", "transaction_type")

    # Conditional field based on transaction type
    builder.add_field_mapping(
        "primary_entity",
        """transaction_type = "835" ? payer.name :
           transaction_type = "837" ? billing_provider.name :
           transaction_type = "834" ? plan_sponsor.name :
           "Unknown" """
    )

    # Conditional formatting based on amount
    builder.add_field_mapping(
        "payment_status",
        """payment_information.total_payment_amount > 10000 ? "Large Payment" :
           payment_information.total_payment_amount > 1000 ? "Standard Payment" :
           payment_information.total_payment_amount > 0 ? "Small Payment" :
           "No Payment" """
    )

    # Filter and transform claims based on conditions
    builder.add_field_mapping(
        "high_value_claims",
        """claims[total_charge_amount > 5000] ~> |$| {
            "claim_id": patient_control_number,
            "amount": total_charge_amount,
            "flag": "HIGH_VALUE"
        } |"""
    )

    # Aggregate with conditions
    builder.add_field_mapping(
        "payment_summary",
        """{
            "total_paid_claims": $count(claims[claim_status.code = "1"]),
            "total_denied_claims": $count(claims[claim_status.code = "4"]),
            "paid_amount": $sum(claims[claim_status.code = "1"].total_paid_amount),
            "denied_amount": $sum(claims[claim_status.code = "4"].total_charge_amount)
        }"""
    )

    return builder.build()


def create_flattened_export_mapping():
    """Create a mapping that flattens nested data for CSV export"""
    builder = MappingBuilder("flattened_export", mapping_type="only_mapped")

    # Flatten claims with all related data denormalized
    builder.add_field_mapping(
        "flattened_claims",
        """claims ~> |$|
            service_lines ~> |$$| {
                "payment_id": %.%.payment_information.check_or_eft_number,
                "payment_date": %.%.payment_information.payment_date,
                "payer_name": %.%.payer.name,
                "payee_name": %.%.payee.name,
                "claim_number": %.patient_control_number,
                "claim_status": %.claim_status.description,
                "patient_name": %.patient.first_name & " " & %.patient.last_name,
                "patient_id": %.patient.member_id,
                "service_procedure": procedure_code,
                "service_charge": charge_amount,
                "service_paid": paid_amount,
                "service_date": dates.service_date
            } |
        |"""
    )

    return builder.build()


def save_all_example_mappings():
    """Save all example mappings to files"""
    mappings = {
        "835_payment_summary.json": create_835_payment_summary_mapping(),
        "837_claim_extract.json": create_837_claim_extract_mapping(),
        "834_enrollment.json": create_834_enrollment_mapping(),
        "mapping_with_lookups.json": create_mapping_with_lookup_tables(),
        "conditional_mapping.json": create_conditional_mapping(),
        "flattened_export.json": create_flattened_export_mapping()
    }

    for filename, mapping in mappings.items():
        filepath = f"sample_mappings/{filename}"
        with open(filepath, "w") as f:
            json.dump(mapping, f, indent=2)
        print(f"Saved mapping to {filepath}")


def test_custom_mapping():
    """Test a custom mapping with sample data"""
    # Create a simple test mapping
    mapping = create_835_payment_summary_mapping()

    # Create pipeline and test
    pipeline = X12Pipeline()

    # You would use actual EDI file here
    # result = pipeline.transform("sample_835.edi", mapping=mapping)
    # print(json.dumps(result, indent=2))

    print("Custom mapping created:")
    print(json.dumps(mapping, indent=2)[:1000])  # Print first 1000 chars


if __name__ == "__main__":
    print("Custom Mapping Examples for X12 EDI Converter\n")
    print("=" * 60)

    # Test a custom mapping
    test_custom_mapping()

    # Uncomment to save all example mappings
    # save_all_example_mappings()

    print("\n" + "=" * 60)
    print("Custom mapping examples complete!")