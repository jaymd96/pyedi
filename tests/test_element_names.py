#!/usr/bin/env python3
"""Test what element names pyx12 provides"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from pyedi import X12Parser

# Simple 834 test
edi_834 = """ISA*00*          *00*          *ZZ*SENDERNAME     *ZZ*RECEIVERNAME   *041227*1324*^*00501*000000103*0*P*>~
GS*BE*SENDERNAME*RECEIVERNAME*20041227*1324*000000103*X*005010X220A1~
ST*834*12345*005010X220A1~
BGN*00*12456*19980520*1200****2~
REF*38*ABCD012354~
SE*5*12345~
GE*1*000000103~
IEA*1*000000103~"""

import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.edi', delete=False) as f:
    f.write(edi_834)
    temp_file = f.name

parser = X12Parser()
parsed = parser.parse(temp_file)

# Print the raw parsed output to see element names
print("Raw parsed segments (first 3):")
segments = parsed['transactions'][0]['segments'][:3]
print(json.dumps(segments, indent=2))

os.unlink(temp_file)