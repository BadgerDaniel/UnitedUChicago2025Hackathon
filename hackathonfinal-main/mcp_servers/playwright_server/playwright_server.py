#!/usr/bin/env python3
"""MCP Playwright Server - Browser automation tools using Playwright."""

import argparse
import asyncio
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from fastmcp import FastMCP

# Global browser state
playwright_instance = None
browser: Optional[Browser] = None
context: Optional[BrowserContext] = None
page: Optional[Page] = None

# Create the FastMCP app
app = FastMCP(
    name="playwright",
    description="Browser automation tools using Playwright for web scraping and testing"
)


async def ensure_browser(headless: bool = True, browser_type: str = "chromium"):
    """Ensure browser is initialized."""
    global playwright_instance, browser, context, page
    
    if playwright_instance is None:
        playwright_instance = await async_playwright().start()
    
    if browser is None:
        if browser_type == "firefox":
            browser = await playwright_instance.firefox.launch(headless=headless)
        elif browser_type == "webkit":
            browser = await playwright_instance.webkit.launch(headless=headless)
        else:  # chromium
            browser = await playwright_instance.chromium.launch(headless=headless)
    
    if context is None:
        context = await browser.new_context()
    
    if page is None:
        page = await context.new_page()


@app.tool()
async def navigate(
    url: str,
    headless: bool = True,
    browser_type: str = "chromium",
    wait_for: str = "load"
) -> str:
    """Navigate to a URL.
    
    Args:
        url: URL to navigate to
        headless: Run browser in headless mode (default: True)
        browser_type: Browser to use (chromium, firefox, webkit)
        wait_for: Wait condition (load, domcontentloaded, networkidle)
    
    Returns:
        Success message with page title or error
    """
    try:
        await ensure_browser(headless, browser_type)
        
        await page.goto(url, wait_until=wait_for)
        title = await page.title()
        
        return f"Successfully navigated to {url}. Page title: '{title}'"
        
    except Exception as e:
        return f"Error navigating to {url}: {str(e)}"


@app.tool()
async def screenshot(
    name: str = "screenshot",
    selector: Optional[str] = None,
    encoded: bool = False,
    width: int = 1280,
    height: int = 720,
    full_page: bool = False
) -> str:
    """Take a screenshot of the current page or element.
    
    Args:
        name: Name for the screenshot file
        selector: CSS selector for element to screenshot (optional)
        encoded: Return as base64 encoded data URI (default: False)
        width: Viewport width (default: 1280)
        height: Viewport height (default: 720)
        full_page: Take full page screenshot (default: False)
    
    Returns:
        Screenshot data or file path or error message
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        # Set viewport size
        await page.set_viewport_size({"width": width, "height": height})
        
        # Take screenshot
        if selector:
            element = await page.query_selector(selector)
            if not element:
                return f"Error: Element with selector '{selector}' not found"
            screenshot_bytes = await element.screenshot()
        else:
            screenshot_bytes = await page.screenshot(full_page=full_page)
        
        if encoded:
            encoded_data = base64.b64encode(screenshot_bytes).decode()
            return f"data:image/png;base64,{encoded_data}"
        else:
            # Save to file
            filename = f"{name}.png"
            Path(filename).write_bytes(screenshot_bytes)
            return f"Screenshot saved as {filename}"
            
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


@app.tool()
async def click(selector: str, wait_for: str = "load") -> str:
    """Click an element on the page.
    
    Args:
        selector: CSS selector for element to click
        wait_for: Wait condition after click (load, domcontentloaded, networkidle, none)
    
    Returns:
        Success message or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        # Wait for element to be visible and enabled
        await page.wait_for_selector(selector, state="visible")
        
        if wait_for == "none":
            await page.click(selector)
        else:
            async with page.expect_load_state(wait_for):
                await page.click(selector)
        
        return f"Successfully clicked element: {selector}"
        
    except Exception as e:
        return f"Error clicking element '{selector}': {str(e)}"


@app.tool()
async def fill(selector: str, value: str, clear: bool = True) -> str:
    """Fill an input field.
    
    Args:
        selector: CSS selector for input field
        value: Value to fill
        clear: Clear field before filling (default: True)
    
    Returns:
        Success message or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        # Wait for element to be visible
        await page.wait_for_selector(selector, state="visible")
        
        if clear:
            await page.fill(selector, value)
        else:
            await page.type(selector, value)
        
        return f"Successfully filled '{selector}' with value"
        
    except Exception as e:
        return f"Error filling input '{selector}': {str(e)}"


@app.tool()
async def select_option(selector: str, value: str) -> str:
    """Select an option in a select element.
    
    Args:
        selector: CSS selector for select element
        value: Value or text to select
    
    Returns:
        Success message or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        await page.wait_for_selector(selector, state="visible")
        await page.select_option(selector, value)
        
        return f"Successfully selected '{value}' in {selector}"
        
    except Exception as e:
        return f"Error selecting option in '{selector}': {str(e)}"


@app.tool()
async def hover(selector: str) -> str:
    """Hover over an element.
    
    Args:
        selector: CSS selector for element to hover
    
    Returns:
        Success message or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        await page.wait_for_selector(selector, state="visible")
        await page.hover(selector)
        
        return f"Successfully hovered over {selector}"
        
    except Exception as e:
        return f"Error hovering over '{selector}': {str(e)}"


@app.tool()
async def evaluate(script: str) -> str:
    """Execute JavaScript in the browser.
    
    Args:
        script: JavaScript code to execute
    
    Returns:
        Result of the JavaScript execution or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        result = await page.evaluate(script)
        return str(result) if result is not None else "null"
        
    except Exception as e:
        return f"Error executing JavaScript: {str(e)}"


@app.tool()
async def get_text(selector: str) -> str:
    """Get text content of an element.
    
    Args:
        selector: CSS selector for element
    
    Returns:
        Text content or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        element = await page.query_selector(selector)
        if not element:
            return f"Error: Element with selector '{selector}' not found"
        
        text = await element.text_content()
        return text or ""
        
    except Exception as e:
        return f"Error getting text from '{selector}': {str(e)}"


@app.tool()
async def get_attribute(selector: str, attribute: str) -> str:
    """Get attribute value of an element.
    
    Args:
        selector: CSS selector for element
        attribute: Attribute name to get
    
    Returns:
        Attribute value or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        element = await page.query_selector(selector)
        if not element:
            return f"Error: Element with selector '{selector}' not found"
        
        value = await element.get_attribute(attribute)
        return value or ""
        
    except Exception as e:
        return f"Error getting attribute '{attribute}' from '{selector}': {str(e)}"


@app.tool()
async def wait_for_selector(selector: str, timeout: int = 30000, state: str = "visible") -> str:
    """Wait for an element to appear.
    
    Args:
        selector: CSS selector for element to wait for
        timeout: Timeout in milliseconds (default: 30000)
        state: State to wait for (visible, hidden, attached, detached)
    
    Returns:
        Success message or error
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        await page.wait_for_selector(selector, timeout=timeout, state=state)
        return f"Element '{selector}' is now {state}"
        
    except Exception as e:
        return f"Error waiting for '{selector}': {str(e)}"


@app.tool()
async def get_page_info() -> str:
    """Get current page information.
    
    Returns:
        Page title, URL, and basic info
    """
    global page
    
    if page is None:
        return "Error: No page loaded. Navigate to a URL first."
    
    try:
        title = await page.title()
        url = page.url
        viewport = page.viewport_size
        
        return f"Title: {title}\nURL: {url}\nViewport: {viewport['width']}x{viewport['height']}"
        
    except Exception as e:
        return f"Error getting page info: {str(e)}"


@app.tool()
async def close_browser() -> str:
    """Close the browser and clean up resources.
    
    Returns:
        Success message
    """
    global playwright_instance, browser, context, page
    
    try:
        if page:
            await page.close()
            page = None
        
        if context:
            await context.close()
            context = None
        
        if browser:
            await browser.close()
            browser = None
        
        if playwright_instance:
            await playwright_instance.stop()
            playwright_instance = None
        
        return "Browser closed successfully"
        
    except Exception as e:
        return f"Error closing browser: {str(e)}"


async def cleanup():
    """Clean up browser resources on shutdown."""
    await close_browser()


def setup_server_config():
    """Setup server configuration from command line args."""
    parser = argparse.ArgumentParser(description="MCP Playwright Server")
    parser.add_argument(
        "--port",
        type=int,
        default=8004,
        help="Port to run server on (default: 8004)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to run server on (default: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    return args


if __name__ == "__main__":
    print("Starting MCP Playwright server...")
    print("Browser automation tools ready")
    
    try:
        args = setup_server_config()
        print(f"Server starting on {args.host}:{args.port}")
        
        # Run the server with SSE transport
        app.run(transport="sse")
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        # Ensure cleanup happens
        asyncio.run(cleanup())