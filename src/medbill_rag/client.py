from google import genai
from .config import settings, Config


def get_genai_client(cfg: Config = None):
    """
    Backward-compatible client factory.

    This MVP always uses Vertex AI (no Developer API key),
    aligned with HIPAA/BAA usage.
    """
    if cfg is None:
        # settings is a lazy proxy
        cfg = settings._get()  # type: ignore

    return genai.Client(
        vertexai=True,
        project=cfg.project_id,
        location=cfg.location,
    )
