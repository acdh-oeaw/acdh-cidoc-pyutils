def remove_trailing_slash(url: str) -> str:
    """Remove trailing slash from a URL."""
    if url[-1] == "/":
        return url[:-1]
    return url
