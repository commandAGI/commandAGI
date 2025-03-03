"""
Benchmarks for commandAGI2 computer implementations.

This module contains benchmarks for measuring the performance of various computer implementations.
"""

import time
import statistics
import argparse
from typing import Dict, List, Type, Any, Optional
import matplotlib.pyplot as plt
import numpy as np
import os

from commandAGI2.computers.base_computer import BaseComputer
from commandAGI2.computers.local_pynput_computer import LocalPynputComputer
from commandAGI2.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandAGI2.types import (
    ClickAction,
    TypeAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    MouseMoveAction,
    MouseScrollAction,
)


def benchmark_computer_operation(
    computer: BaseComputer,
    operation_name: str,
    operation_func: callable,
    num_runs: int = 10,
) -> List[float]:
    """
    Benchmark a specific computer operation.

    Args:
        computer: The computer instance to benchmark
        operation_name: Name of the operation for display
        operation_func: Function to call for the operation
        num_runs: Number of benchmark runs

    Returns:
        List of execution times
    """
    times = []

    for i in range(num_runs):
        print(f"  Run {i+1}/{num_runs} of {operation_name}...", end="", flush=True)

        # Measure operation time
        start = time.time()
        try:
            operation_func()
            end = time.time()
            execution_time = end - start
            times.append(execution_time)
            print(f" {execution_time:.4f}s")
        except Exception as e:
            print(f" Error: {e}")

    return times


def benchmark_computer(
    computer_cls: Type[BaseComputer],
    computer_kwargs: Dict[str, Any],
    num_runs: int = 10,
) -> Dict[str, List[float]]:
    """
    Benchmark a computer implementation by measuring various operations.

    Args:
        computer_cls: The computer class to benchmark
        computer_kwargs: Keyword arguments for the computer constructor
        num_runs: Number of benchmark runs per operation

    Returns:
        Dictionary mapping operation names to execution times
    """
    print(f"Creating {computer_cls.__name__}...")
    computer = computer_cls(**computer_kwargs)

    # Define operations to benchmark
    operations = {
        "get_screenshot": lambda: computer.get_screenshot(),
        "get_mouse_state": lambda: computer.get_mouse_state(),
        "get_keyboard_state": lambda: computer.get_keyboard_state(),
        "mouse_move": lambda: computer.execute_mouse_move(
            MouseMoveAction(x=100, y=100, move_duration=0.1)
        ),
        "mouse_scroll": lambda: computer.execute_mouse_scroll(
            MouseScrollAction(amount=10)
        ),
        "click": lambda: computer.execute_click(
            ClickAction(x=100, y=100, move_duration=0.1, press_duration=0.1)
        ),
        "type_short": lambda: computer.execute_type(TypeAction(text="test")),
        "type_long": lambda: computer.execute_type(
            TypeAction(text="This is a longer text to test typing performance")
        ),
        "hotkey": lambda: computer.execute_keyboard_hotkey(
            KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.A])
        ),
    }

    results = {}
    for name, func in operations.items():
        print(f"\nBenchmarking {name}...")
        times = benchmark_computer_operation(computer, name, func, num_runs)
        results[name] = times

    # Clean up
    try:
        computer.close()
    except Exception as e:
        print(f"Error during cleanup: {e}")

    return results


def print_stats(name: str, times: List[float]) -> None:
    """Print statistics for a set of benchmark times."""
    if not times:
        print(f"{name}: No data")
        return

    print(f"{name}:")
    print(f"  Mean: {statistics.mean(times):.4f}s")
    print(f"  Median: {statistics.median(times):.4f}s")
    print(f"  Min: {min(times):.4f}s")
    print(f"  Max: {max(times):.4f}s")
    if len(times) > 1:
        print(f"  Std Dev: {statistics.stdev(times):.4f}s")


def plot_results(
    results: Dict[str, Dict[str, List[float]]],
    operations: Optional[List[str]] = None,
    title: str = "Computer Implementation Benchmark",
) -> None:
    """
    Plot benchmark results.

    Args:
        results: Dictionary mapping computer names to operation times
        operations: List of operations to include in the plot (None for all)
        title: Plot title
    """
    computers = list(results.keys())

    # Determine which operations to plot
    if operations is None:
        # Use operations from the first computer
        operations = list(results[computers[0]].keys())

    # Create a figure with subplots for each operation
    fig, axes = plt.subplots(len(operations), 1, figsize=(12, 4 * len(operations)))
    if len(operations) == 1:
        axes = [axes]  # Make axes iterable if there's only one subplot

    for i, operation in enumerate(operations):
        ax = axes[i]

        # Calculate means and standard deviations
        means = [
            (
                statistics.mean(results[c][operation])
                if operation in results[c] and results[c][operation]
                else 0
            )
            for c in computers
        ]
        stds = [
            (
                statistics.stdev(results[c][operation])
                if operation in results[c] and len(results[c][operation]) > 1
                else 0
            )
            for c in computers
        ]

        # Create bar chart
        x = np.arange(len(computers))
        bars = ax.bar(x, means, yerr=stds)

        # Add labels
        ax.set_ylabel("Time (s)")
        ax.set_title(f"{operation}")
        ax.set_xticks(x)
        ax.set_xticklabels(computers)

        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.4f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
            )

    fig.suptitle(title, fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.97])  # Adjust for the suptitle
    plt.savefig("computer_benchmark.png")
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark commandAGI2 computer implementations"
    )
    parser.add_argument(
        "--runs", type=int, default=5, help="Number of benchmark runs per operation"
    )
    parser.add_argument("--plot", action="store_true", help="Generate plot of results")
    parser.add_argument(
        "--operations", nargs="+", help="Specific operations to benchmark"
    )
    args = parser.parse_args()

    # Define computers to benchmark
    computers = {
        "LocalPynputComputer": (LocalPynputComputer, {}),
        "LocalPyAutoGUIComputer": (LocalPyAutoGUIComputer, {}),
        # Add more computer implementations as needed
    }

    # Run benchmarks
    results = {}
    for name, (cls, kwargs) in computers.items():
        print(f"\n{'='*50}")
        print(f"Benchmarking {name}...")
        print(f"{'='*50}")

        result = benchmark_computer(cls, kwargs, num_runs=args.runs)
        results[name] = result

        # Print statistics
        print("\nResults:")
        for operation, times in result.items():
            if args.operations is None or operation in args.operations:
                print_stats(operation, times)

    # Plot results if requested
    if args.plot:
        plot_results(results, operations=args.operations)


if __name__ == "__main__":
    main()
