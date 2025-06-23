#!/usr/bin/env python3
"""
Duffel Flight MCP Server - STDIO wrapper
Provides flight search and booking capabilities via Duffel API
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Environment is already set via MCP config, but ensure DUFFEL_API_KEY is available
if not os.getenv("DUFFEL_API_KEY"):
    os.environ["DUFFEL_API_KEY"] = os.getenv("DUFFEL_API_KEY", "")

# Import and run the server
from flights.server import main

if __name__ == "__main__":
    main()