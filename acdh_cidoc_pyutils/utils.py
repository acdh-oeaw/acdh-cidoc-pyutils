def remove_trailing_slash(url: str) -> str:
    """Remove trailing slash from a URL."""
    if url[-1] == "/":
        return url[:-1]
    return url


def normalize_xsd_gYear(year: str) -> str:
    year = year.strip()

    if year.startswith("-"):
        sign = "-"
        digits = year[1:]
    else:
        sign = ""
        digits = year

    if not digits.isdigit():
        raise ValueError(f"Invalid gYear value: {year}")

    if len(digits) > 4:
        raise ValueError(f"Year has more than 4 digits: {year}")

    return f"{sign}{digits.zfill(4)}"
