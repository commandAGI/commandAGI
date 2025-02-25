"""
Benchmarks for CommandLAB screen parsers.

This module contains benchmarks for measuring the performance of screen parsing utilities.
"""

import time
import statistics
import argparse
from typing import Dict, List, Callable, Any, Tuple, Optional
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os
import tempfile

try:
    from commandLAB.processors.screen_parser.pytesseract_screen_parser import parse_screenshot as pytesseract_parse
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

try:
    from commandLAB.processors.screen_parser.screenparse_ai_screen_parser import parse_screenshot as screenparse_ai_parse
    SCREENPARSE_AI_AVAILABLE = True
except ImportError:
    SCREENPARSE_AI_AVAILABLE = False

from commandLAB.utils.image import imageToB64


def generate_test_images(
    sizes: List[Tuple[int, int]],
    text_densities: List[str]
) -> Dict[str, Dict[str, Image.Image]]:
    """
    Generate test images of different sizes and text densities.
    
    Args:
        sizes: List of (width, height) tuples
        text_densities: List of text density names ("low", "medium", "high")
        
    Returns:
        Dictionary mapping size names to dictionaries mapping text densities to PIL Images
    """
    images = {}
    
    # Try to load a font
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        # Use default font if arial is not available
        font = ImageFont.load_default()
    
    for width, height in sizes:
        size_name = f"{width}x{height}"
        images[size_name] = {}
        
        for density in text_densities:
            # Create a new image
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)
            
            # Determine number of text elements based on density
            if density == "low":
                num_elements = 5
            elif density == "medium":
                num_elements = 20
            else:  # high
                num_elements = 50
            
            # Add text elements
            for i in range(num_elements):
                x = (i * width // num_elements) % width
                y = (i * height // num_elements) % height
                draw.text((x, y), f"Text {i}", fill='black', font=font)
            
            # Add some UI elements
            draw.rectangle([width//10, height//10, width//3, height//3], outline='gray', width=1)
            draw.rectangle([width*2//3, height//10, width*9//10, height//3], outline='gray', width=1)
            
            # Add a title
            draw.text((width//2 - 50, 10), f"Test Image {size_name} - {density}", fill='black', font=font)
            
            # Add to dictionary
            images[size_name][density] = image
    
    return images


def benchmark_function(
    func: Callable,
    args: List[Any],
    num_runs: int = 5
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


def benchmark_screen_parsers(
    images: Dict[str, Dict[str, Image.Image]],
    num_runs: int = 5,
    api_key: Optional[str] = None
) -> Dict[str, Dict[str, Dict[str, List[float]]]]:
    """
    Benchmark screen parser functions with different image sizes and text densities.
    
    Args:
        images: Dictionary mapping size names to dictionaries mapping text densities to PIL Images
        num_runs: Number of benchmark runs per function
        api_key: API key for ScreenParse.ai (if available)
        
    Returns:
        Dictionary mapping parser names to dictionaries mapping size names to dictionaries mapping text densities to execution times
    """
    results = {}
    
    # Add pytesseract parser if available
    if PYTESSERACT_AVAILABLE:
        results["pytesseract"] = {}
    
    # Add screenparse.ai parser if available and API key is provided
    if SCREENPARSE_AI_AVAILABLE and api_key:
        results["screenparse_ai"] = {}
    
    for size_name, density_images in images.items():
        for density, image in density_images.items():
            print(f"\nBenchmarking with {size_name} image, {density} text density...")
            
            # Convert image to base64 for testing
            b64_image = imageToB64(image)
            
            # Benchmark pytesseract parser if available
            if PYTESSERACT_AVAILABLE:
                print(f"  Benchmarking pytesseract parser...", end="", flush=True)
                if size_name not in results["pytesseract"]:
                    results["pytesseract"][size_name] = {}
                times = benchmark_function(pytesseract_parse, [b64_image], num_runs)
                results["pytesseract"][size_name][density] = times
                print(f" Mean: {statistics.mean(times):.4f}s")
            
            # Benchmark screenparse.ai parser if available and API key is provided
            if SCREENPARSE_AI_AVAILABLE and api_key:
                print(f"  Benchmarking screenparse.ai parser...", end="", flush=True)
                if size_name not in results["screenparse_ai"]:
                    results["screenparse_ai"][size_name] = {}
                times = benchmark_function(screenparse_ai_parse, [b64_image, api_key], num_runs)
                results["screenparse_ai"][size_name][density] = times
                print(f" Mean: {statistics.mean(times):.4f}s")
    
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
    results: Dict[str, Dict[str, Dict[str, List[float]]]],
    title: str = "Screen Parser Benchmark"
) -> None:
    """
    Plot benchmark results.
    
    Args:
        results: Dictionary mapping parser names to dictionaries mapping size names to dictionaries mapping text densities to execution times
        title: Plot title
    """
    parsers = list(results.keys())
    sizes = list(results[parsers[0]].keys())
    densities = list(results[parsers[0]][sizes[0]].keys())
    
    # Create a figure with subplots for each size and density combination
    fig, axes = plt.subplots(len(sizes), len(densities), figsize=(5 * len(densities), 4 * len(sizes)))
    
    for i, size in enumerate(sizes):
        for j, density in enumerate(densities):
            ax = axes[i, j] if len(sizes) > 1 and len(densities) > 1 else axes[j] if len(sizes) == 1 else axes[i] if len(densities) == 1 else axes
            
            # Calculate means and standard deviations
            means = [statistics.mean(results[parser][size][density]) if size in results[parser] and density in results[parser][size] else 0 for parser in parsers]
            stds = [statistics.stdev(results[parser][size][density]) if size in results[parser] and density in results[parser][size] and len(results[parser][size][density]) > 1 else 0 for parser in parsers]
            
            # Create bar chart
            x = np.arange(len(parsers))
            bars = ax.bar(x, means, yerr=stds)
            
            # Add labels
            ax.set_ylabel('Time (s)')
            ax.set_title(f'{size}, {density} text')
            ax.set_xticks(x)
            ax.set_xticklabels(parsers)
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.4f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
    
    fig.suptitle(title, fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.97])  # Adjust for the suptitle
    plt.savefig('screen_parser_benchmark.png')
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Benchmark CommandLAB screen parsers')
    parser.add_argument('--runs', type=int, default=3, help='Number of benchmark runs per parser')
    parser.add_argument('--plot', action='store_true', help='Generate plot of results')
    parser.add_argument('--api-key', type=str, help='API key for ScreenParse.ai')
    args = parser.parse_args()
    
    # Check if any parsers are available
    if not PYTESSERACT_AVAILABLE and not (SCREENPARSE_AI_AVAILABLE and args.api_key):
        print("Error: No screen parsers available. Please install pytesseract or provide a ScreenParse.ai API key.")
        return
    
    # Define image sizes to test
    sizes = [
        (800, 600),    # SVGA
        (1280, 720),   # HD
    ]
    
    # Define text densities to test
    densities = ["low", "medium", "high"]
    
    # Generate test images
    print("Generating test images...")
    images = generate_test_images(sizes, densities)
    
    # Run benchmarks
    print("\nRunning benchmarks...")
    results = benchmark_screen_parsers(images, num_runs=args.runs, api_key=args.api_key)
    
    # Print detailed statistics
    print("\nDetailed Results:")
    for parser, size_results in results.items():
        print(f"\n{parser}:")
        for size, density_results in size_results.items():
            print(f"  {size}:")
            for density, times in density_results.items():
                print_stats(f"    {density}", times)
    
    # Plot results if requested
    if args.plot:
        plot_results(results)


if __name__ == "__main__":
    main() 