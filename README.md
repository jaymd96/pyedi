# PyEDI

A comprehensive Python package for parsing, transforming, and mapping X12 EDI files to various target schemas using JSONata expressions.

## Features

- **Complete X12 Parsing**: Parse any X12 EDI file to generic JSON using the robust pyx12 library
- **Structured Formatting**: Transform generic JSON to a structured format that preserves X12 organization
- **Flexible Schema Mapping**: Map structured JSON to any target schema using powerful JSONata expressions
- **Simple Pipeline API**: Easy-to-use pipeline for complete EDI transformation
- **Batch Processing**: Process multiple EDI files efficiently
- **Comprehensive Code Sets**: Built-in EDI code descriptions and lookups
- **Extensible Architecture**: Use individual components or the complete pipeline

## Installation

### From PyPI

```bash
pip install pyedi
```

### From Source

```bash
git clone https://github.com/jaymd96/pyedi.git
cd pyedi
pip install -e .
```

### With Optional Features

```bash
# Install with CLI support
pip install pyedi[cli]

# Install with development tools
pip install pyedi[dev]
```

## Quick Start

### Simple Usage

```python
from pyedi import X12Pipeline

# Create pipeline
pipeline = X12Pipeline()

# Transform EDI file with mapping
result = pipeline.transform(
    edi_file="path/to/835.edi",
    mapping="path/to/mapping.json"
)

print(result)
```

### Step-by-Step Processing

```python
from pyedi import X12Parser, StructuredFormatter, SchemaMapper

# Step 1: Parse EDI to generic JSON
parser = X12Parser()
generic_json = parser.parse("path/to/835.edi")

# Step 2: Format to structured JSON
formatter = StructuredFormatter()
structured_json = formatter.format(generic_json)

# Step 3: Map to target schema
mapper = SchemaMapper(mapping_definition)
target_json = mapper.map(structured_json)
```

## Core Components

### X12Parser

Parses X12 EDI files into generic JSON format while preserving all contextual information.

```python
from pyedi import X12Parser

parser = X12Parser()
generic_json = parser.parse("input.edi")
```

**Features:**
- Handles all X12 transaction types
- Preserves loop structure and hierarchy
- Includes segment metadata and paths
- Validates using pyx12 maps

### StructuredFormatter

Transforms generic JSON into a structured format with meaningful field names and code descriptions.

```python
from pyedi import StructuredFormatter

formatter = StructuredFormatter()
structured_json = formatter.format(generic_json, include_technical=True)
```

**Features:**
- Transaction-specific formatting (835, 837, 834, etc.)
- Human-readable code descriptions
- Preserves X12 structure
- Optional technical code inclusion

### SchemaMapper

Maps structured JSON to target schemas using JSONata expressions.

```python
from pyedi import SchemaMapper

mapper = SchemaMapper(mapping_definition)
target_json = mapper.map(structured_json)
```

**Features:**
- Powerful JSONata expression support
- Lookup table support
- Conditional transformations
- Complex field mappings

## Creating Custom Mappings

### Using MappingBuilder

```python
from pyedi import MappingBuilder

# Create builder
builder = MappingBuilder("my_mapping", mapping_type="only_mapped")

# Add simple field mappings
builder.add_field_mapping("payment_id", "trace_information.check_or_eft_number")
builder.add_field_mapping("payment_date", "payment_information.payment_date")

# Add object mapping
builder.add_object_mapping("payer", {
    "name": "payer.name",
    "id": "payer.identification.value"
})

# Add calculated fields using JSONata
builder.add_field_mapping("total_claims", "$count(claims)")

# Build and export
mapping = builder.build()
builder.export_to_file("my_mapping.json")
```

### Inline Mapping Definition

```python
mapping = {
    "name": "simple_835_extract",
    "mapping_type": "only_mapped",
    "expressions": {
        "payment_id": "trace_information.check_or_eft_number",
        "payment_amount": "payment_information.total_payment_amount",
        "claim_count": "$count(claims)",
        "claims": "claims ~> |$| { 'id': patient_control_number, 'amount': total_paid_amount } |"
    }
}
```

## Mapping Types

- **`only_mapped`**: Output contains only mapped fields
- **`merge_with_target`**: Start with target template, override with mapped values
- **`pass_through`**: Start with source data, override with mapped values

## JSONata Expression Examples

### Basic Field Access
```javascript
"payment_information.payment_date"  // Access nested field
"claims[0].claim_number"            // Array index access
```

### Calculations
```javascript
"$count(claims)"                    // Count items
"$sum(claims.total_paid_amount)"    // Sum values
```

### Transformations
```javascript
// Transform array of objects
"claims ~> |$| { 'id': patient_control_number, 'amount': total_paid_amount } |"

// Filter and transform
"claims[total_charge_amount > 1000] ~> |$| claim_number |"
```

### Conditionals
```javascript
"claim_status.code = '1' ? 'Paid' : 'Denied'"
```

## Batch Processing

```python
pipeline = X12Pipeline(verbose=True)

results = pipeline.transform_batch(
    edi_files=["file1.edi", "file2.edi", "file3.edi"],
    mapping="mapping.json",
    output_dir="output/"
)

print(f"Processed: {results['statistics']['files_processed']}")
print(f"Succeeded: {results['statistics']['files_succeeded']}")
```

## CLI Usage

After installation with CLI support:

```bash
# Transform single file
x12-convert input.edi --mapping mapping.json --output result.json

# Transform with options
x12-convert input.edi --mapping mapping.json --verbose --save-intermediate

# Batch processing
x12-convert *.edi --mapping mapping.json --batch --output-dir results/
```

## Supported Transaction Types

- **835** - Healthcare Claim Payment/Remittance Advice
- **837** - Healthcare Claim (Professional, Institutional, Dental)
- **834** - Benefit Enrollment and Maintenance
- **270/271** - Eligibility Inquiry and Response
- **276/277** - Claim Status Request and Response
- **278** - Healthcare Services Review
- And all other X12 transaction types (generic processing)

## Advanced Features

### Return All Intermediate Stages

```python
all_stages = pipeline.transform(
    edi_file="input.edi",
    mapping="mapping.json",
    return_intermediate=True
)

generic_json = all_stages['generic']
structured_json = all_stages['structured']
mapped_json = all_stages['mapped']
```

### Validate Mappings

```python
validation = pipeline.validate_mapping(
    mapping="mapping.json",
    sample_edi="sample.edi"  # Optional
)

if validation['valid']:
    print("Mapping is valid!")
else:
    print("Errors:", validation['errors'])
```

### Custom Lookup Tables

```python
builder = MappingBuilder("mapping_with_lookups")

# Add lookup table
builder.add_lookup_table("status_codes", [
    {"code": "1", "description": "Paid"},
    {"code": "4", "description": "Denied"}
])

# Use in mapping
builder.add_field_mapping(
    "claim_status",
    "$lookupTable('status_codes', 'code', claim_status.code).description"
)
```

## Project Structure

```
x12_edi_converter/
├── core/
│   ├── parser.py              # X12 to generic JSON parser
│   ├── structured_formatter.py # Generic to structured formatter
│   └── mapper.py              # JSONata-based mapper
├── code_sets/
│   └── edi_codes.py          # EDI code descriptions
├── pipelines/
│   └── transform_pipeline.py # Complete transformation pipeline
├── examples/
│   ├── basic_usage.py        # Basic usage examples
│   └── custom_mapping.py     # Custom mapping examples
└── cli/
    └── main.py               # Command-line interface
```

## Requirements

- Python 3.8+
- pyx12 >= 2.3.3
- jsonata >= 0.2.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on top of the excellent [pyx12](https://github.com/azoner/pyx12) library
- Uses [JSONata](https://jsonata.org/) for powerful JSON transformations
- Inspired by enterprise EDI processing needs in healthcare

## Support

- Documentation: [https://pyedi.readthedocs.io](https://pyedi.readthedocs.io)
- Issues: [GitHub Issues](https://github.com/jaymd96/pyedi/issues)
- Discussions: [GitHub Discussions](https://github.com/jaymd96/pyedi/discussions)

## Roadmap

- [ ] Additional transaction type templates
- [ ] Performance optimizations for large files
- [ ] Streaming support for very large EDI files
- [ ] Web-based mapping designer
- [ ] Additional output format support (XML, CSV)
- [ ] EDI validation and compliance checking

---

Built for the healthcare development community