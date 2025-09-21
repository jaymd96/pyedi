# Changelog

## [1.0.6] - 2025-09-21

### Added
- Support for string and StringIO inputs in X12Pipeline, X12Parser, and SchemaMapper
- Flexible input handling for both EDI content and mapping definitions
- Support for in-memory processing without file system operations

### Changed
- `X12Parser.parse()` now accepts:
  - File paths (existing behavior)
  - EDI string content
  - StringIO/BytesIO file-like objects
- `SchemaMapper.__init__()` now accepts:
  - Dictionary mappings (existing behavior)
  - JSON strings
  - StringIO objects
  - File paths
- `X12Pipeline.transform()` now accepts flexible input types for both EDI and mapping

### Examples
```python
from io import StringIO
from pyedi import X12Pipeline

# Use with string content
pipeline = X12Pipeline()
edi_content = "ISA*00*..."
mapping_json = '{"name": "test", ...}'

# String EDI with dict mapping
result = pipeline.transform(edi_content, {"name": "test", ...})

# String EDI with JSON string mapping
result = pipeline.transform(edi_content, mapping_json)

# StringIO for both inputs
edi_io = StringIO(edi_content)
mapping_io = StringIO(mapping_json)
result = pipeline.transform(edi_io, mapping_io)
```

## [1.0.5] - 2025-09-20

### Fixed
- BPR04 payment method code no longer incorrectly converted to float/None
- Generic field names replaced with context-aware naming based on X12 entity codes
- Added comprehensive support for 150+ X12 entity identifier codes
- Qualifier-based field naming for REF, DTP, DTM, CLM, SVC, CAS segments
- All fixes are generic and work with any X12 transaction type

### Added
- Context-aware field naming using loop context and entity codes
- Comprehensive X12 ANSI standard entity code mappings
- Better handling of payment date extraction from BPR segments

## [1.0.4] - 2025-09-19

### Added
- Initial release with full X12 EDI parsing and transformation support
- Support for 835, 837, 834, and other X12 transaction types
- JSONata-based flexible mapping engine
- Stedi Guide JSON format compatibility