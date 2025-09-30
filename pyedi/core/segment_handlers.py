#!/usr/bin/env python3
"""
Specialized Segment Handlers for 837 and 835 Transactions

Provides enhanced parsing for complex segments that contain composite elements
or require special handling for proper field extraction.
"""

from typing import Dict, Any, List, Optional
from collections import OrderedDict
import re

from ..code_sets import edi_codes as codes


class SegmentHandlers:
    """Collection of specialized segment handlers for complex EDI segments"""

    @staticmethod
    def handle_bpr_segment(elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle BPR (Financial Information) segment from 835

        BPR*I*132*C*CHK***********456*20190331~

        Returns structured payment information
        """
        result = OrderedDict()

        # BPR01 - Transaction Handling Code
        if 'BPR01' in elements:
            code = SegmentHandlers._get_value(elements['BPR01'])
            result['transaction_handling_code'] = code
            result['transaction_handling'] = codes.TRANSACTION_HANDLING_CODES.get(code, code)

        # BPR02 - Total Payment Amount
        if 'BPR02' in elements:
            result['total_payment_amount'] = SegmentHandlers._safe_float(elements['BPR02'])

        # BPR03 - Credit/Debit Flag
        if 'BPR03' in elements:
            code = SegmentHandlers._get_value(elements['BPR03'])
            result['credit_debit_flag'] = code
            result['credit_debit'] = codes.CREDIT_DEBIT_CODES.get(code, code)

        # BPR04 - Payment Method Code
        if 'BPR04' in elements:
            code = SegmentHandlers._get_value(elements['BPR04'])
            result['payment_method_code'] = code
            result['payment_method'] = codes.PAYMENT_METHOD_CODES.get(code, code)

        # BPR05-BPR15 - Payer Bank Account Details (if present)
        for i in range(5, 16):
            key = f'BPR{str(i).zfill(2)}'
            if key in elements:
                val = SegmentHandlers._get_value(elements[key])
                if val:
                    result[f'payer_account_field_{i}'] = val

        # BPR16 - Payment Date (CCYYMMDD)
        if 'BPR16' in elements:
            date_val = SegmentHandlers._get_value(elements['BPR16'])
            result['payment_date'] = SegmentHandlers._format_date(date_val)

        return result

    @staticmethod
    def handle_trn_segment(elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle TRN (Trace) segment from 835

        TRN*1*12345*1512345678~
        """
        result = OrderedDict()

        # TRN01 - Trace Type Code
        if 'TRN01' in elements:
            result['trace_type_code'] = SegmentHandlers._get_value(elements['TRN01'])

        # TRN02 - Check or EFT Trace Number
        if 'TRN02' in elements:
            result['check_eft_trace_number'] = SegmentHandlers._get_value(elements['TRN02'])

        # TRN03 - Payer Identifier
        if 'TRN03' in elements:
            result['payer_identifier'] = SegmentHandlers._get_value(elements['TRN03'])

        # TRN04 - Originating Company Supplemental Code
        if 'TRN04' in elements:
            result['originating_company_code'] = SegmentHandlers._get_value(elements['TRN04'])

        return result

    @staticmethod
    def handle_clp_segment(elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle CLP (Claim Payment Information) segment from 835

        CLP*7722337*1*226*132*10*12*119932404007801*11*1**025*0.5*0.4~
        """
        result = OrderedDict()

        # CLP01 - Patient Control Number
        if 'CLP01' in elements:
            result['patient_control_number'] = SegmentHandlers._get_value(elements['CLP01'])

        # CLP02 - Claim Status Code
        if 'CLP02' in elements:
            code = SegmentHandlers._get_value(elements['CLP02'])
            result['claim_status_code'] = code
            result['claim_status'] = codes.get_claim_status_description(code)

        # CLP03 - Total Claim Charge Amount
        if 'CLP03' in elements:
            result['total_charge_amount'] = SegmentHandlers._safe_float(elements['CLP03'])

        # CLP04 - Total Claim Payment Amount
        if 'CLP04' in elements:
            result['total_payment_amount'] = SegmentHandlers._safe_float(elements['CLP04'])

        # CLP05 - Patient Responsibility Amount
        if 'CLP05' in elements:
            result['patient_responsibility_amount'] = SegmentHandlers._safe_float(elements['CLP05'])

        # CLP06 - Claim Filing Indicator Code
        if 'CLP06' in elements:
            code = SegmentHandlers._get_value(elements['CLP06'])
            result['claim_filing_code'] = code
            result['claim_filing'] = codes.get_claim_filing_description(code)

        # CLP07 - Payer Claim Control Number
        if 'CLP07' in elements:
            result['payer_claim_control_number'] = SegmentHandlers._get_value(elements['CLP07'])

        # CLP08 - Facility Type Code
        if 'CLP08' in elements:
            code = SegmentHandlers._get_value(elements['CLP08'])
            result['facility_code'] = code
            result['facility_type'] = codes.get_place_of_service_description(code)

        # CLP09 - Claim Frequency Code
        if 'CLP09' in elements:
            result['claim_frequency_code'] = SegmentHandlers._get_value(elements['CLP09'])

        # CLP10 - Patient Status Code
        if 'CLP10' in elements:
            result['patient_status_code'] = SegmentHandlers._get_value(elements['CLP10'])

        # CLP11 - Diagnosis Related Group (DRG) Code
        if 'CLP11' in elements:
            result['drg_code'] = SegmentHandlers._get_value(elements['CLP11'])

        # CLP12 - DRG Weight
        if 'CLP12' in elements:
            result['drg_weight'] = SegmentHandlers._safe_float(elements['CLP12'])

        # CLP13 - Discharge Fraction
        if 'CLP13' in elements:
            result['discharge_fraction'] = SegmentHandlers._safe_float(elements['CLP13'])

        return result

    @staticmethod
    def handle_cas_segment(elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle CAS (Claims Adjustment) segment

        CAS*CO*197*2000*1*45*30000~
        CAS*PR*132*259~

        Returns structured adjustment information with groups and reasons
        """
        result = OrderedDict()

        # CAS01 - Claim Adjustment Group Code
        if 'CAS01' in elements:
            group_code = SegmentHandlers._get_value(elements['CAS01'])
            result['adjustment_group_code'] = group_code
            result['adjustment_group'] = codes.get_adjustment_group_description(group_code)

        # Process adjustment details (groups of 3-5 elements)
        # CAS02-06 (first adjustment), CAS07-11 (second adjustment), etc.
        adjustments = []
        adjustment_num = 1

        for base in range(2, 20, 5):  # Up to 6 adjustment groups per CAS segment
            reason_key = f'CAS{str(base).zfill(2)}'

            if reason_key not in elements:
                break

            adjustment = OrderedDict()

            # Reason code
            reason_code = SegmentHandlers._get_value(elements[reason_key])
            adjustment['reason_code'] = reason_code
            adjustment['reason'] = codes.get_adjustment_reason_description(reason_code)

            # Amount (next element)
            amount_key = f'CAS{str(base+1).zfill(2)}'
            if amount_key in elements:
                adjustment['amount'] = SegmentHandlers._safe_float(elements[amount_key])

            # Quantity (optional)
            qty_key = f'CAS{str(base+2).zfill(2)}'
            if qty_key in elements:
                qty_val = SegmentHandlers._get_value(elements[qty_key])
                if qty_val:
                    adjustment['quantity'] = SegmentHandlers._safe_float(qty_val)

            adjustments.append(adjustment)
            adjustment_num += 1

        if adjustments:
            result['adjustments'] = adjustments

        return result

    @staticmethod
    def handle_svc_segment(elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle SVC (Service Payment Information) segment from 835

        SVC*HC:99213*100*80**1~
        """
        result = OrderedDict()

        # SVC01 - Composite Medical Procedure Identifier
        if 'SVC01' in elements:
            composite = SegmentHandlers._get_value(elements['SVC01'])
            if isinstance(composite, list):
                # Parse composite: Qualifier:ProcedureCode:Modifier1:Modifier2...
                if len(composite) > 0:
                    result['procedure_qualifier'] = composite[0]
                if len(composite) > 1:
                    result['procedure_code'] = composite[1]
                if len(composite) > 2:
                    modifiers = [m for m in composite[2:] if m]
                    if modifiers:
                        result['procedure_modifiers'] = modifiers
            else:
                result['procedure_identifier'] = composite

        # SVC02 - Line Item Charge Amount
        if 'SVC02' in elements:
            result['line_charge_amount'] = SegmentHandlers._safe_float(elements['SVC02'])

        # SVC03 - Line Item Provider Payment Amount
        if 'SVC03' in elements:
            result['line_payment_amount'] = SegmentHandlers._safe_float(elements['SVC03'])

        # SVC04 - Revenue Code
        if 'SVC04' in elements:
            code = SegmentHandlers._get_value(elements['SVC04'])
            result['revenue_code'] = code
            result['revenue_description'] = codes.get_revenue_code_description(code)

        # SVC05 - Units of Service Paid
        if 'SVC05' in elements:
            result['units_paid'] = SegmentHandlers._safe_float(elements['SVC05'])

        # SVC06 - Composite Medical Procedure Identifier (Original/Submitted)
        if 'SVC06' in elements:
            composite = SegmentHandlers._get_value(elements['SVC06'])
            if isinstance(composite, list) and len(composite) > 1:
                result['original_procedure_code'] = composite[1]

        # SVC07 - Units of Service (Original)
        if 'SVC07' in elements:
            result['units_original'] = SegmentHandlers._safe_float(elements['SVC07'])

        return result

    @staticmethod
    def handle_amt_segment(elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle AMT (Monetary Amount) segment with qualifier-based naming

        AMT*AU*132~
        AMT*D8*100~
        """
        result = OrderedDict()

        # AMT01 - Amount Qualifier Code
        if 'AMT01' in elements:
            qualifier = SegmentHandlers._get_value(elements['AMT01'])
            result['amount_qualifier'] = qualifier
            result['amount_type'] = codes.get_amount_qualifier_description(qualifier)

        # AMT02 - Monetary Amount
        if 'AMT02' in elements:
            result['amount'] = SegmentHandlers._safe_float(elements['AMT02'])

        # AMT03 - Credit/Debit Flag Code (if present)
        if 'AMT03' in elements:
            result['credit_debit_flag'] = SegmentHandlers._get_value(elements['AMT03'])

        return result

    @staticmethod
    def handle_qty_segment(elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle QTY (Quantity) segment with qualifier-based naming

        QTY*CA*4~
        """
        result = OrderedDict()

        # QTY01 - Quantity Qualifier
        if 'QTY01' in elements:
            qualifier = SegmentHandlers._get_value(elements['QTY01'])
            result['quantity_qualifier'] = qualifier
            result['quantity_type'] = codes.get_quantity_qualifier_description(qualifier)

        # QTY02 - Quantity
        if 'QTY02' in elements:
            result['quantity'] = SegmentHandlers._safe_float(elements['QTY02'])

        # QTY03 - Composite Unit of Measure (if present)
        if 'QTY03' in elements:
            unit = SegmentHandlers._get_value(elements['QTY03'])
            if isinstance(unit, list) and len(unit) > 0:
                result['unit_of_measure'] = unit[0]
            else:
                result['unit_of_measure'] = unit

        return result

    @staticmethod
    def handle_clm_segment(elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle CLM (Claim Information) segment from 837

        CLM*26463774*100***11:B:1*Y*A*Y*Y~

        Unpacks composite CLM05 (facility code + frequency + claim type)
        """
        result = OrderedDict()

        # CLM01 - Patient Control Number
        if 'CLM01' in elements:
            result['patient_control_number'] = SegmentHandlers._get_value(elements['CLM01'])

        # CLM02 - Total Claim Charge Amount
        if 'CLM02' in elements:
            result['total_charge_amount'] = SegmentHandlers._safe_float(elements['CLM02'])

        # CLM03-CLM04 are typically not used in 837P

        # CLM05 - Healthcare Service Location Information (Composite)
        if 'CLM05' in elements:
            composite = SegmentHandlers._get_value(elements['CLM05'])
            if isinstance(composite, list):
                # Format: Facility:Frequency:ClaimType
                if len(composite) > 0 and composite[0]:
                    facility_code = composite[0]
                    result['facility_code'] = facility_code
                    result['place_of_service'] = codes.get_place_of_service_description(facility_code)
                if len(composite) > 1 and composite[1]:
                    result['frequency_code'] = composite[1]
                if len(composite) > 2 and composite[2]:
                    result['claim_type_code'] = composite[2]
            else:
                result['service_location_info'] = composite

        # CLM06 - Provider Signature Indicator
        if 'CLM06' in elements:
            result['provider_signature_indicator'] = SegmentHandlers._get_value(elements['CLM06'])

        # CLM07 - Medicare Assignment Code
        if 'CLM07' in elements:
            result['assignment_participation_code'] = SegmentHandlers._get_value(elements['CLM07'])

        # CLM08 - Benefits Assignment Certification Indicator
        if 'CLM08' in elements:
            result['assignment_certification_indicator'] = SegmentHandlers._get_value(elements['CLM08'])

        # CLM09 - Release of Information Code
        if 'CLM09' in elements:
            result['release_of_information_code'] = SegmentHandlers._get_value(elements['CLM09'])

        # CLM10 - Patient Signature Source Code
        if 'CLM10' in elements:
            result['patient_signature_source_code'] = SegmentHandlers._get_value(elements['CLM10'])

        # CLM11 - Related Causes Information (Composite)
        if 'CLM11' in elements:
            composite = SegmentHandlers._get_value(elements['CLM11'])
            if isinstance(composite, list):
                result['related_causes'] = composite
            else:
                result['related_causes'] = composite

        # CLM12 - Special Program Code
        if 'CLM12' in elements:
            result['special_program_code'] = SegmentHandlers._get_value(elements['CLM12'])

        # CLM13-CLM20 - Additional claim fields
        for i in range(13, 21):
            key = f'CLM{str(i).zfill(2)}'
            if key in elements:
                val = SegmentHandlers._get_value(elements[key])
                if val:
                    result[f'claim_field_{i}'] = val

        return result

    @staticmethod
    def handle_pwk_segment(elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle PWK (Paperwork) segment for attachments

        PWK*OZ*BM***AC*DMN0012~
        """
        result = OrderedDict()

        # PWK01 - Report Type Code
        if 'PWK01' in elements:
            result['report_type_code'] = SegmentHandlers._get_value(elements['PWK01'])

        # PWK02 - Report Transmission Code
        if 'PWK02' in elements:
            result['report_transmission_code'] = SegmentHandlers._get_value(elements['PWK02'])

        # PWK03-PWK05 are typically composites or not used

        # PWK06 - Identification Code Qualifier
        if 'PWK06' in elements:
            result['identification_code_qualifier'] = SegmentHandlers._get_value(elements['PWK06'])

        # PWK07 - Attachment Control Number
        if 'PWK07' in elements:
            result['attachment_control_number'] = SegmentHandlers._get_value(elements['PWK07'])

        return result

    @staticmethod
    def handle_ts3_segment(elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle TS3 (Provider Summary Information) segment from 835

        TS3*1851038194*11*20231231*4*29310~
        """
        result = OrderedDict()

        # TS301 - Provider Identifier
        if 'TS301' in elements:
            result['provider_identifier'] = SegmentHandlers._get_value(elements['TS301'])

        # TS302 - Facility Type Code
        if 'TS302' in elements:
            code = SegmentHandlers._get_value(elements['TS302'])
            result['facility_code'] = code
            result['facility_type'] = codes.get_place_of_service_description(code)

        # TS303 - Fiscal Period Date
        if 'TS303' in elements:
            date_val = SegmentHandlers._get_value(elements['TS303'])
            result['fiscal_period_date'] = SegmentHandlers._format_date(date_val)

        # TS304 - Total Claim Count
        if 'TS304' in elements:
            result['total_claim_count'] = int(SegmentHandlers._get_value(elements['TS304']) or 0)

        # TS305 - Total Claim Charge Amount
        if 'TS305' in elements:
            result['total_claim_charge_amount'] = SegmentHandlers._safe_float(elements['TS305'])

        return result

    @staticmethod
    def handle_rdm_segment(elements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle RDM (Remittance Delivery Method) segment from 835

        RDM*BM*Name*9618215141~
        """
        result = OrderedDict()

        # RDM01 - Report Transmission Code
        if 'RDM01' in elements:
            result['report_transmission_code'] = SegmentHandlers._get_value(elements['RDM01'])

        # RDM02 - Name
        if 'RDM02' in elements:
            result['name'] = SegmentHandlers._get_value(elements['RDM02'])

        # RDM03 - Communication Number
        if 'RDM03' in elements:
            result['communication_number'] = SegmentHandlers._get_value(elements['RDM03'])

        return result

    # Helper methods
    @staticmethod
    def _get_value(element: Any) -> Any:
        """Extract value from element (handles dict and direct values)"""
        if isinstance(element, dict):
            if 'value' in element:
                return element['value']
            elif element.get('composite'):
                return element.get('components', [])
        return element

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == '':
            return None

        # Extract value if it's a dict
        if isinstance(value, dict):
            value = value.get('value', value)

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _format_date(date_str: str) -> str:
        """Format date from CCYYMMDD to YYYY-MM-DD"""
        if not date_str or not isinstance(date_str, str):
            return date_str

        # Extract value if it's a dict
        if isinstance(date_str, dict):
            date_str = date_str.get('value', date_str)

        try:
            if len(date_str) == 8:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            elif len(date_str) == 6:
                year_prefix = "20" if int(date_str[:2]) <= 50 else "19"
                return f"{year_prefix}{date_str[:2]}-{date_str[2:4]}-{date_str[4:]}"
        except:
            pass

        return date_str
