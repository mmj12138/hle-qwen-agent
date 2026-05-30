# Author: mmj
# DATE: 30.05.2026
def empty_image(value):
    """
    HLE image fields may be:
    - None
    - "" empty string
    - "data:image/jpeg;base64,..." for real image
    - {"path": None, "bytes": None}
    - PIL image object if decoded
    """
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    if isinstance(value, dict):
        path = value.get("path")
        bytes_ = value.get("bytes")
        return path in [None, ""] and bytes_ in [None, b"", ""]

    # PIL Image object means real image
    if hasattr(value, "size") and hasattr(value, "mode"):
        return False

    return False


def is_text_only(item):
    return (
        empty_image(item.get("image"))
        and empty_image(item.get("image_preview"))
        and empty_image(item.get("rationale_image"))
    )
