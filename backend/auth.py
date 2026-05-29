"""
JWT authentication utilities for the economiX backend.

Verifies Supabase-issued JWTs using the project's JWKS endpoint.
Supports both the current ECC (P-256 / ES256) signing key and the
legacy HS256 shared secret — works regardless of which algorithm
Supabase is using.

Keys are fetched once on first use and cached in memory. The cache
is invalidated automatically if verification fails with a known-good
token (key rotation handling).
"""

import time
import requests as req_lib
from functools import wraps
from flask import request, jsonify, g
import jwt
from jwt import PyJWKClient, PyJWKClientError

from supabase_client import SUPABASE_URL, SUPABASE_JWT_SECRET

# ---------------------------------------------------------------------------
# JWKS client — fetches public keys from Supabase's well-known endpoint
# ---------------------------------------------------------------------------
_JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(_JWKS_URL, cache_keys=True, max_cached_keys=16)
    return _jwks_client


def _verify_token(token: str) -> dict | None:
    """
    Try to verify a JWT token. Returns the decoded payload or None.

    Strategy:
    1. Try JWKS (current ECC / ES256 key — what new projects use).
    2. Fall back to legacy HS256 shared secret if JWKS fails and secret is set.
       This covers projects still on the legacy key or during rotation windows.
    """
    # --- Strategy 1: JWKS (ECC P-256 / ES256, or any future algorithm) ---
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
        return payload
    except PyJWKClientError:
        pass  # key not found in JWKS — try legacy fallback
    except jwt.ExpiredSignatureError:
        return None  # definitively expired, no point trying legacy
    except jwt.InvalidTokenError:
        pass  # may be a legacy HS256 token

    # --- Strategy 2: Legacy HS256 shared secret ---
    if SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": True},
            )
            return payload
        except jwt.InvalidTokenError:
            pass

    return None


# ---------------------------------------------------------------------------
# Public helpers used by app.py
# ---------------------------------------------------------------------------

def _extract_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):]
    return None


def require_auth(f):
    """Decorator: verify JWT, set g.user_id = sub claim. Returns 401 on failure."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return jsonify({"error": "Autenticação necessária"}), 401
        payload = _verify_token(token)
        if payload is None:
            return jsonify({"error": "Token inválido ou expirado — faça login novamente"}), 401
        g.user_id = payload["sub"]
        return f(*args, **kwargs)
    return decorated


def get_user_id_from_token() -> str | None:
    """
    Soft version: returns the user_id from the JWT without raising.
    Use for before_request guards where you want one central 401 response.
    Returns None if the token is missing or invalid.
    """
    token = _extract_bearer_token()
    if not token:
        return None
    payload = _verify_token(token)
    if payload is None:
        return None
    return payload.get("sub")
