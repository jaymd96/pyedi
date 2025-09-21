#!/usr/bin/env python3
"""
Structured EDI Formatter Module

Transforms generic X12 JSON output into a structured format that preserves X12
organization while adding meaningful field names and code descriptions.
Leverages both pyx12's built-in names and custom code mappings.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from collections import OrderedDict
from datetime import datetime

from ..code_sets import edi_codes as codes


class StructuredFormatter:
    """Transform generic X12 JSON to structured format preserving X12 organization"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def format(self, generic_json: Dict[str, Any], include_technical: bool = True) -> Dict[str, Any]:
        """
        Format generic JSON to structured format with meaningful field names

        Args:
            generic_json: Output from X12Parser
            include_technical: Include original codes alongside descriptions

        Returns:
            Structured JSON with meaningful field names and preserved X12 organization
        """
        try:
            transaction_type = generic_json.get('transaction_type')

            if transaction_type == '835':
                return self._transform_835(generic_json, include_technical)
            elif transaction_type == '837':
                return self._transform_837(generic_json, include_technical)
            elif transaction_type == '834':
                return self._transform_834(generic_json, include_technical)
            else:
                # Default transformation for unknown types
                return self._transform_generic(generic_json, include_technical)

        except Exception as e:
            self.logger.error(f"Error transforming to human-readable format: {e}", exc_info=True)
            return generic_json

    def _transform_835(self, generic_json: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Transform 835 Remittance Advice to human-readable format"""

        result = OrderedDict()
        result['transaction_type'] = '835_remittance_advice'
        result['metadata'] = self._transform_interchange_metadata(generic_json)

        # Get segments from first transaction
        segments = generic_json.get('transactions', [{}])[0].get('segments', [])

        # Process segments by type
        segment_map = self._build_segment_map(segments)

        # Financial Information (BPR segment)
        if 'BPR' in segment_map:
            result['payment_information'] = self._transform_bpr_segment(
                segment_map['BPR'][0], include_technical
            )

        # Trace Information (TRN segment)
        if 'TRN' in segment_map:
            trn = segment_map['TRN'][0]
            result['trace_information'] = self._transform_trn_segment(trn, include_technical)

        # Payer Information
        payer_segments = self._get_loop_segments(segments, '1000A')
        if payer_segments:
            result['payer'] = self._transform_entity_loop(payer_segments, 'PR', include_technical)

        # Payee Information
        payee_segments = self._get_loop_segments(segments, '1000B')
        if payee_segments:
            result['payee'] = self._transform_entity_loop(payee_segments, 'PE', include_technical)

        # Claims
        result['claims'] = self._transform_835_claims(segments, include_technical)

        # Provider Adjustments (PLB segments)
        if 'PLB' in segment_map:
            result['provider_adjustments'] = [
                self._transform_plb_segment(plb, include_technical)
                for plb in segment_map['PLB']
            ]

        # Summary
        result['summary'] = self._build_835_summary(result)

        return result

    def _transform_837(self, generic_json: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Transform 837 Professional Claim to human-readable format"""

        result = OrderedDict()
        result['transaction_type'] = '837_professional_claim'
        result['metadata'] = self._transform_interchange_metadata(generic_json)

        # Get segments from first transaction
        segments = generic_json.get('transactions', [{}])[0].get('segments', [])

        # Process segments by type
        segment_map = self._build_segment_map(segments)

        # Transaction header (BHT segment)
        if 'BHT' in segment_map:
            result['transaction_header'] = self._transform_bht_segment(
                segment_map['BHT'][0], include_technical
            )

        # Submitter Information
        submitter_segments = self._get_loop_segments(segments, '1000A')
        if submitter_segments:
            result['submitter'] = self._transform_entity_loop(submitter_segments, '41', include_technical)

        # Receiver Information
        receiver_segments = self._get_loop_segments(segments, '1000B')
        if receiver_segments:
            result['receiver'] = self._transform_entity_loop(receiver_segments, '40', include_technical)

        # Billing Provider
        billing_segments = self._get_loop_segments(segments, '2010AA')
        if billing_segments:
            result['billing_provider'] = self._transform_entity_loop(billing_segments, '85', include_technical)

        # Claims
        result['claims'] = self._transform_837_claims(segments, generic_json.get('transactions', [{}])[0].get('hierarchical_tree', {}), include_technical)

        return result

    def _transform_834(self, generic_json: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Transform 834 Benefit Enrollment to human-readable format"""

        result = OrderedDict()
        result['transaction_type'] = '834_benefit_enrollment'
        result['metadata'] = self._transform_interchange_metadata(generic_json)

        # Get segments from first transaction
        segments = generic_json.get('transactions', [{}])[0].get('segments', [])
        segment_map = self._build_segment_map(segments)

        # Beginning segment (BGN)
        if 'BGN' in segment_map:
            result['transaction_header'] = self._transform_bgn_segment(
                segment_map['BGN'][0], include_technical
            )

        # Policy reference (REF)
        if 'REF' in segment_map:
            for ref in segment_map['REF']:
                qualifier = self._get_element_value(ref, 'REF01')
                if qualifier == '38':
                    result['master_policy_number'] = self._get_element_value(ref, 'REF02')

        # Sponsor Information (N1*P5)
        for n1 in segment_map.get('N1', []):
            entity_code = self._get_element_value(n1, 'N101')
            if entity_code == 'P5':
                result['plan_sponsor'] = {
                    'name': self._get_element_value(n1, 'N102'),
                    'identifier': self._get_element_value(n1, 'N104')
                }
            elif entity_code == 'IN':
                result['payer'] = {
                    'name': self._get_element_value(n1, 'N102'),
                    'identifier': self._get_element_value(n1, 'N104')
                }

        # Member enrollments
        result['members'] = self._transform_834_members(segments, include_technical)

        return result

    def _transform_generic(self, generic_json: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Default transformation for unknown transaction types"""

        result = OrderedDict()
        result['transaction_type'] = generic_json.get('transaction_type', 'unknown')
        result['metadata'] = self._transform_interchange_metadata(generic_json)

        # Get segments from first transaction
        segments = generic_json.get('transactions', [{}])[0].get('segments', [])

        # Group segments by type
        result['segments'] = {}
        for segment in segments:
            seg_id = segment.get('segment_id')
            seg_name = segment.get('segment_name', seg_id)

            if seg_id not in result['segments']:
                result['segments'][seg_id] = {
                    'name': seg_name,
                    'occurrences': []
                }

            # Transform elements
            elements = self._transform_generic_elements(segment.get('elements', {}), include_technical)
            result['segments'][seg_id]['occurrences'].append(elements)

        return result

    def _transform_interchange_metadata(self, generic_json: Dict[str, Any]) -> Dict[str, Any]:
        """Transform interchange and functional group metadata"""

        interchange = generic_json.get('interchange', {})
        functional_group = generic_json.get('functional_groups', [{}])[0]

        return {
            'sender': {
                'id': interchange.get('sender_id'),
                'qualifier': interchange.get('sender_qualifier')
            },
            'receiver': {
                'id': interchange.get('receiver_id'),
                'qualifier': interchange.get('receiver_qualifier')
            },
            'interchange_date': self._format_date(interchange.get('date')),
            'interchange_time': self._format_time(interchange.get('time')),
            'interchange_control_number': interchange.get('control_number'),
            'test_mode': interchange.get('test_indicator') == 'T',
            'functional_group': {
                'type': functional_group.get('functional_id'),
                'sender': functional_group.get('sender_code'),
                'receiver': functional_group.get('receiver_code'),
                'date': self._format_date(functional_group.get('date')),
                'time': self._format_time(functional_group.get('time')),
                'control_number': functional_group.get('control_number'),
                'version': functional_group.get('version')
            }
        }

    def _transform_bpr_segment(self, segment: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Transform BPR (Financial Information) segment"""

        result = OrderedDict()

        # Transaction handling code
        handling_code = self._get_element_value(segment, 'BPR01')
        result['transaction_handling'] = self._format_code_with_description(
            handling_code,
            codes.get_payment_method_description(handling_code),
            include_technical
        )

        # Payment amount
        amount = self._get_element_value(segment, 'BPR02')
        if amount:
            result['total_payment_amount'] = float(amount)

        # Credit/Debit indicator
        credit_debit = self._get_element_value(segment, 'BPR03')
        if credit_debit:
            result['credit_or_debit'] = self._format_code_with_description(
                credit_debit,
                codes.CREDIT_DEBIT_CODES.get(credit_debit, credit_debit),
                include_technical
            )

        # Payment method
        payment_method = self._get_element_value(segment, 'BPR04')
        if payment_method:
            result['payment_method'] = self._format_code_with_description(
                payment_method,
                codes.get_payment_method_description(payment_method),
                include_technical
            )

        # Payment date
        payment_date = self._get_element_value(segment, 'BPR16')
        if payment_date:
            result['payment_date'] = self._format_date(payment_date)

        # Account information
        if self._get_element_value(segment, 'BPR07'):
            result['sender_bank_account'] = {
                'routing_number': self._get_element_value(segment, 'BPR07'),
                'account_number': self._get_element_value(segment, 'BPR09')
            }

        if self._get_element_value(segment, 'BPR13'):
            result['receiver_bank_account'] = {
                'routing_number': self._get_element_value(segment, 'BPR13'),
                'account_number': self._get_element_value(segment, 'BPR15')
            }

        return result

    def _transform_trn_segment(self, segment: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Transform TRN (Trace) segment"""

        return {
            'trace_type': self._get_element_value(segment, 'TRN01'),
            'check_or_eft_number': self._get_element_value(segment, 'TRN02'),
            'originating_company_id': self._get_element_value(segment, 'TRN03'),
            'originating_company_supplemental': self._get_element_value(segment, 'TRN04')
        }

    def _transform_bht_segment(self, segment: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Transform BHT (Beginning of Hierarchical Transaction) segment"""

        return {
            'hierarchical_structure': self._get_element_value(segment, 'BHT01'),
            'transaction_purpose': self._get_element_value(segment, 'BHT02'),
            'reference_number': self._get_element_value(segment, 'BHT03'),
            'creation_date': self._format_date(self._get_element_value(segment, 'BHT04')),
            'creation_time': self._format_time(self._get_element_value(segment, 'BHT05')),
            'transaction_type': self._get_element_value(segment, 'BHT06')
        }

    def _transform_bgn_segment(self, segment: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Transform BGN (Beginning) segment"""

        return {
            'transaction_purpose': self._get_element_value(segment, 'BGN01'),
            'reference_number': self._get_element_value(segment, 'BGN02'),
            'creation_date': self._format_date(self._get_element_value(segment, 'BGN03')),
            'creation_time': self._format_time(self._get_element_value(segment, 'BGN04')),
            'action_code': self._get_element_value(segment, 'BGN08')
        }

    def _transform_plb_segment(self, segment: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Transform PLB (Provider Level Balance) segment"""

        result = {
            'provider_id': self._get_element_value(segment, 'PLB01'),
            'fiscal_period_date': self._format_date(self._get_element_value(segment, 'PLB02')),
            'adjustments': []
        }

        # Process up to 6 adjustment pairs
        for i in range(3, 14, 2):
            adj_id = self._get_element_value(segment, f'PLB{str(i).zfill(2)}')
            adj_amount = self._get_element_value(segment, f'PLB{str(i+1).zfill(2)}')

            if adj_id:
                # Handle composite identifiers
                if isinstance(adj_id, dict) and adj_id.get('composite'):
                    components = adj_id.get('components', [])
                    adj_code = components[0] if components else None
                    reference = components[1] if len(components) > 1 else None
                else:
                    adj_code = adj_id
                    reference = None

                adjustment = {
                    'adjustment_code': self._format_code_with_description(
                        adj_code,
                        codes.PLB_ADJUSTMENT_CODES.get(adj_code, f"Adjustment {adj_code}"),
                        include_technical
                    ),
                    'amount': float(adj_amount) if adj_amount else 0.0
                }

                if reference:
                    adjustment['reference_id'] = reference

                result['adjustments'].append(adjustment)

        return result

    def _transform_entity_loop(self, segments: List[Dict[str, Any]], entity_type: str, include_technical: bool) -> Dict[str, Any]:
        """Transform entity loop (N1, N3, N4, PER segments)"""

        result = OrderedDict()

        # N1 segment
        n1_segment = next((s for s in segments if s.get('segment_id') == 'N1'), None)
        if n1_segment:
            entity_code = self._get_element_value(n1_segment, 'N101')
            result['entity_type'] = self._format_code_with_description(
                entity_code,
                codes.get_entity_description(entity_code),
                include_technical
            )
            result['name'] = self._get_element_value(n1_segment, 'N102')

            id_qualifier = self._get_element_value(n1_segment, 'N103')
            id_value = self._get_element_value(n1_segment, 'N104')
            if id_qualifier and id_value:
                result['identification'] = {
                    'qualifier': self._format_code_with_description(
                        id_qualifier,
                        codes.ID_CODE_QUALIFIERS.get(id_qualifier, id_qualifier),
                        include_technical
                    ),
                    'value': id_value
                }

        # NM1 segment (alternative to N1)
        nm1_segment = next((s for s in segments if s.get('segment_id') == 'NM1'), None)
        if nm1_segment and not n1_segment:
            entity_code = self._get_element_value(nm1_segment, 'NM101')
            result['entity_type'] = self._format_code_with_description(
                entity_code,
                codes.get_entity_description(entity_code),
                include_technical
            )

            # Organization or individual name
            if self._get_element_value(nm1_segment, 'NM102') == '2':
                result['organization_name'] = self._get_element_value(nm1_segment, 'NM103')
            else:
                result['last_name'] = self._get_element_value(nm1_segment, 'NM103')
                result['first_name'] = self._get_element_value(nm1_segment, 'NM104')
                result['middle_name'] = self._get_element_value(nm1_segment, 'NM105')
                result['suffix'] = self._get_element_value(nm1_segment, 'NM107')

            id_qualifier = self._get_element_value(nm1_segment, 'NM108')
            id_value = self._get_element_value(nm1_segment, 'NM109')
            if id_qualifier and id_value:
                result['identification'] = {
                    'qualifier': self._format_code_with_description(
                        id_qualifier,
                        codes.ID_CODE_QUALIFIERS.get(id_qualifier, id_qualifier),
                        include_technical
                    ),
                    'value': id_value
                }

        # Address segments (N3, N4)
        n3_segment = next((s for s in segments if s.get('segment_id') == 'N3'), None)
        n4_segment = next((s for s in segments if s.get('segment_id') == 'N4'), None)

        if n3_segment or n4_segment:
            address = OrderedDict()
            if n3_segment:
                address['street_1'] = self._get_element_value(n3_segment, 'N301')
                address['street_2'] = self._get_element_value(n3_segment, 'N302')
            if n4_segment:
                address['city'] = self._get_element_value(n4_segment, 'N401')
                address['state'] = self._get_element_value(n4_segment, 'N402')
                address['postal_code'] = self._get_element_value(n4_segment, 'N403')
                address['country'] = self._get_element_value(n4_segment, 'N404')
            result['address'] = address

        # Contact information (PER segment)
        per_segment = next((s for s in segments if s.get('segment_id') == 'PER'), None)
        if per_segment:
            contact = OrderedDict()
            contact['function'] = self._get_element_value(per_segment, 'PER01')
            contact['name'] = self._get_element_value(per_segment, 'PER02')

            # Process up to 3 contact methods
            for i in range(3, 9, 2):
                qualifier = self._get_element_value(per_segment, f'PER{str(i).zfill(2)}')
                value = self._get_element_value(per_segment, f'PER{str(i+1).zfill(2)}')

                if qualifier and value:
                    if qualifier == 'TE':
                        contact['telephone'] = value
                    elif qualifier == 'FX':
                        contact['fax'] = value
                    elif qualifier == 'EM':
                        contact['email'] = value
                    elif qualifier == 'EX':
                        contact['extension'] = value

            result['contact'] = contact

        # Reference numbers (REF segments)
        ref_segments = [s for s in segments if s.get('segment_id') == 'REF']
        if ref_segments:
            result['references'] = []
            for ref in ref_segments:
                qualifier = self._get_element_value(ref, 'REF01')
                value = self._get_element_value(ref, 'REF02')
                if qualifier and value:
                    result['references'].append({
                        'type': self._format_code_with_description(
                            qualifier,
                            codes.get_reference_qualifier_description(qualifier),
                            include_technical
                        ),
                        'value': value
                    })

        return result

    def _transform_835_claims(self, segments: List[Dict[str, Any]], include_technical: bool) -> List[Dict[str, Any]]:
        """Transform 835 claims (CLP segments and related)"""

        claims = []
        clp_segments = [s for s in segments if s.get('segment_id') == 'CLP']

        for clp in clp_segments:
            claim = OrderedDict()

            # Basic claim information
            claim['patient_control_number'] = self._get_element_value(clp, 'CLP01')

            status_code = self._get_element_value(clp, 'CLP02')
            claim['claim_status'] = self._format_code_with_description(
                status_code,
                codes.get_claim_status_description(status_code),
                include_technical
            )

            claim['total_charge_amount'] = self._safe_float(self._get_element_value(clp, 'CLP03'))
            claim['total_paid_amount'] = self._safe_float(self._get_element_value(clp, 'CLP04'))
            claim['patient_responsibility'] = self._safe_float(self._get_element_value(clp, 'CLP05'))

            filing_code = self._get_element_value(clp, 'CLP06')
            if filing_code:
                claim['claim_filing_indicator'] = self._format_code_with_description(
                    filing_code,
                    codes.get_claim_filing_description(filing_code),
                    include_technical
                )

            claim['payer_claim_number'] = self._get_element_value(clp, 'CLP07')

            # Get claim loop instance
            loop_instance = clp.get('loop_instance', 0)

            # Get patient information for this claim
            patient_segments = [
                s for s in segments
                if s.get('segment_id') == 'NM1'
                and self._get_element_value(s, 'NM101') == 'QC'
                and s.get('loop_instance') == loop_instance
            ]

            if patient_segments:
                patient = patient_segments[0]
                claim['patient'] = {
                    'last_name': self._get_element_value(patient, 'NM103'),
                    'first_name': self._get_element_value(patient, 'NM104'),
                    'middle_name': self._get_element_value(patient, 'NM105'),
                    'member_id': self._get_element_value(patient, 'NM109')
                }

            # Get service lines for this claim
            service_lines = [
                s for s in segments
                if s.get('segment_id') == 'SVC'
                and s.get('loop_instance') == loop_instance
            ]

            if service_lines:
                claim['service_lines'] = []
                for svc in service_lines:
                    service = self._transform_service_line(svc, segments, loop_instance, include_technical)
                    claim['service_lines'].append(service)

            # Get claim adjustments
            cas_segments = [
                s for s in segments
                if s.get('segment_id') == 'CAS'
                and s.get('loop_id') == '2100'
                and s.get('loop_instance') == loop_instance
            ]

            if cas_segments:
                claim['claim_adjustments'] = [
                    self._transform_cas_segment(cas, include_technical)
                    for cas in cas_segments
                ]

            claims.append(claim)

        return claims

    def _transform_837_claims(self, segments: List[Dict[str, Any]], hl_tree: Dict[str, Any], include_technical: bool) -> List[Dict[str, Any]]:
        """Transform 837 claims (CLM segments and related)"""

        claims = []
        clm_segments = [s for s in segments if s.get('segment_id') == 'CLM']

        for clm in clm_segments:
            claim = OrderedDict()

            # Basic claim information
            claim['claim_number'] = self._get_element_value(clm, 'CLM01')
            claim['total_charge_amount'] = self._safe_float(self._get_element_value(clm, 'CLM02'))

            # Get hierarchical context
            hl_context = clm.get('hierarchical_context', {})
            hl_id = hl_context.get('hl_id')

            # Get subscriber/patient from hierarchical tree
            if hl_id and hl_tree:
                # Find subscriber segments using hierarchical context
                subscriber_segments = [
                    s for s in segments
                    if s.get('segment_id') == 'NM1'
                    and self._get_element_value(s, 'NM101') == 'IL'
                    and s.get('hierarchical_context', {}).get('hl_id') == hl_id
                ]

                if subscriber_segments:
                    subscriber = subscriber_segments[0]
                    claim['subscriber'] = {
                        'last_name': self._get_element_value(subscriber, 'NM103'),
                        'first_name': self._get_element_value(subscriber, 'NM104'),
                        'middle_name': self._get_element_value(subscriber, 'NM105'),
                        'member_id': self._get_element_value(subscriber, 'NM109')
                    }

            # Get service lines
            service_lines = [
                s for s in segments
                if s.get('segment_id') == 'SV1'
                and s.get('hierarchical_context', {}).get('hl_id') == hl_id
            ]

            if service_lines:
                claim['service_lines'] = []
                for sv1 in service_lines:
                    service = self._transform_sv1_segment(sv1, include_technical)
                    claim['service_lines'].append(service)

            claims.append(claim)

        return claims

    def _transform_834_members(self, segments: List[Dict[str, Any]], include_technical: bool) -> List[Dict[str, Any]]:
        """Transform 834 member enrollments (INS segments and related)"""

        members = []
        ins_segments = [s for s in segments if s.get('segment_id') == 'INS']

        for ins in ins_segments:
            member = OrderedDict()

            # Member indicator
            member['member_indicator'] = self._format_code_with_description(
                self._get_element_value(ins, 'INS01'),
                codes.YES_NO_CODES.get(self._get_element_value(ins, 'INS01'), 'Unknown'),
                include_technical
            )

            # Relationship
            relationship_code = self._get_element_value(ins, 'INS02')
            member['relationship'] = self._format_code_with_description(
                relationship_code,
                codes.get_relationship_description(relationship_code),
                include_technical
            )

            # Maintenance type
            member['maintenance_type'] = self._get_element_value(ins, 'INS03')
            member['maintenance_reason'] = self._get_element_value(ins, 'INS04')
            member['benefit_status'] = self._get_element_value(ins, 'INS05')

            # Get loop instance for member-specific segments
            loop_instance = ins.get('loop_instance', 0)

            # Get member name
            nm1_segments = [
                s for s in segments
                if s.get('segment_id') == 'NM1'
                and self._get_element_value(s, 'NM101') == 'IL'
                and s.get('loop_instance') == loop_instance
            ]

            if nm1_segments:
                nm1 = nm1_segments[0]
                member['name'] = {
                    'last_name': self._get_element_value(nm1, 'NM103'),
                    'first_name': self._get_element_value(nm1, 'NM104'),
                    'middle_name': self._get_element_value(nm1, 'NM105'),
                    'member_id': self._get_element_value(nm1, 'NM109')
                }

            # Get demographics
            dmg_segments = [
                s for s in segments
                if s.get('segment_id') == 'DMG'
                and s.get('loop_instance') == loop_instance
            ]

            if dmg_segments:
                dmg = dmg_segments[0]
                member['demographics'] = {
                    'birth_date': self._format_date(self._get_element_value(dmg, 'DMG02')),
                    'gender': self._format_code_with_description(
                        self._get_element_value(dmg, 'DMG03'),
                        codes.get_gender_description(self._get_element_value(dmg, 'DMG03')),
                        include_technical
                    )
                }

            members.append(member)

        return members

    def _transform_service_line(self, svc: Dict[str, Any], segments: List[Dict[str, Any]], loop_instance: int, include_technical: bool) -> Dict[str, Any]:
        """Transform SVC (Service Line) segment"""

        result = OrderedDict()

        # Procedure code (composite)
        svc01 = self._get_element_value(svc, 'SVC01')
        if isinstance(svc01, dict) and svc01.get('composite'):
            components = svc01.get('components', [])
            if len(components) > 0:
                result['product_qualifier'] = components[0]
            if len(components) > 1:
                result['procedure_code'] = components[1]
            if len(components) > 2:
                result['modifiers'] = [c for c in components[2:] if c]
        else:
            result['procedure_code'] = svc01

        # Amounts
        result['charge_amount'] = self._safe_float(self._get_element_value(svc, 'SVC02'))
        result['paid_amount'] = self._safe_float(self._get_element_value(svc, 'SVC03'))
        result['revenue_code'] = self._get_element_value(svc, 'SVC04')
        result['units_paid'] = self._safe_float(self._get_element_value(svc, 'SVC05'))

        # Get service dates
        service_dtm = [
            s for s in segments
            if s.get('segment_id') == 'DTM'
            and s.get('loop_id') == '2110'
            and s.get('loop_instance') == loop_instance
        ]

        if service_dtm:
            dates = {}
            for dtm in service_dtm:
                qualifier = self._get_element_value(dtm, 'DTM01')
                date_value = self._get_element_value(dtm, 'DTM02')
                if qualifier == '472':
                    dates['service_date'] = self._format_date(date_value)
                elif qualifier == '150':
                    dates['service_period_start'] = self._format_date(date_value)
                elif qualifier == '151':
                    dates['service_period_end'] = self._format_date(date_value)
            if dates:
                result['dates'] = dates

        # Get service adjustments
        service_cas = [
            s for s in segments
            if s.get('segment_id') == 'CAS'
            and s.get('loop_id') == '2110'
            and s.get('loop_instance') == loop_instance
        ]

        if service_cas:
            result['adjustments'] = [
                self._transform_cas_segment(cas, include_technical)
                for cas in service_cas
            ]

        return result

    def _transform_sv1_segment(self, sv1: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Transform SV1 (Professional Service) segment"""

        result = OrderedDict()

        # Procedure code (composite)
        sv101 = self._get_element_value(sv1, 'SV101')
        if isinstance(sv101, dict) and sv101.get('composite'):
            components = sv101.get('components', [])
            if len(components) > 0:
                result['product_qualifier'] = components[0]
            if len(components) > 1:
                result['procedure_code'] = components[1]
            if len(components) > 2:
                result['modifiers'] = [c for c in components[2:] if c]
        else:
            result['procedure_code'] = sv101

        # Amounts and units
        result['charge_amount'] = self._safe_float(self._get_element_value(sv1, 'SV102'))
        result['unit_type'] = self._get_element_value(sv1, 'SV103')
        result['units'] = self._safe_float(self._get_element_value(sv1, 'SV104'))
        result['place_of_service'] = self._get_element_value(sv1, 'SV105')

        # Diagnosis code pointers
        diagnosis_pointers = self._get_element_value(sv1, 'SV107')
        if diagnosis_pointers:
            if isinstance(diagnosis_pointers, dict) and diagnosis_pointers.get('composite'):
                result['diagnosis_pointers'] = diagnosis_pointers.get('components', [])
            else:
                result['diagnosis_pointers'] = [diagnosis_pointers]

        return result

    def _transform_cas_segment(self, cas: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Transform CAS (Claim Adjustment) segment"""

        result = OrderedDict()

        # Adjustment group
        group_code = self._get_element_value(cas, 'CAS01')
        result['adjustment_group'] = self._format_code_with_description(
            group_code,
            codes.get_adjustment_group_description(group_code),
            include_technical
        )

        # Process up to 6 adjustment reasons
        result['reasons'] = []
        for i in range(1, 7):
            reason_field = f'CAS{str(i*2).zfill(2)}'
            amount_field = f'CAS{str(i*2+1).zfill(2)}'

            reason_code = self._get_element_value(cas, reason_field)
            amount = self._get_element_value(cas, amount_field)

            if reason_code:
                reason = {
                    'code': self._format_code_with_description(
                        reason_code,
                        codes.get_adjustment_reason_description(reason_code),
                        include_technical
                    ),
                    'amount': self._safe_float(amount)
                }

                # Add quantity if present (only for first 3 reasons)
                if i <= 3:
                    quantity_field = f'CAS{str((i-1)*3+10).zfill(2)}'
                    quantity = self._get_element_value(cas, quantity_field)
                    if quantity:
                        reason['quantity'] = self._safe_float(quantity)

                result['reasons'].append(reason)

        return result

    def _transform_generic_elements(self, elements: Dict[str, Any], include_technical: bool) -> Dict[str, Any]:
        """Transform generic segment elements"""

        result = OrderedDict()

        for elem_id, elem_value in elements.items():
            # If element has metadata (name, value structure)
            if isinstance(elem_value, dict):
                if 'value' in elem_value:
                    # Element with metadata
                    name = elem_value.get('name', elem_id)
                    value = elem_value.get('value')
                    result[self._to_snake_case(name)] = value
                elif elem_value.get('composite'):
                    # Composite element
                    result[elem_id] = {
                        'components': elem_value.get('components', []),
                        'name': elem_value.get('name', 'Composite')
                    }
                else:
                    # Other dict structure
                    result[elem_id] = elem_value
            else:
                # Simple value
                result[elem_id] = elem_value

        return result

    # Helper methods

    def _build_segment_map(self, segments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Build a map of segment ID to list of segments"""
        segment_map = {}
        for segment in segments:
            seg_id = segment.get('segment_id')
            if seg_id not in segment_map:
                segment_map[seg_id] = []
            segment_map[seg_id].append(segment)
        return segment_map

    def _get_loop_segments(self, segments: List[Dict[str, Any]], loop_id: str) -> List[Dict[str, Any]]:
        """Get all segments in a specific loop"""
        return [s for s in segments if s.get('loop_id') == loop_id]

    def _get_element_value(self, segment: Dict[str, Any], element_id: str) -> Any:
        """Get element value from segment"""
        elements = segment.get('elements', {})
        element = elements.get(element_id)

        # Handle different element structures
        if isinstance(element, dict):
            if 'value' in element:
                return element['value']
            elif element.get('composite'):
                return element
            else:
                return element
        else:
            return element

    def _format_code_with_description(self, code: str, description: str, include_technical: bool) -> Union[str, Dict[str, str]]:
        """Format a code with its description"""
        if not code:
            return None

        if include_technical:
            return {
                'code': code,
                'description': description
            }
        else:
            return description

    def _format_date(self, date_str: str) -> str:
        """Format date from CCYYMMDD or YYMMDD to YYYY-MM-DD"""
        if not date_str:
            return None

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
        if not time_str:
            return None

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
        except:
            return None

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        # Remove special characters and convert to lowercase
        import re
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', '_', text)
        return text.lower()

    def _build_835_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Build summary for 835 transaction"""
        summary = {
            'total_claims': len(result.get('claims', [])),
            'total_payment': result.get('payment_information', {}).get('total_payment_amount', 0.0)
        }

        # Calculate claim totals
        claims = result.get('claims', [])
        if claims:
            summary['total_charge_amount'] = sum(c.get('total_charge_amount', 0) for c in claims)
            summary['total_paid_amount'] = sum(c.get('total_paid_amount', 0) for c in claims)
            summary['total_patient_responsibility'] = sum(c.get('patient_responsibility', 0) for c in claims)

        # Calculate provider adjustments
        provider_adjustments = result.get('provider_adjustments', [])
        if provider_adjustments:
            summary['total_provider_adjustments'] = sum(
                sum(a.get('amount', 0) for a in adj.get('adjustments', []))
                for adj in provider_adjustments
            )

        return summary


# Convenience function for backwards compatibility and ease of use
def format_structured(generic_json: Dict[str, Any], include_technical: bool = True) -> Dict[str, Any]:
    """
    Format generic X12 JSON to structured format

    Args:
        generic_json: Output from X12Parser
        include_technical: Include original codes alongside descriptions

    Returns:
        Structured JSON with meaningful field names and preserved X12 organization
    """
    formatter = StructuredFormatter()
    return formatter.format(generic_json, include_technical)