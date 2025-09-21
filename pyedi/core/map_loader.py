#!/usr/bin/env python3
"""
Dynamic Map Element Loader

This module dynamically loads element names and definitions from pyx12 XML map files,
allowing the system to work with any X12 transaction type and version without hardcoding.
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, Optional, Any
from functools import lru_cache

try:
    from pkg_resources import resource_string, resource_exists
except ImportError:
    # Fallback for newer Python versions
    import importlib.resources as resources

    def resource_string(package, path):
        """Compatibility wrapper for resource_string"""
        with resources.files(package).joinpath(path).open('rb') as f:
            return f.read()

    def resource_exists(package, path):
        """Compatibility wrapper for resource_exists"""
        return resources.files(package).joinpath(path).exists()


class MapElementLoader:
    """Dynamically loads element names from pyx12 XML map files"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._cache = {}  # Cache loaded maps
        self._element_cache = {}  # Cache individual element lookups

    @lru_cache(maxsize=32)
    def load_map_elements(self, map_filename: str) -> Dict[str, Dict[str, Any]]:
        """
        Load and parse element definitions from a pyx12 map file

        Args:
            map_filename: Name of the XML map file (e.g., '834.5010.X220.A1.xml')

        Returns:
            Dictionary of segments with their element definitions
        """
        # Check cache first
        if map_filename in self._cache:
            return self._cache[map_filename]

        segments = {}

        try:
            # Check if map exists
            map_path = f'map/{map_filename}'
            if not resource_exists('pyx12', map_path):
                self.logger.warning(f"Map file not found: {map_filename}")
                return segments

            # Load the XML map
            map_content = resource_string('pyx12', map_path)
            root = ET.fromstring(map_content)

            # Extract transaction info
            transaction_id = root.get('xid', 'unknown')
            transaction_name = root.find('.//name')
            if transaction_name is not None:
                self.logger.debug(f"Loading map for: {transaction_name.text}")

            # Find all segment definitions (recursive search)
            for segment in root.iter('segment'):
                seg_id = segment.get('xid')
                if not seg_id:
                    continue

                # Get segment name
                seg_name_elem = segment.find('name')
                seg_name = seg_name_elem.text if seg_name_elem is not None else seg_id

                segments[seg_id] = {
                    'name': seg_name,
                    'elements': {}
                }

                # Get all elements in this segment
                for element in segment.findall('element'):
                    elem_id = element.get('xid')
                    if not elem_id:
                        continue

                    # Extract element metadata
                    elem_name = element.find('name')
                    data_ele = element.find('data_ele')
                    usage = element.find('usage')
                    data_type = element.find('data_type')
                    min_len = element.find('min_len')
                    max_len = element.find('max_len')

                    elem_info = {
                        'name': elem_name.text if elem_name is not None else elem_id,
                        'data_ele': data_ele.text if data_ele is not None else None,
                        'usage': usage.text if usage is not None else 'S',
                        'data_type': data_type.text if data_type is not None else 'AN',
                        'min_len': int(min_len.text) if min_len is not None else None,
                        'max_len': int(max_len.text) if max_len is not None else None
                    }

                    segments[seg_id]['elements'][elem_id] = elem_info

            # Cache the results
            self._cache[map_filename] = segments
            self.logger.info(f"Loaded {len(segments)} segment definitions from {map_filename}")

        except Exception as e:
            self.logger.error(f"Error loading map {map_filename}: {e}", exc_info=True)

        return segments

    def get_element_name(self, map_filename: str, segment_id: str, element_id: str) -> str:
        """
        Get the descriptive name for an element

        Args:
            map_filename: Map file to use (e.g., '834.5010.X220.A1.xml')
            segment_id: Segment ID (e.g., 'BGN')
            element_id: Element ID (e.g., 'BGN01')

        Returns:
            Descriptive element name or the element ID if not found
        """
        # Check element cache first
        cache_key = f"{map_filename}:{segment_id}:{element_id}"
        if cache_key in self._element_cache:
            return self._element_cache[cache_key]

        # Load map if needed
        segments = self.load_map_elements(map_filename)

        # Look up the element
        if segment_id in segments:
            elements = segments[segment_id].get('elements', {})
            if element_id in elements:
                name = elements[element_id].get('name', element_id)
                self._element_cache[cache_key] = name
                return name

        # Fallback to element ID
        self._element_cache[cache_key] = element_id
        return element_id

    def get_element_info(self, map_filename: str, segment_id: str, element_id: str) -> Dict[str, Any]:
        """
        Get complete element information including name, type, usage, etc.

        Args:
            map_filename: Map file to use
            segment_id: Segment ID
            element_id: Element ID

        Returns:
            Dictionary with element metadata
        """
        segments = self.load_map_elements(map_filename)

        if segment_id in segments:
            elements = segments[segment_id].get('elements', {})
            if element_id in elements:
                return elements[element_id]

        # Return minimal info if not found
        return {
            'name': element_id,
            'data_ele': None,
            'usage': 'S',
            'data_type': 'AN'
        }

    def get_segment_name(self, map_filename: str, segment_id: str) -> str:
        """
        Get the descriptive name for a segment

        Args:
            map_filename: Map file to use
            segment_id: Segment ID (e.g., 'BGN')

        Returns:
            Descriptive segment name or the segment ID if not found
        """
        segments = self.load_map_elements(map_filename)

        if segment_id in segments:
            return segments[segment_id].get('name', segment_id)

        return segment_id

    def format_element_name_for_json(self, name: str, element_id: str) -> str:
        """
        Format element name for use as a JSON key (Stedi-style format)

        Args:
            name: Descriptive element name
            element_id: Element ID (e.g., 'BGN01')

        Returns:
            Formatted field name with position number
        """
        import re

        # Extract position number from element ID
        position = re.search(r'\d+$', element_id)
        if position:
            position_num = position.group()
        else:
            position_num = element_id

        # If name is same as element ID, just return it
        if name == element_id:
            return element_id.lower()

        # Convert name to snake_case and clean up
        name = re.sub(r'[^\w\s]', '', name)  # Remove special characters
        name = re.sub(r'\s+', '_', name)  # Replace spaces with underscores
        name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)  # Handle acronyms
        name = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', name)  # Handle camelCase
        name = name.lower()

        # Remove redundant words
        name = re.sub(r'_code_code', '_code', name)
        name = re.sub(r'_id_id', '_id', name)
        name = re.sub(r'_identifier_identifier', '_identifier', name)
        name = re.sub(r'_number_number', '_number', name)

        # Add position number
        return f"{name}_{position_num.zfill(2)}"


# Global instance for convenience
_loader_instance = None

def get_loader() -> MapElementLoader:
    """Get the global MapElementLoader instance"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = MapElementLoader()
    return _loader_instance


def get_element_name(map_filename: str, segment_id: str, element_id: str) -> str:
    """
    Convenience function to get element name

    Args:
        map_filename: Map file to use
        segment_id: Segment ID
        element_id: Element ID

    Returns:
        Descriptive element name
    """
    return get_loader().get_element_name(map_filename, segment_id, element_id)


def format_element_name(name: str, element_id: str) -> str:
    """
    Convenience function to format element name

    Args:
        name: Descriptive element name
        element_id: Element ID

    Returns:
        Formatted field name
    """
    return get_loader().format_element_name_for_json(name, element_id)