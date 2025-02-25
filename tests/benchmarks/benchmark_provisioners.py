"""
Benchmarks for CommandLAB provisioners.

This module contains benchmarks for measuring the performance of various provisioners.
"""

import time
import statistics
import argparse
from typing import Dict, List, Type, Any
import matplotlib.pyplot as plt
import numpy as np

from commandLAB.computers.provisioners.base_provisioner import BaseComputerProvisioner
from commandLAB.computers.provisioners.docker_provisioner import (
    DockerProvisioner,
    DockerPlatform,
)
from commandLAB.computers.provisioners.manual_provisioner import ManualProvisioner


def benchmark_provisioner(
    provisioner_cls: Type[BaseComputerProvisioner],
    provisioner_kwargs: Dict[str, Any],
    num_runs: int = 5,
    include_teardown: bool = True,
) -> Dict[str, List[float]]:
    """
    Benchmark a provisioner by measuring setup and teardown times.

    Args:
        provisioner_cls: The provisioner class to benchmark
        provisioner_kwargs: Keyword arguments for the provisioner constructor
        num_runs: Number of benchmark runs
        include_teardown: Whether to include teardown in the benchmark

    Returns:
        Dictionary with setup and teardown times
    """
    setup_times = []
    teardown_times = []

    for i in range(num_runs):
        print(f"Run {i+1}/{num_runs}...")

        # Create provisioner
        provisioner = provisioner_cls(**provisioner_kwargs)

        # Measure setup time
        setup_start = time.time()
        try:
            provisioner.setup()
            setup_end = time.time()
            setup_time = setup_end - setup_start
            setup_times.append(setup_time)
            print(f"  Setup time: {setup_time:.2f}s")

            # Measure teardown time if requested
            if include_teardown:
                teardown_start = time.time()
                provisioner.teardown()
                teardown_end = time.time()
                teardown_time = teardown_end - teardown_start
                teardown_times.append(teardown_time)
                print(f"  Teardown time: {teardown_time:.2f}s")
        except Exception as e:
            print(f"  Error: {e}")
            # Still teardown if there was an error during setup
            if include_teardown:
                try:
                    provisioner.teardown()
                except Exception as e:
                    print(f"  Teardown error: {e}")

    return {
        "setup": setup_times,
        "teardown": teardown_times if include_teardown else [],
    }


def print_stats(name: str, times: List[float]) -> None:
    """Print statistics for a set of benchmark times."""
    if not times:
        print(f"{name}: No data")
        return

    print(f"{name}:")
    print(f"  Mean: {statistics.mean(times):.2f}s")
    print(f"  Median: {statistics.median(times):.2f}s")
    print(f"  Min: {min(times):.2f}s")
    print(f"  Max: {max(times):.2f}s")
    if len(times) > 1:
        print(f"  Std Dev: {statistics.stdev(times):.2f}s")


def plot_results(
    results: Dict[str, Dict[str, List[float]]], title: str = "Provisioner Benchmark"
) -> None:
    """
    Plot benchmark results.

    Args:
        results: Dictionary mapping provisioner names to setup/teardown times
        title: Plot title
    """
    provisioners = list(results.keys())
    setup_means = [
        statistics.mean(results[p]["setup"]) if results[p]["setup"] else 0
        for p in provisioners
    ]
    teardown_means = [
        statistics.mean(results[p]["teardown"]) if results[p]["teardown"] else 0
        for p in provisioners
    ]

    setup_stds = [
        statistics.stdev(results[p]["setup"]) if len(results[p]["setup"]) > 1 else 0
        for p in provisioners
    ]
    teardown_stds = [
        (
            statistics.stdev(results[p]["teardown"])
            if len(results[p]["teardown"]) > 1
            else 0
        )
        for p in provisioners
    ]

    x = np.arange(len(provisioners))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width / 2, setup_means, width, label="Setup", yerr=setup_stds)
    rects2 = ax.bar(
        x + width / 2, teardown_means, width, label="Teardown", yerr=teardown_stds
    )

    ax.set_ylabel("Time (s)")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(provisioners)
    ax.legend()

    # Add labels on top of bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(
                f"{height:.1f}",
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
            )

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()
    plt.savefig("provisioner_benchmark.png")
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Benchmark CommandLAB provisioners")
    parser.add_argument("--runs", type=int, default=3, help="Number of benchmark runs")
    parser.add_argument(
        "--no-teardown", action="store_true", help="Skip teardown benchmarking"
    )
    parser.add_argument("--plot", action="store_true", help="Generate plot of results")
    args = parser.parse_args()

    # Define provisioners to benchmark
    provisioners = {
        "Docker (Local)": (
            DockerProvisioner,
            {
                "port": 8000,
                "platform": DockerPlatform.LOCAL,
                "container_name": "benchmark-test",
                "version": "latest",
            },
        ),
        "Manual": (ManualProvisioner, {"port": 8000}),
        # Add more provisioners as needed
    }

    # Run benchmarks
    results = {}
    for name, (cls, kwargs) in provisioners.items():
        print(f"\nBenchmarking {name}...")
        result = benchmark_provisioner(
            cls, kwargs, num_runs=args.runs, include_teardown=not args.no_teardown
        )
        results[name] = result

        # Print statistics
        print("\nResults:")
        print_stats("Setup", result["setup"])
        if not args.no_teardown:
            print_stats("Teardown", result["teardown"])

    # Plot results if requested
    if args.plot:
        plot_results(results)


if __name__ == "__main__":
    main()
