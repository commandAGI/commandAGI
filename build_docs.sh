#!/bin/bash

# Create examples directory if it doesn't exist
mkdir -p docs/examples

# Copy notebooks from examples to docs/examples
cp examples/*.ipynb docs/examples/

# Build the documentation
mkdocs build 