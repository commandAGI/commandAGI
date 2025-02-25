"""
Benchmarks for CommandLAB daemon server.

This module contains benchmarks for measuring the performance of the daemon server.
"""

import time
import statistics
import argparse
import threading
import multiprocessing
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import numpy as np
import requests
import base64
from PIL import Image, ImageDraw
import io
import json
import uuid

from commandLAB.daemon.server import ComputerDaemon
from commandLAB.computers.local_pynput_computer import LocalPynputComputer
from commandLAB.computers.local_pyautogui_computer import LocalPyAutoGUIComputer
from commandLAB.types import (
    ClickAction,
    TypeAction,
    KeyboardHotkeyAction,
    KeyboardKey,
    MouseMoveAction,
    MouseScrollAction
)


def generate_test_image(width=800, height=600):
    """Generate a test image for benchmarking."""
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Draw some shapes
    draw.rectangle([50, 50, 200, 200], outline='red', width=2)
    draw.ellipse([300, 100, 500, 300], outline='blue', width=2)
    draw.line([600, 100, 700, 500], fill='green', width=3)
    
    # Add some text
    draw.text((100, 400), "CommandLAB Benchmark", fill='black')
    
    # Convert to base64
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def start_daemon_server(port=8000, computer_cls=LocalPynputComputer):
    """Start a daemon server in a separate process."""
    daemon = ComputerDaemon(computer_cls=computer_cls)
    
    # Get the API token
    api_token = daemon.API_TOKEN
    
    # Start the server in a thread
    import uvicorn
    server_thread = threading.Thread(
        target=uvicorn.run,
        args=(daemon.app,),
        kwargs={"host": "127.0.0.1", "port": port, "log_level": "error"}
    )
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    return api_token


def benchmark_daemon_endpoint(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None,
    port: int = 8000,
    api_token: str = None,
    num_runs: int = 10
) -> List[float]:
    """
    Benchmark a specific daemon endpoint.
    
    Args:
        endpoint: The endpoint to benchmark (e.g., "/screenshot")
        method: HTTP method to use
        data: Data to send for POST requests
        port: Daemon server port
        api_token: API token for authentication
        num_runs: Number of benchmark runs
        
    Returns:
        List of response times
    """
    url = f"http://127.0.0.1:{port}{endpoint}"
    headers = {"Authorization": f"Bearer {api_token}"} if api_token else {}
    
    times = []
    for i in range(num_runs):
        print(f"  Run {i+1}/{num_runs} of {endpoint}...", end="", flush=True)
        
        # Measure response time
        start = time.time()
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end = time.time()
            response_time = end - start
            
            if response.status_code == 200:
                times.append(response_time)
                print(f" {response_time:.4f}s")
            else:
                print(f" Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f" Error: {e}")
    
    return times


def benchmark_daemon(
    port: int = 8000,
    computer_cls=LocalPynputComputer,
    num_runs: int = 10
) -> Dict[str, List[float]]:
    """
    Benchmark the daemon server by measuring response times for various endpoints.
    
    Args:
        port: Daemon server port
        computer_cls: Computer class to use for the daemon
        num_runs: Number of benchmark runs per endpoint
        
    Returns:
        Dictionary mapping endpoint names to response times
    """
    # Start daemon server
    print(f"Starting daemon server with {computer_cls.__name__}...")
    api_token = start_daemon_server(port, computer_cls)
    
    # Generate test data
    test_image = generate_test_image()
    
    # Define endpoints to benchmark
    endpoints = {
        "screenshot": {
            "endpoint": "/screenshot",
            "method": "GET",
            "data": None
        },
        "mouse_state": {
            "endpoint": "/mouse/state",
            "method": "GET",
            "data": None
        },
        "keyboard_state": {
            "endpoint": "/keyboard/state",
            "method": "GET",
            "data": None
        },
        "mouse_move": {
            "endpoint": "/mouse/move",
            "method": "POST",
            "data": MouseMoveAction(x=100, y=100, move_duration=0.1).model_dump()
        },
        "click": {
            "endpoint": "/mouse/button/down",
            "method": "POST",
            "data": {"button": "left"}
        },
        "type": {
            "endpoint": "/type",
            "method": "POST",
            "data": TypeAction(text="test").model_dump()
        },
        "hotkey": {
            "endpoint": "/keyboard/hotkey",
            "method": "POST",
            "data": KeyboardHotkeyAction(keys=[KeyboardKey.CTRL, KeyboardKey.A]).model_dump()
        }
    }
    
    results = {}
    for name, config in endpoints.items():
        print(f"\nBenchmarking {name}...")
        times = benchmark_daemon_endpoint(
            endpoint=config["endpoint"],
            method=config["method"],
            data=config["data"],
            port=port,
            api_token=api_token,
            num_runs=num_runs
        )
        results[name] = times
    
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
    endpoints: Optional[List[str]] = None,
    title: str = "Daemon Server Benchmark"
) -> None:
    """
    Plot benchmark results.
    
    Args:
        results: Dictionary mapping computer names to endpoint times
        endpoints: List of endpoints to include in the plot (None for all)
        title: Plot title
    """
    computers = list(results.keys())
    
    # Determine which endpoints to plot
    if endpoints is None:
        # Use endpoints from the first computer
        endpoints = list(results[computers[0]].keys())
    
    # Create a figure with subplots for each endpoint
    fig, axes = plt.subplots(len(endpoints), 1, figsize=(12, 4 * len(endpoints)))
    if len(endpoints) == 1:
        axes = [axes]  # Make axes iterable if there's only one subplot
    
    for i, endpoint in enumerate(endpoints):
        ax = axes[i]
        
        # Calculate means and standard deviations
        means = [statistics.mean(results[c][endpoint]) if endpoint in results[c] and results[c][endpoint] else 0 for c in computers]
        stds = [statistics.stdev(results[c][endpoint]) if endpoint in results[c] and len(results[c][endpoint]) > 1 else 0 for c in computers]
        
        # Create bar chart
        x = np.arange(len(computers))
        bars = ax.bar(x, means, yerr=stds)
        
        # Add labels
        ax.set_ylabel('Time (s)')
        ax.set_title(f'{endpoint}')
        ax.set_xticks(x)
        ax.set_xticklabels(computers)
        
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
    plt.savefig('daemon_benchmark.png')
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Benchmark CommandLAB daemon server')
    parser.add_argument('--port', type=int, default=8000, help='Daemon server port')
    parser.add_argument('--runs', type=int, default=5, help='Number of benchmark runs per endpoint')
    parser.add_argument('--plot', action='store_true', help='Generate plot of results')
    parser.add_argument('--endpoints', nargs='+', help='Specific endpoints to benchmark')
    args = parser.parse_args()
    
    # Define computer implementations to benchmark
    computers = {
        "LocalPynputComputer": LocalPynputComputer,
        "LocalPyAutoGUIComputer": LocalPyAutoGUIComputer
        # Add more computer implementations as needed
    }
    
    # Run benchmarks
    results = {}
    for name, cls in computers.items():
        print(f"\n{'='*50}")
        print(f"Benchmarking daemon with {name}...")
        print(f"{'='*50}")
        
        result = benchmark_daemon(port=args.port, computer_cls=cls, num_runs=args.runs)
        results[name] = result
        
        # Print statistics
        print("\nResults:")
        for endpoint, times in result.items():
            if args.endpoints is None or endpoint in args.endpoints:
                print_stats(endpoint, times)
    
    # Plot results if requested
    if args.plot:
        plot_results(results, endpoints=args.endpoints)


if __name__ == "__main__":
    main() 