import socket
from typing import Optional, Tuple

def find_free_port(preferred_port: Optional[int] = None, port_range: Optional[Tuple[int, int]] = None) -> int:
    """Find a free port to use.
    
    Args:
        preferred_port: The preferred port to use. If None or unavailable, another port will be chosen.
        port_range: A tuple of (min_port, max_port) to search within. If None, any available port will be used.
        
    Returns:
        An available port number
        
    Raises:
        RuntimeError: If no free ports are available in the specified range
    """
    # First try the preferred port if specified
    if preferred_port is not None:
        if _is_port_available(preferred_port):
            return preferred_port
    
    # If we have a port range, search within that range
    if port_range is not None:
        min_port, max_port = port_range
        for port in range(min_port, max_port + 1):
            # Skip the preferred port as we already checked it
            if port == preferred_port:
                continue
                
            if _is_port_available(port):
                return port
                
        raise RuntimeError(f"No available ports found in range {min_port}-{max_port}")
    
    # If no range specified or preferred port is unavailable, find any free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def _is_port_available(port: int) -> bool:
    """Check if a port is available on all interfaces.
    
    Args:
        port: The port number to check
        
    Returns:
        True if the port is available, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Bind to all interfaces
            s.bind(("", port))
            return True
        except socket.error:
            return False 