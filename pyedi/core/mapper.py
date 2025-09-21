#!/usr/bin/env python3
"""
Schema Mapper Module

Provides a flexible mapping engine that uses JSONata expressions to transform
structured JSON documents to target schema formats. Supports complex field
mappings, lookups, and transformations.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pathlib import Path
from io import StringIO, BytesIO
from jsonata.jsonata import Jsonata


class MappingType(Enum):
    """Mapping type determines how output fields are generated"""
    ONLY_MAPPED = "only_mapped"  # Only include fields with mapping expressions
    MERGE_WITH_TARGET = "merge_with_target"  # Start with target example, override with mapped
    PASS_THROUGH = "pass_through"  # Start with source, override with mapped


class SchemaMapper:
    """Schema mapper using JSONata expressions for complex transformations"""

    def __init__(self, mapping_definition: Union[Dict[str, Any], str, StringIO, Path]):
        """
        Initialize mapper with mapping definition

        Args:
            mapping_definition: Mapping as:
                - Dictionary containing mapping configuration
                - JSON string with mapping
                - StringIO containing JSON mapping
                - Path to JSON mapping file

                Dictionary should contain:
                - name: Mapping name
                - mapping_type: Type of mapping (only_mapped, merge_with_target, pass_through)
                - expressions: Dictionary of target field paths to JSONata expressions
                - target_example: Optional target template (for merge_with_target)
                - lookup_tables: Optional lookup tables for value conversion
                - schemas: Optional source/target schemas
        """
        # Load mapping definition if not already a dict
        if not isinstance(mapping_definition, dict):
            mapping_definition = self._load_mapping_definition(mapping_definition)
        self.logger = logging.getLogger(__name__)
        self.name = mapping_definition.get('name', 'unnamed_mapping')
        self.mapping_type = MappingType(mapping_definition.get('mapping_type', 'only_mapped'))
        self.expressions = mapping_definition.get('expressions', {})
        self.target_example = mapping_definition.get('target_example', {})
        self.lookup_tables = mapping_definition.get('lookup_tables', {})
        self.schemas = mapping_definition.get('schemas', {})

        # Pre-compile JSONata expressions for performance
        self.compiled_expressions = {}
        self._compile_expressions()

    def _compile_expressions(self):
        """Pre-compile all JSONata expressions"""
        for field_path, expression in self.expressions.items():
            if isinstance(expression, str):
                try:
                    # Create JSONata expression and bind lookup tables if needed
                    expr = Jsonata(expression)

                    # Register lookup table function if tables exist
                    if self.lookup_tables:
                        self._register_lookup_function(expr)

                    self.compiled_expressions[field_path] = expr
                except Exception as e:
                    self.logger.error(f"Failed to compile expression for {field_path}: {e}")
                    self.compiled_expressions[field_path] = None
            elif isinstance(expression, dict):
                # Handle nested object mappings
                self.compiled_expressions[field_path] = self._compile_nested_expressions(expression)

    def _compile_nested_expressions(self, expressions: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively compile nested expressions"""
        compiled = {}
        for key, value in expressions.items():
            if isinstance(value, str):
                try:
                    expr = Jsonata(value)
                    if self.lookup_tables:
                        self._register_lookup_function(expr)
                    compiled[key] = expr
                except Exception as e:
                    self.logger.error(f"Failed to compile nested expression: {e}")
                    compiled[key] = None
            elif isinstance(value, dict):
                compiled[key] = self._compile_nested_expressions(value)
            else:
                compiled[key] = value
        return compiled

    def _register_lookup_function(self, expr: Jsonata):
        """Register custom $lookupTable function with JSONata expression"""
        def lookup_table(table_name: str, key_field: str, value: Any, wildcard: Optional[str] = None):
            """
            Lookup a value in a table

            Args:
                table_name: Name of the lookup table
                key_field: Field to match against
                value: Value to lookup
                wildcard: Optional wildcard character for pattern matching

            Returns:
                Matching row from lookup table or None
            """
            if table_name not in self.lookup_tables:
                return None

            table = self.lookup_tables[table_name]

            for row in table:
                if wildcard and key_field in row:
                    # Handle wildcard matching
                    pattern = row[key_field].replace(wildcard, '.*')
                    import re
                    if re.match(pattern, str(value)):
                        return row
                elif key_field in row and row[key_field] == value:
                    return row

            return None

        # Register the function with the expression
        expr.register_lambda('lookupTable', lookup_table)

    def map(self, source: Union[Dict[str, Any], str, StringIO, Path]) -> Dict[str, Any]:
        """
        Map source JSON to target schema using mapping definition

        Args:
            source: Source JSON as dict, JSON string, StringIO, or path to JSON file

        Returns:
            Mapped JSON according to target schema definition
        """
        # Load source if needed
        if not isinstance(source, dict):
            source = self._load_json(source)

        # Initialize output based on mapping type
        output = self._initialize_output(source)

        # Apply mapping expressions
        for field_path, compiled_expr in self.compiled_expressions.items():
            try:
                result = self._evaluate_expression(compiled_expr, source)

                # Skip if expression returns None or $omitField
                if result is None or result == '$omitField':
                    continue

                # Set value in output
                self._set_nested_value(output, field_path, result)

            except Exception as e:
                self.logger.warning(f"Failed to evaluate expression for {field_path}: {e}")

        return output

    def _initialize_output(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize output based on mapping type"""
        if self.mapping_type == MappingType.MERGE_WITH_TARGET:
            # Start with deep copy of target example
            import copy
            return copy.deepcopy(self.target_example)
        elif self.mapping_type == MappingType.PASS_THROUGH:
            # Start with deep copy of source
            import copy
            return copy.deepcopy(source)
        else:  # ONLY_MAPPED
            # Start with empty dict
            return {}

    def _evaluate_expression(self, expr: Any, source: Dict[str, Any]) -> Any:
        """Evaluate a compiled expression or nested expressions"""
        if isinstance(expr, Jsonata):
            # Add lookup tables to context
            context = source.copy()
            if self.lookup_tables:
                context['$tables'] = self.lookup_tables

            # Evaluate JSONata expression
            return expr.evaluate(context)
        elif isinstance(expr, dict):
            # Recursively evaluate nested expressions
            result = {}
            for key, value in expr.items():
                evaluated = self._evaluate_expression(value, source)
                if evaluated is not None and evaluated != '$omitField':
                    result[key] = evaluated
            return result if result else None
        else:
            return expr

    def _set_nested_value(self, obj: Dict[str, Any], path: str, value: Any):
        """Set a value in nested dict using dot notation path"""
        keys = path.split('.')
        current = obj

        for key in keys[:-1]:
            # Handle array indices
            if '[' in key and ']' in key:
                base_key = key[:key.index('[')]
                index = int(key[key.index('[') + 1:key.index(']')])

                if base_key not in current:
                    current[base_key] = []

                # Extend array if needed
                while len(current[base_key]) <= index:
                    current[base_key].append({})

                current = current[base_key][index]
            else:
                if key not in current:
                    current[key] = {}
                current = current[key]

        # Set the final value
        final_key = keys[-1]
        if '[' in final_key and ']' in final_key:
            base_key = final_key[:final_key.index('[')]
            index = int(final_key[final_key.index('[') + 1:final_key.index(']')])

            if base_key not in current:
                current[base_key] = []

            while len(current[base_key]) <= index:
                current[base_key].append(None)

            current[base_key][index] = value
        else:
            current[final_key] = value

    def _load_json(self, source: Union[str, StringIO, Path]) -> Dict[str, Any]:
        """Load JSON from string, StringIO, or file"""
        # Handle StringIO
        if isinstance(source, StringIO):
            content = source.read()
            source.seek(0)  # Reset position
            return json.loads(content)

        # Handle Path object
        elif isinstance(source, Path):
            with open(source, 'r') as f:
                return json.load(f)

        # Handle string (could be path or JSON)
        elif isinstance(source, str):
            source_stripped = source.strip()

            # Check if it's a file path
            is_file_path = (
                source_stripped.startswith('/') or
                source_stripped.startswith('./') or
                source_stripped.startswith('../') or
                '\\' in source or  # Windows path
                ':' in source[:10] or  # Windows drive letter
                (not source_stripped.startswith('{') and
                 not source_stripped.startswith('['))  # Not JSON
            )

            if is_file_path and os.path.exists(source):
                # Load from file
                with open(source, 'r') as f:
                    return json.load(f)
            else:
                # Parse JSON string
                return json.loads(source)
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

    def _load_mapping_definition(self, source: Union[str, StringIO, Path]) -> Dict[str, Any]:
        """Load mapping definition from various sources"""
        return self._load_json(source)

    def validate(self, output: Dict[str, Any]) -> List[str]:
        """
        Validate output against target schema if available

        Args:
            output: Transformed output to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if 'target' in self.schemas:
            # TODO: Implement JSON Schema validation
            pass

        return errors


class MappingBuilder:
    """Helper class to build mapping definitions programmatically"""

    def __init__(self, name: str, mapping_type: str = 'only_mapped'):
        """Initialize mapping builder"""
        self.mapping_def = {
            'name': name,
            'mapping_type': mapping_type,
            'expressions': {},
            'lookup_tables': {}
        }

    def add_field_mapping(self, target_field: str, jsonata_expr: str) -> 'MappingBuilder':
        """Add a field mapping expression"""
        self.mapping_def['expressions'][target_field] = jsonata_expr
        return self

    def add_object_mapping(self, target_object: str, field_mappings: Dict[str, str]) -> 'MappingBuilder':
        """Add mappings for an object's fields"""
        self.mapping_def['expressions'][target_object] = field_mappings
        return self

    def add_list_mapping(self, target_list: str, source_list: str, field_mappings: Dict[str, str]) -> 'MappingBuilder':
        """Add list context and field mappings"""
        # Create JSONata expression for list transformation
        mappings_str = ', '.join([f'"{k}": {v}' for k, v in field_mappings.items()])
        expr = f"{source_list} ~> |$| {{ {mappings_str} }} |"
        self.mapping_def['expressions'][target_list] = expr
        return self

    def add_lookup_table(self, name: str, table_data: List[Dict[str, Any]]) -> 'MappingBuilder':
        """Add a lookup table"""
        self.mapping_def['lookup_tables'][name] = table_data
        return self

    def set_target_example(self, target_example: Dict[str, Any]) -> 'MappingBuilder':
        """Set target example for merge_with_target mode"""
        self.mapping_def['target_example'] = target_example
        return self

    def set_schemas(self, source_schema: Optional[Dict] = None, target_schema: Optional[Dict] = None) -> 'MappingBuilder':
        """Set source and/or target schemas"""
        self.mapping_def['schemas'] = {}
        if source_schema:
            self.mapping_def['schemas']['source'] = source_schema
        if target_schema:
            self.mapping_def['schemas']['target'] = target_schema
        return self

    def build(self) -> Dict[str, Any]:
        """Build and return the mapping definition"""
        return self.mapping_def

    def export_to_file(self, file_path: str):
        """Export mapping definition to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.mapping_def, f, indent=2)

    def create_mapper(self) -> SchemaMapper:
        """Create a SchemaMapper instance from this definition"""
        return SchemaMapper(self.mapping_def)


# Convenience functions
def load_mapping_definition(source: Union[str, StringIO, Path]) -> Dict[str, Any]:
    """
    Load mapping definition from various sources

    Args:
        source: Mapping definition as file path, JSON string, or StringIO

    Returns:
        Mapping definition dictionary
    """
    mapper = SchemaMapper({'name': 'temp', 'mapping_type': 'only_mapped', 'expressions': {}})
    return mapper._load_json(source)


def map_to_schema(source: Union[Dict, str, StringIO, Path], mapping: Union[Dict, str, StringIO, Path]) -> Dict[str, Any]:
    """
    Quick mapping function for JSON-to-JSON transformations

    Args:
        source: Source JSON (dict, string, StringIO, or file path)
        mapping: Mapping definition (dict, string, StringIO, or file path)

    Returns:
        Mapped JSON according to target schema
    """
    # Create mapper and map
    mapper = SchemaMapper(mapping)
    return mapper.map(source)