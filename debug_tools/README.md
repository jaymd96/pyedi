# PyEDI Debug Tools

A comprehensive suite of debugging and analysis tools for the PyEDI X12 EDI transformation pipeline.

## Overview

These tools help developers debug, optimize, and understand the EDI transformation process at every stage. Each tool is designed to address specific debugging needs:

## Tools

### 1. EDI Inspector (`edi_inspector.py`)
Interactive tool for visualizing EDI structure, loop hierarchy, and segment details.

```bash
# Basic inspection
python debug_tools/edi_inspector.py sample.edi

# Verbose mode with interactive exploration
python debug_tools/edi_inspector.py sample.edi -v

# Export analysis to JSON
python debug_tools/edi_inspector.py sample.edi --export
```

**Features:**
- Tree view of EDI structure
- Loop hierarchy visualization
- Segment detail inspection
- Interactive exploration mode
- Export analysis reports

### 2. Pipeline Debugger (`pipeline_debugger.py`)
Step-through debugger for the transformation pipeline with inspection at each stage.

```bash
# Debug EDI transformation
python debug_tools/pipeline_debugger.py sample.edi

# Debug with mapping
python debug_tools/pipeline_debugger.py sample.edi -m mapping.json

# Save intermediate files
python debug_tools/pipeline_debugger.py sample.edi --save

# Run without pausing
python debug_tools/pipeline_debugger.py sample.edi --no-step
```

**Features:**
- Step-by-step transformation debugging
- Inspect data at each stage
- Diff between transformation stages
- Save intermediate results
- Validate structure at each step

### 3. JSONata Tester (`jsonata_tester.py`)
Interactive tool for testing and debugging JSONata mapping expressions.

```bash
# Start interactive tester
python debug_tools/jsonata_tester.py

# Load EDI file as test data
python debug_tools/jsonata_tester.py sample.edi

# Load JSON file as test data
python debug_tools/jsonata_tester.py structured.json
```

**Features:**
- Real-time expression evaluation
- Save and reuse expressions
- Expression history
- Import/export expression libraries
- Built-in examples

### 4. Segment Lookup (`segment_lookup.py`)
Quick reference tool for EDI segments, elements, and code values.

```bash
# Lookup segment
python debug_tools/segment_lookup.py NM1

# Lookup element
python debug_tools/segment_lookup.py NM101

# Lookup code
python debug_tools/segment_lookup.py IL

# Interactive mode
python debug_tools/segment_lookup.py --interactive
```

**Features:**
- Segment descriptions and structure
- Element definitions and types
- Code value meanings
- Usage examples
- Search capabilities

### 5. Performance Profiler (`performance_profiler.py`)
Profile and optimize pipeline performance to identify bottlenecks.

```bash
# Profile single file
python debug_tools/performance_profiler.py sample.edi

# Profile with mapping
python debug_tools/performance_profiler.py sample.edi -m mapping.json

# Run multiple iterations
python debug_tools/performance_profiler.py sample.edi -i 10

# Detailed cProfile analysis
python debug_tools/performance_profiler.py sample.edi --detailed

# Batch benchmark
python debug_tools/performance_profiler.py --batch file1.edi file2.edi file3.edi
```

**Features:**
- Component timing breakdown
- Memory usage analysis
- Bottleneck identification
- Optimization recommendations
- Batch processing benchmarks

## Common Use Cases

### Debugging a Failed Transformation

1. Use **EDI Inspector** to understand the EDI structure:
   ```bash
   python debug_tools/edi_inspector.py problem.edi -v
   ```

2. Use **Pipeline Debugger** to find where it fails:
   ```bash
   python debug_tools/pipeline_debugger.py problem.edi --save
   ```

3. Check intermediate files in `debug_output/` directory

### Optimizing Slow Processing

1. Profile the file to identify bottlenecks:
   ```bash
   python debug_tools/performance_profiler.py slow.edi -v
   ```

2. Get detailed function-level profiling:
   ```bash
   python debug_tools/performance_profiler.py slow.edi --detailed
   ```

3. Follow the optimization recommendations

### Testing Mapping Expressions

1. Load your structured JSON:
   ```bash
   python debug_tools/jsonata_tester.py structured.json
   ```

2. Test expressions interactively:
   ```
   jsonata> $.detail.claim[amount > 100]
   jsonata> $sum($.detail.claim.amount)
   ```

3. Save working expressions:
   ```
   jsonata> save getTotalAmount $sum($.detail.claim.amount)
   ```

### Understanding EDI Codes

1. Interactive lookup session:
   ```bash
   python debug_tools/segment_lookup.py -i
   ```

2. Quick lookups:
   ```
   lookup> NM1
   lookup> NM101
   lookup> IL
   ```

## Installation

The debug tools are included with the PyEDI package. No additional installation is required.

## Requirements

- Python 3.8+
- PyEDI package installed
- jsonata-python (for JSONata tester)

## Tips

1. **Start with EDI Inspector** to understand your file structure
2. **Use Pipeline Debugger** when transformations fail
3. **Test JSONata expressions** before adding to mappings
4. **Profile regularly** to catch performance regressions
5. **Keep Segment Lookup handy** for quick reference

## Support

For issues or questions about the debug tools, please open an issue on the PyEDI GitHub repository.