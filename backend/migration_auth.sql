-- economiX Auth Migration
-- Adds: profiles table, handle_new_user trigger, scanned_by columns + indexes, RLS policies

-- 1. profiles table (mirrors auth.users, auto-populated by trigger)
CREATE TABLE IF NOT EXISTS public.profiles (
    id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email text,
    full_name text,
    avatar_url text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- 2. Auto-create profile on signup (handles both email and Google OAuth)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name'),
        NEW.raw_user_meta_data->>'avatar_url'
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 3. Add scanned_by to processed_urls (nullable so existing rows stay intact)
ALTER TABLE public.processed_urls
    ADD COLUMN IF NOT EXISTS scanned_by uuid REFERENCES public.profiles(id);

CREATE INDEX IF NOT EXISTS idx_processed_urls_scanned_by
    ON public.processed_urls(scanned_by);

-- 4. Add scanned_by to scanned_prices (nullable)
ALTER TABLE public.scanned_prices
    ADD COLUMN IF NOT EXISTS scanned_by uuid REFERENCES public.profiles(id);

CREATE INDEX IF NOT EXISTS idx_scanned_prices_scanned_by
    ON public.scanned_prices(scanned_by);

-- 5. RLS on profiles (users can only read/update their own row)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    CREATE POLICY "profiles_select_own"
        ON public.profiles FOR SELECT
        USING ((SELECT auth.uid()) = id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY "profiles_update_own"
        ON public.profiles FOR UPDATE
        USING ((SELECT auth.uid()) = id)
        WITH CHECK ((SELECT auth.uid()) = id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 6. RLS on processed_urls (select own scans; writes via service role bypass RLS)
ALTER TABLE public.processed_urls ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    CREATE POLICY "processed_urls_select_own"
        ON public.processed_urls FOR SELECT
        USING ((SELECT auth.uid()) = scanned_by);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 7. RLS on scanned_prices (select own scans)
ALTER TABLE public.scanned_prices ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    CREATE POLICY "scanned_prices_select_own"
        ON public.scanned_prices FOR SELECT
        USING ((SELECT auth.uid()) = scanned_by);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
