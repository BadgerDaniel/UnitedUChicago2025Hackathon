#!/usr/bin/env python3

import os
import json
from pathlib import Path
from typing import Any, Sequence
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("File System Server")

# Set your project root directory
PROJECT_ROOT = "/Users/lindaji/Desktop/A2A"
# PROJECT_ROOT = "/Users/lindaji/Desktop"

@mcp.tool()
def read_file(file_path: str) -> str:
    """Read the contents of a file."""
    try:
        full_path = Path(PROJECT_ROOT) / file_path
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        full_path = Path(PROJECT_ROOT) / file_path
        # Create directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def list_directory(dir_path: str = "") -> str:
    """List contents of a directory."""
    try:
        full_path = Path(PROJECT_ROOT) / dir_path
        items = []
        for item in full_path.iterdir():
            if item.is_file():
                items.append(f"📄 {item.name}")
            elif item.is_dir():
                items.append(f"📁 {item.name}/")
        return "\n".join(sorted(items))
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
def create_file(file_path: str, content: str = "") -> str:
    """Create a new file with optional content."""
    try:
        full_path = Path(PROJECT_ROOT) / file_path
        if full_path.exists():
            return f"File {file_path} already exists"
        
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully created {file_path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"

@mcp.tool()
def get_project_structure(max_depth: int = 3) -> str:
    """Get the project directory structure."""
    def build_tree(path: Path, prefix: str = "", depth: int = 0):
        if depth > max_depth:
            return ""
        
        items = []
        try:
            entries = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                current_prefix = "└── " if is_last else "├── "
                items.append(f"{prefix}{current_prefix}{entry.name}")
                
                if entry.is_dir() and not entry.name.startswith('.') and entry.name != '__pycache__':
                    extension = "    " if is_last else "│   "
                    items.append(build_tree(entry, prefix + extension, depth + 1))
        except PermissionError:
            pass
        
        return "\n".join(filter(None, items))
    
    return build_tree(Path(PROJECT_ROOT))

if __name__ == "__main__":
    mcp.run()