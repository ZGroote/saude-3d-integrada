-- Vista da câmera salva junto do achado. Importação FHIR não informa a coluna: fica nula.
CREATE FUNCTION public.vista_valida(p_vista jsonb)
RETURNS boolean LANGUAGE plpgsql IMMUTABLE SET search_path = ''
AS $$
DECLARE chaves constant text[] := ARRAY['atlas','atlas_versao','posicao','alvo','sistemas'];
  campo text; item jsonb;
BEGIN
  IF p_vista IS NULL THEN RETURN true; END IF;
  IF jsonb_typeof(p_vista) <> 'object' OR octet_length(p_vista::text) > 2000 THEN RETURN false; END IF;
  IF NOT p_vista ?& chaves OR p_vista - chaves <> '{}'::jsonb THEN RETURN false; END IF;
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

ALTER TABLE public.achados ADD COLUMN vista jsonb;
ALTER TABLE public.achados ADD CONSTRAINT achados_vista_check CHECK (public.vista_valida(vista));

DROP FUNCTION public.registrar_achado(uuid,jsonb,text,public.categoria_achado,
  public.lado_achado,public.status_achado,date,text,uuid);
CREATE FUNCTION public.registrar_achado(
  p_paciente uuid, p_ancora jsonb, p_cid10 text, p_categoria public.categoria_achado,
  p_lado public.lado_achado, p_status public.status_achado, p_inicio date,
  p_observacao text, p_substitui uuid DEFAULT NULL,
  p_vista jsonb DEFAULT NULL
)
RETURNS uuid LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE
  usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); esp text;
  sigilo public.nivel_sigilo := 'normal'; novo uuid; sexo_paciente public.sexo;
  ancora_validada jsonb; lateralidade_catalogo text;
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RAISE EXCEPTION 'Perfil ausente' USING ERRCODE='42501'; END IF;
  SELECT p.especialidade INTO esp FROM public.perfis AS p WHERE p.id=usuario;
  IF NOT EXISTS (
    SELECT 1 FROM public.vinculos AS v WHERE v.paciente_id=p_paciente AND v.unidade_id=unidade
      AND v.desde<=CURRENT_DATE AND (v.ate IS NULL OR v.ate>CURRENT_DATE)
  ) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN NULL;
  END IF;
  IF p_ancora IS NOT NULL THEN
    SELECT p.sexo INTO sexo_paciente FROM public.pacientes AS p WHERE p.id=p_paciente;
    ancora_validada := public.normalizar_ancora(p_ancora,sexo_paciente);
    lateralidade_catalogo := ancora_validada->>'lateralidade';
    -- só contradição explícita: malha sem lado (pele inteira, órgão mediano) aceita o lado clínico informado
    IF (lateralidade_catalogo='left' AND p_lado='direito') OR
       (lateralidade_catalogo='right' AND p_lado='esquerdo') THEN
      RAISE EXCEPTION 'Âncora anatômica inválida' USING ERRCODE='22023';
    END IF;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.cid10 AS c WHERE c.codigo=p_cid10) THEN
    RAISE EXCEPTION 'CID-10 inexistente' USING ERRCODE='22023';
  END IF;
  SELECT 'restrito'::public.nivel_sigilo INTO sigilo FROM public.cid10_sigilo AS s
    WHERE p_cid10 LIKE s.prefixo || '%' ORDER BY length(s.prefixo) DESC LIMIT 1;
  sigilo := COALESCE(sigilo,'normal'::public.nivel_sigilo);
  IF p_substitui IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM public.achados AS a WHERE a.id=p_substitui AND a.paciente_id=p_paciente AND a.unidade_id=unidade
  ) THEN RAISE EXCEPTION 'Achado substituído indisponível' USING ERRCODE='42501'; END IF;
  INSERT INTO public.achados(paciente_id,autor_id,unidade_id,especialidade,ancora,cid10,categoria,lado,status,
    nivel_sigilo,inicio,observacao,substitui_id,vista)
  VALUES(p_paciente,usuario,unidade,esp,ancora_validada,p_cid10,p_categoria,p_lado,p_status,
    sigilo,p_inicio,p_observacao,p_substitui,p_vista) RETURNING id INTO novo;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
    VALUES(usuario,unidade,p_paciente,'registrar_achado');
  RETURN novo;
END
$$;
REVOKE ALL ON FUNCTION public.registrar_achado(uuid,jsonb,text,public.categoria_achado,
  public.lado_achado,public.status_achado,date,text,uuid,jsonb) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.registrar_achado(uuid,jsonb,text,public.categoria_achado,
  public.lado_achado,public.status_achado,date,text,uuid,jsonb) TO authenticated;

DROP FUNCTION public.listar_achados(uuid);
CREATE FUNCTION public.listar_achados(p_paciente uuid)
RETURNS TABLE(
  id uuid, ancora jsonb, estrutura text, cid10 text, cid10_descricao text,
  categoria public.categoria_achado, lado public.lado_achado, status public.status_achado,
  nivel_sigilo public.nivel_sigilo, inicio date, observacao text, especialidade text,
  autor_nome text, unidade_nome text, unidade_id uuid, substitui_id uuid, criado_em timestamptz, vista jsonb
) LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade();
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN; END IF;
  IF NOT EXISTS (SELECT 1 FROM public.vinculos AS v WHERE v.paciente_id=p_paciente AND v.unidade_id=unidade
    AND v.desde<=CURRENT_DATE AND (v.ate IS NULL OR v.ate>CURRENT_DATE)) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,NULL,'acesso_negado'); RETURN;
  END IF;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,p_paciente,'listar_achados');
  RETURN QUERY SELECT a.id,a.ancora,a.estrutura,a.cid10,c.descricao,a.categoria,a.lado,a.status,a.nivel_sigilo,
    a.inicio,a.observacao,a.especialidade,p.nome,u.nome,a.unidade_id,a.substitui_id,a.criado_em,a.vista
    FROM public.achados AS a JOIN public.cid10 AS c ON c.codigo=a.cid10
    JOIN public.perfis AS p ON p.id=a.autor_id JOIN public.unidades AS u ON u.id=a.unidade_id
    WHERE a.paciente_id=p_paciente AND (a.nivel_sigilo='normal' OR a.unidade_id=unidade)
      AND NOT EXISTS(SELECT 1 FROM public.achados AS prox WHERE prox.substitui_id=a.id)
    ORDER BY a.criado_em,a.id;
END
$$;

DROP FUNCTION public.historico_achado(uuid);
CREATE FUNCTION public.historico_achado(p_achado uuid)
RETURNS TABLE(
  id uuid, ancora jsonb, estrutura text, cid10 text, cid10_descricao text,
  categoria public.categoria_achado, lado public.lado_achado, status public.status_achado,
  nivel_sigilo public.nivel_sigilo, inicio date, observacao text, especialidade text,
  autor_nome text, unidade_nome text, unidade_id uuid, substitui_id uuid, criado_em timestamptz, vista jsonb
) LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); paciente uuid;
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN; END IF;
  SELECT a.paciente_id INTO paciente FROM public.achados AS a WHERE a.id=p_achado;
  IF paciente IS NULL OR NOT EXISTS(SELECT 1 FROM public.vinculos AS v WHERE v.paciente_id=paciente AND v.unidade_id=unidade
    AND v.desde<=CURRENT_DATE AND (v.ate IS NULL OR v.ate>CURRENT_DATE)) OR NOT EXISTS(
      SELECT 1 FROM public.achados AS a WHERE a.id=p_achado AND (a.nivel_sigilo='normal' OR a.unidade_id=unidade)) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,NULL,'acesso_negado'); RETURN;
  END IF;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,paciente,'historico_achado');
  RETURN QUERY WITH RECURSIVE anteriores(id,ordem) AS (
    SELECT p_achado,0 UNION ALL SELECT a.substitui_id,c.ordem-1 FROM public.achados AS a JOIN anteriores AS c ON a.id=c.id WHERE a.substitui_id IS NOT NULL
  ), cadeia(id,ordem) AS (
    SELECT ant.id,ant.ordem FROM anteriores AS ant UNION ALL
    SELECT prox.id,c.ordem+1 FROM public.achados AS prox JOIN cadeia AS c ON prox.substitui_id=c.id
  )
  SELECT a.id,a.ancora,a.estrutura,a.cid10,cid.descricao,a.categoria,a.lado,a.status,a.nivel_sigilo,
    a.inicio,a.observacao,a.especialidade,p.nome,u.nome,a.unidade_id,a.substitui_id,a.criado_em,a.vista
    FROM public.achados AS a JOIN public.cid10 AS cid ON cid.codigo=a.cid10
    JOIN public.perfis AS p ON p.id=a.autor_id JOIN public.unidades AS u ON u.id=a.unidade_id
    JOIN (SELECT c.id,min(c.ordem) AS ordem FROM cadeia AS c GROUP BY c.id) AS ch ON ch.id=a.id
    WHERE a.paciente_id=paciente AND (a.nivel_sigilo='normal' OR a.unidade_id=unidade) ORDER BY ch.ordem;
END
$$;

REVOKE ALL ON FUNCTION public.listar_achados(uuid), public.historico_achado(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.listar_achados(uuid), public.historico_achado(uuid) TO authenticated;
