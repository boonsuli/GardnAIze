from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}

def decode_image(content: bytes, mime_type: str) -> Image.Image:
    try:
        with Image.open(BytesIO(content)) as img:
            if img.format not in ALLOWED_FORMATS or ALLOWED_FORMATS[img.format] != mime_type:
                raise ValueError("Unsupported image format or MIME mismatch")
            img.verify()
        with Image.open(BytesIO(content)) as img:
            img = ImageOps.exif_transpose(img)
            return img.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Invalid image data") from exc
