"""
Centralized Supabase client and shared backend configuration.

All backend modules import the singleton `supabase` from here instead of
calling `create_client` themselves. Keeping a single client per process
avoids duplicate connection pools and ensures environment validation
happens in exactly one place.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET', '')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(
        "Missing required environment variables: "
        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY. "
        "Copy backend/.env.example to backend/.env and fill in the values."
    )

if not SUPABASE_JWT_SECRET:
    print(
        "[INFO] SUPABASE_JWT_SECRET is not set. "
        "Token verification will use the JWKS endpoint (recommended for ECC keys). "
        "Set this variable only if you are still on the legacy HS256 signing key."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
