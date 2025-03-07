"""
Benchmarks for commandAGI image utilities.

This module contains benchmarks for measuring the performance of image utility functions.
"""

import time
import statistics
import argparse
from typing import Dict, List, Callable, Any, Tuple
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
import io
import base64

from commandAGI.utils.image import b64ToImage, imageToB64, imageToBytes, bytesToImage
from commandAGI.processors.grid_overlay import overlay_grid


def generate_test_images(sizes: List[Tuple[int, int]]) -> Dict[str, Image.Image]:
    """
    Generate test images of different sizes.

    Args:
        sizes: List of (width, height) tuples

    Returns:
        Dictionary mapping size names to PIL Images
    """
    images = {}

    for width, height in sizes:
        # Create a new image
        image = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(image)

        # Draw some shapes
        draw.rectangle(
            [width // 10, height // 10, width // 3, height // 3], outline="red", width=2
        )
        draw.ellipse(
            [width // 2, height // 4, width * 3 // 4, height * 3 // 4],
            outline="blue",
            width=2,
        )
        draw.line(
            [width * 4 // 5, height // 10, width * 9 // 10, height * 9 // 10],
            fill="green",
            width=3,
        )

        # Add some text
        draw.text((width // 5, height * 4 // 5), f"{width}x{height}", fill="black")

        # Add to dictionary
        images[f"{width}x{height}"] = image

    return images


def benchmark_function(
    func: Callable, args: List[Any], num_runs: int = 10
) -> List[float]:
    """
    Benchmark a function by measuring execution time.

    Args:
        func: Function to benchmark
        args: Arguments to pass to the function
        num_runs: Number of benchmark runs

    Returns:
        List of execution times
    """
    times = []

    for i in range(num_runs):
        # Measure execution time
        start = time.time()
        try:
            result = func(*args)
            end = time.time()
            execution_time = end - start
            times.append(execution_time)
        except Exception as e:
            print(f"Error: {e}")

    return times


def benchmark_image_utils(
    images: Dict[str, Image.Image], num_runs: int = 10
) -> Dict[str, Dict[str, List[float]]]:
    """
    Benchmark image utility functions with different image sizes.

    Args:
        images: Dictionary mapping size names to PIL Images
        num_runs: Number of benchmark runs per function

    Returns:
        Dictionary mapping function names to dictionaries mapping image sizes to execution times
    """
    results = {
        "b64ToImage": {},
        "imageToB64": {},
        "imageToBytes": {},
        "bytesToImage": {},
        "overlay_grid": {},
    }

    for size_name, image in images.items():
        print(f"\nBenchmarking with {size_name} image...")

        # Convert image to base64 and bytes for testing
        b64_image = imageToB64(image)
        bytes_image = imageToBytes(image)

        # Benchmark imageToB64
        print(f"  Benchmarking imageToB64...", end="", flush=True)
        times = benchmark_function(imageToB64, [image], num_runs)
        results["imageToB64"][size_name] = times
        print(f" Mean: {statistics.mean(times):.6f}s")

        # Benchmark b64ToImage
        print(f"  Benchmarking b64ToImage...", end="", flush=True)
        times = benchmark_function(b64ToImage, [b64_image], num_runs)
        results["b64ToImage"][size_name] = times
        print(f" Mean: {statistics.mean(times):.6f}s")

        # Benchmark imageToBytes
        print(f"  Benchmarking imageToBytes...", end="", flush=True)
        times = benchmark_function(imageToBytes, [image], num_runs)
        results["imageToBytes"][size_name] = times
        print(f" Mean: {statistics.mean(times):.6f}s")

        # Benchmark bytesToImage
        print(f"  Benchmarking bytesToImage...", end="", flush=True)
        times = benchmark_function(bytesToImage, [bytes_image], num_runs)
        results["bytesToImage"][size_name] = times
        print(f" Mean: {statistics.mean(times):.6f}s")

        # Benchmark overlay_grid
        print(f"  Benchmarking overlay_grid...", end="", flush=True)
        times = benchmark_function(overlay_grid, [image, 50], num_runs)
        results["overlay_grid"][size_name] = times
        print(f" Mean: {statistics.mean(times):.6f}s")

    return results


def print_stats(name: str, times: List[float]) -> None:
    """Print statistics for a set of benchmark times."""
    if not times:
        print(f"{name}: No data")
        return

    print(f"{name}:")
    print(f"  Mean: {statistics.mean(times):.6f}s")
    print(f"  Median: {statistics.median(times):.6f}s")
    print(f"  Min: {min(times):.6f}s")
    print(f"  Max: {max(times):.6f}s")
    if len(times) > 1:
        print(f"  Std Dev: {statistics.stdev(times):.6f}s")


def plot_results(
    results: Dict[str, Dict[str, List[float]]], title: str = "Image Utilities Benchmark"
) -> None:
    """
    Plot benchmark results.

    Args:
        results: Dictionary mapping function names to dictionaries mapping image sizes to execution times
        title: Plot title
    """
    functions = list(results.keys())
    sizes = list(results[functions[0]].keys())

    # Create a figure with subplots for each function
    fig, axes = plt.subplots(len(functions), 1, figsize=(12, 4 * len(functions)))
    if len(functions) == 1:
        axes = [axes]  # Make axes iterable if there's only one subplot

    for i, function in enumerate(functions):
        ax = axes[i]

        # Calculate means and standard deviations
        means = [statistics.mean(results[function][size]) for size in sizes]
        stds = [
            (
                statistics.stdev(results[function][size])
                if len(results[function][size]) > 1
                else 0
            )
            for size in sizes
        ]

        # Create bar chart
        x = np.arange(len(sizes))
        bars = ax.bar(x, means, yerr=stds)

        # Add labels
        ax.set_ylabel("Time (s)")
        ax.set_title(f"{function}")
        ax.set_xticks(x)
        ax.set_xticklabels(sizes)

        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.6f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
            )

    fig.suptitle(title, fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.97])  # Adjust for the suptitle
    plt.savefig("image_utils_benchmark.png")
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Benchmark commandAGI image utilities")
    parser.add_argument(
        "--runs", type=int, default=10, help="Number of benchmark runs per function"
    )
    parser.add_argument("--plot", action="store_true", help="Generate plot of results")
    args = parser.parse_args()

    # Define image sizes to test
    sizes = [
        (640, 480),  # VGA
        (800, 600),  # SVGA
        (1024, 768),  # XGA
        (1280, 720),  # HD
        (1920, 1080),  # Full HD
    ]

    # Generate test images
    print("Generating test images...")
    images = generate_test_images(sizes)

    # Run benchmarks
    print("\nRunning benchmarks...")
    results = benchmark_image_utils(images, num_runs=args.runs)

    # Print detailed statistics
    print("\nDetailed Results:")
    for function, size_results in results.items():
        print(f"\n{function}:")
        for size, times in size_results.items():
            print_stats(f"  {size}", times)

    # Plot results if requested
    if args.plot:
        plot_results(results)


if __name__ == "__main__":
    main()
