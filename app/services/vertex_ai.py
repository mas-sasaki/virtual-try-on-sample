from google import genai
from google.genai import types

from app.config import settings

_OUTERWEAR_KEYWORDS = {"jacket", "coat", "blazer", "outerwear", "outer"}
_NEGATIVE_PROMPT_OUTERWEAR = (
    "bare skin, bare chest, shirtless, no inner clothing, remove shirt, remove inner layer"
)


def _client() -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=settings.gcp_project,
        location=settings.vertex_ai_region,
    )


def _call_tryon(
    person_image_bytes: bytes,
    garment_image_bytes: bytes,
    negative_prompt: str | None = None,
) -> bytes:
    config_kwargs: dict = {"number_of_images": 1}
    if negative_prompt:
        config_kwargs["negative_prompt"] = negative_prompt

    response = _client().models.recontext_image(
        model="virtual-try-on-001",
        source=types.RecontextImageSource(
            person_image=types.Image(image_bytes=person_image_bytes),
            product_images=[
                types.ProductImage(
                    product_image=types.Image(image_bytes=garment_image_bytes)
                )
            ],
        ),
        config=types.RecontextImageConfig(**config_kwargs),
    )
    return response.generated_images[0].image.image_bytes


def _outerwear_negative_prompt(label: str | None) -> str | None:
    if not label:
        return None
    lower = label.lower()
    if any(kw in lower for kw in _OUTERWEAR_KEYWORDS):
        return _NEGATIVE_PROMPT_OUTERWEAR
    return None


def run_virtual_tryon(
    person_image_bytes: bytes,
    top_image_bytes: bytes | None,
    bottom_image_bytes: bytes | None,
    top_label: str | None = None,
) -> bytes:
    result = person_image_bytes
    if top_image_bytes:
        result = _call_tryon(
            result,
            top_image_bytes,
            negative_prompt=_outerwear_negative_prompt(top_label),
        )
    if bottom_image_bytes:
        result = _call_tryon(result, bottom_image_bytes)
    return result
