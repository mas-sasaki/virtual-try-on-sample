from google import genai
from google.genai import types

from app.config import settings

def _call_tryon(person_image_bytes: bytes, garment_image_bytes: bytes) -> bytes:
    with genai.Client(
        vertexai=True,
        project=settings.gcp_project,
        location=settings.vertex_ai_region,
    ) as client:
        response = client.models.recontext_image(
            model="virtual-try-on-001",
            source=types.RecontextImageSource(
                person_image=types.Image(image_bytes=person_image_bytes),
                product_images=[
                    types.ProductImage(
                        product_image=types.Image(image_bytes=garment_image_bytes)
                    )
                ],
            ),
            config=types.RecontextImageConfig(number_of_images=1),
        )
    return response.generated_images[0].image.image_bytes


def run_virtual_tryon(
    person_image_bytes: bytes,
    top_image_bytes: bytes | None,
    bottom_image_bytes: bytes | None,
) -> bytes:
    result = person_image_bytes
    # ボトムスを先に適用し、その上にトップスを重ねることで
    # トップス適用時（上半身処理）にボトムスが残りやすくなる
    if bottom_image_bytes:
        result = _call_tryon(result, bottom_image_bytes)
    if top_image_bytes:
        result = _call_tryon(result, top_image_bytes)
    return result
