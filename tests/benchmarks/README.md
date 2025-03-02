# CommandLAB Benchmarks

This directory contains benchmarks for measuring the performance of various CommandLAB components.

## Available Benchmarks

- **Provisioners**: Measures setup and teardown times for different provisioners
- **Computers**: Measures execution times for various computer operations
- **Daemon**: Measures response times for daemon server endpoints
- **Image Utilities**: Measures execution times for image utility functions
- **Screen Parser**: Measures execution times for screen parsing utilities

## Running Benchmarks

### Running All Benchmarks

To run all benchmarks:

```bash
python -m tests.benchmarks.run_benchmarks
```

### Running Specific Benchmarks

To run specific benchmarks:

```bash
python -m tests.benchmarks.run_benchmarks --benchmarks benchmark_provisioners benchmark_image_utils
```

### Common Options

- `--runs N`: Number of benchmark runs (default: 3)
- `--plot`: Generate plots of results
- `--output DIR`: Output directory for results (default: benchmark_results)

### Benchmark-Specific Options

#### Screen Parser Benchmark

- `--api-key KEY`: API key for ScreenParse.ai (required for ScreenParse.ai benchmarks)

```bash
python -m tests.benchmarks.benchmark_screen_parser --api-key your_api_key --plot
```

## Individual Benchmark Modules

### Provisioner Benchmark

Measures setup and teardown times for different provisioners.

```bash
python -m tests.benchmarks.benchmark_provisioners --runs 5 --plot
```

### Computer Benchmark

Measures execution times for various computer operations.

```bash
python -m tests.benchmarks.benchmark_computers --runs 5 --plot
```

### Daemon Benchmark

Measures response times for daemon server endpoints.

```bash
python -m tests.benchmarks.benchmark_daemon --runs 5 --plot
```

### Image Utilities Benchmark

Measures execution times for image utility functions with different image sizes.

```bash
python -m tests.benchmarks.benchmark_image_utils --runs 10 --plot
```

### Screen Parser Benchmark

Measures execution times for screen parsing utilities with different image sizes and text densities.

```bash
python -m tests.benchmarks.benchmark_screen_parser --runs 3 --plot --api-key your_api_key
```

## Interpreting Results

Each benchmark generates statistics including:

- **Mean**: Average execution time
- **Median**: Middle value of execution times
- **Min/Max**: Minimum and maximum execution times
- **Std Dev**: Standard deviation of execution times

When using the `--plot` option, benchmarks will generate visualizations of the results.

## Adding New Benchmarks

To add a new benchmark:

1. Create a new Python file in the `tests/benchmarks` directory
2. Implement the benchmark using the pattern from existing benchmarks
3. Add the benchmark to the `benchmarks` dictionary in `run_benchmarks.py`

## Best Practices

- Run benchmarks on a quiet system with minimal background activity
- Run multiple iterations (at least 3) to account for variability
- Compare relative performance rather than absolute numbers
- Be aware that performance can vary based on hardware and system load
