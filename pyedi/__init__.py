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

# CRITICAL: Apply Python 3.11+ compatibility patch BEFORE any imports
# This must happen before pyx12 is imported anywhere
import sys
if sys.version_info >= (3, 11):
    import builtins
    _original_open = builtins.open

    def _patched_open(*args, **kwargs):
        """Remove deprecated 'U' mode for Python 3.11+ compatibility"""
        # Handle positional mode argument
        if len(args) > 1 and isinstance(args[1], str):
            if args[1] == 'U':
                # 'U' mode alone should become 'r' (text mode)
                args = list(args)
                args[1] = 'r'
            elif 'U' in args[1]:
                # Remove 'U' from compound modes like 'rU'
                args = list(args)
                args[1] = args[1].replace('U', '')
        # Handle keyword mode argument
        if 'mode' in kwargs and isinstance(kwargs['mode'], str):
            if kwargs['mode'] == 'U':
                kwargs['mode'] = 'r'
            elif 'U' in kwargs['mode']:
                kwargs['mode'] = kwargs['mode'].replace('U', '')
        return _original_open(*args, **kwargs)

    builtins.open = _patched_open

__version__ = "1.1.0"
__author__ = "James"

# NOW we can safely import modules that use pyx12
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