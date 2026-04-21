from datetime import datetime, timezone

def parse_str_to_datetime(dt_str: str) -> datetime:
    """
    Converts ISO 8601 string (e.g. "2026-04-19T18:25:43Z") to datetime
    """

    # Handle trailing 'Z' (UTC)
    if dt_str.endswith("Z"):
        dt_str = dt_str.replace("Z", "+00:00")
    
    return datetime.fromisoformat(dt_str)

def parse_datetime_to_str(dt: datetime) -> str:
    """
    Converts datetime to ISO 8601 string with 'Z' (UTC), e.g. "2026-04-19T18:25:43Z"
    """

    # Ensure it's timezone-aware (assume UTC if naive)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to UTC explicitly (in case it's another timezone)
    dt = dt.astimezone(timezone.utc)

    # Convert to ISO string and replace +00:00 with Z
    return dt.isoformat().replace("+00:00", "Z")

from datetime import datetime, timezone, timedelta

def get_token_expiration(seconds: int) -> datetime:
    """
    Returns current UTC time + `seconds` as ISO 8601 string with 'Z'
    """
    if seconds is None:
        raise ValueError("Spotify token response is missing expires_in")

    try:
        seconds = int(seconds)
    except (TypeError, ValueError) as exc:
        raise ValueError("Spotify token response contains an invalid expires_in") from exc

    if seconds <= 0:
        raise ValueError("Spotify token response contains a non-positive expires_in")

    dt = datetime.now(timezone.utc) + timedelta(seconds=seconds)

    return dt
