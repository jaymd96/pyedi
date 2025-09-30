#!/usr/bin/env python3
"""
Fixed Structured EDI Formatter Module

This is a fixed version of StructuredFormatter that addresses:
1. Multi-transaction processing (returns all transactions, not just first)
2. Consistent array handling for repeatable segments
3. Proper HI segment field naming (hi01_01, hi02_01, etc.)
4. Loop structures that repeat are always arrays
5. Consistent segment structure (always arrays for repeatable segments)
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from collections import OrderedDict
from datetime import datetime
import re

from ..code_sets import edi_codes as codes
from .map_loader import MapElementLoader
from .segment_handlers import SegmentHandlers


class StructuredFormatter:
    """Transform generic X12 JSON to structured format preserving X12 organization

    FIXED: Now handles multiple transactions properly and consistent array handling"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.map_loader = MapElementLoader()

    def format(self, generic_json: Dict[str, Any], include_technical: bool = True) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Format generic JSON to structured format with meaningful field names

        FIXED: Now processes ALL transactions, not just the first one

        Args:
            generic_json: Output from X12Parser
            include_technical: Include original codes alongside descriptions (for compatibility)

        Returns:
            Single structured JSON for single transaction, or list for multiple transactions
        """
        try:
            # Store transaction type and map file for element name lookups
            self._current_transaction_type = generic_json.get('transaction_type')
            self._current_map_file = generic_json.get('map_file')

            # Get ALL transactions (FIXED: was only getting first)
            transactions = generic_json.get('transactions', [])
            if not transactions:
                return generic_json

            # Process each transaction
            results = []
            for transaction in transactions:
                segments = transaction.get('segments', [])

                # Build the structured output for this transaction
                result = OrderedDict()

                # Add interchange and functional group metadata
                result['interchange'] = self._format_interchange(generic_json)
                result['functional_group'] = self._format_functional_group(generic_json)

                # Group segments into heading and detail sections
                heading_segments, detail_segments = self._partition_segments(segments)

                # Process heading section
                if heading_segments:
                    result['heading'] = self._process_segment_group(heading_segments)

                # Process detail section
                if detail_segments:
                    result['detail'] = self._process_segment_group(detail_segments)

                # Add transaction type for convenience
                result['transaction_type'] = self._current_transaction_type

                results.append(result)

            # Return single dict for single transaction, list for multiple
            return results[0] if len(results) == 1 else results

        except Exception as e:
            self.logger.error(f"Error transforming to structured format: {e}", exc_info=True)
            return generic_json

    def _format_interchange(self, generic_json: Dict[str, Any]) -> Dict[str, Any]:
        """Format interchange information"""
        interchange = generic_json.get('interchange', {})
        return {
            'sender_id': interchange.get('sender_id'),
            'sender_qualifier': interchange.get('sender_qualifier'),
            'receiver_id': interchange.get('receiver_id'),
            'receiver_qualifier': interchange.get('receiver_qualifier'),
            'date': interchange.get('date'),
            'time': interchange.get('time'),
            'control_number': interchange.get('control_number'),
            'version': interchange.get('version'),
            'test_indicator': interchange.get('test_indicator')
        }

    def _format_functional_group(self, generic_json: Dict[str, Any]) -> Dict[str, Any]:
        """Format functional group information"""
        groups = generic_json.get('functional_groups', [])
        if not groups:
            return {}

        group = groups[0]
        return {
            'functional_id': group.get('functional_id'),
            'sender_code': group.get('sender_code'),
            'receiver_code': group.get('receiver_code'),
            'date': group.get('date'),
            'time': group.get('time'),
            'control_number': group.get('control_number'),
            'version': group.get('version')
        }

    def _partition_segments(self, segments: List[Dict[str, Any]]) -> tuple:
        """
        Partition segments into heading and detail sections.
        Heading typically includes setup segments like ST, BGN/BHT, N1 loops, etc.
        Detail includes the main content like claims, members, service lines, etc.
        """
        heading_segments = []
        detail_segments = []

        # Common heading loop IDs and segment IDs
        heading_loops = {'1000A', '1000B', '1000C'}  # Submitter, Receiver, etc.
        heading_segment_ids = {'ST', 'BHT', 'BGN', 'BPR', 'TRN', 'CUR', 'REF', 'DTM', 'BGN'}

        # Segments that typically start the detail section
        detail_start_segments = {'CLP', 'CLM', 'INS', 'HL', 'LX'}

        in_detail = False

        for segment in segments:
            seg_id = segment.get('segment_id')
            loop_id = segment.get('loop_id', '')

            # Check if we've entered the detail section
            if seg_id in detail_start_segments:
                in_detail = True

            # Classify segment
            if not in_detail:
                # Check if it's a heading segment
                if seg_id in heading_segment_ids or loop_id in heading_loops:
                    heading_segments.append(segment)
                elif seg_id == 'N1':
                    # N1 segments in the beginning are usually heading
                    heading_segments.append(segment)
                else:
                    detail_segments.append(segment)
            else:
                detail_segments.append(segment)

        return heading_segments, detail_segments

    def _process_segment_group(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a group of segments into structured format"""
        result = OrderedDict()

        # Group segments by loop
        loops = self._group_segments_by_loop(segments)

        for loop_key, loop_segments in loops.items():
            if loop_key == 'no_loop':
                # Process segments not in a loop
                for segment in loop_segments:
                    seg_key = self._create_segment_key(segment)
                    seg_data = self._format_segment(segment)

                    # FIXED: Always use arrays for repeatable segments
                    if seg_key in result:
                        # Convert to list if not already
                        if not isinstance(result[seg_key], list):
                            result[seg_key] = [result[seg_key]]
                        result[seg_key].append(seg_data)
                    else:
                        # Check if this segment typically repeats
                        if self._is_repeatable_segment(segment):
                            result[seg_key] = [seg_data]
                        else:
                            result[seg_key] = seg_data
            else:
                # Process loop
                loop_name = self._format_loop_name(loop_key, loop_segments)
                loop_data = self._process_loop(loop_segments)

                # FIXED: Loops that can repeat should always be arrays
                if loop_name in result:
                    # Already exists, must be a repeating loop
                    if not isinstance(result[loop_name], list):
                        result[loop_name] = [result[loop_name]]
                    result[loop_name].append(loop_data)
                else:
                    # Check if this loop typically repeats
                    if self._is_repeating_loop(loop_key, loop_segments):
                        result[loop_name] = [loop_data]
                    else:
                        result[loop_name] = loop_data

        return result

    def _group_segments_by_loop(self, segments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group segments by their loop ID and instance"""
        loops = OrderedDict()

        for segment in segments:
            loop_id = segment.get('loop_id')
            loop_instance = segment.get('loop_instance', 0)

            if loop_id:
                # Create a unique key for this loop instance
                loop_key = f"{loop_id}_{loop_instance}"
            else:
                loop_key = 'no_loop'

            if loop_key not in loops:
                loops[loop_key] = []
            loops[loop_key].append(segment)

        return loops

    def _process_loop(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process segments within a loop"""
        result = OrderedDict()

        # Group segments by type within the loop
        segment_groups = OrderedDict()
        for segment in segments:
            seg_id = segment.get('segment_id')
            if seg_id not in segment_groups:
                segment_groups[seg_id] = []
            segment_groups[seg_id].append(segment)

        # Process each segment type
        for seg_id, seg_list in segment_groups.items():
            seg_key = self._create_segment_key(seg_list[0])

            # FIXED: Always use arrays for segments that can repeat
            if len(seg_list) == 1 and not self._is_repeatable_segment(seg_list[0]):
                result[seg_key] = self._format_segment(seg_list[0])
            else:
                # Multiple segments or repeatable segment - always use array
                result[seg_key] = [self._format_segment(seg) for seg in seg_list]

        return result

    def _format_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single segment with descriptive field names and position numbers"""
        result = OrderedDict()
        elements = segment.get('elements', {})
        seg_id = segment.get('segment_id', '')
        loop_id = segment.get('loop_id', '')
        loop_type = self._get_loop_type(loop_id, segment)

        # Build context for naming
        context = {
            'segment_id': seg_id,
            'loop_id': loop_id,
            'loop_type': loop_type
        }

        # Extract entity code for NM1/N1 segments to provide context
        if seg_id == 'NM1' and 'NM101' in elements:
            entity_code = self._get_element_value_raw(elements.get('NM101'))
            context['entity_code'] = entity_code
            # Also store entity type (1=person, 2=org)
            if 'NM102' in elements:
                context['entity_type'] = self._get_element_value_raw(elements.get('NM102'))
            # Store for use by subsequent segments in same loop
            self._current_entity_code = entity_code
        elif seg_id == 'N1' and 'N101' in elements:
            entity_code = self._get_element_value_raw(elements.get('N101'))
            context['entity_code'] = entity_code
            self._current_entity_code = entity_code
        elif hasattr(self, '_current_entity_code'):
            # Use stored entity code for other segments in same loop
            context['entity_code'] = self._current_entity_code

        # Extract qualifiers for REF and DTP/DTM segments
        if seg_id == 'REF' and 'REF01' in elements:
            context['ref_qualifier'] = self._get_element_value_raw(elements.get('REF01'))
        elif seg_id in ['DTP', 'DTM'] and f'{seg_id}01' in elements:
            context['date_qualifier'] = self._get_element_value_raw(elements.get(f'{seg_id}01'))

        # Get transaction type from the root context if available
        transaction_type = getattr(self, '_current_transaction_type', None)

        # SPECIAL HANDLING FOR COMPLEX SEGMENTS
        # These segments have composite elements or special structure requiring custom parsing

        if seg_id == 'HI':
            # Diagnosis codes segment
            return self._format_hi_segment(elements)
        elif seg_id == 'BPR':
            # 835 Payment information
            return SegmentHandlers.handle_bpr_segment(elements)
        elif seg_id == 'TRN':
            # 835 Trace/Check number
            return SegmentHandlers.handle_trn_segment(elements)
        elif seg_id == 'CLP':
            # 835 Claim payment information
            return SegmentHandlers.handle_clp_segment(elements)
        elif seg_id == 'CAS':
            # Claim adjustment segment
            return SegmentHandlers.handle_cas_segment(elements)
        elif seg_id == 'SVC':
            # 835 Service payment information
            return SegmentHandlers.handle_svc_segment(elements)
        elif seg_id == 'AMT':
            # Amount segment with qualifier
            return SegmentHandlers.handle_amt_segment(elements)
        elif seg_id == 'QTY':
            # Quantity segment with qualifier
            return SegmentHandlers.handle_qty_segment(elements)
        elif seg_id == 'CLM':
            # 837 Claim information with composite facility code
            return SegmentHandlers.handle_clm_segment(elements)
        elif seg_id == 'PWK':
            # Paperwork/Attachment segment
            return SegmentHandlers.handle_pwk_segment(elements)
        elif seg_id == 'TS3':
            # 835 Provider summary
            return SegmentHandlers.handle_ts3_segment(elements)
        elif seg_id == 'RDM':
            # 835 Remittance delivery method
            return SegmentHandlers.handle_rdm_segment(elements)

        for elem_id, elem_data in elements.items():
            # Extract position number from element ID (e.g., 'BGN01' -> '01')
            position = re.search(r'\d+$', elem_id)
            if position:
                position_num = position.group()
            else:
                position_num = elem_id

            # Get element name and value
            if isinstance(elem_data, dict):
                # First try to use the name from the parser if available
                elem_name = elem_data.get('name')
                elem_value = elem_data.get('value')

                # Handle composite elements
                if elem_data.get('composite'):
                    elem_value = elem_data.get('components', [])
            else:
                elem_name = None
                elem_value = elem_data

            # If no name from parser, try to get it from the map loader
            if not elem_name and self._current_map_file:
                elem_name = self.map_loader.get_element_name(self._current_map_file, seg_id, elem_id)

            # If still no name, use the element ID
            if not elem_name or elem_name == elem_id:
                elem_name = elem_id
                # Use simple format for fallback
                field_name = self._format_field_name_improved(elem_name, elem_id, context)
            else:
                # Use improved field naming without position suffixes
                field_name = self._format_field_name_improved(elem_name, elem_id, context)

            # Apply any data type conversions
            if elem_value is not None:
                elem_value = self._convert_value(elem_value, elem_name, elem_id)

            result[field_name] = elem_value

        return result

    def _format_hi_segment(self, elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        FIXED: Special formatting for HI segment to properly name diagnosis fields

        HI segment has composite elements HI01, HI02, etc.
        Each should be named hiXX_01 where XX is the position (01, 02, 03...)
        """
        result = OrderedDict()

        # Process each HI element (HI01, HI02, etc.)
        for elem_id, elem_data in sorted(elements.items()):
            # Extract position from element ID (HI01 -> 01, HI02 -> 02)
            match = re.match(r'HI(\d+)', elem_id)
            if not match:
                continue

            position = match.group(1)

            # Get the value (usually a composite with diagnosis qualifier and code)
            if isinstance(elem_data, dict):
                elem_value = elem_data.get('components', elem_data.get('value'))
            else:
                elem_value = elem_data

            # Create proper field name (hi01_01, hi02_01, etc.)
            field_name = f"hi{position}_01"
            result[field_name] = elem_value

        return result

    def _is_repeatable_segment(self, segment: Dict[str, Any]) -> bool:
        """
        Determine if a segment type typically repeats

        FIXED: More accurate detection of repeatable segments
        """
        seg_id = segment.get('segment_id', '')

        # Common repeatable segments
        repeatable_segments = {
            'NM1',  # Multiple entities in a loop
            'N1',   # Multiple parties
            'REF',  # Multiple references
            'DTP',  # Multiple dates
            'DTM',  # Multiple dates/times
            'CAS',  # Multiple adjustments
            'AMT',  # Multiple amounts
            'QTY',  # Multiple quantities
            'HI',   # Multiple diagnoses (but handled specially)
            'LX',   # Service lines
            'SV1', 'SV2', 'SV3',  # Service segments
            'PWK',  # Paperwork
            'PER',  # Contact information
            'DMG',  # Demographics (can repeat in some contexts)
        }

        return seg_id in repeatable_segments

    def _is_repeating_loop(self, loop_key: str, segments: List[Dict[str, Any]] = None) -> bool:
        """
        Check if a loop can repeat

        FIXED: Better detection of repeating loops
        """
        # Extract loop ID from key
        parts = loop_key.rsplit('_', 1)
        loop_id = parts[0] if parts else loop_key

        # Known repeating loops in healthcare transactions
        repeating_loops = {
            # 837 Claims
            '2000A', '2000B', '2000C',  # Hierarchical levels
            '2300',   # Claim information
            '2310A', '2310B', '2310C',  # Providers
            '2320',   # Other insurance
            '2400',   # Service lines
            '2420A', '2420B', '2420C',  # Line providers

            # 835 Remittance
            '1000A', '1000B',  # Payer/Payee
            '2000',   # Header number
            '2100',   # Claim payment
            '2110',   # Service payment

            # 834 Enrollment
            '2000',   # Member level
            '2300',   # Health coverage
            '2310',   # Provider information

            # Common
            '1000',   # Party identification loops often repeat
            '2000',   # Detail loops often repeat
        }

        # Check if this loop ID is known to repeat
        for repeating_id in repeating_loops:
            if loop_id.startswith(repeating_id):
                return True

        # Check metadata from segments
        if segments:
            for segment in segments:
                max_use = segment.get('loop_max_use')
                if max_use:
                    if max_use == 'unbounded':
                        return True
                    try:
                        if int(max_use) > 1:
                            return True
                    except (ValueError, TypeError):
                        pass

        # Special case: claim and service loops should always be arrays
        if segments and len(segments) > 0:
            first_seg = segments[0]
            seg_id = first_seg.get('segment_id', '')
            if seg_id in ['CLM', 'CLP', 'SVC', 'LX']:
                return True

        return False

    def _get_element_value_raw(self, element: Any) -> str:
        """Get raw element value without conversion"""
        if isinstance(element, dict):
            return element.get('value', '')
        return str(element) if element else ''

    def _get_loop_type(self, loop_id: str, segment: Dict[str, Any]) -> str:
        """Determine loop type from loop ID and context"""
        # Common healthcare loop patterns
        if 'payer' in loop_id.lower() or loop_id in ['1000A', '1000']:
            return 'payer'
        elif 'payee' in loop_id.lower() or loop_id in ['1000B']:
            return 'payee'
        elif 'subscriber' in loop_id.lower() or loop_id in ['2000B', '2010BA']:
            return 'subscriber'
        elif 'patient' in loop_id.lower() or loop_id in ['2000C', '2010CA']:
            return 'patient'
        elif 'billing' in loop_id.lower() or loop_id in ['2010AA']:
            return 'billing_provider'
        elif 'rendering' in loop_id.lower() or loop_id in ['2310B', '2420A']:
            return 'rendering_provider'
        elif 'referring' in loop_id.lower() or loop_id in ['2310A', '2420B']:
            return 'referring_provider'
        elif 'receiver' in loop_id.lower() or loop_id in ['1000B']:
            return 'receiver'
        elif 'submitter' in loop_id.lower() or loop_id in ['1000A']:
            return 'submitter'

        # Check segment name hints
        seg_name = segment.get('segment_name', '').lower()
        if 'payer' in seg_name:
            return 'payer'
        elif 'payee' in seg_name:
            return 'payee'
        elif 'patient' in seg_name:
            return 'patient'
        elif 'subscriber' in seg_name or 'insured' in seg_name:
            return 'subscriber'
        elif 'provider' in seg_name:
            return 'provider'

        return ''

    def _format_field_name(self, name: str, position: str) -> str:
        """Format field name with position number in snake_case"""
        # Convert name to snake_case
        name = re.sub(r'[^\w\s]', '', name)  # Remove special characters
        name = re.sub(r'\s+', '_', name)  # Replace spaces with underscores
        name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)  # Handle acronyms
        name = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', name)  # Handle camelCase
        name = name.lower()

        # Remove redundant words
        name = re.sub(r'_code_code', '_code', name)
        name = re.sub(r'_id_id', '_id', name)
        name = re.sub(r'_number_number', '_number', name)

        # Add position number
        return f"{name}_{position.zfill(2)}"

    def _format_field_name_improved(self, name: str, elem_id: str, context: Dict[str, str]) -> str:
        """
        Format field name with improved semantic naming

        FIXED: Creates cleaner field names without unnecessary position suffixes
        """
        segment_id = context.get('segment_id', '')
        entity_code = context.get('entity_code', '')

        # Map entity codes to cleaner context names (used across segments)
        entity_context = {
            'IL': 'insured',
            'QC': 'patient',
            'PR': 'payer',
            'PE': 'payee',
            '40': 'receiver',
            '41': 'submitter',
            '71': 'attending_physician',
            '72': 'operating_physician',
            '73': 'other_physician',
            '77': 'service_location',
            '82': 'rendering_provider',
            '85': 'billing_provider',
            '87': 'pay_to_provider',
            'DN': 'referring_provider',
            'DK': 'ordering_provider',
            'DQ': 'supervising_provider',
            'FA': 'facility'
        }

        ctx = entity_context.get(entity_code, '')
        entity_type = context.get('entity_type', '')

        # Special handling for NM1 segments
        if segment_id == 'NM1':
            # Map NM1 elements to clean field names
            field_map = {
                'NM101': 'entity_identifier_code',
                'NM102': 'entity_type_qualifier',
                'NM103': f"{ctx}_{'last_name' if entity_type == '1' else 'name'}" if ctx else 'name',
                'NM104': f"{ctx}_first_name" if ctx and entity_type == '1' else 'first_name',
                'NM105': f"{ctx}_middle_name" if ctx and entity_type == '1' else 'middle_name',
                'NM106': f"{ctx}_prefix" if ctx else 'prefix',
                'NM107': f"{ctx}_suffix" if ctx else 'suffix',
                'NM108': f"{ctx}_id_qualifier" if ctx else 'id_qualifier',
                'NM109': f"{ctx}_id" if ctx else 'identifier'
            }

            if elem_id in field_map:
                return field_map[elem_id]

        # Special handling for N1 segments (Party Identification)
        elif segment_id == 'N1':
            field_map = {
                'N101': 'entity_identifier_code',
                'N102': 'name',
                'N103': 'id_qualifier',
                'N104': 'identifier'
            }

            if elem_id in field_map:
                return field_map[elem_id]

        # Special handling for N3 segments (Address)
        elif segment_id == 'N3':
            field_map = {
                'N301': 'address_line_1',
                'N302': 'address_line_2'
            }

            if elem_id in field_map:
                ctx = entity_context.get(entity_code, '')
                if ctx:
                    return f"{ctx}_{field_map[elem_id]}"
                return field_map[elem_id]

        # Special handling for N4 segments (City/State/Zip)
        elif segment_id == 'N4':
            field_map = {
                'N401': 'city',
                'N402': 'state',
                'N403': 'zip_code',
                'N404': 'country_code'
            }

            if elem_id in field_map:
                ctx = entity_context.get(entity_code, '')
                if ctx:
                    return f"{ctx}_{field_map[elem_id]}"
                return field_map[elem_id]

        # Special handling for CLM segments (Claim Information)
        elif segment_id == 'CLM':
            field_map = {
                'CLM01': 'claim_id',
                'CLM02': 'total_charge_amount',
                'CLM03': 'claim_filing_indicator',
                'CLM04': 'non_institutional_claim_type',
                'CLM05': 'facility_code',
                'CLM06': 'claim_frequency_code',
                'CLM07': 'provider_signature',
                'CLM08': 'assignment_code',
                'CLM09': 'benefits_assignment',
                'CLM10': 'release_info_code',
                'CLM11': 'patient_signature_code',
                'CLM12': 'related_causes_code'
            }

            if elem_id in field_map:
                return field_map[elem_id]

        # Special handling for CLP segments (Claim Payment)
        elif segment_id == 'CLP':
            field_map = {
                'CLP01': 'claim_id',
                'CLP02': 'claim_status',
                'CLP03': 'total_charge_amount',
                'CLP04': 'total_paid_amount',
                'CLP05': 'patient_responsibility',
                'CLP06': 'claim_filing_indicator',
                'CLP07': 'payer_claim_control_number',
                'CLP08': 'facility_type',
                'CLP09': 'claim_frequency_code'
            }

            if elem_id in field_map:
                return field_map[elem_id]

        # Special handling for SVC segments (Service Payment)
        elif segment_id == 'SVC':
            field_map = {
                'SVC01': 'procedure_code',
                'SVC02': 'charge_amount',
                'SVC03': 'paid_amount',
                'SVC04': 'revenue_code',
                'SVC05': 'units_paid',
                'SVC06': 'procedure_code_2',
                'SVC07': 'units_original'
            }

            if elem_id in field_map:
                return field_map[elem_id]

        # Special handling for CAS segments (Claim Adjustment)
        elif segment_id == 'CAS':
            field_map = {
                'CAS01': 'adjustment_group_code',
                'CAS02': 'adjustment_reason_code',
                'CAS03': 'adjustment_amount',
                'CAS04': 'adjustment_quantity',
                'CAS05': 'adjustment_reason_code_2',
                'CAS06': 'adjustment_amount_2',
                'CAS07': 'adjustment_quantity_2'
            }

            if elem_id in field_map:
                return field_map[elem_id]

        # Special handling for DTM/DTP segments (Date/Time)
        elif segment_id in ['DTM', 'DTP']:
            qualifier = context.get('date_qualifier', '')

            # Map common date qualifiers to meaningful names
            date_types = {
                '036': 'expiration_date',
                '050': 'received_date',
                '096': 'discharge_date',
                '097': 'delivery_date',
                '098': 'certification_date',
                '102': 'issue_date',
                '139': 'claim_date',
                '232': 'claim_statement_period_start',
                '233': 'claim_statement_period_end',
                '290': 'coordination_of_benefits',
                '291': 'signature_date',
                '304': 'latest_visit',
                '360': 'initial_disability',
                '361': 'last_disability',
                '386': 'employment_begin',
                '431': 'onset_of_illness',
                '434': 'statement_date',
                '435': 'admission_date',
                '454': 'initial_treatment',
                '471': 'prescription_date',
                '472': 'service_date',
                '484': 'last_menstrual_period',
                '573': 'date_claim_paid'
            }

            if qualifier in date_types:
                return date_types[qualifier]
            elif elem_id.endswith('01'):
                return 'date_qualifier'
            elif elem_id.endswith('02'):
                return 'date_format'
            elif elem_id.endswith('03'):
                return 'date_value'

        # Special handling for REF segments (Reference)
        elif segment_id == 'REF':
            qualifier = context.get('ref_qualifier', '')

            # Map common reference qualifiers to meaningful names
            ref_types = {
                '0B': 'state_license_number',
                '0F': 'subluxation_documentation',
                '0K': 'policy_number',
                '1A': 'blue_cross_provider_id',
                '1B': 'blue_shield_provider_id',
                '1C': 'medicare_provider_id',
                '1D': 'medicaid_provider_id',
                '1G': 'provider_upin',
                '1H': 'champus_id',
                '1J': 'facility_id',
                '1K': 'payor_claim_number',
                '1L': 'group_number',
                '1S': 'ambulatory_patient_group',
                '1W': 'member_id',
                '2U': 'payer_id',
                '4N': 'special_payment_reference',
                '6P': 'group_number',
                '6R': 'provider_control_number',
                '9A': 'repriced_claim_reference',
                '9B': 'repriced_line_item_reference',
                '9C': 'adjusted_repriced_claim',
                '9D': 'adjusted_repriced_line',
                '9F': 'referral_number',
                'D9': 'claim_number',
                'EA': 'medical_record_number',
                'EI': 'employer_id',
                'EJ': 'patient_account_number',
                'F8': 'original_reference_number',
                'G1': 'prior_authorization',
                'G3': 'predetermination_of_benefits',
                'HPI': 'health_plan_id',
                'IG': 'insurance_policy_number',
                'LU': 'location_number',
                'N5': 'provider_plan_network_id',
                'N7': 'facility_network_id',
                'SY': 'social_security_number',
                'TJ': 'federal_tax_id'
            }

            if qualifier in ref_types:
                return ref_types[qualifier]
            elif elem_id.endswith('01'):
                return 'reference_qualifier'
            elif elem_id.endswith('02'):
                return 'reference_value'

        # Default formatting - clean up the name without position suffix
        # Convert to snake_case
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
        name = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', name)
        name = name.lower()

        # Remove redundant words
        name = re.sub(r'_code_code', '_code', name)
        name = re.sub(r'_id_id', '_id', name)
        name = re.sub(r'_identifier_identifier', '_identifier', name)
        name = re.sub(r'_number_number', '_number', name)

        # For key fields, don't add position suffix
        if any(key in name for key in ['identifier', 'code', 'date', 'amount', 'name', 'address', 'city', 'state', 'zip']):
            return name

        # Extract position for other fields
        position = re.search(r'\d+$', elem_id)
        if position:
            position_num = position.group()
            # Only add position if it's meaningful
            if int(position_num) > 1 or segment_id in ['ST', 'SE', 'GS', 'GE']:
                return f"{name}_{position_num.zfill(2)}"

        return name

    def _create_segment_key(self, segment: Dict[str, Any]) -> str:
        """Create a descriptive key for a segment"""
        seg_id = segment.get('segment_id')
        seg_name = segment.get('segment_name', seg_id)

        # Convert to snake_case
        key = re.sub(r'[^\w\s]', '', seg_name)
        key = re.sub(r'\s+', '_', key)
        key = key.lower()

        # Add segment ID if not already included
        if seg_id and seg_id.lower() not in key:
            key = f"{key}_{seg_id}"

        return key

    def _format_loop_name(self, loop_key: str, segments: List[Dict[str, Any]]) -> str:
        """Create a descriptive name for a loop"""
        # Extract loop ID from key (format: "loopid_instance")
        parts = loop_key.rsplit('_', 1)
        loop_id = parts[0] if parts else loop_key

        # Get the first segment to help identify the loop
        first_segment = segments[0] if segments else None
        if first_segment:
            seg_id = first_segment.get('segment_id')
            seg_name = first_segment.get('segment_name', seg_id)

            # Try to get a descriptive name from the segment
            if seg_id == 'N1' or seg_id == 'NM1':
                # Entity loops - try to get entity type
                entity_code = self._get_element_value(first_segment, f'{seg_id}01')
                entity_desc = codes.get_entity_description(entity_code) if entity_code else seg_name

                # Format the name
                name = re.sub(r'[^\w\s]', '', entity_desc)
                name = re.sub(r'\s+', '_', name)
                name = name.lower()

                return f"{name}_{seg_id}_loop"
            else:
                # Generic loop name
                seg_key = re.sub(r'[^\w\s]', '', seg_name)
                seg_key = re.sub(r'\s+', '_', seg_key)
                seg_key = seg_key.lower()

                return f"{seg_key}_loop"

        # Fallback to loop ID
        return f"{loop_id}_loop"

    def _get_element_value(self, segment: Dict[str, Any], element_id: str) -> Any:
        """Get element value from segment"""
        elements = segment.get('elements', {})
        element = elements.get(element_id)

        if isinstance(element, dict):
            if 'value' in element:
                return element['value']
            elif element.get('composite'):
                return element.get('components', [])

        return element

    def _convert_value(self, value: Any, name: str, elem_id: str) -> Any:
        """Convert value based on its type or name"""
        if value is None or value == '':
            return None

        # Check for date patterns
        if any(word in name.lower() for word in ['date', 'datetime']):
            return self._format_date(value)

        # Check for time patterns
        if 'time' in name.lower() and 'datetime' not in name.lower():
            return self._format_time(value)

        # Check for amount/money patterns - but exclude method/format codes
        name_lower = name.lower()
        if ('method' not in name_lower and 'format' not in name_lower and 'code' not in name_lower):
            if any(word in name_lower for word in ['amount', 'charge', 'paid', 'payment', 'price', 'cost', 'fee']):
                return self._safe_float(value)

        # Check for quantity/count patterns
        if any(word in name.lower() for word in ['quantity', 'count', 'units', 'number_of']):
            try:
                # Try integer first for counts
                return int(value)
            except (ValueError, TypeError):
                return self._safe_float(value)

        # Check for control numbers (should remain as strings even if numeric)
        if 'control_number' in name.lower() or 'reference_number' in name.lower():
            return str(value)

        return value

    def _format_date(self, date_str: str) -> str:
        """Format date from CCYYMMDD or YYMMDD to YYYY-MM-DD"""
        if not date_str or not isinstance(date_str, str):
            return date_str

        try:
            if len(date_str) == 8:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            elif len(date_str) == 6:
                year_prefix = "20" if int(date_str[:2]) <= 50 else "19"
                return f"{year_prefix}{date_str[:2]}-{date_str[2:4]}-{date_str[4:]}"
            else:
                return date_str
        except:
            return date_str

    def _format_time(self, time_str: str) -> str:
        """Format time from HHMM or HHMMSS to HH:MM or HH:MM:SS"""
        if not time_str or not isinstance(time_str, str):
            return time_str

        try:
            if len(time_str) == 4:
                return f"{time_str[:2]}:{time_str[2:]}"
            elif len(time_str) == 6:
                return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
            else:
                return time_str
        except:
            return time_str

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


# Convenience function for backwards compatibility and ease of use
def format_structured(generic_json: Dict[str, Any], include_technical: bool = True) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Format generic X12 JSON to structured format

    FIXED: Now processes ALL transactions, not just the first one

    Args:
        generic_json: Output from X12Parser
        include_technical: Include original codes alongside descriptions (for compatibility)

    Returns:
        Single structured JSON for single transaction, or list for multiple transactions
    """
    formatter = StructuredFormatter()
    return formatter.format(generic_json, include_technical)