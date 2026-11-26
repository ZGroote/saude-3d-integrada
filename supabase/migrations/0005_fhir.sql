CREATE UNIQUE INDEX achados_unidade_fhir_id_uidx ON public.achados(unidade_id,fhir_id);

CREATE TABLE public.importacoes_fhir (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  autor_id uuid NOT NULL REFERENCES public.perfis(id),
  unidade_id uuid NOT NULL REFERENCES public.unidades(id),
  arquivo text NOT NULL,
  recursos int NOT NULL CHECK (recursos >= 0),
  importados int NOT NULL DEFAULT 0 CHECK (importados >= 0),
  erros_count int NOT NULL DEFAULT 0 CHECK (erros_count >= 0),
  erros jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(erros)='array'),
  criado_em timestamptz NOT NULL DEFAULT now(),
  concluido_em timestamptz
);

CREATE TABLE public.eventos_clinicos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  paciente_id uuid NOT NULL REFERENCES public.pacientes(id),
  unidade_id uuid NOT NULL REFERENCES public.unidades(id),
  importacao_id uuid NOT NULL REFERENCES public.importacoes_fhir(id),
  fhir_id text NOT NULL,
  origem text NOT NULL DEFAULT 'fhir' CHECK (origem='fhir'),
  tipo text NOT NULL CHECK (tipo IN ('Observation','Encounter')),
  data timestamptz,
  codigo text,
  descricao text,
  valor text,
  criado_em timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX eventos_clinicos_unidade_fhir_id_uidx ON public.eventos_clinicos(unidade_id,fhir_id);
CREATE INDEX eventos_clinicos_paciente_data_idx ON public.eventos_clinicos(paciente_id,data DESC);

CREATE TABLE public.paciente_fhir (
  unidade_id uuid NOT NULL REFERENCES public.unidades(id),
  fhir_id text NOT NULL,
  paciente_id uuid NOT NULL REFERENCES public.pacientes(id),
  criado_em timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (unidade_id,fhir_id)
);
CREATE INDEX paciente_fhir_paciente_idx ON public.paciente_fhir(unidade_id,paciente_id);

CREATE TABLE public.bodysite_estrutura (
  snomed text PRIMARY KEY,
  descricao text NOT NULL,
  estrutura_fma text,
  estrutura_uberon text,
  lado text CHECK (lado IN ('direito','esquerdo')),
  fonte_url text NOT NULL,
  verificado boolean NOT NULL DEFAULT true CHECK (verificado),
  CHECK (estrutura_fma IS NOT NULL OR estrutura_uberon IS NOT NULL)
);
-- CSV verificado=sim pela API oficial; avaliação clínica do uso das âncoras permanece pendente.
INSERT INTO public.bodysite_estrutura(snomed,descricao,estrutura_fma,estrutura_uberon,lado,fonte_url) VALUES
  -- validação médica pendente: escolha da malha representante (ex.: lobo caudado).
  ('80891009','Heart structure','FMA13884','UBERON:0002084',NULL,'https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/80891009'),
  ('10200004','Liver structure','FMA13365','UBERON:0001106',NULL,'https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/10200004'),
  ('3341006','Right lung structure','FMA68211','UBERON:0004888','direito','https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/3341006'),
  ('44029006','Left lung structure','FMA68223','UBERON:0004887','esquerdo','https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/44029006'),
  ('9846003','Right kidney structure','FMA7204','UBERON:0002189','direito','https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/9846003'),
  ('18639004','Left kidney structure','FMA7205','UBERON:0002189','esquerdo','https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/18639004'),
  ('52612000','Structure of lumbar region of back','FMA13072','UBERON:0004617',NULL,'https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/52612000'),
  ('6757004','Structure of right knee region','FMA24486',NULL,'direito','https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/6757004'),
  ('82169009','Structure of left knee region','FMA24487',NULL,'esquerdo','https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/82169009'),
  ('35039007','Uterine structure',NULL,'UBERON:0009853',NULL,'https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/35039007'),
  ('73056007','Right breast structure',NULL,'UBERON:0018140','direito','https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/73056007'),
  ('80248007','Left breast structure',NULL,'UBERON:0018140','esquerdo','https://snomed.hl7.org.br/snowstorm/snomed-ct/browser/MAIN/concepts/80248007');

ALTER TABLE public.importacoes_fhir ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eventos_clinicos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.paciente_fhir ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bodysite_estrutura ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.importacoes_fhir, public.eventos_clinicos,
  public.paciente_fhir, public.bodysite_estrutura FROM PUBLIC, anon, authenticated;

CREATE FUNCTION public.iniciar_importacao(p_arquivo text, p_recursos int)
RETURNS uuid LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); novo uuid;
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN NULL; END IF;
  IF NOT public.eh_admin() THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN NULL;
  END IF;
  IF p_recursos IS NULL OR p_recursos < 0 OR NULLIF(btrim(p_arquivo),'') IS NULL THEN
    RAISE EXCEPTION 'Metadados de importação inválidos' USING ERRCODE='22023';
  END IF;
  INSERT INTO public.importacoes_fhir(autor_id,unidade_id,arquivo,recursos)
    VALUES(usuario,unidade,p_arquivo,p_recursos) RETURNING id INTO novo;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
    VALUES(usuario,unidade,NULL,'iniciar_importacao');
  RETURN novo;
END
$$;

CREATE FUNCTION public.importar_paciente_fhir(
  p_importacao uuid, p_fhir_id text, p_cns text, p_nome text,
  p_sexo public.sexo, p_nascimento date
)
RETURNS uuid LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); paciente uuid; cns_limpo text;
        paciente_mapeado uuid; cns_mapeado text;
BEGIN
  p_fhir_id := NULLIF(btrim(p_fhir_id),'');
  IF usuario IS NULL OR unidade IS NULL THEN RETURN NULL; END IF;
  IF NOT public.eh_admin() OR NOT EXISTS (
    SELECT 1 FROM public.importacoes_fhir AS i WHERE i.id=p_importacao
      AND i.autor_id=usuario AND i.unidade_id=unidade AND i.concluido_em IS NULL
  ) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN NULL;
  END IF;
  IF p_fhir_id IS NULL OR NULLIF(btrim(p_nome),'') IS NULL THEN
    RAISE EXCEPTION 'Paciente FHIR inválido' USING ERRCODE='22023';
  END IF;
  cns_limpo := NULLIF(btrim(p_cns),'');
  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtext(unidade::text),pg_catalog.hashtext(p_fhir_id));
  SELECT pf.paciente_id,p.cns INTO paciente_mapeado,cns_mapeado
    FROM public.paciente_fhir AS pf JOIN public.pacientes AS p ON p.id=pf.paciente_id
    WHERE pf.unidade_id=unidade AND pf.fhir_id=p_fhir_id;
  IF paciente_mapeado IS NOT NULL AND cns_limpo IS NOT NULL THEN
    IF cns_limpo IS DISTINCT FROM cns_mapeado THEN
      RAISE EXCEPTION 'Recurso Patient inconsistente' USING ERRCODE='22023';
    END IF;
  END IF;
  paciente := paciente_mapeado;
  IF paciente IS NULL AND cns_limpo IS NOT NULL THEN
    SELECT p.id INTO paciente FROM public.pacientes AS p WHERE p.cns=cns_limpo;
  END IF;
  IF paciente IS NULL THEN
    INSERT INTO public.pacientes(nome,cns,sexo,data_nascimento)
      VALUES(btrim(p_nome),cns_limpo,p_sexo,p_nascimento)
      ON CONFLICT DO NOTHING RETURNING id INTO paciente;
    IF paciente IS NULL THEN
      IF cns_limpo IS NOT NULL THEN
        SELECT p.id INTO paciente FROM public.pacientes AS p WHERE p.cns=cns_limpo;
      END IF;
    END IF;
  END IF;
  IF paciente IS NULL THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN NULL;
  END IF;
  INSERT INTO public.paciente_fhir(unidade_id,fhir_id,paciente_id)
    VALUES(unidade,p_fhir_id,paciente) ON CONFLICT(unidade_id,fhir_id) DO NOTHING
    RETURNING paciente_id INTO paciente_mapeado;
  IF paciente_mapeado IS NULL THEN
    SELECT pf.paciente_id INTO paciente_mapeado FROM public.paciente_fhir AS pf
      WHERE pf.unidade_id=unidade AND pf.fhir_id=p_fhir_id;
  END IF;
  IF paciente_mapeado IS NULL THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN NULL;
  END IF;
  IF paciente_mapeado<>paciente THEN
    RAISE EXCEPTION 'Recurso Patient inconsistente' USING ERRCODE='22023';
  END IF;
  INSERT INTO public.vinculos(paciente_id,unidade_id,motivo,origem,criado_por,desde)
    VALUES(paciente,unidade,'Importação FHIR','importacao',usuario,CURRENT_DATE)
    ON CONFLICT(paciente_id,unidade_id,desde) DO UPDATE SET
      motivo=EXCLUDED.motivo, origem=EXCLUDED.origem, criado_por=EXCLUDED.criado_por, ate=NULL;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
    VALUES(usuario,unidade,paciente,'importar_paciente_fhir');
  RETURN paciente;
END
$$;

CREATE FUNCTION public.importar_condicao_fhir(
  p_importacao uuid, p_paciente uuid, p_fhir_id text, p_cid10 text,
  p_ancora jsonb, p_status public.status_achado, p_inicio date
)
RETURNS uuid LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); existente public.achados; novo uuid; sigilo public.nivel_sigilo;
BEGIN
  p_fhir_id := NULLIF(btrim(p_fhir_id),'');
  IF usuario IS NULL OR unidade IS NULL THEN RETURN NULL; END IF;
  IF NOT public.eh_admin() OR NOT EXISTS (
    SELECT 1 FROM public.importacoes_fhir AS i WHERE i.id=p_importacao
      AND i.autor_id=usuario AND i.unidade_id=unidade AND i.concluido_em IS NULL
  ) OR NOT EXISTS (
    SELECT 1 FROM public.vinculos AS v WHERE v.paciente_id=p_paciente AND v.unidade_id=unidade
      AND v.desde<=CURRENT_DATE AND (v.ate IS NULL OR v.ate>CURRENT_DATE)
  ) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN NULL;
  END IF;
  IF p_fhir_id IS NULL THEN
    RAISE EXCEPTION 'Identificador FHIR inválido' USING ERRCODE='22023';
  END IF;
  SELECT a.* INTO existente FROM public.achados AS a
    WHERE a.unidade_id=unidade AND a.origem='fhir' AND a.fhir_id=p_fhir_id;
  IF FOUND THEN
    IF existente.paciente_id=p_paciente THEN
      INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
        VALUES(usuario,unidade,p_paciente,'importar_condicao_fhir');
      RETURN existente.id;
    END IF;
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.cid10 AS c WHERE c.codigo=p_cid10) THEN
    RAISE EXCEPTION 'CID-10 inexistente' USING ERRCODE='22023';
  END IF;
  IF p_ancora IS NOT NULL AND (jsonb_typeof(p_ancora)<>'object'
    OR NULLIF(p_ancora->>'atlas','') IS NULL OR NULLIF(p_ancora->>'atlas_versao','') IS NULL
    OR NULLIF(p_ancora->>'sistema','') IS NULL OR NULLIF(p_ancora->>'malha','') IS NULL) THEN
    RAISE EXCEPTION 'Âncora FHIR inválida' USING ERRCODE='22023';
  END IF;
  SELECT 'restrito'::public.nivel_sigilo INTO sigilo FROM public.cid10_sigilo AS s
    WHERE p_cid10 LIKE s.prefixo || '%' ORDER BY length(s.prefixo) DESC LIMIT 1;
  sigilo := COALESCE(sigilo,'normal'::public.nivel_sigilo);
  INSERT INTO public.achados(paciente_id,autor_id,unidade_id,especialidade,ancora,cid10,categoria,
    lado,status,nivel_sigilo,inicio,origem,fhir_id)
  SELECT p_paciente,usuario,unidade,p.especialidade,p_ancora,p_cid10,'doenca','nao_se_aplica',
    p_status,sigilo,p_inicio,'fhir',p_fhir_id
    FROM public.perfis AS p WHERE p.id=usuario
    ON CONFLICT (unidade_id,fhir_id) DO NOTHING RETURNING id INTO novo;
  IF novo IS NULL THEN
    SELECT a.* INTO existente FROM public.achados AS a
      WHERE a.unidade_id=unidade AND a.origem='fhir' AND a.fhir_id=p_fhir_id;
    IF existente.id IS NULL OR existente.paciente_id<>p_paciente THEN
      INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
        VALUES(usuario,unidade,NULL,'acesso_negado');
      RETURN NULL;
    END IF;
    novo := existente.id;
  END IF;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
    VALUES(usuario,unidade,p_paciente,'importar_condicao_fhir');
  RETURN novo;
END
$$;

CREATE FUNCTION public.importar_evento_fhir(
  p_importacao uuid, p_paciente uuid, p_fhir_id text, p_tipo text,
  p_data timestamptz, p_codigo text, p_descricao text, p_valor text
)
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); existente public.eventos_clinicos;
BEGIN
  p_fhir_id := NULLIF(btrim(p_fhir_id),'');
  IF usuario IS NULL OR unidade IS NULL THEN RETURN; END IF;
  IF NOT public.eh_admin() OR NOT EXISTS (
    SELECT 1 FROM public.importacoes_fhir AS i WHERE i.id=p_importacao
      AND i.autor_id=usuario AND i.unidade_id=unidade AND i.concluido_em IS NULL
  ) OR NOT EXISTS (
    SELECT 1 FROM public.vinculos AS v WHERE v.paciente_id=p_paciente AND v.unidade_id=unidade
      AND v.desde<=CURRENT_DATE AND (v.ate IS NULL OR v.ate>CURRENT_DATE)
  ) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN;
  END IF;
  IF p_fhir_id IS NULL OR p_tipo IS NULL OR p_tipo NOT IN ('Observation','Encounter') THEN
    RAISE EXCEPTION 'Evento FHIR inválido' USING ERRCODE='22023';
  END IF;
  INSERT INTO public.eventos_clinicos(paciente_id,unidade_id,importacao_id,fhir_id,tipo,data,codigo,descricao,valor)
    VALUES(p_paciente,unidade,p_importacao,p_fhir_id,p_tipo,p_data,p_codigo,p_descricao,p_valor)
    ON CONFLICT(unidade_id,fhir_id) DO NOTHING RETURNING * INTO existente;
  IF NOT FOUND THEN
    SELECT e.* INTO existente FROM public.eventos_clinicos AS e
      WHERE e.unidade_id=unidade AND e.fhir_id=p_fhir_id;
  END IF;
  IF existente.id IS NULL OR existente.paciente_id<>p_paciente THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN;
  END IF;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
    VALUES(usuario,unidade,p_paciente,'importar_evento_fhir');
END
$$;

CREATE FUNCTION public.concluir_importacao(p_importacao uuid, p_erros jsonb)
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); quantidade_erros int; erros_seguros jsonb;
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN; END IF;
  IF NOT public.eh_admin() OR NOT EXISTS (
    SELECT 1 FROM public.importacoes_fhir AS i WHERE i.id=p_importacao
      AND i.autor_id=usuario AND i.unidade_id=unidade AND i.concluido_em IS NULL
  ) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN;
  END IF;
  IF p_erros IS NULL OR jsonb_typeof(p_erros)<>'array' THEN
    RAISE EXCEPTION 'Erros devem ser uma lista' USING ERRCODE='22023';
  END IF;
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
      'id',left(COALESCE(item->>'id',''),200),
      'motivo',left(COALESCE(item->>'motivo','Recurso inválido'),500)
    )), '[]'::jsonb), count(*)::int INTO erros_seguros,quantidade_erros
    FROM jsonb_array_elements(p_erros) AS dados(item);
  UPDATE public.importacoes_fhir AS i SET erros=erros_seguros,erros_count=quantidade_erros,
    importados=GREATEST(i.recursos-quantidade_erros,0),concluido_em=now()
    WHERE i.id=p_importacao;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
    VALUES(usuario,unidade,NULL,'concluir_importacao');
END
$$;

CREATE FUNCTION public.listar_eventos(p_paciente uuid)
RETURNS TABLE(id uuid,importacao_id uuid,fhir_id text,tipo text,data timestamptz,codigo text,
  descricao text,valor text,criado_em timestamptz)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade();
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN; END IF;
  IF NOT EXISTS (SELECT 1 FROM public.vinculos AS v WHERE v.paciente_id=p_paciente AND v.unidade_id=unidade
    AND v.desde<=CURRENT_DATE AND (v.ate IS NULL OR v.ate>CURRENT_DATE)) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
      VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN;
  END IF;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
    VALUES(usuario,unidade,p_paciente,'listar_eventos');
  RETURN QUERY SELECT e.id,e.importacao_id,e.fhir_id,e.tipo,e.data,e.codigo,e.descricao,e.valor,e.criado_em
    FROM public.eventos_clinicos AS e WHERE e.paciente_id=p_paciente
      AND e.unidade_id=unidade ORDER BY e.data NULLS LAST,e.criado_em;
END
$$;

REVOKE ALL ON FUNCTION public.iniciar_importacao(text,int),
  public.importar_paciente_fhir(uuid,text,text,text,public.sexo,date),
  public.importar_condicao_fhir(uuid,uuid,text,text,jsonb,public.status_achado,date),
  public.importar_evento_fhir(uuid,uuid,text,text,timestamptz,text,text,text),
  public.concluir_importacao(uuid,jsonb), public.listar_eventos(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.iniciar_importacao(text,int),
  public.importar_paciente_fhir(uuid,text,text,text,public.sexo,date),
  public.importar_condicao_fhir(uuid,uuid,text,text,jsonb,public.status_achado,date),
  public.importar_evento_fhir(uuid,uuid,text,text,timestamptz,text,text,text),
  public.concluir_importacao(uuid,jsonb), public.listar_eventos(uuid) TO authenticated;
