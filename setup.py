from setuptools import setup, find_packages

setup(
    name="mcp-trends-server",
    version="1.0.0",
    description="Custom MCP server with Google Trends scraping tools using Playwright",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "fastmcp",
        "playwright",
        "pandas",
        "asyncio",
    ],
    entry_points={
        "console_scripts": [
            "mcp-trends-server=mcp_project.playwright.server:main",
        ],
    },
    python_requires=">=3.8",
) 