"""Quick CLI: report how many purchases are pending / completed / backlogged."""

from supabase_client import supabase


def check_status():
    pending = supabase.table('purchases').select('id', count='exact').eq('enriched', False).execute()
    completed = supabase.table('purchases').select('id', count='exact').eq('enrichment_status', 'completed').execute()
    backlog = supabase.table('purchases').select('id', count='exact').eq('enrichment_status', 'backlog').execute()

    print(f"Pending:   {pending.count or 0}")
    print(f"Completed: {completed.count or 0}")
    print(f"Backlog:   {backlog.count or 0}")


if __name__ == "__main__":
    check_status()
