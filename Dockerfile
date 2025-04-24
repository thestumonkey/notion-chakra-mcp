FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
# Create data directory

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-install-project --frozen --dev 

RUN uv pip install debugpy
# RUN /app/.venv/bin/pip install debugpy
# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --dev
    # --frozen --dev

# Place executables in the environment at the front of the path

ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the FastAPI application by default
# Uses `fastapi dev` to enable hot-reloading when the `watch` sync occurs
# Uses `--host 0.0.0.0` to allow access from outside the container
# CMD ["fastapi", "dev", "--host", "0.0.0.0", "src.main:mcp", "--reload"]
# CMD [command: ["sh", "-c", "pip install debugpy -t /tmp && python /tmp/debugpy --wait-for-client --listen 0.0.0.0:5555 -m uvicorn src.main:mcp --host 0.0.0.0 --port 8050"]]
# Command to run the MCP server
CMD ["uv", "run", "src/main.py"]