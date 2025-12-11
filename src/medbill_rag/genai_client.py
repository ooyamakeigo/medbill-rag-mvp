from google import genai
from .config import Config


def get_genai_client(cfg: Config):
    """
    Vertex AI Gemini client (no Developer API key).
    """
    return genai.Client(
        vertexai=True,
        project=cfg.project_id,
        location=cfg.location,
    )
