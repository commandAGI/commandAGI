def run_tests() -> None:
    """
    Run all pytests in the tests/ directory.
    """
    import sys
    import pytest

    # Explicitly run pytest in the 'tests/' subdirectory.
    sys.exit(pytest.main(["tests/"]))


def run_doctests() -> None:
    """
    Run doctests across the repository.
    """
    import sys
    import pytest

    # Run pytest in doctest mode across the entire repo.
    # (Assumes your code files are doctest-enabled.)
    sys.exit(pytest.main(["--doctest-modules", "."]))


def run_format() -> None:
    """
    Format the repository code by first running autoflake to remove unused import lines,
    and then using black to format the code.
    """
    import subprocess
    import sys

    commands = [
        ["autoflake", "--in-place", "--recursive", "--remove-all-unused-imports", "."],
        ["black", "."],
    ]

    for cmd in commands:
        print("Running command:", " ".join(cmd))
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(
                f"Command {' '.join(cmd)} failed with return code {result.returncode}"
            )
            sys.exit(result.returncode)
