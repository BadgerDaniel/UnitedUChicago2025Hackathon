#!/usr/bin/env python3
"""MCP Playwright Server - stdio version for integration with agents."""

import asyncio
import base64
import json
import sys
from pathlib import Path
from typing import Optional, Any

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

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
server = Server("playwright-server")

# Global browser state
playwright_instance = None
browser: Optional[Browser] = None
context: Optional[BrowserContext] = None
page: Optional[Page] = None


async def ensure_browser(headless: bool = True):
    """Ensure browser is initialized."""
    global playwright_instance, browser, context, page
    
    if playwright_instance is None:
        playwright_instance = await async_playwright().start()
    
    if browser is None:
        browser = await playwright_instance.chromium.launch(headless=headless)
    
    if context is None:
        context = await browser.new_context()
    
    if page is None:
        page = await context.new_page()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools that the server provides."""
    return [
        types.Tool(
            name="navigate",
            description="Navigate to a URL in the browser",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to navigate to"
                    },
                    "wait_for": {
                        "type": "string",
                        "description": "Wait condition (load, domcontentloaded, networkidle)",
                        "default": "load"
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="screenshot",
            description="Take a screenshot of the current page or element",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for element to screenshot (optional)"
                    },
                    "full_page": {
                        "type": "boolean",
                        "description": "Take full page screenshot",
                        "default": False
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="click",
            description="Click an element on the page",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for element to click"
                    }
                },
                "required": ["selector"]
            }
        ),
        types.Tool(
            name="fill",
            description="Fill an input field",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for input field"
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to fill"
                    }
                },
                "required": ["selector", "value"]
            }
        ),
        types.Tool(
            name="get_text",
            description="Get text content of an element",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for element"
                    }
                },
                "required": ["selector"]
            }
        ),
        types.Tool(
            name="evaluate",
            description="Execute JavaScript in the browser",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "JavaScript code to execute"
                    }
                },
                "required": ["script"]
            }
        ),
        types.Tool(
            name="get_page_info",
            description="Get current page information (title, URL)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent]:
    """Handle tool execution requests."""
    global page, browser, context
    
    try:
        if name == "navigate":
            url = arguments.get("url") if arguments else None
            wait_for = arguments.get("wait_for", "load") if arguments else "load"
            
            if not url:
                return [types.TextContent(
                    type="text",
                    text="Error: URL is required"
                )]
            
            await ensure_browser()
            await page.goto(url, wait_until=wait_for)
            title = await page.title()
            
            return [types.TextContent(
                type="text",
                text=f"Successfully navigated to {url}. Page title: '{title}'"
            )]
        
        elif name == "screenshot":
            if page is None:
                return [types.TextContent(
                    type="text",
                    text="Error: No page loaded. Navigate to a URL first."
                )]
            
            selector = arguments.get("selector") if arguments else None
            full_page = arguments.get("full_page", False) if arguments else False
            
            if selector:
                element = await page.query_selector(selector)
                if not element:
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Element with selector '{selector}' not found"
                    )]
                screenshot_bytes = await element.screenshot()
            else:
                screenshot_bytes = await page.screenshot(full_page=full_page)
            
            # Return as base64 encoded image
            encoded_data = base64.b64encode(screenshot_bytes).decode()
            return [types.ImageContent(
                type="image",
                data=encoded_data,
                mimeType="image/png"
            )]
        
        elif name == "click":
            if page is None:
                return [types.TextContent(
                    type="text",
                    text="Error: No page loaded. Navigate to a URL first."
                )]
            
            selector = arguments.get("selector") if arguments else None
            if not selector:
                return [types.TextContent(
                    type="text",
                    text="Error: selector is required"
                )]
            
            await page.wait_for_selector(selector, state="visible")
            await page.click(selector)
            
            return [types.TextContent(
                type="text",
                text=f"Successfully clicked element: {selector}"
            )]
        
        elif name == "fill":
            if page is None:
                return [types.TextContent(
                    type="text",
                    text="Error: No page loaded. Navigate to a URL first."
                )]
            
            selector = arguments.get("selector") if arguments else None
            value = arguments.get("value") if arguments else None
            
            if not selector or value is None:
                return [types.TextContent(
                    type="text",
                    text="Error: selector and value are required"
                )]
            
            await page.wait_for_selector(selector, state="visible")
            await page.fill(selector, value)
            
            return [types.TextContent(
                type="text",
                text=f"Successfully filled '{selector}' with value"
            )]
        
        elif name == "get_text":
            if page is None:
                return [types.TextContent(
                    type="text",
                    text="Error: No page loaded. Navigate to a URL first."
                )]
            
            selector = arguments.get("selector") if arguments else None
            if not selector:
                return [types.TextContent(
                    type="text",
                    text="Error: selector is required"
                )]
            
            element = await page.query_selector(selector)
            if not element:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Element with selector '{selector}' not found"
                )]
            
            text = await element.text_content()
            return [types.TextContent(
                type="text",
                text=text or ""
            )]
        
        elif name == "evaluate":
            if page is None:
                return [types.TextContent(
                    type="text",
                    text="Error: No page loaded. Navigate to a URL first."
                )]
            
            script = arguments.get("script") if arguments else None
            if not script:
                return [types.TextContent(
                    type="text",
                    text="Error: script is required"
                )]
            
            result = await page.evaluate(script)
            return [types.TextContent(
                type="text",
                text=str(result) if result is not None else "null"
            )]
        
        elif name == "get_page_info":
            if page is None:
                return [types.TextContent(
                    type="text",
                    text="Error: No page loaded. Navigate to a URL first."
                )]
            
            title = await page.title()
            url = page.url
            
            return [types.TextContent(
                type="text",
                text=f"Title: {title}\nURL: {url}"
            )]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def cleanup():
    """Clean up browser resources."""
    global playwright_instance, browser, context, page
    
    if page:
        await page.close()
    if context:
        await context.close()
    if browser:
        await browser.close()
    if playwright_instance:
        await playwright_instance.stop()


async def main():
    """Main entry point for the MCP server."""
    try:
        # Run the server using stdio transport
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="playwright-server",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        await cleanup()


if __name__ == "__main__":
    asyncio.run(main())