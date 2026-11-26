INSERT INTO public.cid10_sigilo (prefixo, motivo) VALUES ('O98.7', 'HIV na gestação')
ON CONFLICT (prefixo) DO UPDATE SET motivo = EXCLUDED.motivo;
INSERT INTO public.cid10 (codigo, descricao) VALUES ('O98.7', 'Doença pelo HIV complicando a gravidez, o parto e o puerpério')
ON CONFLICT (codigo) DO NOTHING;

CREATE TABLE public.gestacoes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mae_id uuid NOT NULL REFERENCES public.pacientes(id),
  dum date NOT NULL,
  dpp date GENERATED ALWAYS AS (dum + 280) STORED,
  inicio_pre_natal date,
  desfecho text NOT NULL DEFAULT 'em_curso'
    CHECK (desfecho IN ('nascido_vivo','obito_fetal','aborto','em_curso')),
  autor_id uuid NOT NULL REFERENCES public.perfis(id),
  unidade_id uuid NOT NULL REFERENCES public.unidades(id),
  criado_em timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX gestacoes_uma_em_curso_por_mae_idx
  ON public.gestacoes(mae_id) WHERE desfecho = 'em_curso';

CREATE TABLE public.condicoes_gestacao (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  gestacao_id uuid NOT NULL REFERENCES public.gestacoes(id),
  cid10 text NOT NULL REFERENCES public.cid10(codigo),
  semana int NOT NULL CHECK (semana BETWEEN 0 AND 45),
  nivel_sigilo public.nivel_sigilo NOT NULL DEFAULT 'normal',
  autor_id uuid NOT NULL REFERENCES public.perfis(id),
  unidade_id uuid NOT NULL REFERENCES public.unidades(id),
  criado_em timestamptz NOT NULL DEFAULT now()
);

CREATE FUNCTION public.calcular_sigilo_condicao_gestacao()
RETURNS trigger LANGUAGE plpgsql SET search_path = ''
AS $$
BEGIN
  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM public.cid10_sigilo AS s WHERE NEW.cid10 LIKE s.prefixo || '%'
  ) THEN 'restrito'::public.nivel_sigilo ELSE 'normal'::public.nivel_sigilo END
  INTO NEW.nivel_sigilo;
  RETURN NEW;
END
$$;
CREATE TRIGGER condicoes_gestacao_sigilo
  BEFORE INSERT OR UPDATE OF cid10 ON public.condicoes_gestacao
  FOR EACH ROW EXECUTE FUNCTION public.calcular_sigilo_condicao_gestacao();

CREATE TABLE public.nascimentos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  gestacao_id uuid NOT NULL REFERENCES public.gestacoes(id),
  crianca_id uuid NOT NULL UNIQUE REFERENCES public.pacientes(id),
  data date NOT NULL,
  peso_g int NOT NULL CHECK (peso_g > 0),
  idade_gestacional_sem int NOT NULL CHECK (idade_gestacional_sem BETWEEN 0 AND 45),
  apgar_5 int NOT NULL CHECK (apgar_5 BETWEEN 0 AND 10),
  autor_id uuid NOT NULL REFERENCES public.perfis(id),
  unidade_id uuid NOT NULL REFERENCES public.unidades(id),
  criado_em timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.gestacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.condicoes_gestacao ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nascimentos ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.gestacoes, public.condicoes_gestacao, public.nascimentos FROM PUBLIC, anon, authenticated;

CREATE FUNCTION public.registrar_gestacao(p_mae uuid, p_dum date, p_inicio_pre_natal date)
RETURNS uuid LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); novo uuid;
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN NULL; END IF;
  IF NOT EXISTS (SELECT 1 FROM public.vinculos AS v JOIN public.pacientes AS p ON p.id=v.paciente_id
    WHERE v.paciente_id=p_mae AND v.unidade_id=unidade AND p.sexo='feminino'
      AND v.desde<=CURRENT_DATE AND (v.ate IS NULL OR v.ate>CURRENT_DATE)) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN NULL;
  END IF;
  INSERT INTO public.gestacoes(mae_id,dum,inicio_pre_natal,autor_id,unidade_id)
    VALUES(p_mae,p_dum,p_inicio_pre_natal,usuario,unidade) RETURNING id INTO novo;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,p_mae,'registrar_gestacao');
  RETURN novo;
END
$$;

CREATE FUNCTION public.registrar_condicao_gestacao(p_gestacao uuid, p_cid10 text, p_semana int)
RETURNS uuid LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); mae uuid; novo uuid;
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN NULL; END IF;
  SELECT g.mae_id INTO mae FROM public.gestacoes AS g JOIN public.vinculos AS v ON v.paciente_id=g.mae_id
    WHERE g.id=p_gestacao AND v.unidade_id=unidade AND v.desde<=CURRENT_DATE
      AND (v.ate IS NULL OR v.ate>CURRENT_DATE);
  IF mae IS NULL THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,NULL,'acesso_negado');
    RETURN NULL;
  END IF;
  IF p_semana NOT BETWEEN 0 AND 45 OR NOT EXISTS(SELECT 1 FROM public.cid10 AS c WHERE c.codigo=p_cid10) THEN
    RAISE EXCEPTION 'Condição gestacional inválida' USING ERRCODE='22023';
  END IF;
  INSERT INTO public.condicoes_gestacao(gestacao_id,cid10,semana,autor_id,unidade_id)
    VALUES(p_gestacao,p_cid10,p_semana,usuario,unidade) RETURNING id INTO novo;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,mae,'registrar_condicao_gestacao');
  RETURN novo;
END
$$;

CREATE FUNCTION public.encerrar_gestacao(p_gestacao uuid, p_desfecho text)
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); mae uuid; desfecho_atual text;
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN; END IF;
  SELECT g.mae_id,g.desfecho INTO mae,desfecho_atual FROM public.gestacoes AS g
    JOIN public.vinculos AS v ON v.paciente_id=g.mae_id
    WHERE g.id=p_gestacao AND v.unidade_id=unidade AND v.desde<=CURRENT_DATE
      AND (v.ate IS NULL OR v.ate>CURRENT_DATE);
  IF mae IS NULL THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,NULL,'acesso_negado'); RETURN;
  END IF;
  IF desfecho_atual <> 'em_curso' THEN RAISE EXCEPTION 'Gestação já encerrada' USING ERRCODE='22023'; END IF;
  IF p_desfecho IS NULL OR p_desfecho NOT IN ('obito_fetal','aborto') THEN
    RAISE EXCEPTION 'Desfecho deve ser obito_fetal ou aborto' USING ERRCODE='22023';
  END IF;
  UPDATE public.gestacoes AS g SET desfecho=p_desfecho WHERE g.id=p_gestacao;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,mae,'encerrar_gestacao');
END
$$;

CREATE FUNCTION public.registrar_nascimento(
  p_gestacao uuid, p_nome text, p_sexo public.sexo, p_data date, p_peso_g int,
  p_idade_gestacional_sem int, p_apgar_5 int
)
RETURNS uuid LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade(); mae uuid; filho uuid; dum date; desfecho_atual text;
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN NULL; END IF;
  SELECT g.mae_id,g.dum,g.desfecho INTO mae,dum,desfecho_atual
    FROM public.gestacoes AS g JOIN public.vinculos AS v ON v.paciente_id=g.mae_id
    WHERE g.id=p_gestacao AND v.unidade_id=unidade AND v.desde<=CURRENT_DATE
      AND (v.ate IS NULL OR v.ate>CURRENT_DATE);
  IF mae IS NULL THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,NULL,'acesso_negado'); RETURN NULL;
  END IF;
  IF desfecho_atual NOT IN ('em_curso','nascido_vivo') THEN
    RAISE EXCEPTION 'Gestação encerrada sem nascido vivo' USING ERRCODE='22023';
  END IF;
  IF p_data IS NULL OR p_data<dum OR p_data>CURRENT_DATE THEN
    RAISE EXCEPTION 'Data do nascimento fora do período gestacional' USING ERRCODE='22023';
  END IF;
  INSERT INTO public.pacientes(nome,sexo,data_nascimento)
    VALUES(p_nome,p_sexo,p_data) RETURNING id INTO filho;
  INSERT INTO public.nascimentos(gestacao_id,crianca_id,data,peso_g,idade_gestacional_sem,apgar_5,autor_id,unidade_id)
    VALUES(p_gestacao,filho,p_data,p_peso_g,p_idade_gestacional_sem,p_apgar_5,usuario,unidade);
  UPDATE public.gestacoes AS g SET desfecho='nascido_vivo' WHERE g.id=p_gestacao
    AND g.desfecho='em_curso';
  INSERT INTO public.vinculos(paciente_id,unidade_id,motivo,origem,criado_por,desde)
    VALUES(filho,unidade,'nascimento','atendimento',usuario,p_data);
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao)
    VALUES(usuario,unidade,mae,'registrar_nascimento'),(usuario,unidade,filho,'registrar_nascimento');
  RETURN filho;
END
$$;

CREATE FUNCTION public.listar_gestacoes(p_mae uuid)
  RETURNS TABLE(gestacao_id uuid,dum date,dpp date,inicio_pre_natal date,desfecho text,condicoes jsonb,nascimentos jsonb)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade();
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN; END IF;
  IF NOT EXISTS(SELECT 1 FROM public.vinculos AS v WHERE v.paciente_id=p_mae AND v.unidade_id=unidade
    AND v.desde<=CURRENT_DATE AND (v.ate IS NULL OR v.ate>CURRENT_DATE)) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,NULL,'acesso_negado'); RETURN;
  END IF;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,p_mae,'listar_gestacoes');
  RETURN QUERY SELECT g.id,g.dum,g.dpp,g.inicio_pre_natal,g.desfecho,
    COALESCE((SELECT jsonb_agg(jsonb_build_object('cid10',c.cid10,'cid10_descricao',cidc.descricao,
      'semana',c.semana,'nivel_sigilo',c.nivel_sigilo)
      ORDER BY c.semana) FROM public.condicoes_gestacao AS c
        JOIN public.cid10 AS cidc ON cidc.codigo=c.cid10
      WHERE c.gestacao_id=g.id AND (c.nivel_sigilo='normal' OR c.unidade_id=unidade)),'[]'::jsonb),
    COALESCE((SELECT jsonb_agg(jsonb_build_object('crianca_id',n.crianca_id,'crianca_nome',p.nome,
      'data',n.data,'peso_g',n.peso_g) ORDER BY n.data)
      FROM public.nascimentos AS n JOIN public.pacientes AS p ON p.id=n.crianca_id WHERE n.gestacao_id=g.id),'[]'::jsonb)
    FROM public.gestacoes AS g WHERE g.mae_id=p_mae ORDER BY g.dum;
END
$$;

CREATE FUNCTION public.historico_gestacional_crianca(p_crianca uuid)
RETURNS TABLE(nome_mae text,mae_id uuid,cid10 text,cid10_descricao text,semana int,idade_gestacional_sem int,peso_g int,apgar_5 int,data date)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE usuario uuid := auth.uid(); unidade uuid := public.minha_unidade();
BEGIN
  IF usuario IS NULL OR unidade IS NULL THEN RETURN; END IF;
  IF NOT EXISTS(SELECT 1 FROM public.vinculos AS v WHERE v.paciente_id=p_crianca AND v.unidade_id=unidade
    AND v.desde<=CURRENT_DATE AND (v.ate IS NULL OR v.ate>CURRENT_DATE)) THEN
    INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,NULL,'acesso_negado'); RETURN;
  END IF;
  INSERT INTO public.auditoria(autor_id,unidade_id,paciente_id,acao) VALUES(usuario,unidade,p_crianca,'historico_gestacional_crianca');
  RETURN QUERY SELECT mae.nome,mae.id,c.cid10,cid.descricao,c.semana,n.idade_gestacional_sem,n.peso_g,n.apgar_5,n.data
    FROM public.nascimentos AS n JOIN public.gestacoes AS g ON g.id=n.gestacao_id
    JOIN public.pacientes AS mae ON mae.id=g.mae_id
    LEFT JOIN public.condicoes_gestacao AS c ON c.gestacao_id=g.id
      AND (c.nivel_sigilo='normal' OR c.unidade_id=unidade)
    LEFT JOIN public.cid10 AS cid ON cid.codigo=c.cid10
    WHERE n.crianca_id=p_crianca ORDER BY c.semana NULLS LAST;
END
$$;

DROP FUNCTION public.listar_achados(uuid);
CREATE FUNCTION public.listar_achados(p_paciente uuid)
RETURNS TABLE(
  id uuid, ancora jsonb, estrutura text, cid10 text, cid10_descricao text,
  categoria public.categoria_achado, lado public.lado_achado, status public.status_achado,
  nivel_sigilo public.nivel_sigilo, inicio date, observacao text, especialidade text,
  autor_nome text, unidade_nome text, unidade_id uuid, substitui_id uuid, criado_em timestamptz
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
    a.inicio,a.observacao,a.especialidade,p.nome,u.nome,a.unidade_id,a.substitui_id,a.criado_em
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
  autor_nome text, unidade_nome text, unidade_id uuid, substitui_id uuid, criado_em timestamptz
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
    a.inicio,a.observacao,a.especialidade,p.nome,u.nome,a.unidade_id,a.substitui_id,a.criado_em
    FROM public.achados AS a JOIN public.cid10 AS cid ON cid.codigo=a.cid10
    JOIN public.perfis AS p ON p.id=a.autor_id JOIN public.unidades AS u ON u.id=a.unidade_id
    JOIN (SELECT c.id,min(c.ordem) AS ordem FROM cadeia AS c GROUP BY c.id) AS ch ON ch.id=a.id
    WHERE a.paciente_id=paciente AND (a.nivel_sigilo='normal' OR a.unidade_id=unidade) ORDER BY ch.ordem;
END
$$;

REVOKE ALL ON FUNCTION public.calcular_sigilo_condicao_gestacao() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.registrar_gestacao(uuid,date,date),
  public.registrar_condicao_gestacao(uuid,text,int), public.encerrar_gestacao(uuid,text),
  public.registrar_nascimento(uuid,text,public.sexo,date,int,int,int),
  public.listar_gestacoes(uuid), public.historico_gestacional_crianca(uuid),
  public.listar_achados(uuid), public.historico_achado(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.registrar_gestacao(uuid,date,date),
  public.registrar_condicao_gestacao(uuid,text,int), public.encerrar_gestacao(uuid,text),
  public.registrar_nascimento(uuid,text,public.sexo,date,int,int,int),
  public.listar_gestacoes(uuid), public.historico_gestacional_crianca(uuid),
  public.listar_achados(uuid), public.historico_achado(uuid) TO authenticated;
