"""
PyEDI - Python X12 EDI Parser and Transformer

A comprehensive Python package for parsing, transforming, and mapping X12 EDI files
to various target schemas using JSONata expressions.

Main Components:
    - X12Parser: Parse X12 EDI files to generic JSON
    - StructuredFormatter: Format generic JSON to structured format
    - SchemaMapper: Map structured JSON to target schemas
    - X12Pipeline: Complete transformation pipeline

Basic Usage:
    from pyedi import X12Pipeline

    pipeline = X12Pipeline()
    result = pipeline.transform("input.edi", mapping="mapping.json")

Advanced Usage:
    from pyedi import X12Parser, StructuredFormatter, SchemaMapper

    # Step-by-step processing
    parser = X12Parser()
    generic_json = parser.parse("input.edi")

    formatter = StructuredFormatter()
    structured_json = formatter.format(generic_json)

    mapper = SchemaMapper(mapping_definition)
    target_json = mapper.map(structured_json)
"""

__version__ = "1.0.2"
__author__ = "James"

# Core components
from .core.parser import X12Parser
from .core.structured_formatter import StructuredFormatter, format_structured
from .core.mapper import SchemaMapper, MappingBuilder, load_mapping_definition, map_to_schema

# Pipeline for simplified usage
from .pipelines.transform_pipeline import X12Pipeline

# Convenience exports
__all__ = [
    # Main classes
    "X12Parser",
    "StructuredFormatter",
    "SchemaMapper",
    "X12Pipeline",

    # Builder and utilities
    "MappingBuilder",

    # Convenience functions
    "format_structured",
    "load_mapping_definition",
    "map_to_schema",

    # Version info
    "__version__",
]