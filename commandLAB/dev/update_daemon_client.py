import os
import time
import subprocess
import requests
from pathlib import Path

from commandLAB.daemon.server import ComputerDaemon

def generate_openapi_client():
    # Start the daemon server in a separate process
    daemon = ComputerDaemon()
    
    # Get the API token
    api_token = daemon.API_TOKEN
    
    # Start the server in a subprocess
    server_process = subprocess.Popen(
        ["uvicorn", "commandLAB.daemon.server:ComputerDaemon().app", "--host", "0.0.0.0", "--port", "8000"]
    )
    
    try:
        # Wait for the server to start
        time.sleep(2)
        
        # Generate the OpenAPI client using openapi-python-client
        subprocess.run([
            "openapi-python-client", "generate",
            "--url", "http://localhost:8000/openapi.json",
            "--meta", "none",
            "--output", str(Path(__file__).parent.parent / "daemon")
        ], check=True)
        
        # Move the generated client.py to the correct location
        generated_client_dir = Path(__file__).parent.parent / "daemon" / "client"
        if generated_client_dir.exists():
            client_file = generated_client_dir / "client.py"
            target_file = Path(__file__).parent.parent / "daemon" / "client.py"
            
            if client_file.exists():
                # Copy the content and clean up
                client_content = client_file.read_text()
                target_file.write_text(client_content)
                
                # Clean up generated files
                import shutil
                shutil.rmtree(generated_client_dir.parent)
                
    finally:
        # Cleanup: Stop the server
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    generate_openapi_client()
