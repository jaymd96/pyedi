#!/usr/bin/env python3
"""
Dynamic Map Element Loader

This module dynamically loads element names and definitions from pyx12 XML map files,
allowing the system to work with any X12 transaction type and version without hardcoding.
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, Optional, Any
from functools import lru_cache

try:
    from pkg_resources import resource_string, resource_exists
except ImportError:
    # Fallback for newer Python versions
    import importlib.resources as resources

    def resource_string(package, path):
        """Compatibility wrapper for resource_string"""
        with resources.files(package).joinpath(path).open('rb') as f:
            return f.read()

    def resource_exists(package, path):
        """Compatibility wrapper for resource_exists"""
        return resources.files(package).joinpath(path).exists()


class MapElementLoader:
    """Dynamically loads element names from pyx12 XML map files"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._cache = {}  # Cache loaded maps
        self._element_cache = {}  # Cache individual element lookups

    @lru_cache(maxsize=32)
    def load_map_elements(self, map_filename: str) -> Dict[str, Dict[str, Any]]:
        """
        Load and parse element definitions from a pyx12 map file

        Args:
            map_filename: Name of the XML map file (e.g., '834.5010.X220.A1.xml')

        Returns:
            Dictionary of segments with their element definitions
        """
        # Check cache first
        if map_filename in self._cache:
            return self._cache[map_filename]

        segments = {}

        try:
            # Check if map exists
            map_path = f'map/{map_filename}'
            if not resource_exists('pyx12', map_path):
                self.logger.warning(f"Map file not found: {map_filename}")
                return segments

            # Load the XML map
            map_content = resource_string('pyx12', map_path)
            root = ET.fromstring(map_content)

            # Extract transaction info
            transaction_id = root.get('xid', 'unknown')
            transaction_name = root.find('.//name')
            if transaction_name is not None:
                self.logger.debug(f"Loading map for: {transaction_name.text}")

            # Find all segment definitions (recursive search)
            for segment in root.iter('segment'):
                seg_id = segment.get('xid')
                if not seg_id:
                    continue

                # Get segment name
                seg_name_elem = segment.find('name')
                seg_name = seg_name_elem.text if seg_name_elem is not None else seg_id

                segments[seg_id] = {
                    'name': seg_name,
                    'elements': {}
                }

                # Get all elements in this segment
                for element in segment.findall('element'):
                    elem_id = element.get('xid')
                    if not elem_id:
                        continue

                    # Extract element metadata
                    elem_name = element.find('name')
                    data_ele = element.find('data_ele')
                    usage = element.find('usage')
                    data_type = element.find('data_type')
                    min_len = element.find('min_len')
                    max_len = element.find('max_len')

                    elem_info = {
                        'name': elem_name.text if elem_name is not None else elem_id,
                        'data_ele': data_ele.text if data_ele is not None else None,
                        'usage': usage.text if usage is not None else 'S',
                        'data_type': data_type.text if data_type is not None else 'AN',
                        'min_len': int(min_len.text) if min_len is not None else None,
                        'max_len': int(max_len.text) if max_len is not None else None
                    }

                    segments[seg_id]['elements'][elem_id] = elem_info

            # Cache the results
            self._cache[map_filename] = segments
            self.logger.info(f"Loaded {len(segments)} segment definitions from {map_filename}")

        except Exception as e:
            self.logger.error(f"Error loading map {map_filename}: {e}", exc_info=True)

        return segments

    def get_element_name(self, map_filename: str, segment_id: str, element_id: str) -> str:
        """
        Get the descriptive name for an element

        Args:
            map_filename: Map file to use (e.g., '834.5010.X220.A1.xml')
            segment_id: Segment ID (e.g., 'BGN')
            element_id: Element ID (e.g., 'BGN01')

        Returns:
            Descriptive element name or the element ID if not found
        """
        # Check element cache first
        cache_key = f"{map_filename}:{segment_id}:{element_id}"
        if cache_key in self._element_cache:
            return self._element_cache[cache_key]

        # Load map if needed
        segments = self.load_map_elements(map_filename)

        # Look up the element
        if segment_id in segments:
            elements = segments[segment_id].get('elements', {})
            if element_id in elements:
                name = elements[element_id].get('name', element_id)
                self._element_cache[cache_key] = name
                return name

        # Fallback to element ID
        self._element_cache[cache_key] = element_id
        return element_id

    def get_element_info(self, map_filename: str, segment_id: str, element_id: str) -> Dict[str, Any]:
        """
        Get complete element information including name, type, usage, etc.

        Args:
            map_filename: Map file to use
            segment_id: Segment ID
            element_id: Element ID

        Returns:
            Dictionary with element metadata
        """
        segments = self.load_map_elements(map_filename)

        if segment_id in segments:
            elements = segments[segment_id].get('elements', {})
            if element_id in elements:
                return elements[element_id]

        # Return minimal info if not found
        return {
            'name': element_id,
            'data_ele': None,
            'usage': 'S',
            'data_type': 'AN'
        }

    def get_segment_name(self, map_filename: str, segment_id: str) -> str:
        """
        Get the descriptive name for a segment

        Args:
            map_filename: Map file to use
            segment_id: Segment ID (e.g., 'BGN')

        Returns:
            Descriptive segment name or the segment ID if not found
        """
        segments = self.load_map_elements(map_filename)

        if segment_id in segments:
            return segments[segment_id].get('name', segment_id)

        return segment_id

    def format_element_name_for_json(self, name: str, element_id: str, context: Dict[str, str] = None) -> str:
        """
        Format element name for use as a JSON key (Stedi-style format)

        Args:
            name: Descriptive element name
            element_id: Element ID (e.g., 'BGN01')
            context: Optional context dict with 'loop_id', 'segment_id', 'entity_code' etc.

        Returns:
            Formatted field name with position number
        """
        import re

        # Extract position number from element ID
        position = re.search(r'\d+$', element_id)
        if position:
            position_num = position.group()
        else:
            position_num = element_id

        # If name is same as element ID, just return it
        if name == element_id:
            return element_id.lower()

        # Apply context-aware naming for generic fields
        if context:
            name = self._apply_context_naming(name, element_id, context)

        # Convert name to snake_case and clean up
        name = re.sub(r'[^\w\s]', '', name)  # Remove special characters
        name = re.sub(r'\s+', '_', name)  # Replace spaces with underscores
        name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)  # Handle acronyms
        name = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', name)  # Handle camelCase
        name = name.lower()

        # Remove redundant words
        name = re.sub(r'_code_code', '_code', name)
        name = re.sub(r'_id_id', '_id', name)
        name = re.sub(r'_identifier_identifier', '_identifier', name)
        name = re.sub(r'_number_number', '_number', name)

        # Add position number
        return f"{name}_{position_num.zfill(2)}"

    def _apply_context_naming(self, name: str, element_id: str, context: Dict[str, str]) -> str:
        """
        Apply context-specific naming for generic field names based on X12 ANSI standards

        This method uses comprehensive X12 knowledge including entity identifier codes,
        segment contexts, and loop structures to provide accurate field names.
        """
        segment_id = context.get('segment_id', '')
        entity_code = context.get('entity_code', '')
        loop_type = context.get('loop_type', '')  # e.g., 'payer', 'payee', 'subscriber'
        loop_id = context.get('loop_id', '')  # e.g., '1000A', '2010AA'

        # Handle NM1 (Individual or Organizational Name) segment - X12 standard
        if segment_id == 'NM1':
            # Comprehensive entity code mapping per X12 ANSI standard
            # Based on X12 Entity Identifier Code (98) data element
            entity_context = {
                # Healthcare specific (270/271, 276/277, 834, 835, 837)
                'IL': 'insured',           # Insured or Subscriber
                'QC': 'patient',           # Patient (if different from subscriber)
                'PR': 'payer',             # Payer
                'PE': 'payee',             # Payee
                '1P': 'provider',          # Provider
                '2B': 'third_party_admin', # Third-Party Administrator
                '36': 'employer',          # Employer
                '40': 'receiver',          # Receiver
                '41': 'submitter',         # Submitter
                '45': 'drop_off_location', # Drop-off Location
                '71': 'attending_physician',
                '72': 'operating_physician',
                '73': 'other_physician',
                '77': 'service_location',
                '82': 'rendering_provider',
                '85': 'billing_provider',
                '86': 'group_practice',
                '87': 'pay_to_provider',
                'DN': 'referring_provider',
                'DK': 'ordering_provider',
                'DQ': 'supervising_provider',
                'FA': 'facility',
                'GB': 'other_insured',
                'HH': 'home_health_agency',
                'P3': 'primary_care_provider',
                'P4': 'prior_insurance_carrier',
                'P5': 'plan_sponsor',
                'PRP': 'primary_payer',
                'SEP': 'secondary_payer',
                'TTP': 'tertiary_payer',
                'VN': 'vendor',
                'Y2': 'managed_care_org',

                # Business transactions (810, 850, 855, 856)
                'BT': 'bill_to_party',
                'BY': 'buying_party',
                'CN': 'consignee',
                'RE': 'release_to_party',
                'SE': 'selling_party',
                'SF': 'ship_from',
                'ST': 'ship_to',
                'SU': 'supplier',

                # Additional common codes
                'BO': 'broker',
                'CA': 'carrier',
                'CC': 'subsequent_owner',
                'CD': 'co_driver',
                'CF': 'corporate_office',
                'CK': 'pharmacist',
                'CZ': 'admitting_surgeon',
                'D2': 'commercial_insurer',
                'DD': 'assistant_surgeon',
                'DJ': 'consulting_physician',
                'DK': 'ordering_physician',
                'E1': 'person_or_org_who_cert',
                'EI': 'expiry_insurer',
                'EXS': 'ex_spouse',
                'FD': 'functional_disability_insurer',
                'FH': 'fourth_party',
                'G0': 'goal_insurer',
                'G2': 'gateway_provider',
                'G3': 'key_person_insurer',
                'G5': 'mail_to',
                'GB': 'other_insured',
                'GD': 'guardian',
                'GI': 'paramedic',
                'GJ': 'physician_assistant',
                'GK': 'medical_supplier',
                'GM': 'prime_contractor',
                'GW': 'group_purchasing_org',
                'HF': 'third_party_reviewing_org',
                'HH': 'home_health_agency',
                'I3': 'independent_adjuster',
                'IN': 'insurer',
                'LI': 'independent_lab',
                'LR': 'legal_representative',
                'MI': 'medical_insurance_carrier',
                'MR': 'medical_necessity_reviewer',
                'MS': 'medical_staff',
                'MT': 'material_safety_data_sheet',
                'OC': 'origin_carrier',
                'OD': 'doctor_of_optometry',
                'OI': 'other_insured_identified',
                'OX': 'oxygen_therapy_facility',
                'P0': 'patient_facility',
                'P1': 'preparer',
                'P2': 'primary_insured',
                'P3': 'primary_care_provider',
                'P4': 'prior_insurance_carrier',
                'P5': 'plan_sponsor',
                'P6': 'third_party_reviewing_preferred',
                'P7': 'third_party_reviewing_organization',
                'PC': 'party_to_receive_cert',
                'PW': 'pickup',
                'QA': 'pharmacy',
                'QB': 'purchase_service_provider',
                'QD': 'responsible_party',
                'QE': 'policyholder',
                'QH': 'physician',
                'QK': 'managed_care_contractor',
                'QL': 'dealership',
                'QM': 'medical_purchasing_org',
                'QN': 'dentist',
                'QO': 'doctor_of_osteopathy',
                'QP': 'public_health_insurer',
                'QQ': 'regulatory_agency_state',
                'QR': 'regulatory_agency_federal',
                'QS': 'podiatrist',
                'QT': 'qty_surveyor',
                'QU': 'state_div_comp',
                'QV': 'qualified_medicare_beneficiary',
                'QY': 'medical_doctor',
                'R1': 'appraiser',
                'R2': 'appraisal_company',
                'R3': 'architect',
                'RA': 'alternate_return_address',
                'RB': 'received_by',
                'RW': 'rural_health_clinic',
                'S1': 'parent',
                'S2': 'student',
                'S3': 'custodial_parent',
                'S5': 'state_agency',
                'SB': 'storage',
                'SEP': 'secondary_payer',
                'SJ': 'service_provider',
                'SK': 'school_district',
                'SV': 'service_performance_site',
                'T1': 'provider_of_service',
                'TQ': 'third_party_reviewing_org_3',
                'TT': 'transfer_to',
                'TTP': 'tertiary_payer',
                'TU': 'third_party_agency',
                'TY': 'subcontractor',
                'TZ': 'treatment_facility',
                'UH': 'urgent_care_facility',
                'VP': 'vendor_part',
                'VY': 'organization',
                'X3': 'utilization_management_org',
                'X4': 'spouse_insured',
                'X5': 'durable_medical_equipment_supplier',
                'Y2': 'managed_care_organization',
                'ZZ': 'mutually_defined'
            }

            ctx = entity_context.get(entity_code, '')

            # Apply context to NM1 fields based on X12 standards
            if element_id == 'NM103':
                # NM103 = Name Last or Organization Name (Free Form)
                # For individuals (entity type 1), this is last name
                # For organizations (entity type 2), this is org name
                entity_type = context.get('entity_type', '')
                if ctx:
                    if entity_type == '1' or entity_code in ['IL', 'QC', '71', '72', '73', '82', 'DN', 'DK', 'DQ']:
                        return f"{ctx}_last_name"
                    else:
                        return f"{ctx}_name"
            elif element_id == 'NM104':
                # NM104 = Name First (Free Form)
                if ctx and entity_code in ['IL', 'QC', '71', '72', '73', '82', 'DN', 'DK', 'DQ', 'S1', 'S2', 'S3', 'GB']:
                    return f"{ctx}_first_name"
            elif element_id == 'NM105':
                # NM105 = Name Middle (Free Form)
                if ctx and entity_code in ['IL', 'QC', '71', '72', '73', '82', 'DN', 'DK', 'DQ', 'S1', 'S2', 'S3', 'GB']:
                    return f"{ctx}_middle_name"
            elif element_id == 'NM106':
                # NM106 = Name Prefix (Free Form)
                if ctx:
                    return f"{ctx}_prefix"
            elif element_id == 'NM107':
                # NM107 = Name Suffix (Free Form)
                if ctx:
                    return f"{ctx}_suffix"
            elif element_id == 'NM108':
                # NM108 = Identification Code Qualifier
                if ctx:
                    return f"{ctx}_id_qualifier"
            elif element_id == 'NM109':
                # NM109 = Identification Code
                if ctx:
                    return f"{ctx}_identifier"

        # Handle N1 (Party Identification) segment - simpler than NM1
        elif segment_id == 'N1':
            # N1 uses same entity codes but simpler structure
            entity_context_n1 = {
                'PR': 'payer',
                'PE': 'payee',
                'BY': 'buyer',
                'SE': 'seller',
                'ST': 'ship_to',
                'SF': 'ship_from',
                'BT': 'bill_to'
            }

            ctx = entity_context_n1.get(entity_code, '')

            if element_id == 'N102' and ctx:
                return f"{ctx}_name"
            elif element_id == 'N103' and ctx:
                return f"{ctx}_id_qualifier"
            elif element_id == 'N104' and ctx:
                return f"{ctx}_identifier"

        # Handle DMG (Demographic Information) segment
        elif segment_id == 'DMG':
            # DMG context depends on the preceding NM1 or loop
            if loop_type in ['subscriber', 'insured'] or 'IL' in str(entity_code):
                prefix = 'insured'
            elif loop_type == 'patient' or 'QC' in str(entity_code):
                prefix = 'patient'
            elif loop_type == 'dependent':
                prefix = 'dependent'
            else:
                prefix = 'individual'

            if element_id == 'DMG02':
                return f'{prefix}_birth_date'
            elif element_id == 'DMG03':
                return f'{prefix}_gender_code'
            elif element_id == 'DMG04':
                return f'{prefix}_marital_status'
            elif element_id == 'DMG05':
                return f'{prefix}_ethnicity'
            elif element_id == 'DMG06':
                return f'{prefix}_citizenship'
            elif element_id == 'DMG07':
                return f'{prefix}_country_code'
            elif element_id == 'DMG10':
                return f'{prefix}_race'

        # Handle REF (Reference Identification) segment
        elif segment_id == 'REF':
            ref_qualifier = context.get('ref_qualifier', '')
            # REF01 qualifier codes determine the type of reference
            ref_types = {
                '0B': 'state_license_number',
                '1G': 'provider_upin',
                '2U': 'payer_id',
                '4N': 'special_payment_reference',
                '6R': 'provider_control_number',
                '9A': 'repriced_claim_reference',
                '9F': 'referral_number',
                'BB': 'authorization_number',
                'CE': 'class_of_contract',
                'D9': 'claim_number',
                'EA': 'medical_record_id',
                'EI': 'employer_id',
                'F8': 'original_reference',
                'G1': 'prior_authorization',
                'IG': 'insurance_policy_number',
                'SY': 'social_security_number'
            }

            if ref_qualifier and ref_qualifier in ref_types:
                base = ref_types[ref_qualifier]
                if element_id == 'REF02':
                    return base

        # Handle DTP (Date or Time Period) segment
        elif segment_id == 'DTP' or segment_id == 'DTM':
            date_qualifier = context.get('date_qualifier', '')
            # DTP01/DTM01 qualifier codes determine the type of date
            date_types = {
                '096': 'discharge_date',
                '097': 'delivery_date',
                '098': 'begin_therapy_date',
                '102': 'issue_date',
                '139': 'accident_date',
                '150': 'service_date',
                '151': 'service_date',
                '232': 'claim_statement_date',
                '233': 'claim_statement_end_date',
                '291': 'signature_date',
                '304': 'latest_visit_date',
                '405': 'production_date',
                '431': 'onset_of_symptoms_date',
                '434': 'statement_date',
                '435': 'admission_date',
                '439': 'accident_date',
                '441': 'onset_of_illness_date',
                '454': 'initial_treatment_date',
                '455': 'latest_menstrual_period_date',
                '471': 'prescription_date',
                '472': 'service_date',
                '484': 'last_menstrual_period_date',
                '573': 'date_claim_paid'
            }

            if date_qualifier and date_qualifier in date_types:
                base = date_types[date_qualifier]
                if element_id in ['DTP02', 'DTM02']:
                    return base

        # Handle CLM (Health Claim) segment
        elif segment_id == 'CLM':
            clm_fields = {
                'CLM01': 'patient_control_number',
                'CLM02': 'total_claim_charge_amount',
                'CLM05': 'facility_code_value',
                'CLM06': 'provider_signature_on_file',
                'CLM07': 'assignment_plan_participation',
                'CLM08': 'assignment_of_benefits',
                'CLM09': 'release_of_information',
                'CLM10': 'patient_signature_source',
                'CLM11': 'related_causes_info',
                'CLM12': 'special_program_code'
            }

            if element_id in clm_fields:
                return clm_fields[element_id]

        # Handle SVC (Service Payment Information) segment
        elif segment_id == 'SVC':
            svc_fields = {
                'SVC01': 'composite_medical_procedure_identifier',
                'SVC02': 'line_item_charge_amount',
                'SVC03': 'line_item_provider_payment_amount',
                'SVC04': 'revenue_code',
                'SVC05': 'units_of_service_paid',
                'SVC06': 'composite_medical_procedure_identifier_2',
                'SVC07': 'original_units_of_service'
            }

            if element_id in svc_fields:
                return svc_fields[element_id]

        # Handle CAS (Claims Adjustment) segment
        elif segment_id == 'CAS':
            cas_fields = {
                'CAS01': 'claim_adjustment_group_code',
                'CAS02': 'adjustment_reason_code',
                'CAS03': 'adjustment_amount',
                'CAS04': 'adjustment_quantity'
            }

            if element_id in cas_fields:
                return cas_fields[element_id]

        # Handle generic address segments (N3, N4)
        elif segment_id in ['N3', 'N4']:
            if loop_type:
                # Replace generic location/address with context
                name = name.replace('Ambulance Drop-off Location', f'{loop_type.title()} Address')
                name = name.replace('Ambulance Drop-off', loop_type.title())

                # N3 = Address Information
                if segment_id == 'N3':
                    if element_id == 'N301':
                        return f'{loop_type}_address_line_1'
                    elif element_id == 'N302':
                        return f'{loop_type}_address_line_2'

                # N4 = Geographic Location
                elif segment_id == 'N4':
                    if element_id == 'N401':
                        return f'{loop_type}_city'
                    elif element_id == 'N402':
                        return f'{loop_type}_state'
                    elif element_id == 'N403':
                        return f'{loop_type}_zip_code'
                    elif element_id == 'N404':
                        return f'{loop_type}_country_code'

        # Handle PER (Administrative Communications Contact) segment
        elif segment_id == 'PER':
            per_fields = {
                'PER01': 'contact_function_code',
                'PER02': 'contact_name',
                'PER03': 'communication_number_qualifier_1',
                'PER04': 'communication_number_1',
                'PER05': 'communication_number_qualifier_2',
                'PER06': 'communication_number_2',
                'PER07': 'communication_number_qualifier_3',
                'PER08': 'communication_number_3'
            }

            if element_id in per_fields:
                if loop_type:
                    return f'{loop_type}_{per_fields[element_id]}'
                return per_fields[element_id]

        return name


# Global instance for convenience
_loader_instance = None

def get_loader() -> MapElementLoader:
    """Get the global MapElementLoader instance"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = MapElementLoader()
    return _loader_instance


def get_element_name(map_filename: str, segment_id: str, element_id: str) -> str:
    """
    Convenience function to get element name

    Args:
        map_filename: Map file to use
        segment_id: Segment ID
        element_id: Element ID

    Returns:
        Descriptive element name
    """
    return get_loader().get_element_name(map_filename, segment_id, element_id)


def format_element_name(name: str, element_id: str) -> str:
    """
    Convenience function to format element name

    Args:
        name: Descriptive element name
        element_id: Element ID

    Returns:
        Formatted field name
    """
    return get_loader().format_element_name_for_json(name, element_id)