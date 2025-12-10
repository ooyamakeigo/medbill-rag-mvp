import os
from google import genai
from .config import settings

def get_genai_client():
    """
    Use Vertex AI Gemini by default.
    On Compute Engine with a service account, ADC will be used automatically.
    """
    if settings.use_vertex:
        if not settings.project_id:
            raise RuntimeError("PROJECT_ID is not set")
        return genai.Client(
            vertexai=True,
            project=settings.project_id,
            location=settings.vertex_location,
        )

    # Non-PHI local testing only
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required when USE_VERTEX=false")
    return genai.Client(api_key=api_key)
