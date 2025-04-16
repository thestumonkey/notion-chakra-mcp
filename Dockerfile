FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY requirements.txt .
COPY src/ src/

# Install dependencies
RUN uv pip install --system -r requirements.txt

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PORT=8050

# Run the server
CMD ["python", "-m", "src.main"] 