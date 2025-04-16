# Notion Chakra MCP

## Docker Setup

### Prerequisites
- Docker
- Docker Compose

### Configuration
1. Create a `.env` file in the project root with your configuration:
```env
NOTION_DB_TASKS_DB=your_notion_db_id
# Add other environment variables as needed
```

2. Create a `data` directory in the project root:
```bash
mkdir -p data
```

### Running with Docker Compose
```bash
# Build and start the container
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Override environment variables
PORT=9000 docker-compose up
```

### Running with Docker
```bash
# Build the image
docker build -t notion-chakra-mcp .

# Run the container
docker run -p 8050:8050 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/data:/app/data \
  notion-chakra-mcp

# Override environment variables
docker run -p 9000:9000 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/data:/app/data \
  -e PORT=9000 \
  notion-chakra-mcp
```

### Environment Variables
- `NOTION_DB_TASKS_DB`: Notion database ID for tasks
- `PORT`: Server port (default: 8050)
- `HOST`: Server host (default: 0.0.0.0)

Environment variables can be set in three ways, in order of precedence:
1. Command-line overrides (`docker run -e` or environment prefix with `docker-compose up`)
2. `.env` file
3. Default values in Dockerfile 