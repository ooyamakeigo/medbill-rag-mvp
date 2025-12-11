"""
REST API client for Gemini models that are not yet supported by Python SDK.
Uses REST API calls to Vertex AI.
"""
import json
import subprocess
from typing import Optional, Dict, Any, List

try:
    from google.auth import default
    from google.auth.transport.requests import Request
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    # Fallback: try to use gcloud command if google.auth is not available
    default = None
    Request = None
    GOOGLE_AUTH_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .config import settings


def _get_access_token() -> str:
    """Get GCP access token using Application Default Credentials (ADC)."""
    # Try using google.auth first (works in Docker with service account or ADC)
    if GOOGLE_AUTH_AVAILABLE:
        try:
            credentials, _ = default()
            # Refresh the token if needed
            if not credentials.valid:
                credentials.refresh(Request())
            return credentials.token
        except Exception as e:
            # Fallback to gcloud command if ADC fails
            pass

    # Fallback: try gcloud command (for local development)
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        error_msg = (
            "Failed to get access token. "
            "Please ensure Application Default Credentials are set up. "
            "In Docker, this can be done by:\n"
            "1. Setting GOOGLE_APPLICATION_CREDENTIALS to a service account key file path, or\n"
            "2. Running 'gcloud auth application-default login' on the host and mounting ~/.config/gcloud"
        )
        raise RuntimeError(error_msg) from e


def _build_request_body(contents: List[str], response_mime_type: Optional[str] = None) -> Dict[str, Any]:
    """Build request body for Vertex AI generateContent API."""
    # Combine all contents into a single text part
    # (This matches how the SDK handles multiple strings in contents)
    combined_text = "\n\n".join(contents)
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": combined_text}]
            }
        ]
    }
    if response_mime_type:
        body["generationConfig"] = {
            "responseMimeType": response_mime_type
        }
    return body


def generate_content_rest(
    model_id: str,
    contents: List[str],
    response_mime_type: Optional[str] = None,
) -> str:
    """
    Call Vertex AI generateContent API using REST API (curl-like).

    Args:
        model_id: Model ID (e.g., "gemini-3-pro-preview")
        contents: List of prompt strings
        response_mime_type: Optional response MIME type (e.g., "application/json")

    Returns:
        Response text from the model
    """
    cfg = settings._get()
    access_token = _get_access_token()

    url = (
        f"https://aiplatform.googleapis.com/v1/projects/{cfg.project_id}"
        f"/locations/{cfg.location}/publishers/google/models/{model_id}:generateContent"
    )

    request_body = _build_request_body(contents, response_mime_type)

    # Use requests library if available, otherwise fall back to curl
    if REQUESTS_AVAILABLE:
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=utf-8",
            }
            response = requests.post(url, json=request_body, headers=headers, timeout=300)
            if not response.ok:
                # Try to get detailed error message
                try:
                    error_json = response.json()
                    error_msg = error_json.get("error", {}).get("message", response.text)
                    error_details = json.dumps(error_json, indent=2)
                    raise RuntimeError(
                        f"API call failed with status {response.status_code}: {error_msg}\n"
                        f"Request URL: {url}\n"
                        f"Request body: {json.dumps(request_body, indent=2)}\n"
                        f"Response: {error_details}"
                    )
                except (ValueError, KeyError):
                    raise RuntimeError(
                        f"API call failed with status {response.status_code}: {response.text}\n"
                        f"Request URL: {url}\n"
                        f"Request body: {json.dumps(request_body, indent=2)}"
                    )
            response_json = response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API call failed: {e}") from e
    else:
        # Fallback: use curl command
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(request_body, f)
            request_file = f.name

        try:
            curl_cmd = [
                "curl", "-sS", "-X", "POST",
                "-H", f"Authorization: Bearer {access_token}",
                "-H", "Content-Type: application/json; charset=utf-8",
                "-d", f"@{request_file}",
                url,
            ]

            result = subprocess.run(
                curl_cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            response_json = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e.stdout or "Unknown error"
            raise RuntimeError(f"API call failed (exit code {e.returncode}): {error_msg}") from e
        finally:
            try:
                Path(request_file).unlink()
            except Exception:
                pass

    # Extract text from response
    # Vertex AI response structure: candidates[0].content.parts[0].text
    if "candidates" in response_json and len(response_json["candidates"]) > 0:
        candidate = response_json["candidates"][0]
        if "content" in candidate and "parts" in candidate["content"]:
            parts = candidate["content"]["parts"]
            if len(parts) > 0 and "text" in parts[0]:
                return parts[0]["text"]

    # Check for errors in response
    if "error" in response_json:
        error_info = response_json["error"]
        error_msg = error_info.get("message", "Unknown error")
        raise RuntimeError(f"API returned an error: {error_msg}")

    # Fallback: return raw response if structure is different
    raise RuntimeError(f"Unexpected response structure: {response_json}")


def generate_content(
    model_id: Optional[str] = None,
    contents: List[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Compatibility wrapper that mimics the SDK's generate_content interface.

    Args:
        model_id: Model ID (defaults to settings.model_id)
        contents: List of prompt strings
        config: Optional config dict (e.g., {"response_mime_type": "application/json"})

    Returns:
        Object with .text attribute containing the response
    """
    if model_id is None:
        model_id = settings.model_id

    if contents is None:
        raise ValueError("contents is required")

    response_mime_type = None
    if config and "response_mime_type" in config:
        response_mime_type = config["response_mime_type"]

    text = generate_content_rest(model_id, contents, response_mime_type)

    # Return an object that mimics the SDK response
    class Response:
        def __init__(self, text: str):
            self.text = text

    return Response(text)

