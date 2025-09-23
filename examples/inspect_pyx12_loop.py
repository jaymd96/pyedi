#!/usr/bin/env python3
"""Inspect pyx12 loop properties"""

import pyx12.map_if
import pyx12.map_index
import pyx12.params

# Get the map for 835
params = pyx12.params.params()
map_path = pyx12.map_index.get_map_path('00501', '835')
print(f'Map path: {map_path}')

# Load the map and inspect loop properties
map_obj = pyx12.map_if.load_map_file(map_path, params)
print('\nMap loaded. Checking for loop properties...\n')

# Look for loop nodes
def inspect_node(node, depth=0):
    indent = '  ' * depth

    # Check if it's a loop
    if hasattr(node, 'base_name') and node.base_name == 'loop':
        print(f'{indent}Loop: {node.id} - {node.name}')

        # Check various attributes
        attrs_to_check = ['max_use', 'usage', 'pos', 'repeat', 'required', 'min_use']
        for attr in attrs_to_check:
            if hasattr(node, attr):
                val = getattr(node, attr)
                if val is not None:
                    print(f'{indent}  {attr}: {val}')

        # Check if it can repeat
        if hasattr(node, 'max_use'):
            if node.max_use and (node.max_use == 'unbounded' or (isinstance(node.max_use, (int, str)) and str(node.max_use) != '1')):
                print(f'{indent}  --> REPEATING LOOP')

        print()  # blank line for readability

    # Recursively check children
    if hasattr(node, '__iter__'):
        for child in node:
            if hasattr(child, 'base_name'):
                inspect_node(child, depth + 1)

inspect_node(map_obj)

print("\n\n=== Now checking 834 ===\n")
map_path_834 = pyx12.map_index.get_map_path('00501', '834')
map_obj_834 = pyx12.map_if.load_map_file(map_path_834, params)
inspect_node(map_obj_834)