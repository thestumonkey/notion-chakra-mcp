"""
OpenTelemetry configuration for the Notion MCP server.
"""

import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor

logger = logging.getLogger(__name__)

def setup_telemetry(app=None):
    """Initialize OpenTelemetry with the specified configuration."""
    try:
        # Set up the tracer
        tracer_provider = TracerProvider()
        trace.set_tracer_provider(tracer_provider)

        # Create OTLP Span Exporter
        otlp_exporter = OTLPSpanExporter()
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)

        # Instrument HTTP libraries
        RequestsInstrumentor().instrument()
        AioHttpClientInstrumentor().instrument()

        # Instrument FastAPI if app is provided
        if app:
            FastAPIInstrumentor.instrument_app(app)

        logger.info("OpenTelemetry initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        raise 