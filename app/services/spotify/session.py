from __future__ import annotations
import base64
import os

from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx
from httpx import Response

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


class SpotifyTokenRequestError(Exception):
    def __init__(self, detail: str, status_code: int = 502) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code

def _get_b64_encoded_auth_string():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise SpotifyTokenRequestError(
            "Spotify client credentials are not configured",
            status_code=500,
        )
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    return base64.b64encode(auth_string.encode()).decode()

def request_tokens_with_code(code: str) -> Dict:
    """
    Used to get the initial access token after the user logs in and is redirected back to the App
    User must navigate to: https://accounts.spotify.com/authorize?client_id=400ccbc311e24c878036fc6821ec6e98&response_type=code&redirect_uri=http://127.0.0.1:3000&scope=user-read-currently-playing%20user-modify-playback-state
    """
    url = "https://accounts.spotify.com/api/token"
    redirect_uri = os.getenv("SPOTIFY_APP_REDIRECT_URI")

    if not redirect_uri:
        raise SpotifyTokenRequestError(
            "Spotify redirect URI is not configured",
            status_code=500,
        )

    b64_encoded_auth = _get_b64_encoded_auth_string()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_encoded_auth}"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    try:
        response = httpx.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        try:
            payload = exc.response.json()
        except ValueError:
            payload = exc.response.text

        if exc.response.status_code in (400, 401):
            raise SpotifyTokenRequestError(
                f"Spotify rejected the token request: {payload}",
                status_code=exc.response.status_code,
            ) from exc

        raise SpotifyTokenRequestError(
            f"Spotify token endpoint failed: {payload}",
            status_code=502,
        ) from exc
    except httpx.RequestError as exc:
        raise SpotifyTokenRequestError(
            "Could not reach Spotify token endpoint",
            status_code=502,
        ) from exc

def request_token_via_refresh(refresh_token: str) -> Response:
    url = "https://accounts.spotify.com/api/token"
    b64_encoded_auth = _get_b64_encoded_auth_string()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_encoded_auth}"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    try:
        response = httpx.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        try:
            payload = exc.response.json()
        except ValueError:
            payload = exc.response.text

        if exc.response.status_code in (400, 401):
            raise SpotifyTokenRequestError(
                f"Spotify rejected the refresh request: {payload}",
                status_code=exc.response.status_code,
            ) from exc

        raise SpotifyTokenRequestError(
            f"Spotify refresh endpoint failed: {payload}",
            status_code=502,
        ) from exc
    except httpx.RequestError as exc:
        raise SpotifyTokenRequestError(
            "Could not reach Spotify token endpoint",
            status_code=502,
        ) from exc


class ApiSession:
    """
    Minimal HTTP session wrapper.

    Responsibilities:
    - Keep base_url + auth in one place
    - Provide small helpers (get/post/put/delete)
    - Return JSON payloads
    - Raise a basic error when the API call fails
    """

    def __init__(
        self,
        base_url: str,
        access_token: str,
        timeout: float = 5.0,
        max_retires: int = 10,
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.max_retries = max_retires

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if default_headers:
            headers.update(default_headers)
        self.session = httpx.AsyncClient(headers=headers, timeout=self.timeout)

    async def close(self) -> None:
        await self.session.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = urljoin(self.base_url, path.lstrip("/"))

        attempt = 0
        while True:
            try:
                resp = await self.session.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json,
                )
                break
            except httpx.TimeoutException as exc:
                if attempt >= self.max_retries:
                    raise RuntimeError(f"API request timed out after {self.timeout}s: {method.upper()} {url}") from exc
                attempt += 1
                continue

        # If it's not a 2xx, raise a simple error with context.
        if not (200 <= resp.status_code < 300):
            # Try to include response body to help debugging.
            try:
                body = resp.json()
            except ValueError:
                body = resp.text

            raise RuntimeError(
                f"API request failed: {method.upper()} {url} "
                f"-> {resp.status_code} {resp.reason_phrase}. Response: {body}"
            )

        # No Content
        if resp.status_code == 204:
            return None

        # Try JSON first; if API returns non-JSON, fall back to text.
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type.lower():
            return resp.json()

        return resp.text

    # Convenience wrappers
    async def get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, *, json: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request("POST", path, json=json)

    async def put(self, path: str, *, json: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request("PUT", path, json=json)

    async def delete(self, path: str) -> Any:
        return await self.request("DELETE", path)
