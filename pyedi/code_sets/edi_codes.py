#!/usr/bin/env python3
"""
EDI Code Descriptions for Human-Readable Transformation

This module provides comprehensive mappings of EDI codes to their human-readable descriptions.
These supplement the element names available in pyx12's XML maps.
"""

# Entity Identifier Codes (NM1-01, N1-01, etc.)
ENTITY_IDENTIFIER_CODES = {
    "00": "Alternate Insurer",
    "03": "Dependent",
    "04": "Spouse",
    "05": "Child",
    "06": "Employee",
    "07": "Subscriber",
    "0B": "State",
    "0D": "Assistant Surgeon",
    "0P": "Primary Care Provider",
    "1P": "Provider",
    "1T": "Translator",
    "2B": "Third Party Administrator",
    "36": "Employer",
    "40": "Receiver",
    "41": "Submitter",
    "45": "Drop Off Location",
    "71": "Attending Physician",
    "72": "Operating Physician",
    "73": "Other Physician",
    "74": "Corrected Insured",
    "75": "Corrected Priority Payer",
    "76": "Service Location",
    "77": "Service Location",
    "80": "Hospital",
    "82": "Rendering Provider",
    "85": "Billing Provider",
    "87": "Pay-to Provider",
    "DN": "Referring Provider",
    "DQ": "Supervising Provider",
    "DK": "Ordering Provider",
    "FA": "Facility",
    "GB": "Other Insured",
    "HH": "Home Health Agency",
    "IL": "Insured or Subscriber",
    "IN": "Insurer",
    "LI": "Independent Lab",
    "LR": "Legal Representative",
    "P3": "Primary Care Provider",
    "P4": "Prior Insurance Carrier",
    "P5": "Plan Sponsor",
    "PR": "Payer",
    "PE": "Payee",
    "PRP": "Primary Payer",
    "PW": "Pick Up Location",
    "QC": "Patient",
    "QB": "Purchase Service Provider",
    "QD": "Responsible Party",
    "QV": "Group Practice",
    "SJ": "Service Provider",
    "TT": "Transfer To",
    "TTP": "Tertiary Payer",
    "VN": "Vendor",
    "Y2": "Managed Care Organization"
}

# Date/Time Qualifiers (DTM-01, DTP-01)
DATE_TIME_QUALIFIERS = {
    "036": "Expiration",
    "050": "Received",
    "090": "Report Start",
    "091": "Report End",
    "096": "Discharge",
    "098": "Certification",
    "139": "Estimated",
    "150": "Service Period Start",
    "151": "Service Period End",
    "156": "Effective Period",
    "193": "Period Start",
    "194": "Period End",
    "198": "Completion",
    "220": "Onset of Symptoms",
    "232": "Claim Statement Period Start",
    "233": "Claim Statement Period End",
    "234": "Statement From Date",
    "235": "Statement Through Date",
    "291": "Coordination of Benefits",
    "304": "Latest Activity",
    "307": "Disability",
    "318": "Added",
    "340": "Admission Date/Time",
    "341": "Accident",
    "342": "Issue",
    "343": "Prescription",
    "344": "Initial Treatment",
    "347": "Initial Placement",
    "348": "Initial Return to Work",
    "349": "Last Menstrual Period",
    "350": "Begin Therapy",
    "351": "End Therapy",
    "352": "Medicare Begin",
    "353": "Medicare End",
    "354": "Medicaid Begin",
    "355": "Medicaid End",
    "356": "Eligibility Begin",
    "357": "Eligibility End",
    "382": "Enrollment",
    "405": "Production",
    "435": "Admission",
    "439": "Accident",
    "441": "Prior Placement",
    "442": "Date of Death",
    "444": "First Visit or Consultation",
    "453": "Acute Manifestation",
    "454": "Initial Treatment",
    "455": "Last X-Ray",
    "461": "Last Certification",
    "463": "Begin Therapy",
    "464": "End Therapy",
    "465": "Last Company Visit",
    "471": "Prescription",
    "472": "Service",
    "473": "Medicaid Begin",
    "474": "Medicaid End",
    "484": "Last Menstrual Period",
    "573": "Date Claim Paid"
}

# Reference Identification Qualifiers (REF-01)
REFERENCE_QUALIFIERS = {
    "0F": "Subscriber Number",
    "0K": "Policy Number",
    "1A": "Blue Cross Provider Number",
    "1B": "Blue Shield Provider Number",
    "1C": "Medicare Provider Number",
    "1D": "Medicaid Provider Number",
    "1E": "Dentist License Number",
    "1F": "Anesthesia License Number",
    "1G": "Provider UPIN Number",
    "1H": "CHAMPUS Identification Number",
    "1J": "Facility ID Number",
    "1K": "Payor's Claim Number",
    "1L": "Group or Policy Number",
    "1W": "Member Identification Number",
    "2U": "Payer Identification",
    "38": "Master Policy Number",
    "3H": "Case Number",
    "4N": "Special Payment Reference Number",
    "6P": "Group Number",
    "6R": "Provider Control Number",
    "9A": "Repriced Claim Reference Number",
    "9B": "Adjusted Repriced Claim Reference Number",
    "9C": "Adjusted Claim Number",
    "9F": "Referral Number",
    "A6": "Employee Identification Number",
    "BB": "Authorization Number",
    "CE": "Class of Contract Code",
    "CT": "Contract Type Code",
    "D9": "Claim Number",
    "DX": "Department/Agency Number",
    "EA": "Medical Record Number",
    "EI": "Employer's Identification Number",
    "EJ": "Patient Account Number",
    "F4": "Federal Taxpayer's Identification Number",
    "F8": "Original Reference Number",
    "FJ": "Line Item Control Number",
    "FY": "Claim Office Number",
    "G1": "Prior Authorization Number",
    "G3": "Predetermination of Benefits Number",
    "HPI": "Health Care Provider Identifier",
    "IG": "Insurance Policy Number",
    "LX": "Qualified Products List",
    "LU": "Location Number",
    "N5": "Provider Plan Network Identification Number",
    "N7": "Facility Network Identification Number",
    "PQ": "Payee Identification",
    "SY": "Social Security Number",
    "TJ": "Federal Taxpayer's Identification Number",
    "X4": "Clinical Laboratory Improvement Amendment Number",
    "X5": "State Industrial Accident Provider Number",
    "XZ": "Pharmacy Prescription Number",
    "Y4": "Claim Administrator Claim Number"
}

# Claim Status Codes (CLP-02)
CLAIM_STATUS_CODES = {
    "1": "Processed as Primary",
    "2": "Processed as Secondary",
    "3": "Processed as Tertiary",
    "4": "Denied",
    "5": "Pended",
    "19": "Processed as Primary, Forwarded to Additional Payer(s)",
    "20": "Processed as Secondary, Forwarded to Additional Payer(s)",
    "21": "Processed as Tertiary, Forwarded to Additional Payer(s)",
    "22": "Reversal of Previous Payment",
    "23": "Not Our Claim, Forwarded to Additional Payer(s)",
    "25": "Predetermination Pricing Only - No Payment",
    "27": "Reviewed"
}

# Claim Adjustment Group Codes (CAS-01)
ADJUSTMENT_GROUP_CODES = {
    "CO": "Contractual Obligations",
    "CR": "Correction and Reversals",
    "OA": "Other Adjustments",
    "PI": "Payor Initiated Reductions",
    "PR": "Patient Responsibility"
}

# Claim Adjustment Reason Codes (CAS-02) - Common ones
ADJUSTMENT_REASON_CODES = {
    "1": "Deductible",
    "2": "Coinsurance",
    "3": "Co-payment",
    "4": "The procedure code is inconsistent with the modifier used",
    "5": "The procedure code/bill type is inconsistent",
    "6": "The procedure/revenue code is inconsistent with patient's age",
    "7": "The procedure/revenue code is inconsistent with patient's gender",
    "8": "The procedure code is inconsistent with provider type/specialty",
    "9": "The diagnosis is inconsistent with the patient's age",
    "10": "The diagnosis is inconsistent with the patient's gender",
    "11": "The diagnosis is inconsistent with the procedure",
    "12": "The diagnosis is inconsistent with the provider type",
    "13": "The date of death precedes the date of service",
    "14": "The date of birth follows the date of service",
    "15": "The authorization number is missing, invalid, or does not apply",
    "16": "Claim/service lacks information needed for adjudication",
    "18": "Exact duplicate claim/service",
    "19": "This is a work-related injury/illness",
    "20": "This injury/illness is covered by the liability carrier",
    "21": "This injury/illness is the liability of the no-fault carrier",
    "22": "This care may be covered by another payer",
    "23": "The impact of prior payer(s) adjudication",
    "24": "Charges are covered under a capitation agreement/managed care plan",
    "26": "Expenses incurred prior to coverage",
    "27": "Expenses incurred after coverage terminated",
    "29": "The time limit for filing has expired",
    "31": "Patient cannot be identified as our insured",
    "32": "Our records indicate that this dependent is not an eligible dependent",
    "33": "Insured has no dependent coverage",
    "34": "Insured has no coverage for newborns",
    "35": "Lifetime benefit maximum has been reached",
    "45": "Charges exceed your contracted/legislated fee arrangement",
    "49": "This is a non-covered service",
    "50": "These services are non-covered",
    "51": "These are non-covered days",
    "53": "Services by an immediate relative or member of the same household",
    "54": "Multiple physicians/assistants are not covered",
    "55": "Procedure/treatment is deemed experimental/investigational",
    "56": "Procedure/treatment not approved by the FDA",
    "58": "Treatment was deemed by the payer to have been rendered in an inappropriate setting",
    "59": "Charges are adjusted based on multiple surgery rules",
    "60": "Charges for outpatient services with this proximity to inpatient services",
    "61": "Penalty for failure to obtain second surgical opinion",
    "66": "Blood deductible",
    "69": "Day outlier amount",
    "70": "Cost outlier - Adjustment to compensate for additional costs",
    "74": "Indirect medical education adjustment",
    "75": "Direct medical education adjustment",
    "76": "Disproportionate share adjustment",
    "78": "Non-covered days/Room charge adjustment",
    "85": "Patient interest adjustment",
    "87": "Transfer amount",
    "89": "Professional fees removed from charges",
    "90": "Ingredient cost adjustment",
    "91": "Dispensing fee adjustment",
    "94": "Processed in excess of charges",
    "95": "Plan procedures not followed",
    "96": "Non-covered charges",
    "97": "The benefit for this service is included in the payment/allowance",
    "100": "Payment made to patient/insured/responsible party",
    "101": "Predetermination: anticipated payment upon completion",
    "102": "Major medical adjustment",
    "103": "Provider promotional discount",
    "104": "Managed care withholding",
    "105": "Tax withholding",
    "106": "Patient payment option/election not in effect",
    "107": "The related or qualifying claim/service was not identified",
    "108": "Rent/purchase guidelines were not met",
    "109": "Claim/service not covered by this payer/contractor",
    "110": "Billing date predates service date",
    "111": "Not covered unless the provider accepts assignment",
    "112": "Service not furnished directly to the patient",
    "114": "Procedure/product not approved by the FDA",
    "115": "Procedure postponed, canceled, or delayed",
    "116": "The advance indemnification notice signed by the patient",
    "117": "Transportation is only covered to the closest facility",
    "118": "ESRD network support adjustment",
    "119": "Benefit maximum for this time period has been reached",
    "121": "Indemnification adjustment",
    "122": "Psychiatric reduction",
    "125": "Submission/billing error(s)",
    "128": "Newborn's services are covered in the mother's allowance",
    "129": "Prior processing information appears incorrect",
    "130": "Claim submission fee",
    "131": "Claim specific negotiated discount",
    "132": "Prearranged demonstration project adjustment",
    "133": "The disposition of this claim/service is pending further review",
    "134": "Technical fees removed from charges",
    "135": "Interim bills cannot be processed",
    "136": "Failure to follow prior payer's coverage rules",
    "137": "Regulatory surcharges, assessments or health related taxes",
    "138": "Appeal procedures not followed or time limits not met",
    "139": "Contracted funding agreement",
    "140": "Patient/insured health identification number and/or name do not match",
    "141": "Claim spans eligible and ineligible periods of coverage",
    "142": "Monthly Medicaid patient liability amount",
    "143": "Portion of payment deferred",
    "144": "Incentive adjustment",
    "146": "Diagnosis was invalid for the date(s) of service reported",
    "147": "Provider contracted/negotiated rate expired or not on file",
    "148": "Information from another provider was not provided",
    "149": "Lifetime benefit maximum has been reached for this service",
    "150": "Payer deems the information submitted does not support this level of service",
    "151": "Payment adjusted because the payer deems the information submitted does not support this many services",
    "152": "Payer deems the information submitted does not support this length of service",
    "153": "Payer deems the information submitted does not support this dosage",
    "154": "Payer deems the information submitted does not support this day's supply",
    "155": "Patient refused the service/procedure",
    "157": "Service/procedure was provided as a result of an act of war",
    "158": "Service/procedure was provided outside the United States",
    "159": "Service/procedure was provided as a result of terrorism",
    "160": "Injury/illness was the result of an activity that is a benefit exclusion",
    "161": "Provider performance bonus",
    "163": "Attachment/other documentation referenced on the claim was not received",
    "164": "Attachment/other documentation referenced on the claim was not received in a timely fashion",
    "165": "Provider rate increase(s) not covered",
    "166": "These services were submitted after this payers responsibility",
    "167": "This (these) diagnosis(es) is (are) not covered",
    "168": "Service(s) have been considered under the patient's medical plan",
    "169": "Alternate benefit has been provided",
    "170": "Payment is denied when performed by this type of provider",
    "171": "Payment is denied when performed by this type of facility",
    "172": "Payment is adjusted when performed in this type of facility",
    "173": "Service/equipment was not prescribed by a physician",
    "174": "Service was not prescribed prior to delivery",
    "175": "Prescription is incomplete",
    "176": "Prescription is not current",
    "177": "Patient has not met the required eligibility requirements",
    "178": "Patient has not met the required spend down requirements",
    "179": "Patient has not met the required waiting requirements",
    "180": "Patient has not met the required residency requirements",
    "181": "Procedure code was invalid on the date of service",
    "182": "Procedure modifier was invalid on the date of service",
    "183": "The referring provider is not eligible to refer",
    "184": "The prescribing/ordering provider is not eligible to prescribe/order the service billed",
    "185": "The rendering provider is not eligible to perform the service billed",
    "186": "Level of care change adjustment",
    "187": "Consumer spending account payments",
    "188": "This product/procedure is only covered when used according to FDA recommendations",
    "189": "'Not otherwise classified' or 'unlisted' procedure code",
    "190": "Payment is included in the allowance for another service/procedure",
    "192": "Non standard adjustment code from paper remittance advice",
    "193": "Original payment decision is being maintained",
    "194": "Anesthesia performed by the operating physician",
    "195": "Refund issued to an erroneous priority payer for this claim/service",
    "197": "Precertification/authorization/notification absent",
    "198": "Precertification/authorization exceeded",
    "199": "Revenue code and procedure code do not match",
    "200": "Expenses incurred during lapse in coverage",
    "201": "Patient is responsible for amount of this claim/service",
    "202": "Non-covered personal comfort or convenience services",
    "203": "Discontinued or reduced service",
    "204": "This service/equipment/drug is not covered",
    "205": "Pharmacy discount card processing fee",
    "206": "National provider identifier - missing",
    "207": "National provider identifier - invalid format",
    "208": "National provider identifier - not matched",
    "209": "Per regulatory or other agreement",
    "210": "National provider identifier - not eligible for electronic funds transfer",
    "211": "National drug codes units not consistent with billing units",
    "212": "Administrative surcharges are not covered",
    "213": "Non-compliance with the physician self-referral prohibition legislation",
    "215": "Based on subrogation of a third party settlement",
    "216": "Based on the findings of a review organization",
    "217": "Based on payer reasonable and customary fees",
    "218": "Based on entitlement to benefits",
    "219": "Based on extent of injury",
    "220": "Based on the findings of a review/review organization",
    "221": "Workers' compensation claim adjudicated as non-compensable",
    "222": "Exceeds the contracted maximum number of hours/days/units",
    "223": "Adjustment code for mandated federal state or local law/regulation",
    "224": "Patient identification compromised by identity theft",
    "225": "Penalty or interest payment by payer",
    "226": "Information requested from the billing/rendering provider",
    "227": "Information requested from the patient/insured/responsible party",
    "228": "Denied for failure to follow carrier's authorization protocols",
    "229": "Partial charge amount not considered",
    "230": "No available or correlating CPT/HCPCS code",
    "231": "Mutually exclusive procedures cannot be done in the same session",
    "232": "Institutional transfer amount",
    "233": "Services/charges related to the treatment of a hospital-acquired condition",
    "234": "This procedure is not paid separately",
    "235": "Sales tax",
    "236": "This procedure or procedure/modifier combination is not compatible",
    "237": "Legislated/regulatory penalty",
    "238": "Claim spans multiple rate periods",
    "239": "Claim spans multiple years",
    "240": "The diagnosis is inconsistent with the patient's birth weight",
    "241": "Low income subsidy co-payment amount",
    "242": "Services not provided by network providers",
    "243": "Services not authorized by network providers",
    "244": "Partial approval amount rescinded",
    "245": "Provider performance program withhold",
    "246": "This non-payable code is for reporting purposes only",
    "247": "Deductible waived per contract agreement",
    "248": "Coinsurance waived per contract agreement",
    "249": "Copayment waived per contract agreement",
    "250": "The attachment content received is inconsistent",
    "251": "The attachment content received did not contain the content required",
    "252": "An attachment is required",
    "253": "Sequestration - reduction in federal payment",
    "254": "Claim adjusted",
    "256": "Service not payable per managed care contract",
    "257": "Medical review or utilization review",
    "258": "Claim/service not covered when patient is in custody",
    "259": "Additional payment for covered service",
    "260": "Processed under Medicaid ACA enhanced fee schedule"
}

# Transaction Handling Codes (BPR-01)
TRANSACTION_HANDLING_CODES = {
    "C": "Payment Accompanies Remittance Advice",
    "D": "Make Payment Only",
    "H": "Notification Only",
    "I": "Remittance Information Only",
    "P": "Pre-notification of Future Transfer",
    "U": "Split Payment and Remittance",
    "X": "Handling Party's Option to Split"
}

# Payment Method Codes (BPR-04)
PAYMENT_METHOD_CODES = {
    "ACH": "Automated Clearing House",
    "BOP": "Financial Institution Option",
    "CHK": "Check",
    "FWT": "Federal Reserve Wire Transfer",
    "NON": "Non-payment Data",
    "SWT": "Society for Worldwide Interbank Financial Telecommunication (SWIFT)",
    "VEN": "Vendor Express Network"
}

# Credit/Debit Codes (BPR-03)
CREDIT_DEBIT_CODES = {
    "C": "Credit",
    "D": "Debit"
}

# Identification Code Qualifiers (NM1-08, N1-03, etc.)
ID_CODE_QUALIFIERS = {
    "00": "Contracting Corporation",
    "01": "Commercial and Government Entity (CAGE)",
    "10": "Department of Defense Activity Address Code",
    "11": "Drug Enforcement Administration",
    "13": "Federal Communications Commission (FCC)",
    "15": "Standard Industry Classification (SIC)",
    "16": "ZIP Code",
    "17": "Dunn & Bradstreet Number",
    "18": "Federal Maritime Commission (FMC)",
    "19": "Department of Transportation",
    "20": "International Air Transport Association (IATA)",
    "21": "Plant Code",
    "22": "Terminal Code",
    "24": "Employer's Identification Number",
    "25": "Carrier's Customer Code",
    "26": "NVOCC Code",
    "27": "Government Bill Of Lading Office Code",
    "28": "American Paper Institute",
    "30": "American Petroleum Institute Location Code",
    "32": "Brand Code",
    "33": "Buyer's Location Number",
    "34": "Social Security Number",
    "35": "Railroad Commission Code",
    "36": "Warehouse Code",
    "38": "UCC Communication ID",
    "39": "Standard Carrier Alpha Code (Motor)",
    "40": "Receiver's Sub Code",
    "41": "American Bankers Association (ABA) Transit/Routing Number",
    "42": "Receiver's Office Code",
    "43": "Save On Foods Account Number",
    "44": "Shipper's Sub Code",
    "45": "Shipper's Office Code",
    "46": "Electronic Transfer ID Number",
    "47": "Warehouse Storage Location Number",
    "48": "American Petroleum Institute Location Code",
    "53": "Bank of New England",
    "54": "Bank of Nova Scotia",
    "55": "Bank of Tokyo",
    "56": "Barclays Bank",
    "57": "Dai-Ichi Kangyo Bank, Ltd.",
    "58": "Bank One",
    "BD": "Blue Cross Blue Shield Association Plan Code",
    "BS": "Blue Shield Provider Number",
    "EI": "Employer's Identification Number",
    "FI": "Federal Taxpayer's Identification Number",
    "G2": "Provider Commercial Number",
    "HPI": "Health Care Provider Identifier",
    "II": "Standard Unique Health Identifier for each Individual in the United States",
    "MI": "Member Identification Number",
    "NI": "National Association of Insurance Commissioners (NAIC) Code",
    "PI": "Payor Identification",
    "PP": "Pharmacy Processor Number",
    "SV": "Service Provider Number",
    "XV": "Health Care Financing Administration Chain Number",
    "XX": "Centers for Medicare and Medicaid Services National Provider Identifier",
    "ZZ": "Mutually Defined"
}

# Individual Relationship Codes (INS-02)
INDIVIDUAL_RELATIONSHIP_CODES = {
    "01": "Spouse",
    "18": "Self",
    "19": "Child",
    "20": "Employee",
    "21": "Unknown",
    "39": "Organ Donor",
    "40": "Cadaver Donor",
    "53": "Life Partner",
    "60": "Sponsored Dependent",
    "G8": "Other Relationship"
}

# Yes/No Indicator Codes (INS-01, etc.)
YES_NO_CODES = {
    "N": "No",
    "U": "Unknown",
    "W": "Not Applicable",
    "Y": "Yes"
}

# Gender Codes (DMG-03)
GENDER_CODES = {
    "F": "Female",
    "M": "Male",
    "U": "Unknown"
}

# Provider Level Balance (PLB) Adjustment Codes
PLB_ADJUSTMENT_CODES = {
    "50": "Late filing penalty",
    "51": "Interest Penalty Charges",
    "72": "Authorized return",
    "AH": "Origination fee",
    "AM": "Applied to borrower account",
    "AP": "Acceleration of benefits",
    "B2": "Rebate",
    "B3": "Recovery allowance",
    "BD": "Bad debt adjustment",
    "BN": "Bonus",
    "C5": "Temporary allowance",
    "CI": "Contracted interest adjustment",
    "CS": "Adjustment",
    "CT": "Capitated services",
    "CV": "Capital passthru",
    "CW": "Certified registered nurse anesthetist passthru",
    "DM": "Direct medical education passthru",
    "E3": "Withholding",
    "FB": "Forfeiture / Beneficiary",
    "FC": "Fund allocation",
    "GO": "Graduate medical education passthru",
    "HM": "Hemophilia clotting factor supplement",
    "IP": "Incentive premium payment",
    "IR": "Internal revenue service withholding",
    "IS": "Interim settlement",
    "J1": "Non-reimbursable",
    "L3": "Penalty",
    "L6": "Interest owed",
    "LE": "Levy",
    "LS": "Lump sum",
    "OA": "Organ acquisition",
    "OB": "Offset for affiliated providers",
    "OC": "Other recoupment",
    "PI": "Periodic interim payment",
    "PL": "Payment final",
    "RA": "Retro-activity adjustment",
    "RE": "Return on equity",
    "SL": "Student loan repayment",
    "TL": "Third party liability",
    "WO": "Overpayment recovery",
    "WU": "Unspecified recovery"
}

# Hierarchical Level Codes (HL-03)
HIERARCHICAL_LEVEL_CODES = {
    "20": "Information Source",
    "21": "Information Receiver",
    "22": "Subscriber",
    "23": "Dependent",
    "19": "Provider of Service",
    "PT": "Party",
    "PI": "Payor"
}

# Claim Filing Indicator Codes (CLP-06, SBR-09)
CLAIM_FILING_CODES = {
    "09": "Self-Pay",
    "10": "Central Certification",
    "11": "Other Non-Federal Programs",
    "12": "Preferred Provider Organization (PPO)",
    "13": "Point of Service (POS)",
    "14": "Exclusive Provider Organization (EPO)",
    "15": "Indemnity Insurance",
    "16": "Health Maintenance Organization (HMO) Medicare Risk",
    "17": "Dental Maintenance Organization",
    "18": "Automobile Medical",
    "19": "Liability",
    "20": "Disability",
    "21": "Health Maintenance Organization",
    "22": "Liability Medical",
    "AM": "Automobile Medical",
    "BL": "Blue Cross/Blue Shield",
    "CH": "CHAMPUS",
    "CI": "Commercial Insurance Co.",
    "CN": "County Sponsored",
    "CO": "Consolidated Omnibus Budget Reconciliation Act (COBRA)",
    "CP": "Medicare Conditionally Primary",
    "DI": "Disability",
    "FI": "Federal Employees Program",
    "HM": "Health Maintenance Organization",
    "HS": "Special Low Income Medicare Beneficiary",
    "IN": "Indemnity",
    "LA": "Liability Auto",
    "LI": "Liability",
    "LM": "Liability Medical",
    "MA": "Medicare Part A",
    "MB": "Medicare Part B",
    "MC": "Medicaid",
    "MH": "Maternal and Child Health",
    "MI": "Military Treatment Facility",
    "MP": "Medicare Primary",
    "OT": "Other",
    "SP": "State Sponsored",
    "TF": "Tax Equity Fiscal Responsibility Act (TEFRA)",
    "TV": "Title V",
    "VA": "Veteran Administration Plan",
    "WC": "Workers' Compensation Health Claim",
    "ZZ": "Mutually Defined"
}


def get_entity_description(code: str) -> str:
    """Get description for entity identifier code"""
    return ENTITY_IDENTIFIER_CODES.get(code, f"Entity Code {code}")


def get_date_qualifier_description(code: str) -> str:
    """Get description for date/time qualifier"""
    return DATE_TIME_QUALIFIERS.get(code, f"Date Type {code}")


def get_reference_qualifier_description(code: str) -> str:
    """Get description for reference identification qualifier"""
    return REFERENCE_QUALIFIERS.get(code, f"Reference Type {code}")


def get_claim_status_description(code: str) -> str:
    """Get description for claim status code"""
    return CLAIM_STATUS_CODES.get(code, f"Claim Status {code}")


def get_adjustment_group_description(code: str) -> str:
    """Get description for claim adjustment group code"""
    return ADJUSTMENT_GROUP_CODES.get(code, f"Adjustment Group {code}")


def get_adjustment_reason_description(code: str) -> str:
    """Get description for claim adjustment reason code"""
    return ADJUSTMENT_REASON_CODES.get(code, f"Adjustment Reason {code}")


def get_payment_method_description(code: str) -> str:
    """Get description for payment method code"""
    return PAYMENT_METHOD_CODES.get(code, f"Payment Method {code}")


def get_relationship_description(code: str) -> str:
    """Get description for individual relationship code"""
    return INDIVIDUAL_RELATIONSHIP_CODES.get(code, f"Relationship {code}")


def get_gender_description(code: str) -> str:
    """Get description for gender code"""
    return GENDER_CODES.get(code, f"Gender {code}")


def get_claim_filing_description(code: str) -> str:
    """Get description for claim filing indicator code"""
    return CLAIM_FILING_CODES.get(code, f"Filing Code {code}")