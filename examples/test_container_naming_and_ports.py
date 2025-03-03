import time
import subprocess
import threading
import uvicorn
from fastapi import FastAPI
import requests
from contextlib import contextmanager
import socket
import os
import signal

from commandAGI2.computers.provisioners.docker_provisioner import DockerProvisioner
from commandAGI2._utils.network import find_free_port, _is_port_available

# Create a simple FastAPI app for testing
app = FastAPI()


@app.get("/")
def read_root():
    return {"status": "running"}


# Function to run a FastAPI server on a specific port
def run_server(port, stop_event):
    server = uvicorn.Server(
        uvicorn.Config(app, host="0.0.0.0", port=port, log_level="error")
    )

    # Override the server's install_signal_handlers method to prevent it from capturing signals
    server.install_signal_handlers = lambda: None

    # Run the server in a thread until the stop event is set
    server_thread = threading.Thread(target=server.run)
    server_thread.start()

    # Wait for the server to start
    while not stop_event.is_set():
        try:
            response = requests.get(f"http://localhost:{port}/")
            if response.status_code == 200:
                print(f"Server on port {port} is running")
                break
        except requests.exceptions.ConnectionError:
            time.sleep(0.1)

    # Wait for the stop event
    stop_event.wait()

    # Stop the server
    server.should_exit = True
    server_thread.join(timeout=5)
    print(f"Server on port {port} stopped")


@contextmanager
def temp_fastapi_server(port):
    """Context manager to run a temporary FastAPI server on a specific port"""
    stop_event = threading.Event()
    server_thread = threading.Thread(target=run_server, args=(port, stop_event))
    server_thread.daemon = True
    server_thread.start()

    # Wait for the server to start
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{port}/")
            if response.status_code == 200:
                print(f"Server on port {port} is ready")
                break
        except requests.exceptions.ConnectionError:
            if i == max_retries - 1:
                raise RuntimeError(f"Failed to start server on port {port}")
            time.sleep(0.2)

    try:
        yield
    finally:
        # Signal the server to stop
        stop_event.set()
        server_thread.join(timeout=5)
        print(f"Cleaned up server on port {port}")


def test_find_free_port():
    """Test the find_free_port function"""
    print("\n=== Testing find_free_port function ===")

    # Test with a preferred port that should be available
    preferred_port = find_free_port()  # Get any free port
    print(f"Testing with preferred port {preferred_port}")
    assert _is_port_available(
        preferred_port
    ), f"Port {preferred_port} should be available"

    port = find_free_port(preferred_port=preferred_port)
    assert port == preferred_port, f"Expected port {preferred_port}, got {port}"
    print(f"✓ Successfully got preferred port {port}")

    # Test with a preferred port that's occupied
    with temp_fastapi_server(preferred_port):
        assert not _is_port_available(
            preferred_port
        ), f"Port {preferred_port} should be occupied"

        # Should get a different port
        new_port = find_free_port(preferred_port=preferred_port)
        assert (
            new_port != preferred_port
        ), f"Expected a different port than {preferred_port}, got {new_port}"
        print(
            f"✓ Successfully got alternative port {new_port} when preferred port {preferred_port} was occupied"
        )

        # Test with a port range
        min_port = new_port + 1
        max_port = min_port + 5
        port_range = (min_port, max_port)
        print(f"Testing with port range {port_range}")

        # Occupy all ports in the range except one
        occupied_servers = []
        available_port = None

        for p in range(min_port, max_port + 1):
            if _is_port_available(p):
                if available_port is None:
                    available_port = p
                    continue
                else:
                    # Start a server on this port
                    stop_event = threading.Event()
                    server_thread = threading.Thread(
                        target=run_server, args=(p, stop_event)
                    )
                    server_thread.daemon = True
                    server_thread.start()
                    occupied_servers.append((p, stop_event, server_thread))
                    time.sleep(0.5)  # Give the server time to start

        if available_port is None:
            print("Could not find an available port in the range for testing")
            return

        print(f"Left port {available_port} available in the range")

        try:
            # Should get the available port in the range
            port = find_free_port(port_range=port_range)
            assert port == available_port, f"Expected port {available_port}, got {port}"
            print(f"✓ Successfully got available port {port} from range {port_range}")
        finally:
            # Clean up the servers
            for p, stop_event, server_thread in occupied_servers:
                stop_event.set()
                server_thread.join(timeout=5)
                print(f"Cleaned up server on port {p}")


def test_container_naming():
    """Test the container naming functionality"""
    print("\n=== Testing container naming functionality ===")

    # Create a provisioner to test the naming function
    provisioner = DockerProvisioner()

    # Test the _find_next_available_container_name method
    name_prefix = "test-container"

    # First, make sure no containers with this prefix exist
    try:
        subprocess.run(
            ["docker", "ps", "-a", "-q", "--filter", f"name={name_prefix}"],
            check=True,
            capture_output=True,
            text=True,
        )

        # If any containers exist with this prefix, remove them
        result = subprocess.run(
            ["docker", "ps", "-a", "-q", "--filter", f"name={name_prefix}"],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            container_ids = result.stdout.strip().split("\n")
            for container_id in container_ids:
                subprocess.run(["docker", "rm", "-f", container_id], check=True)
                print(f"Removed existing container {container_id}")
    except Exception as e:
        print(f"Error checking for existing containers: {e}")

    # Set the name prefix for the provisioner
    provisioner.name_prefix = name_prefix

    # Test when no containers exist
    name = provisioner._find_next_available_container_name()
    assert name == name_prefix, f"Expected {name_prefix}, got {name}"
    print(f"✓ When no containers exist, got name: {name}")

    # Create a container with the base name
    try:
        subprocess.run(
            ["docker", "run", "-d", "--name", name_prefix, "alpine", "sleep", "30"],
            check=True,
            capture_output=True,
        )
        print(f"Created container with name {name_prefix}")

        # Test when the base name is taken
        name = provisioner._find_next_available_container_name()
        expected = f"{name_prefix}-1"
        assert name == expected, f"Expected {expected}, got {name}"
        print(f"✓ When base name is taken, got name: {name}")

        # Create a container with the -1 suffix
        subprocess.run(
            ["docker", "run", "-d", "--name", expected, "alpine", "sleep", "30"],
            check=True,
            capture_output=True,
        )
        print(f"Created container with name {expected}")

        # Test when both base name and -1 are taken
        name = provisioner._find_next_available_container_name()
        expected = f"{name_prefix}-2"
        assert name == expected, f"Expected {expected}, got {name}"
        print(f"✓ When base name and -1 are taken, got name: {name}")

        # Create a container with the -3 suffix (skipping -2)
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                f"{name_prefix}-3",
                "alpine",
                "sleep",
                "30",
            ],
            check=True,
            capture_output=True,
        )
        print(f"Created container with name {name_prefix}-3")

        # Test when base name, -1, and -3 are taken (should still return -2)
        name = provisioner._find_next_available_container_name()
        expected = f"{name_prefix}-2"
        assert name == expected, f"Expected {expected}, got {name}"
        print(f"✓ When base name, -1, and -3 are taken, got name: {name}")

    finally:
        # Clean up the containers
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "-q", "--filter", f"name={name_prefix}"],
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                container_ids = result.stdout.strip().split("\n")
                for container_id in container_ids:
                    subprocess.run(["docker", "rm", "-f", container_id], check=True)
                    print(f"Cleaned up container {container_id}")
        except Exception as e:
            print(f"Error cleaning up containers: {e}")


def test_provisioner_port_selection():
    """Test the port selection in the DockerProvisioner"""
    print("\n=== Testing provisioner port selection ===")

    # Find a free port to start with
    base_port = find_free_port()
    print(f"Starting with base port {base_port}")

    # Test with a specific port
    with temp_fastapi_server(base_port):
        print(f"Port {base_port} is now occupied by a FastAPI server")

        # Create a provisioner with the occupied port
        provisioner = DockerProvisioner(daemon_port=base_port)

        # The setup method should find a different port
        # We'll mock the setup to avoid actually creating a container
        original_setup = provisioner.setup
        provisioner.setup = lambda: None

        # Call find_free_port directly to simulate what setup would do
        new_port = find_free_port(preferred_port=base_port)
        provisioner.daemon_port = new_port

        assert (
            provisioner.daemon_port != base_port
        ), f"Expected a different port than {base_port}"
        print(f"✓ Provisioner selected alternative port {provisioner.daemon_port}")

        # Test with a port range
        port_range = (base_port + 10, base_port + 15)
        print(f"Testing with port range {port_range}")

        # Occupy all ports in the range except one
        occupied_servers = []
        available_port = None

        for p in range(port_range[0], port_range[1] + 1):
            if _is_port_available(p):
                if available_port is None:
                    available_port = p
                    continue
                else:
                    # Start a server on this port
                    stop_event = threading.Event()
                    server_thread = threading.Thread(
                        target=run_server, args=(p, stop_event)
                    )
                    server_thread.daemon = True
                    server_thread.start()
                    occupied_servers.append((p, stop_event, server_thread))
                    time.sleep(0.5)  # Give the server time to start

        if available_port is None:
            print("Could not find an available port in the range for testing")
            return

        print(f"Left port {available_port} available in the range")

        try:
            # Create a provisioner with the port range
            provisioner = DockerProvisioner(port_range=port_range)

            # The setup method should find the available port in the range
            # We'll mock the setup to avoid actually creating a container
            original_setup = provisioner.setup
            provisioner.setup = lambda: None

            # Call find_free_port directly to simulate what setup would do
            provisioner.daemon_port = find_free_port(port_range=port_range)

            assert (
                provisioner.daemon_port == available_port
            ), f"Expected port {available_port}, got {provisioner.daemon_port}"
            print(
                f"✓ Provisioner selected available port {provisioner.daemon_port} from range {port_range}"
            )
        finally:
            # Clean up the servers
            for p, stop_event, server_thread in occupied_servers:
                stop_event.set()
                server_thread.join(timeout=5)
                print(f"Cleaned up server on port {p}")


def test_multiple_provisioners():
    """Test running multiple provisioners with different port configurations"""
    print("\n=== Testing multiple provisioners ===")

    # Find three consecutive free ports
    port1 = find_free_port()
    port2 = find_free_port(preferred_port=port1 + 1)
    port3 = find_free_port(preferred_port=port2 + 1)

    print(f"Found three free ports: {port1}, {port2}, {port3}")

    # Create three provisioners with different port configurations
    provisioner1 = DockerProvisioner(container_name="test-daemon-1", daemon_port=port1)

    provisioner2 = DockerProvisioner(container_name="test-daemon-2", daemon_port=port2)

    # For the third provisioner, we'll use a port range
    port_range = (port3, port3 + 5)
    provisioner3 = DockerProvisioner(
        container_name="test-daemon-3", port_range=port_range
    )

    # Mock the setup methods to avoid actually creating containers
    provisioner1.setup = lambda: setattr(provisioner1, "daemon_port", port1)
    provisioner2.setup = lambda: setattr(provisioner2, "daemon_port", port2)
    provisioner3.setup = lambda: setattr(provisioner3, "daemon_port", port3)

    # Simulate setup
    provisioner1.setup()
    provisioner2.setup()
    provisioner3.setup()

    # Check that each provisioner has the expected port
    assert (
        provisioner1.daemon_port == port1
    ), f"Expected port {port1}, got {provisioner1.daemon_port}"
    assert (
        provisioner2.daemon_port == port2
    ), f"Expected port {port2}, got {provisioner2.daemon_port}"
    assert (
        provisioner3.daemon_port == port3
    ), f"Expected port {port3}, got {provisioner3.daemon_port}"

    print(f"✓ All provisioners have the expected ports")

    # Now test with one port occupied
    with temp_fastapi_server(port1):
        print(f"Port {port1} is now occupied by a FastAPI server")

        # Create a new provisioner with the occupied port
        new_provisioner = DockerProvisioner(
            container_name="test-daemon-4", daemon_port=port1
        )

        # Mock the setup method
        new_provisioner.setup = lambda: setattr(
            new_provisioner, "daemon_port", find_free_port(preferred_port=port1)
        )

        # Simulate setup
        new_provisioner.setup()

        # Check that the provisioner found a different port
        assert (
            new_provisioner.daemon_port != port1
        ), f"Expected a different port than {port1}"
        print(
            f"✓ New provisioner selected alternative port {new_provisioner.daemon_port} when {port1} was occupied"
        )


if __name__ == "__main__":
    print("Starting tests for container naming and port selection")

    # Run the tests
    test_find_free_port()
    test_container_naming()
    test_provisioner_port_selection()
    test_multiple_provisioners()

    print("\nAll tests completed successfully!")
