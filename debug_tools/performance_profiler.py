#!/usr/bin/env python3
"""
Performance Profiler Tool

Profile and optimize X12 transformation pipeline performance.
Identifies bottlenecks and provides optimization suggestions.
"""

import json
import argparse
import sys
import time
import cProfile
import pstats
import io
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import tracemalloc
import gc
import textwrap

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyedi import X12Parser, StructuredFormatter, SchemaMapper, X12Pipeline


class PerformanceProfiler:
    """Performance profiler for X12 transformation pipeline"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = []
        self.memory_snapshots = []

    def profile_file(self,
                     edi_file: str,
                     mapping_file: Optional[str] = None,
                     iterations: int = 1) -> Dict[str, Any]:
        """
        Profile EDI file processing

        Args:
            edi_file: Path to EDI file
            mapping_file: Optional mapping file
            iterations: Number of iterations for averaging

        Returns:
            Performance metrics
        """
        print("\n" + "="*80)
        print("⚡ PERFORMANCE PROFILER")
        print("="*80 + "\n")

        print(f"📄 File: {edi_file}")
        print(f"🔄 Iterations: {iterations}")
        print(f"🗺️ Mapping: {mapping_file or 'None'}\n")

        # Get file size
        file_size = Path(edi_file).stat().st_size
        print(f"📊 File size: {self._format_bytes(file_size)}\n")

        # Profile each component
        metrics = {
            'file_size': file_size,
            'iterations': iterations,
            'components': {},
            'totals': {},
            'memory': {},
            'bottlenecks': [],
            'recommendations': []
        }

        # 1. Profile parsing
        print("1️⃣ Profiling Parser...")
        parse_metrics = self._profile_parser(edi_file, iterations)
        metrics['components']['parser'] = parse_metrics

        # 2. Profile formatting
        print("2️⃣ Profiling Formatter...")
        format_metrics = self._profile_formatter(edi_file, iterations)
        metrics['components']['formatter'] = format_metrics

        # 3. Profile mapping (if provided)
        if mapping_file:
            print("3️⃣ Profiling Mapper...")
            map_metrics = self._profile_mapper(edi_file, mapping_file, iterations)
            metrics['components']['mapper'] = map_metrics

        # 4. Profile complete pipeline
        print("4️⃣ Profiling Complete Pipeline...")
        pipeline_metrics = self._profile_pipeline(edi_file, mapping_file, iterations)
        metrics['components']['pipeline'] = pipeline_metrics

        # Calculate totals and analyze
        metrics['totals'] = self._calculate_totals(metrics['components'])
        metrics['bottlenecks'] = self._identify_bottlenecks(metrics)
        metrics['recommendations'] = self._generate_recommendations(metrics)

        # Display results
        self._display_results(metrics)

        return metrics

    def _profile_parser(self, edi_file: str, iterations: int) -> Dict[str, Any]:
        """Profile X12Parser performance"""
        parser = X12Parser()
        times = []
        memory_usage = []

        for i in range(iterations):
            gc.collect()  # Clean up before measurement

            # Memory tracking
            tracemalloc.start()
            memory_before = tracemalloc.get_traced_memory()[0]

            # Time tracking
            start_time = time.perf_counter()

            # Parse
            with open(edi_file, 'r') as f:
                content = f.read()
            result = parser.parse(content)

            end_time = time.perf_counter()

            # Memory measurement
            memory_after = tracemalloc.get_traced_memory()[0]
            memory_used = memory_after - memory_before
            tracemalloc.stop()

            times.append(end_time - start_time)
            memory_usage.append(memory_used)

            if self.verbose:
                print(f"  Iteration {i+1}: {times[-1]:.3f}s, {self._format_bytes(memory_used)}")

        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        avg_memory = sum(memory_usage) / len(memory_usage)

        # Count elements in result
        segment_count = 0
        if 'transactions' in result:
            for trans in result['transactions']:
                segment_count += len(trans.get('segments', []))

        return {
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'avg_memory': avg_memory,
            'segments_processed': segment_count,
            'segments_per_second': segment_count / avg_time if avg_time > 0 else 0
        }

    def _profile_formatter(self, edi_file: str, iterations: int) -> Dict[str, Any]:
        """Profile StructuredFormatter performance"""
        parser = X12Parser()
        formatter = StructuredFormatter()

        # Parse once for formatting tests
        with open(edi_file, 'r') as f:
            content = f.read()
        generic_json = parser.parse(content)

        times = []
        memory_usage = []

        for i in range(iterations):
            gc.collect()

            tracemalloc.start()
            memory_before = tracemalloc.get_traced_memory()[0]

            start_time = time.perf_counter()
            result = formatter.format(generic_json)
            end_time = time.perf_counter()

            memory_after = tracemalloc.get_traced_memory()[0]
            memory_used = memory_after - memory_before
            tracemalloc.stop()

            times.append(end_time - start_time)
            memory_usage.append(memory_used)

            if self.verbose:
                print(f"  Iteration {i+1}: {times[-1]:.3f}s, {self._format_bytes(memory_used)}")

        return {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'avg_memory': sum(memory_usage) / len(memory_usage)
        }

    def _profile_mapper(self, edi_file: str, mapping_file: str, iterations: int) -> Dict[str, Any]:
        """Profile SchemaMapper performance"""
        parser = X12Parser()
        formatter = StructuredFormatter()

        # Prepare data
        with open(edi_file, 'r') as f:
            content = f.read()
        generic_json = parser.parse(content)
        structured_json = formatter.format(generic_json)

        # Load mapping
        with open(mapping_file, 'r') as f:
            mapping_def = json.load(f)

        mapper = SchemaMapper(mapping_def)

        times = []
        memory_usage = []

        for i in range(iterations):
            gc.collect()

            tracemalloc.start()
            memory_before = tracemalloc.get_traced_memory()[0]

            start_time = time.perf_counter()
            result = mapper.map(structured_json)
            end_time = time.perf_counter()

            memory_after = tracemalloc.get_traced_memory()[0]
            memory_used = memory_after - memory_before
            tracemalloc.stop()

            times.append(end_time - start_time)
            memory_usage.append(memory_used)

            if self.verbose:
                print(f"  Iteration {i+1}: {times[-1]:.3f}s, {self._format_bytes(memory_used)}")

        return {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'avg_memory': sum(memory_usage) / len(memory_usage),
            'expressions_count': len(mapping_def.get('expressions', {}))
        }

    def _profile_pipeline(self, edi_file: str, mapping_file: Optional[str], iterations: int) -> Dict[str, Any]:
        """Profile complete pipeline"""
        pipeline = X12Pipeline()

        times = []
        memory_usage = []

        for i in range(iterations):
            gc.collect()

            tracemalloc.start()
            memory_before = tracemalloc.get_traced_memory()[0]

            start_time = time.perf_counter()
            result = pipeline.transform(edi_file, mapping=mapping_file)
            end_time = time.perf_counter()

            memory_after = tracemalloc.get_traced_memory()[0]
            memory_used = memory_after - memory_before
            tracemalloc.stop()

            times.append(end_time - start_time)
            memory_usage.append(memory_used)

            if self.verbose:
                print(f"  Iteration {i+1}: {times[-1]:.3f}s, {self._format_bytes(memory_used)}")

        return {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'avg_memory': sum(memory_usage) / len(memory_usage)
        }

    def _calculate_totals(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total metrics"""
        total_time = sum(c.get('avg_time', 0) for c in components.values())
        total_memory = sum(c.get('avg_memory', 0) for c in components.values())

        return {
            'total_time': total_time,
            'total_memory': total_memory,
            'component_breakdown': {
                name: {
                    'time_pct': (c.get('avg_time', 0) / total_time * 100) if total_time > 0 else 0,
                    'memory_pct': (c.get('avg_memory', 0) / total_memory * 100) if total_memory > 0 else 0
                }
                for name, c in components.items()
            }
        }

    def _identify_bottlenecks(self, metrics: Dict[str, Any]) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []

        # Check for slow components (>50% of total time)
        breakdown = metrics['totals'].get('component_breakdown', {})
        for name, stats in breakdown.items():
            if stats['time_pct'] > 50:
                bottlenecks.append(f"{name.capitalize()} takes {stats['time_pct']:.1f}% of total time")

        # Check for memory intensive components
        for name, component in metrics['components'].items():
            if component.get('avg_memory', 0) > 100_000_000:  # >100MB
                bottlenecks.append(f"{name.capitalize()} uses {self._format_bytes(component['avg_memory'])}")

        # Check for slow segment processing
        if 'parser' in metrics['components']:
            sps = metrics['components']['parser'].get('segments_per_second', 0)
            if sps > 0 and sps < 1000:
                bottlenecks.append(f"Slow segment processing: {sps:.0f} segments/second")

        return bottlenecks

    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        # Parser recommendations
        if 'parser' in metrics['components']:
            parser_time = metrics['components']['parser'].get('avg_time', 0)
            if parser_time > 1.0:
                recommendations.append("Consider streaming parser for large files")
                recommendations.append("Pre-validate EDI structure to fail fast")

        # Formatter recommendations
        if 'formatter' in metrics['components']:
            formatter_memory = metrics['components']['formatter'].get('avg_memory', 0)
            if formatter_memory > 50_000_000:
                recommendations.append("Consider lazy evaluation in formatter")
                recommendations.append("Process transactions in chunks")

        # Mapper recommendations
        if 'mapper' in metrics['components']:
            expr_count = metrics['components']['mapper'].get('expressions_count', 0)
            if expr_count > 50:
                recommendations.append("Consider simplifying JSONata expressions")
                recommendations.append("Cache compiled JSONata expressions")

        # General recommendations
        if metrics['totals']['total_time'] > 5.0:
            recommendations.append("Consider parallel processing for multiple files")
            recommendations.append("Implement caching for frequently processed files")

        if not recommendations:
            recommendations.append("Performance is optimal for current file size")

        return recommendations

    def _display_results(self, metrics: Dict[str, Any]) -> None:
        """Display profiling results"""
        print("\n" + "="*80)
        print("📊 PERFORMANCE RESULTS")
        print("="*80 + "\n")

        # Component performance
        print("⏱️ COMPONENT TIMING:")
        print("-"*40)
        for name, component in metrics['components'].items():
            avg_time = component.get('avg_time', 0)
            min_time = component.get('min_time', 0)
            max_time = component.get('max_time', 0)
            print(f"{name.capitalize():12} Avg: {avg_time:6.3f}s  Min: {min_time:6.3f}s  Max: {max_time:6.3f}s")

        # Memory usage
        print("\n💾 MEMORY USAGE:")
        print("-"*40)
        for name, component in metrics['components'].items():
            avg_memory = component.get('avg_memory', 0)
            print(f"{name.capitalize():12} {self._format_bytes(avg_memory):>12}")

        # Performance breakdown
        print("\n📈 PERFORMANCE BREAKDOWN:")
        print("-"*40)
        breakdown = metrics['totals'].get('component_breakdown', {})
        for name, stats in breakdown.items():
            print(f"{name.capitalize():12} Time: {stats['time_pct']:5.1f}%  Memory: {stats['memory_pct']:5.1f}%")

        # Bottlenecks
        if metrics['bottlenecks']:
            print("\n⚠️ BOTTLENECKS IDENTIFIED:")
            print("-"*40)
            for bottleneck in metrics['bottlenecks']:
                print(f"  • {bottleneck}")

        # Recommendations
        print("\n💡 OPTIMIZATION RECOMMENDATIONS:")
        print("-"*40)
        for rec in metrics['recommendations']:
            print(f"  ✓ {rec}")

        # Summary
        print("\n📋 SUMMARY:")
        print("-"*40)
        print(f"Total Time:       {metrics['totals']['total_time']:.3f} seconds")
        print(f"Total Memory:     {self._format_bytes(metrics['totals']['total_memory'])}")
        print(f"File Size:        {self._format_bytes(metrics['file_size'])}")
        print(f"Processing Rate:  {metrics['file_size'] / metrics['totals']['total_time'] / 1024:.1f} KB/s")

    def _format_bytes(self, bytes_value: float) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"

    def profile_with_cprofile(self, edi_file: str, mapping_file: Optional[str] = None) -> None:
        """Detailed profiling with cProfile"""
        print("\n🔬 DETAILED PROFILING WITH cProfile")
        print("="*80 + "\n")

        pipeline = X12Pipeline()

        # Create profiler
        profiler = cProfile.Profile()

        # Profile the transformation
        profiler.enable()
        result = pipeline.transform(edi_file, mapping=mapping_file)
        profiler.disable()

        # Print statistics
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(30)  # Top 30 functions

        print(s.getvalue())

    def benchmark_batch(self, edi_files: List[str], mapping_file: Optional[str] = None) -> None:
        """Benchmark batch processing"""
        print("\n" + "="*80)
        print("📦 BATCH PROCESSING BENCHMARK")
        print("="*80 + "\n")

        print(f"Files to process: {len(edi_files)}")

        total_size = sum(Path(f).stat().st_size for f in edi_files if Path(f).exists())
        print(f"Total data size: {self._format_bytes(total_size)}\n")

        pipeline = X12Pipeline()

        # Process files
        start_time = time.perf_counter()
        results = []

        for i, edi_file in enumerate(edi_files, 1):
            file_start = time.perf_counter()
            result = pipeline.transform(edi_file, mapping=mapping_file)
            file_time = time.perf_counter() - file_start

            results.append({
                'file': Path(edi_file).name,
                'size': Path(edi_file).stat().st_size,
                'time': file_time
            })

            print(f"  [{i}/{len(edi_files)}] {Path(edi_file).name}: {file_time:.3f}s")

        total_time = time.perf_counter() - start_time

        # Display summary
        print("\n📊 BATCH SUMMARY:")
        print("-"*40)
        print(f"Total files:      {len(edi_files)}")
        print(f"Total size:       {self._format_bytes(total_size)}")
        print(f"Total time:       {total_time:.3f}s")
        print(f"Avg time/file:    {total_time/len(edi_files):.3f}s")
        print(f"Processing rate:  {total_size/total_time/1024:.1f} KB/s")


def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(
        description='Performance Profiler - Profile and optimize X12 transformation performance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
        Examples:
          %(prog)s sample.edi                     # Profile single file
          %(prog)s sample.edi -m mapping.json     # Profile with mapping
          %(prog)s sample.edi -i 10               # Run 10 iterations
          %(prog)s sample.edi --detailed          # Detailed cProfile output
          %(prog)s --batch file1.edi file2.edi    # Batch benchmark

        Output includes:
          - Component timing breakdown
          - Memory usage analysis
          - Bottleneck identification
          - Optimization recommendations
        ''')
    )

    parser.add_argument('edi_file', nargs='?',
                       help='EDI file to profile')
    parser.add_argument('-m', '--mapping',
                       help='Mapping definition file')
    parser.add_argument('-i', '--iterations', type=int, default=3,
                       help='Number of iterations for averaging (default: 3)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed iteration results')
    parser.add_argument('--detailed', action='store_true',
                       help='Run detailed cProfile analysis')
    parser.add_argument('--batch', nargs='+',
                       help='Benchmark batch processing of multiple files')

    args = parser.parse_args()

    # Create profiler
    profiler = PerformanceProfiler(verbose=args.verbose)

    if args.batch:
        # Batch benchmark mode
        profiler.benchmark_batch(args.batch, mapping_file=args.mapping)
    elif args.edi_file:
        # Single file profiling
        metrics = profiler.profile_file(
            args.edi_file,
            mapping_file=args.mapping,
            iterations=args.iterations
        )

        # Detailed profiling if requested
        if args.detailed:
            profiler.profile_with_cprofile(args.edi_file, args.mapping)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()