CREATE SCHEMA auth;
CREATE TABLE auth.users (
  id uuid PRIMARY KEY,
  email text
);
CREATE TABLE auth.sessions (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  not_after timestamptz
);
CREATE FUNCTION auth.jwt()
RETURNS jsonb LANGUAGE plpgsql STABLE
AS $$
DECLARE raw_claims text;
BEGIN
  raw_claims := NULLIF(current_setting('request.jwt.claims', true), '');
  IF raw_claims IS NULL THEN
    raw_claims := jsonb_build_object('sub', NULLIF(current_setting('request.jwt.claim.sub', true), ''))::text;
  END IF;
  RETURN COALESCE(raw_claims::jsonb, '{}'::jsonb);
EXCEPTION WHEN OTHERS THEN
  RETURN '{}'::jsonb;
END
$$;
CREATE FUNCTION auth.uid()
RETURNS uuid LANGUAGE plpgsql STABLE
AS $$
DECLARE subject text;
BEGIN
  subject := COALESCE(NULLIF(auth.jwt()->>'sub', ''), NULLIF(current_setting('request.jwt.claim.sub', true), ''));
  RETURN NULLIF(subject, '')::uuid;
EXCEPTION WHEN OTHERS THEN
  RETURN NULL;
END
$$;

CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role NOLOGIN BYPASSRLS;
GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION auth.uid(), auth.jwt() TO anon, authenticated, service_role;
GRANT USAGE ON SCHEMA public TO anon, authenticated;
