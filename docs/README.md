# CommandLAB Documentation

This directory contains the documentation for CommandLAB.

## Building the Documentation

To build the documentation:

1. Install the required dependencies:

```bash
pip install -e ".[dev]"
```

2. Run the build script:

```bash
python docs/build_docs.py
```

This will:

- Generate documentation pages for all examples
- Generate API documentation pages

3. Preview the documentation:

```bash
mkdocs serve
```

This will start a local server at http://127.0.0.1:8000/ where you can preview the documentation.

## Documentation Structure

- `api/`: API reference documentation
- `concepts/`: Core concepts documentation
- `examples/`: Example code documentation
- `tutorials/`: Step-by-step tutorials
- `developers/`: Documentation for library developers
- `macros/`: MkDocs macros for dynamic content

## Adding New Documentation

### Adding a New Example

1. Add your example to the `examples/` directory
1. Run the build script to generate the documentation page
1. Update the example's documentation page with key concepts and next steps

### Adding New API Documentation

1. Add your module to the list in `docs/generate_api_docs.py`
1. Run the build script to generate the documentation page
1. Update the mkdocs.yml file to include the new page in the navigation

## Customizing the Documentation

- `mkdocs.yml`: MkDocs configuration file
- `docs/macros/__init__.py`: MkDocs macros for dynamic content
- `docs/generate_example_docs.py`: Script to generate example documentation
- `docs/generate_api_docs.py`: Script to generate API documentation
- `docs/build_docs.py`: Script to build all documentation
