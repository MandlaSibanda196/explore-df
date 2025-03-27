import pandas as pd
import streamlit as st
import subprocess
import sys
from pathlib import Path
import os
import webbrowser
import time
import socket
import requests
from urllib.error import URLError

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for the Streamlit server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            time.sleep(0.5)
    return False

def find_available_port(start_port: int = 8501, max_tries: int = 100) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_tries):
        if not is_port_in_use(port):
            return port
    raise RuntimeError(f"Could not find an available port in range {start_port}-{start_port + max_tries}")

def analyze(df: pd.DataFrame, port: int = None):
    """
    Launch the Streamlit-based EDA interface for the given DataFrame.
    
    Args:
        df: pandas DataFrame to analyze
        port: port number for the Streamlit server (default: auto-select)
    """
    # Input validation
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")
    
    if df.empty:
        raise ValueError("DataFrame is empty")
    
    # Find available port if not specified
    if port is None:
        port = find_available_port()
    elif is_port_in_use(port):
        raise RuntimeError(f"Port {port} is already in use. Try a different port or let the system choose automatically.")
    
    # Create temp directory if it doesn't exist
    temp_dir = Path(__file__).parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    # Save DataFrame to a temporary file
    temp_path = temp_dir / "temp_df.pkl"
    df.to_pickle(temp_path)
    
    # Get the path to the Streamlit app
    app_path = Path(__file__).parent / "main.py"
    
    # Construct the Streamlit command
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(port),
        "--server.address",
        "localhost",
        "--browser.serverAddress",
        "localhost",
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false"
    ]
    
    try:
        # Launch Streamlit
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        url = f"http://localhost:{port}"
        
        # Wait for server to be ready
        print("Starting Explore DF server...", end="", flush=True)
        if wait_for_server(url):
            print(" Ready! 🚀")
            
            # Open the browser
            webbrowser.open(url)
            
            print(f"""
            📊 Explore DF interface launched!
                  
            Stop the server by stopping this cell
            
            Access the interface at: {url}
            
            ❓ If you close the browser window, you can always:
               1. Copy and paste the URL above into your browser
               2. Or run analyze(df) again to reopen the interface
            """)
            
            # Keep the server running
            process.wait()
        else:
            raise RuntimeError("Server failed to start within the timeout period")
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Explore DF server...")
        process.terminate()
        
    except Exception as e:
        print(f"\n❌ Error launching Explore DF: {str(e)}")
        if process:
            process.terminate()
            stderr = process.stderr.read()
            if stderr:
                print("\nServer error output:")
                print(stderr)
        raise
    
    finally:
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

def _cleanup_temp_files():
    """Clean up temporary files on exit."""
    temp_dir = Path(__file__).parent / "temp"
    if temp_dir.exists():
        for file in temp_dir.glob("*.pkl"):
            file.unlink()

# Register cleanup handler
import atexit
atexit.register(_cleanup_temp_files) 