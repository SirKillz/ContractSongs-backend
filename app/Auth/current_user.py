import os
from typing import Any

from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.models import CurrentUser
from app.auth.security import bearer_scheme


def fake_current_user() -> CurrentUser:
    return CurrentUser(
        sub="test-user-sub-123",
        username="test.user@example.com",
        client_id="local-test-client-id",
        token_use="access",
        scope="email openid profile",
        iss="https://cognito-idp.us-east-2.amazonaws.com/us-east-2_LOCAL",
    )


def _claims_from_aws_event(request: Request) -> dict[str, Any] | None:
    event = request.scope.get("aws.event") or {}
    return (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims")
    )


def _current_user_from_claims(claims: dict[str, Any]) -> CurrentUser:
    token_use = claims.get("token_use")
    if token_use and token_use != "access":
        raise HTTPException(
            status_code=401,
            detail=f"Unexpected token_use '{token_use}', expected 'access'",
        )

    return CurrentUser(
        sub=claims["sub"],
        username=claims.get("username"),
        client_id=claims.get("client_id"),
        token_use=claims.get("token_use"),
        scope=claims.get("scope"),
        iss=claims.get("iss"),
    )


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> CurrentUser:
    """
    Production:
      - API Gateway JWT authorizer authenticates the request
      - Mangum exposes the AWS event in request.scope["aws.event"]
      - this dependency extracts identity details for route logic

    Docs/local:
      - security scheme still appears in OpenAPI
      - bearer token can still be supplied from Swagger UI
      - for now, local can fall back to fake user
    """
    env = os.getenv("ENV", "dev")

    claims = _claims_from_aws_event(request)
    if claims:
        return _current_user_from_claims(claims)

    if env == "dev":
        return fake_current_user()

    # In prod, if API Gateway should have authenticated but claims are absent,
    # that means this route was reached without the expected authorizer context.
    raise HTTPException(status_code=401, detail="Not authenticated")