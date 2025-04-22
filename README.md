# Notion Chakra MCP

This is a Notion integration service that provides MCP (Message Control Protocol) endpoints for interacting with Notion databases and pages.

## Features
- List and query Notion databases
- Create and update pages
- Search Notion content
- Manage blocks and children
- Support for both stdio and SSE transports

## Setup Options

### 1. MCP Client Configuration (Recommended)
Add the following to your `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "notion-chakra-mcp": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v",
        "/path/to/notion-chakra-mcp/data:/app/data",
        "-e",
        "TRANSPORT",
        "-e",
        "NOTION_API_KEY",
        "-e",
        "HOST",
        "-e",
        "PORT",
        "-e",
        "PYTHONPATH=/app/src",
        "notion-chakra-mcp"
      ],
      "env": {
        "TRANSPORT": "stdio",
        "NOTION_API_KEY": "your_notion_api_key",
        "HOST": "0.0.0.0",
        "PORT": "8050"
      }
    }
  }
}
```

Make sure to:
1. Replace `/path/to/notion-chakra-mcp` with your actual project path
2. Set your `NOTION_API_KEY` value
3. Create a `data` directory in your project root: `mkdir -p data`

### 2. Docker Compose Setup
For development or standalone usage, you can use Docker Compose:

```bash
# Build and start with stdio transport
TRANSPORT=stdio docker-compose up notion-chakra-mcp

# Or with SSE transport
TRANSPORT=sse docker-compose up notion-chakra-mcp
```

### 3. Direct Docker Usage
For manual testing or custom setups:

```bash
# Build the image
docker build -t notion-chakra-mcp .

# Run with stdio transport
docker run --rm -i \
  -v $(pwd)/data:/app/data \
  -e TRANSPORT=stdio \
  -e NOTION_API_KEY=your_key \
  -e PYTHONPATH=/app/src \
  notion-chakra-mcp

# Run with SSE transport
docker run --rm -i \
  -v $(pwd)/data:/app/data \
  -e TRANSPORT=sse \
  -e NOTION_API_KEY=your_key \
  -e HOST=0.0.0.0 \
  -e PORT=8050 \
  -p 8050:8050 \
  -e PYTHONPATH=/app/src \
  notion-chakra-mcp
```

## Configuration

### Environment Variables
- `NOTION_API_KEY`: Your Notion integration token (required)
- `TRANSPORT`: Transport type (`stdio` or `sse`, defaults to `stdio`)
- `HOST`: Server host for SSE transport (defaults to `0.0.0.0`)
- `PORT`: Server port for SSE transport (defaults to `8050`)
- `PYTHONPATH`: Python module path (should be `/app/src`)

### Data Persistence
The service uses a `data` directory for persistent storage:
- Mounted at `/app/data` inside the container
- Stores schemas, database mappings, and other persistent data
- Must be created before running the container: `mkdir -p data`

## Development

### Running Tests
```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v
```

### Adding New Features
1. Add your feature implementation in `src/`
2. Add tests in `tests/`
3. Update requirements.txt if needed
4. Run tests to verify everything works 