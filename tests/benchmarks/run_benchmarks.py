#!/usr/bin/env python3
"""
Run all CommandLAB benchmarks.

This script runs all the benchmark modules and generates a summary report.
"""

import argparse
import os
import sys
import time
import subprocess
import datetime
from pathlib import Path


def run_benchmark(benchmark_module: str, args: list = None) -> bool:
    """
    Run a benchmark module with the given arguments.
    
    Args:
        benchmark_module: Name of the benchmark module to run
        args: Additional arguments to pass to the benchmark module
        
    Returns:
        True if the benchmark ran successfully, False otherwise
    """
    if args is None:
        args = []
    
    print(f"\n{'='*80}")
    print(f"Running {benchmark_module}...")
    print(f"{'='*80}")
    
    cmd = [sys.executable, "-m", f"tests.benchmarks.{benchmark_module}"] + args
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running {benchmark_module}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Run CommandLAB benchmarks')
    parser.add_argument('--runs', type=int, default=3, help='Number of benchmark runs')
    parser.add_argument('--plot', action='store_true', help='Generate plots')
    parser.add_argument('--output', type=str, default='benchmark_results', help='Output directory for results')
    parser.add_argument('--benchmarks', nargs='+', help='Specific benchmarks to run')
    parser.add_argument('--screenparse-api-key', type=str, help='API key for ScreenParse.ai')
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Define available benchmarks
    benchmarks = {
        "benchmark_provisioners": [],
        "benchmark_computers": [],
        "benchmark_daemon": [],
        "benchmark_image_utils": [],
        "benchmark_screen_parser": []
    }
    
    # Filter benchmarks if specified
    if args.benchmarks:
        benchmarks = {k: v for k, v in benchmarks.items() if k in args.benchmarks}
    
    # Add common arguments
    for benchmark in benchmarks:
        benchmarks[benchmark].extend(["--runs", str(args.runs)])
        if args.plot:
            benchmarks[benchmark].append("--plot")
    
    # Add specific arguments for certain benchmarks
    if "benchmark_screen_parser" in benchmarks and args.screenparse_api_key:
        benchmarks["benchmark_screen_parser"].extend(["--api-key", args.screenparse_api_key])
    
    # Run benchmarks
    start_time = time.time()
    results = {}
    
    for benchmark, benchmark_args in benchmarks.items():
        success = run_benchmark(benchmark, benchmark_args)
        results[benchmark] = "Success" if success else "Failed"
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Generate summary report
    report_path = os.path.join(args.output, "benchmark_summary.txt")
    with open(report_path, "w") as f:
        f.write(f"CommandLAB Benchmark Summary\n")
        f.write(f"===========================\n\n")
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total time: {total_time:.2f}s\n\n")
        
        f.write(f"Results:\n")
        for benchmark, status in results.items():
            f.write(f"  {benchmark}: {status}\n")
    
    print(f"\n{'='*80}")
    print(f"Benchmark Summary")
    print(f"{'='*80}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Results:")
    for benchmark, status in results.items():
        print(f"  {benchmark}: {status}")
    print(f"Summary report written to {report_path}")


if __name__ == "__main__":
    main() 