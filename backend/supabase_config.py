"""
Supabase Configuration and Client Setup
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')

# PostgreSQL Connection String (for SQLAlchemy)
DATABASE_URL = os.environ.get('DATABASE_URL')

# Validate required environment variables
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required. Please check your .env file.")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required. Please check your .env file.")
if not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_ANON_KEY environment variable is required. Please check your .env file.")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required. Please check your .env file and add your database password.")

# Lazy initialization - clients created on first access
_supabase_admin = None
_supabase_public = None


def get_supabase_admin_client() -> Client:
    """Get Supabase admin client for server-side operations"""
    global _supabase_admin
    if _supabase_admin is None:
        try:
            _supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        except TypeError as e:
            if 'proxy' in str(e):
                # Workaround for httpx compatibility issue
                print("⚠️  Warning: Using compatibility workaround for Supabase client")
                # Try with updated httpx first
                import subprocess
                import sys
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'httpx==0.24.1', '--quiet'])
                    _supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
                except:
                    raise RuntimeError(
                        "Supabase client initialization failed due to httpx compatibility issue.\n"
                        "Please run: pip install httpx==0.24.1 --force-reinstall"
                    )
            else:
                raise
    return _supabase_admin


def get_supabase_public_client() -> Client:
    """Get Supabase public client for client-side operations"""
    global _supabase_public
    if _supabase_public is None:
        try:
            _supabase_public = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        except TypeError as e:
            if 'proxy' in str(e):
                # Workaround for httpx compatibility issue
                print("⚠️  Warning: Using compatibility workaround for Supabase client")
                import subprocess
                import sys
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'httpx==0.24.1', '--quiet'])
                    _supabase_public = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                except:
                    raise RuntimeError(
                        "Supabase client initialization failed due to httpx compatibility issue.\n"
                        "Please run: pip install httpx==0.24.1 --force-reinstall"
                    )
            else:
                raise
    return _supabase_public


def get_database_url() -> str:
    """Get PostgreSQL database URL for SQLAlchemy"""
    return DATABASE_URL
