"""
EDI Code Sets and Descriptions

This module provides comprehensive mappings of EDI codes to their human-readable
descriptions, supplementing the element names available in pyx12's XML maps.
"""

from . import edi_codes

# Export commonly used code lookups
from .edi_codes import (
    ENTITY_IDENTIFIER_CODES,
    DATE_TIME_QUALIFIERS,
    get_entity_description,
    get_reference_qualifier_description,
    get_claim_status_description,
    get_adjustment_group_description,
    get_adjustment_reason_description,
    get_claim_filing_description,
    get_payment_method_description,
    get_relationship_description,
    get_gender_description,
)

__all__ = [
    "edi_codes",
    "ENTITY_IDENTIFIER_CODES",
    "DATE_TIME_QUALIFIERS",
    "get_entity_description",
    "get_reference_qualifier_description",
    "get_claim_status_description",
    "get_adjustment_group_description",
    "get_adjustment_reason_description",
    "get_claim_filing_description",
    "get_payment_method_description",
    "get_relationship_description",
    "get_gender_description",
]