from setuptools import setup, find_packages

setup(
    name="notion-chakra-mcp",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "notion-client>=2.2.1",
        "python-dotenv>=1.0.0",
        "fastmcp>=0.1.0",
        "aiohttp>=3.9.0",
        "tenacity>=8.2.3",
        "httpx>=0.23.0",
        "rich>=13.9.4",
    ],
    python_requires=">=3.10",
    author="Stu",
    description="A Notion MCP server for personal knowledge and goal management",
) 