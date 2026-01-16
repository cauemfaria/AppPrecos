import os
from dotenv import load_dotenv
from supabase import create_client

# Explicitly load .env from the backend directory
dotenv_path = os.path.join('c:\\AppPrecos\\backend', '.env')
load_dotenv(dotenv_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Supabase credentials not found in environment.")
    exit(1)

supabase = create_client(url, key)

def check_status():
    # Count pending purchases
    pending = supabase.table('purchases').select('id', count='exact').eq('enriched', False).execute()
    pending_count = pending.count if pending.count is not None else 0

    # Count completed enrichments
    completed = supabase.table('purchases').select('id', count='exact').eq('enrichment_status', 'completed').execute()
    completed_count = completed.count if completed.count is not None else 0

    # Count backlog items
    backlog = supabase.table('purchases').select('id', count='exact').eq('enrichment_status', 'backlog').execute()
    backlog_count = backlog.count if backlog.count is not None else 0

    print(f"Pending: {pending_count}")
    print(f"Completed: {completed_count}")
    print(f"Backlog: {backlog_count}")

if __name__ == "__main__":
    check_status()
