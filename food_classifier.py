"""Client-side helpers for the NutriLens food classifier.

The classifier itself (pretrained ViT `yfh/food`) runs in Google Colab.
This module only prepares the image locally (Pillow) and calls the Colab
service over HTTPS. It has no Streamlit or deep-learning dependency, so it
is light enough for a laptop with little free disk space.
"""

import importlib.util
import io
import json
from functools import lru_cache
from pathlib import Path

import requests
from PIL import Image, ImageOps, UnidentifiedImageError

MODEL_ID = "yfh/food"  # fallback: pretrained ViT fine-tuned on Food-101 by its author
# Your own fine-tuned model (made with training/NutriLens_Train_Food101.ipynb).
# If this folder exists, the app uses it instead of MODEL_ID.
CUSTOM_MODEL_DIR = Path(__file__).resolve().parent / "models" / "nutrilens_food"
MIN_SIDE = 64      # smaller images are too tiny to classify
MAX_SIDE = 1024    # larger images are shrunk to keep uploads fast


class ClassifierError(Exception):
    """A problem with the classifier service that is safe to show to the user."""


def prepare_image(raw_bytes):
    """Validate an upload and return (jpeg_bytes, 'image/jpeg').

    Raises ValueError with a friendly message for unreadable or tiny images.
    """
    try:
        image = Image.open(io.BytesIO(raw_bytes))
        image.load()
    except (UnidentifiedImageError, OSError):
        raise ValueError("That file could not be read as an image. Please upload a JPG, PNG or WebP photo.")

    image = ImageOps.exif_transpose(image).convert("RGB")  # fix phone-photo rotation

    if min(image.size) < MIN_SIDE:
        raise ValueError(f"The image is too small (under {MIN_SIDE} pixels). Please upload a larger, clearer photo.")

    image.thumbnail((MAX_SIDE, MAX_SIDE))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue(), "image/jpeg"


def classify_food_image(image_bytes, url, token="", timeout=60):
    """Send an image to the Colab service and return the top predictions.

    Returns a list like [{"label": "Pizza", "score": 0.93}, ...].
    Raises ClassifierError with a readable message on any failure.
    """
    if not url:
        raise ClassifierError("The classifier URL is not configured.")

    # This header skips ngrok's browser warning page on free tunnels.
    headers = {"ngrok-skip-browser-warning": "true"}
    if token:
        headers["X-API-Token"] = token

    try:
        response = requests.post(
            f"{url.rstrip('/')}/classify",
            files={"file": ("meal.jpg", image_bytes, "image/jpeg")},
            headers=headers,
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        raise ClassifierError("The classifier took too long to respond. The Colab session may be starting up; try again.") from None
    except requests.exceptions.RequestException:
        raise ClassifierError(
            "Could not reach the classifier. Check that the Colab notebook is still running "
            "and that CLASSIFIER_URL in secrets.toml is the latest ngrok URL."
        ) from None

    if response.status_code in (401, 403):
        raise ClassifierError("The classifier rejected the request. Check that CLASSIFIER_TOKEN matches the token shown in Colab.")

    try:
        payload = response.json()
    except ValueError:
        raise ClassifierError(
            f"The classifier returned an unexpected reply (HTTP {response.status_code}). "
            "The ngrok URL may be old or the Colab session may have ended."
        ) from None

    if not response.ok:
        detail = payload.get("detail") if isinstance(payload, dict) else None
        raise ClassifierError(f"The classifier could not process the image: {detail or f'HTTP {response.status_code}'}")

    predictions = payload.get("predictions") if isinstance(payload, dict) else None
    if not isinstance(predictions, list) or not predictions:
        raise ClassifierError("The classifier returned no predictions.")

    cleaned = []
    for item in predictions[:3]:
        try:
            cleaned.append({"label": str(item["label"]), "score": float(item["score"])})
        except (KeyError, TypeError, ValueError):
            raise ClassifierError("The classifier returned predictions in an unexpected format.") from None
    return cleaned


def local_classifier_available():
    """True when torch and transformers are installed on this computer."""
    return all(importlib.util.find_spec(name) is not None for name in ("torch", "transformers"))


def local_model_info():
    """Say which model the local classifier will use.

    Returns {"source": "custom" | "pretrained", "name": str, "report": dict | None}.
    "custom" means the fine-tuned model in models/nutrilens_food/ exists.
    """
    if (CUSTOM_MODEL_DIR / "config.json").exists():
        report = None
        try:
            report = json.loads((CUSTOM_MODEL_DIR / "training_report.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        return {"source": "custom", "name": str(CUSTOM_MODEL_DIR), "report": report}
    return {"source": "pretrained", "name": MODEL_ID, "report": None}


def _square_crop(image, max_ratio=1.25):
    """Centre-crop very wide or tall photos to a square so the model does not see them squashed."""
    width, height = image.size
    if max(width, height) / min(width, height) <= max_ratio:
        return image
    side = min(width, height)
    left, top = (width - side) // 2, (height - side) // 2
    return image.crop((left, top, left + side, top + side))


@lru_cache(maxsize=1)
def _load_local_pipeline():
    # Imported here so the app starts fast and still runs when these packages are missing.
    # The pretrained fallback downloads from Hugging Face on first use (a few hundred MB).
    from transformers import pipeline
    info = local_model_info()
    model = info["name"] if info["source"] == "custom" else MODEL_ID
    return pipeline("image-classification", model=model)


def classify_food_image_local(image_bytes, top_k=3):
    """Run the pretrained model on this computer (inference only, no training).

    Returns the same format as classify_food_image().
    Raises ClassifierError with a readable message on any failure.
    """
    if not local_classifier_available():
        raise ClassifierError("torch and transformers are not installed, so the local classifier cannot run.")
    try:
        image = _square_crop(Image.open(io.BytesIO(image_bytes)).convert("RGB"))
        results = _load_local_pipeline()(image, top_k=top_k)
        return [
            {"label": str(r["label"]).replace("_", " ").strip().title(), "score": float(r["score"])}
            for r in results
        ]
    except Exception as error:
        raise ClassifierError(
            f"The local classifier failed ({type(error).__name__}: {error}). "
            "On the first run it needs internet to download the model."
        ) from None


def summarize_predictions(predictions):
    """'Pizza (93%), Focaccia (3%), Calzone (1%)' - used in prompts and Telegram."""
    return ", ".join(f"{p['label']} ({p['score']:.0%})" for p in predictions)
