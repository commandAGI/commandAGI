import subprocess
import sys
import time
from pathlib import Path




def generate_openapi_client():
    api_token = "test"

    # Start the server in a subprocess
    server_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "commandAGI.daemon.cli",
            "--port",
            "8000",
            "--token",
            api_token,
            "--backend",
            "pynput",
        ]
    )

    output_dir = Path(__file__).parent.parent / "daemon" / "client"

    try:
        # Wait for the server to start
        time.sleep(2)

        # Generate the OpenAPI client using openapi-python-client
        subprocess.run(
            [
                "openapi-python-client",
                "generate",
                "--overwrite",
                "--url",
                "http://localhost:8000/openapi.json",
                "--meta",
                "none",
                "--output-path",
                str(output_dir),
            ],
            check=True,
        )

    finally:
        # Cleanup: Stop the server
        server_process.terminate()
        server_process.wait()


if __name__ == "__main__":
    generate_openapi_client()
