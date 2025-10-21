"""
Supabase Configuration and Client Setup
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import os

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://gqfnbhhlvyrljfmfdcsf.supabase.co')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdxZm5iaGhzdnlybGpmbWZkY3NmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDkzMDAyOCwiZXhwIjoyMDc2NTA2MDI4fQ.W0-nL-QU7RHoH2bfLaqPujx1XRejkfp3QdGqumta4go')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdxZm5iaGhzdnlybGpmbWZkY3NmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA5MzAwMjgsImV4cCI6MjA3NjUwNjAyOH0._BS5qOOItkHyUzdVFKQHy228NOf-HjF8mPZxvZvCtjM')

# PostgreSQL Connection String (for SQLAlchemy)
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@gqfnbhhlvyrljfmfdcsf.db.supabase.co:5432/postgres')

# Initialize Supabase Client (with service role for admin operations)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Initialize Supabase Client (with anon key for public operations)
supabase_public: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_supabase_admin_client() -> Client:
    """Get Supabase admin client for server-side operations"""
    return supabase_admin


def get_supabase_public_client() -> Client:
    """Get Supabase public client for client-side operations"""
    return supabase_public


def get_database_url() -> str:
    """Get PostgreSQL database URL for SQLAlchemy"""
    return DATABASE_URL
