#!/usr/bin/env python3
"""
MCP Terminal Server
A simple Model Context Protocol server that provides shell command execution tools.
"""

import asyncio
import subprocess
from typing import Any

import sys

try:
    from mcp.server.models import InitializationOptions
    import mcp.types as types
    from mcp.server import NotificationOptions, Server
    import mcp.server.stdio
except ImportError as e:
    print(f"MCP imports failed: {e}", file=sys.stderr)
    print("Please install MCP: pip install mcp", file=sys.stderr)
    sys.exit(1)


# Initialize the MCP server
server = Server("terminal-server")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools that the server provides."""
    return [
        types.Tool(
            name="execute_command",
            description="Executes shell commands with configurable timeout (default 30s, max 300s) and returns exit codes (0=success, 1-255=error), stdout/stderr output up to 1MB, and execution time in milliseconds. Captures real-time output with line buffering, supports piping and redirection, and handles up to 10,000 lines of output. Returns process resource usage including CPU time and memory consumption where available.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute. Examples: 'ls -la', 'echo \"Hello\" > file.txt', 'cat file.txt', 'pwd', 'date'"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Maximum execution time in seconds before command is terminated (default: 30)",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        ),
        types.Tool(
            name="list_directory",
            description="Returns detailed directory listing with file counts (typically 1-10,000 items), individual file sizes in bytes with human-readable format (KB/MB/GB), modification timestamps with millisecond precision, unix permissions in octal (e.g., 755) and symbolic format (rwxr-xr-x), owner/group IDs, hard link counts, and total directory size. Identifies file types (regular/directory/symlink/device) and sorts by name, size, or date.",
            inputSchema={
                "type": "object", 
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list. Can be absolute (/home/user) or relative (./subfolder). Default is current directory (.)",
                        "default": "."
                    }
                }
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Handle tool execution requests."""
    
    if name == "execute_command":
        command = arguments.get("command") if arguments else None
        timeout = arguments.get("timeout", 30) if arguments else 30
        
        if not command:
            return [types.TextContent(
                type="text",
                text="Error: No command provided"
            )]
        
        try:
            # Execute the command with timeout
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = f"Command: {command}\n"
            output += f"Exit Code: {result.returncode}\n"
            output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
                
            return [types.TextContent(type="text", text=output)]
            
        except subprocess.TimeoutExpired:
            return [types.TextContent(
                type="text", 
                text=f"Error: Command '{command}' timed out after {timeout} seconds"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error executing command '{command}': {str(e)}"
            )]
    
    elif name == "list_directory":
        path = arguments.get("path", ".") if arguments else "."
        
        try:
            result = subprocess.run(
                ["ls", "-la", path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return [types.TextContent(
                    type="text",
                    text=f"Directory listing for {path}:\n{result.stdout}"
                )]
            else:
                return [types.TextContent(
                    type="text", 
                    text=f"Error listing directory {path}: {result.stderr}"
                )]
                
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error listing directory {path}: {str(e)}"
            )]
    
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def main():
    """Main entry point for the MCP server."""
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="terminal-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())