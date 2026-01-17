import os

OTEL_ENABLED = os.getenv("OTEL_ENABLED", "false").lower() == "true"


def setup_otel(app=None):
    if not OTEL_ENABLED:
        return
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "valhalla-exports")})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318"))
    )
    provider.add_span_processor(processor)

    from opentelemetry import trace

    trace.set_tracer_provider(provider)
    if app:
        FastAPIInstrumentor.instrument_app(app)
