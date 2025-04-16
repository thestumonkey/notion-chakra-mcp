# Notion Chakra MCP

A FastMCP server implementation for interacting with Notion API, featuring a Chakra UI frontend.

## Features

- Notion API integration using `notion-client`
- FastMCP server for handling Notion operations
- Async support with retry mechanisms
- Comprehensive test suite

## Setup

1. Clone the repository:
```bash
git clone git@github.com:thestumonkey/notion-chakra-mcp.git
cd notion-chakra-mcp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Notion API token and other settings
```

## Running Tests

```bash
pytest tests/
```

## Development

The project uses FastMCP for server implementation and pytest for testing. Key components:

- `src/notion_tools.py`: Main Notion API integration tools
- `tests/`: Test suite for all functionality
- `main.py`: Server entry point

## License

MIT 