CREATE TYPE public.categoria_achado AS ENUM ('doenca','sintoma','lesao','cirurgia','dispositivo','alergia');
CREATE TYPE public.lado_achado AS ENUM ('esquerdo','direito','bilateral','nao_se_aplica');
CREATE TYPE public.status_achado AS ENUM ('ativo','resolvido','suspeito');
CREATE TYPE public.nivel_sigilo AS ENUM ('normal','restrito');
CREATE TYPE public.origem_achado AS ENUM ('manual','fhir');

CREATE TABLE public.cid10_sigilo (
  prefixo text PRIMARY KEY,
  motivo text NOT NULL
);
INSERT INTO public.cid10_sigilo (prefixo, motivo) VALUES
  ('B20','HIV'), ('B21','HIV'), ('B22','HIV'), ('B23','HIV'), ('B24','HIV'), ('Z21','HIV'),
  ('T74','violência'), ('Y05','violência'), ('Y07','violência'),
  ('F','saúde mental'), ('O04','aborto'), ('O05','aborto'), ('O06','aborto'), ('O07','aborto');

CREATE TABLE public.achados (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  paciente_id uuid NOT NULL REFERENCES public.pacientes(id),
  autor_id uuid NOT NULL REFERENCES public.perfis(id),
  unidade_id uuid NOT NULL REFERENCES public.unidades(id),
  especialidade text,
  ancora jsonb,
  estrutura text GENERATED ALWAYS AS (ancora->>'estrutura') STORED,
  cid10 text NOT NULL REFERENCES public.cid10(codigo),
  categoria public.categoria_achado NOT NULL,
  lado public.lado_achado NOT NULL,
  status public.status_achado NOT NULL,
  nivel_sigilo public.nivel_sigilo NOT NULL DEFAULT 'normal',
  inicio date,
  observacao text,
  substitui_id uuid REFERENCES public.achados(id),
  origem public.origem_achado NOT NULL DEFAULT 'manual',
  fhir_id text,
  criado_em timestamptz NOT NULL DEFAULT now(),
  CHECK (substitui_id IS NULL OR substitui_id <> id)
);
CREATE INDEX achados_paciente_vigentes_idx ON public.achados (paciente_id, criado_em DESC);
CREATE INDEX achados_substitui_idx ON public.achados (substitui_id);
ALTER TABLE public.achados ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cid10_sigilo ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.achados, public.cid10_sigilo FROM PUBLIC, anon, authenticated;
ALTER TABLE public.auditoria ALTER COLUMN paciente_id DROP NOT NULL;

CREATE OR REPLACE FUNCTION public.abrir_prontuario(p_paciente uuid)
RETURNS public.pacientes LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE
  paciente public.pacientes;
  usuario uuid := auth.uid();
  unidade uuid := public.minha_unidade();
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN NULL; END IF;
  IF EXISTS (
    SELECT 1 FROM public.vinculos AS v
    WHERE v.paciente_id=p_paciente AND v.unidade_id=unidade
      AND v.desde <= CURRENT_DATE AND (v.ate IS NULL OR v.ate > CURRENT_DATE)
  ) THEN
    SELECT p.* INTO paciente FROM public.pacientes AS p WHERE p.id=p_paciente;
    IF FOUND THEN
      INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
        VALUES(usuario,unidade,p_paciente,'abrir_prontuario');
      RETURN paciente;
    END IF;
  END IF;
  IF EXISTS (SELECT 1 FROM public.pacientes AS p WHERE p.id=p_paciente) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,p_paciente,'acesso_negado');
  ELSE
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
  END IF;
  RETURN NULL;
END
$$;
REVOKE ALL ON FUNCTION public.abrir_prontuario(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.abrir_prontuario(uuid) TO authenticated;

CREATE FUNCTION public.buscar_cid10(p_texto text, p_limite int DEFAULT 20)
RETURNS TABLE(codigo text, descricao text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = ''
AS $$
  SELECT c.codigo, c.descricao
  FROM public.cid10 AS c
  WHERE auth.uid() IS NOT NULL AND (
    c.codigo ILIKE COALESCE(p_texto, '') || '%'
    OR translate(lower(c.descricao), 'áàâãäéèêëíìîïóòôõöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')
       ILIKE '%' || translate(lower(COALESCE(p_texto, '')), 'áàâãäéèêëíìîïóòôöõúùûüç', 'aaaaaeeeeiiiiooooouuuuc') || '%'
  )
  ORDER BY c.codigo LIMIT GREATEST(0, LEAST(COALESCE(p_limite,20),100))
$$;

CREATE FUNCTION public.registrar_achado(
  p_paciente uuid, p_ancora jsonb, p_cid10 text, p_categoria public.categoria_achado,
  p_lado public.lado_achado, p_status public.status_achado, p_inicio date,
  p_observacao text, p_substitui uuid DEFAULT NULL
)
RETURNS uuid LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE
  usuario uuid := auth.uid();
  unidade uuid := public.minha_unidade();
  esp text;
  sigilo public.nivel_sigilo := 'normal';
  novo uuid;
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN
    RAISE EXCEPTION 'Perfil ausente' USING ERRCODE = '42501';
  END IF;
  SELECT p.especialidade INTO esp FROM public.perfis AS p WHERE p.id = usuario;
  IF NOT EXISTS (
    SELECT 1 FROM public.vinculos AS v WHERE v.paciente_id=p_paciente AND v.unidade_id=unidade
      AND v.desde <= CURRENT_DATE AND (v.ate IS NULL OR v.ate > CURRENT_DATE)
  ) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN NULL;
  END IF;
  IF p_ancora IS NOT NULL THEN
    IF jsonb_typeof(p_ancora) <> 'object' OR NULLIF(p_ancora->>'atlas','') IS NULL
      OR NULLIF(p_ancora->>'atlas_versao','') IS NULL OR NULLIF(p_ancora->>'sistema','') IS NULL
      OR NULLIF(p_ancora->>'malha','') IS NULL THEN
      RAISE EXCEPTION 'Âncora incompleta' USING ERRCODE = '22023';
    END IF;
    IF p_ancora ? 'lateralidade' AND (
      (p_ancora->>'lateralidade'='left' AND p_lado NOT IN ('esquerdo','bilateral')) OR
      (p_ancora->>'lateralidade'='right' AND p_lado NOT IN ('direito','bilateral')) OR
      (p_ancora->>'lateralidade' IS NULL AND p_lado IN ('esquerdo','direito','bilateral'))
    ) THEN RAISE EXCEPTION 'Lado incompatível com âncora' USING ERRCODE = '22023'; END IF;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.cid10 AS c WHERE c.codigo=p_cid10) THEN
    RAISE EXCEPTION 'CID-10 inexistente' USING ERRCODE = '22023';
  END IF;
  SELECT 'restrito'::public.nivel_sigilo INTO sigilo FROM public.cid10_sigilo AS s
    WHERE p_cid10 LIKE s.prefixo || '%' ORDER BY length(s.prefixo) DESC LIMIT 1;
  sigilo := COALESCE(sigilo,'normal'::public.nivel_sigilo);
  IF p_substitui IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM public.achados AS a WHERE a.id=p_substitui AND a.paciente_id=p_paciente
      AND a.unidade_id=unidade
  ) THEN RAISE EXCEPTION 'Achado substituído inexistente ou indisponível' USING ERRCODE = '42501'; END IF;
  INSERT INTO public.achados(paciente_id,autor_id,unidade_id,especialidade,ancora,cid10,categoria,lado,status,
    nivel_sigilo,inicio,observacao,substitui_id)
  VALUES(p_paciente,usuario,unidade,esp,p_ancora,p_cid10,p_categoria,p_lado,p_status,
    sigilo,p_inicio,p_observacao,p_substitui) RETURNING id INTO novo;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
  VALUES(usuario,unidade,p_paciente,'registrar_achado');
  RETURN novo;
END
$$;

CREATE FUNCTION public.listar_achados(p_paciente uuid)
RETURNS TABLE(
  id uuid, ancora jsonb, estrutura text, cid10 text, cid10_descricao text,
  categoria public.categoria_achado, lado public.lado_achado, status public.status_achado,
  nivel_sigilo public.nivel_sigilo, inicio date, observacao text, especialidade text,
  autor_nome text, unidade_nome text, substitui_id uuid, criado_em timestamptz
) LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade();
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN; END IF;
  IF NOT EXISTS (SELECT 1 FROM public.vinculos AS v WHERE v.paciente_id=p_paciente AND v.unidade_id=unidade
    AND v.desde <= CURRENT_DATE AND (v.ate IS NULL OR v.ate > CURRENT_DATE)) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN;
  END IF;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
    VALUES(usuario,unidade,p_paciente,'listar_achados');
  RETURN QUERY SELECT a.id,a.ancora,a.estrutura,a.cid10,c.descricao,a.categoria,a.lado,a.status,
      a.nivel_sigilo,a.inicio,a.observacao,a.especialidade,p.nome,u.nome,a.substitui_id,a.criado_em
    FROM public.achados AS a
    JOIN public.cid10 AS c ON c.codigo=a.cid10
    JOIN public.perfis AS p ON p.id=a.autor_id
    JOIN public.unidades AS u ON u.id=a.unidade_id
    WHERE a.paciente_id=p_paciente
      AND (a.nivel_sigilo='normal' OR a.unidade_id=unidade)
      AND NOT EXISTS (SELECT 1 FROM public.achados AS prox WHERE prox.substitui_id=a.id)
    ORDER BY a.criado_em,a.id;
END
$$;

CREATE FUNCTION public.historico_achado(p_achado uuid)
RETURNS TABLE(
  id uuid, ancora jsonb, estrutura text, cid10 text, cid10_descricao text,
  categoria public.categoria_achado, lado public.lado_achado, status public.status_achado,
  nivel_sigilo public.nivel_sigilo, inicio date, observacao text, especialidade text,
  autor_nome text, unidade_nome text, substitui_id uuid, criado_em timestamptz
) LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); paciente uuid;
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN; END IF;
  SELECT a.paciente_id INTO paciente FROM public.achados AS a WHERE a.id=p_achado;
  IF paciente IS NULL OR NOT EXISTS (SELECT 1 FROM public.vinculos AS v WHERE v.paciente_id=paciente AND v.unidade_id=unidade
    AND v.desde <= CURRENT_DATE AND (v.ate IS NULL OR v.ate > CURRENT_DATE)) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.achados AS a WHERE a.id=p_achado
    AND (a.nivel_sigilo='normal' OR a.unidade_id=unidade)) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN;
  END IF;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
    VALUES(usuario,unidade,paciente,'historico_achado');
  RETURN QUERY
  WITH RECURSIVE anteriores(id,ordem) AS (
    SELECT p_achado,0
    UNION ALL
    SELECT a.substitui_id,c.ordem-1 FROM public.achados AS a JOIN anteriores AS c ON a.id=c.id
      WHERE a.substitui_id IS NOT NULL
  ), cadeia(id,ordem) AS (
    SELECT ant.id,ant.ordem FROM anteriores AS ant
    UNION ALL
    SELECT prox.id,c.ordem+1 FROM public.achados AS prox JOIN cadeia AS c ON prox.substitui_id=c.id
  )
  SELECT a.id,a.ancora,a.estrutura,a.cid10,cid.descricao,a.categoria,a.lado,a.status,
      a.nivel_sigilo,a.inicio,a.observacao,a.especialidade,p.nome,u.nome,a.substitui_id,a.criado_em
  FROM public.achados AS a
  JOIN public.cid10 AS cid ON cid.codigo=a.cid10
  JOIN public.perfis AS p ON p.id=a.autor_id
  JOIN public.unidades AS u ON u.id=a.unidade_id
  JOIN (
    SELECT c.id,min(c.ordem) AS ordem FROM cadeia AS c GROUP BY c.id
  ) AS c ON c.id=a.id
    WHERE a.paciente_id=paciente AND (a.nivel_sigilo='normal' OR a.unidade_id=unidade)
    ORDER BY c.ordem;
END
$$;

REVOKE ALL ON FUNCTION public.buscar_cid10(text,int),
  public.registrar_achado(uuid,jsonb,text,public.categoria_achado,public.lado_achado,public.status_achado,date,text,uuid),
  public.listar_achados(uuid), public.historico_achado(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.buscar_cid10(text,int),
  public.registrar_achado(uuid,jsonb,text,public.categoria_achado,public.lado_achado,public.status_achado,date,text,uuid),
  public.listar_achados(uuid), public.historico_achado(uuid) TO authenticated;
