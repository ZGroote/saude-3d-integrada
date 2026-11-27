-- "up" da vista precisa ser (quase) unitário: [0,0,0] não define orientação.
CREATE OR REPLACE FUNCTION public.vista_valida(p_vista jsonb)
RETURNS boolean LANGUAGE plpgsql IMMUTABLE SET search_path = ''
AS $$
DECLARE chaves constant text[] := ARRAY['atlas','atlas_versao','posicao','alvo','sistemas'];
  campo text; item jsonb; norma2 numeric := 0;
BEGIN
  IF p_vista IS NULL THEN RETURN true; END IF;
  IF jsonb_typeof(p_vista) <> 'object' OR octet_length(p_vista::text) > 2000 THEN RETURN false; END IF;
  IF NOT p_vista ?& chaves OR p_vista - chaves - 'up' <> '{}'::jsonb THEN RETURN false; END IF;
  IF jsonb_typeof(p_vista->'atlas') <> 'string' OR char_length(p_vista->>'atlas') NOT BETWEEN 1 AND 40
    OR jsonb_typeof(p_vista->'atlas_versao') <> 'string'
    OR char_length(p_vista->>'atlas_versao') NOT BETWEEN 1 AND 20 THEN RETURN false; END IF;
  FOREACH campo IN ARRAY ARRAY['posicao','alvo'] LOOP
    IF jsonb_typeof(p_vista->campo) <> 'array' THEN RETURN false; END IF;
    IF jsonb_array_length(p_vista->campo) <> 3 THEN RETURN false; END IF;
    FOR item IN SELECT e FROM jsonb_array_elements(p_vista->campo) AS e LOOP
      IF jsonb_typeof(item) <> 'number' THEN RETURN false; END IF;
      IF abs(item::text::numeric) > 10 THEN RETURN false; END IF;
    END LOOP;
  END LOOP;
  IF p_vista ? 'up' THEN
    IF jsonb_typeof(p_vista->'up') <> 'array' THEN RETURN false; END IF;
    IF jsonb_array_length(p_vista->'up') <> 3 THEN RETURN false; END IF;
    FOR item IN SELECT e FROM jsonb_array_elements(p_vista->'up') AS e LOOP
      IF jsonb_typeof(item) <> 'number' THEN RETURN false; END IF;
      IF abs(item::text::numeric) > 1 THEN RETURN false; END IF;
      norma2 := norma2 + item::text::numeric * item::text::numeric;
    END LOOP;
    -- norma entre 0,99 e 1,01, comparada ao quadrado
    IF norma2 NOT BETWEEN 0.9801 AND 1.0201 THEN RETURN false; END IF;
  END IF;
  IF jsonb_typeof(p_vista->'sistemas') <> 'array' THEN RETURN false; END IF;
  IF jsonb_array_length(p_vista->'sistemas') > 20 THEN RETURN false; END IF;
  FOR item IN SELECT e FROM jsonb_array_elements(p_vista->'sistemas') AS e LOOP
    IF jsonb_typeof(item) <> 'string' OR (item #>> '{}') !~ '^[a-z_]{1,40}$' THEN RETURN false; END IF;
  END LOOP;
  RETURN true;
END
$$;
REVOKE ALL ON FUNCTION public.vista_valida(jsonb) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.vista_valida(jsonb) TO service_role;
