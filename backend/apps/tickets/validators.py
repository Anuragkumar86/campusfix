"""Upload validation: size limit + real content check (not the file extension)."""
import os
import re

from django.conf import settings
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers


def validate_image_upload(upload):
    """Return (content_type, extension, safe_original_name) or raise a field error."""
    max_size = settings.MAX_UPLOAD_SIZE
    if upload.size > max_size:
        raise serializers.ValidationError(f"File is too large. Maximum size is {max_size // (1024 * 1024)} MB.")
    if upload.size == 0:
        raise serializers.ValidationError("The uploaded file is empty.")
    try:
        upload.seek(0)
        with Image.open(upload) as img:
            fmt = img.format
            img.verify()  # detects truncated / corrupt images
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError):
        raise serializers.ValidationError("Upload a valid image file (JPEG, PNG, WEBP or GIF).")
    finally:
        upload.seek(0)
    allowed = settings.ALLOWED_IMAGE_FORMATS
    if fmt not in allowed:
        raise serializers.ValidationError("Unsupported image type. Allowed: " + ", ".join(sorted(allowed)) + ".")
    content_type, ext = allowed[fmt]
    name = os.path.basename(upload.name or "image")
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name)[:200] or "image"
    return content_type, ext, name
