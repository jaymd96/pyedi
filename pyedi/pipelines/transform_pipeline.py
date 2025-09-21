"""
X12 Transformation Pipeline

Complete pipeline for transforming X12 EDI files to target schemas through
parsing, formatting, and mapping stages.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Union, Optional, List
from datetime import datetime

from ..core.parser import X12Parser
from ..core.structured_formatter import StructuredFormatter, format_structured
from ..core.mapper import SchemaMapper, load_mapping_definition, MappingBuilder


class X12Pipeline:
    """
    Complete transformation pipeline for X12 EDI files.

    Provides a simplified API for transforming EDI files through all stages:
    1. Parse EDI to generic JSON
    2. Format to structured JSON
    3. Map to target schema

    Examples:
        # Simple usage with file paths
        pipeline = X12Pipeline()
        result = pipeline.transform("input.edi", mapping="mapping.json")

        # With inline mapping definition
        pipeline = X12Pipeline()
        result = pipeline.transform(
            "input.edi",
            mapping={
                "name": "custom_mapping",
                "mapping_type": "only_mapped",
                "expressions": {...}
            }
        )

        # With custom configuration
        pipeline = X12Pipeline(verbose=True, save_intermediate=True)
        result = pipeline.transform("input.edi", "mapping.json", output="result.json")
    """

    def __init__(
        self,
        map_path: Optional[str] = None,
        verbose: bool = False,
        save_intermediate: bool = False,
        include_technical: bool = True
    ):
        """
        Initialize the transformation pipeline.

        Args:
            map_path: Optional path to pyx12 X12 maps directory
            verbose: Enable verbose logging
            save_intermediate: Save intermediate transformation files for debugging
            include_technical: Include technical codes in structured format
        """
        self.parser = X12Parser(map_path=map_path)
        self.formatter = StructuredFormatter()
        self.verbose = verbose
        self.save_intermediate = save_intermediate
        self.include_technical = include_technical

        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'files_succeeded': 0,
            'files_failed': 0,
            'processing_time': 0
        }

        # Configure logging
        self.logger = logging.getLogger(__name__)
        if verbose:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )

    def transform(
        self,
        edi_file: Union[str, Path],
        mapping: Union[Dict[str, Any], str, Path],
        output: Optional[Union[str, Path]] = None,
        return_intermediate: bool = False
    ) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        Transform an EDI file through the complete pipeline.

        Args:
            edi_file: Path to X12 EDI file
            mapping: Mapping definition (dict or file path) or None for structured only
            output: Optional output file path for final result
            return_intermediate: Return all intermediate transformations

        Returns:
            If return_intermediate is False: Final transformed JSON
            If return_intermediate is True: Dict with 'generic', 'structured', and 'mapped' keys

        Raises:
            FileNotFoundError: If EDI file doesn't exist
            ValueError: If mapping is invalid
        """
        start_time = datetime.now()

        # Ensure paths
        edi_path = Path(edi_file)
        if not edi_path.exists():
            raise FileNotFoundError(f"EDI file not found: {edi_file}")

        self.logger.info(f"Starting transformation of: {edi_path}")

        # Step 1: Parse EDI to generic JSON
        self.logger.info("Step 1: Parsing EDI to generic JSON...")
        generic_json = self.parser.parse(str(edi_path))

        if self.save_intermediate:
            intermediate_path = edi_path.with_suffix('.generic.json')
            self._save_json(generic_json, intermediate_path)
            self.logger.info(f"Saved generic JSON to: {intermediate_path}")

        # Step 2: Format to structured JSON
        self.logger.info("Step 2: Formatting to structured JSON...")
        structured_json = self.formatter.format(generic_json, self.include_technical)

        if self.save_intermediate:
            intermediate_path = edi_path.with_suffix('.structured.json')
            self._save_json(structured_json, intermediate_path)
            self.logger.info(f"Saved structured JSON to: {intermediate_path}")

        # Step 3: Map to target schema (if mapping provided)
        mapped_json = structured_json
        if mapping is not None:
            self.logger.info("Step 3: Mapping to target schema...")

            # Load mapping if it's a file path
            if isinstance(mapping, (str, Path)):
                mapping = load_mapping_definition(str(mapping))

            # Create mapper and perform mapping
            mapper = SchemaMapper(mapping)
            mapped_json = mapper.map(structured_json)

            if self.save_intermediate:
                intermediate_path = edi_path.with_suffix('.mapped.json')
                self._save_json(mapped_json, intermediate_path)
                self.logger.info(f"Saved mapped JSON to: {intermediate_path}")

        # Save final output if requested
        if output:
            output_path = Path(output)
            self._save_json(mapped_json, output_path)
            self.logger.info(f"Saved final result to: {output_path}")

        # Update statistics
        processing_time = (datetime.now() - start_time).total_seconds()
        self.stats['files_processed'] += 1
        self.stats['files_succeeded'] += 1
        self.stats['processing_time'] += processing_time

        self.logger.info(f"Transformation completed in {processing_time:.2f} seconds")

        # Return results
        if return_intermediate:
            return {
                'generic': generic_json,
                'structured': structured_json,
                'mapped': mapped_json
            }
        else:
            return mapped_json

    def transform_batch(
        self,
        edi_files: List[Union[str, Path]],
        mapping: Union[Dict[str, Any], str, Path],
        output_dir: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Transform multiple EDI files in batch.

        Args:
            edi_files: List of EDI file paths
            mapping: Mapping definition (dict or file path)
            output_dir: Optional directory for output files

        Returns:
            Dictionary with results and statistics
        """
        results = {}
        errors = {}

        # Create output directory if specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

        # Process each file
        for edi_file in edi_files:
            try:
                edi_path = Path(edi_file)
                self.logger.info(f"Processing {edi_path.name}...")

                # Determine output file path
                output_file = None
                if output_dir:
                    output_file = output_path / edi_path.with_suffix('.json').name

                # Transform file
                result = self.transform(edi_file, mapping, output_file)
                results[str(edi_file)] = result

            except Exception as e:
                self.logger.error(f"Failed to process {edi_file}: {e}")
                errors[str(edi_file)] = str(e)
                self.stats['files_failed'] += 1

        return {
            'results': results,
            'errors': errors,
            'statistics': self.stats
        }

    def create_mapping_builder(self, name: str, mapping_type: str = 'only_mapped') -> MappingBuilder:
        """
        Create a mapping builder for building custom mappings.

        Args:
            name: Name for the mapping
            mapping_type: Type of mapping ('only_mapped', 'merge_with_target', 'pass_through')

        Returns:
            MappingBuilder instance
        """
        return MappingBuilder(name, mapping_type)

    def validate_mapping(
        self,
        mapping: Union[Dict[str, Any], str, Path],
        sample_edi: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Validate a mapping definition, optionally with a sample EDI file.

        Args:
            mapping: Mapping definition to validate
            sample_edi: Optional sample EDI file to test

        Returns:
            Validation results with any errors or warnings
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        try:
            # Load mapping if it's a file path
            if isinstance(mapping, (str, Path)):
                mapping = load_mapping_definition(str(mapping))

            # Check required fields
            if 'name' not in mapping:
                results['warnings'].append("Mapping missing 'name' field")

            if 'mapping_type' not in mapping:
                results['warnings'].append("Mapping missing 'mapping_type' field")

            if 'expressions' not in mapping or not mapping.get('expressions'):
                results['errors'].append("Mapping missing or empty 'expressions' field")
                results['valid'] = False

            # Try to create mapper
            mapper = SchemaMapper(mapping)

            # If sample EDI provided, try the full pipeline
            if sample_edi:
                try:
                    self.transform(sample_edi, mapping)
                    results['sample_test'] = 'passed'
                except Exception as e:
                    results['errors'].append(f"Sample test failed: {str(e)}")
                    results['sample_test'] = 'failed'

        except Exception as e:
            results['errors'].append(f"Mapping validation failed: {str(e)}")
            results['valid'] = False

        return results

    def _save_json(self, data: Dict[str, Any], file_path: Union[str, Path], pretty: bool = True):
        """Save JSON data to file."""
        with open(file_path, 'w') as f:
            if pretty:
                json.dump(data, f, indent=2)
            else:
                json.dump(data, f)

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.copy()

    def reset_statistics(self):
        """Reset processing statistics."""
        self.stats = {
            'files_processed': 0,
            'files_succeeded': 0,
            'files_failed': 0,
            'processing_time': 0
        }