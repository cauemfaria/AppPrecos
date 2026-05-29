"""
JWT authentication utilities for the economiX backend.

Verifies Supabase-issued JWTs locally using SUPABASE_JWT_SECRET (HS256).
No network call per request — fully stateless and horizontally scalable.
"""

import jwt
from functools import wraps
from flask import request, jsonify, g
from supabase_client import SUPABASE_JWT_SECRET


def _extract_bearer_token() -> str | None:
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[len('Bearer '):]
    return None


def require_auth(f):
    """Decorator: verify JWT, set g.user_id = sub claim. Returns 401 on failure."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return jsonify({'error': 'Autenticação necessária'}), 401
        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=['HS256'],
                audience='authenticated',
            )
            g.user_id = payload['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado — faça login novamente'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'error': f'Token inválido: {e}'}), 401
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
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=['HS256'],
            audience='authenticated',
        )
        return payload.get('sub')
    except jwt.InvalidTokenError:
        return None
