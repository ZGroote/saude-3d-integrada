CREATE TYPE public.papel AS ENUM ('profissional', 'admin');
CREATE TYPE public.origem_vinculo AS ENUM ('atendimento', 'encaminhamento', 'importacao');
CREATE TYPE public.sexo AS ENUM ('feminino', 'masculino', 'indeterminado');

CREATE TABLE public.unidades (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nome text NOT NULL,
  cnes text UNIQUE,
  municipio_ibge text
);

CREATE TABLE public.perfis (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  nome text NOT NULL,
  unidade_id uuid NOT NULL REFERENCES public.unidades(id),
  especialidade text,
  papel public.papel NOT NULL DEFAULT 'profissional'
);

CREATE TABLE public.pacientes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nome text NOT NULL,
  cns text UNIQUE,
  cpf_hash text UNIQUE,
  sexo public.sexo NOT NULL DEFAULT 'indeterminado',
  data_nascimento date,
  municipio_ibge text
);

CREATE TABLE public.vinculos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  paciente_id uuid NOT NULL REFERENCES public.pacientes(id),
  unidade_id uuid NOT NULL REFERENCES public.unidades(id),
  motivo text NOT NULL,
  origem public.origem_vinculo NOT NULL,
  criado_por uuid NOT NULL REFERENCES public.perfis(id),
  desde date NOT NULL,
  ate date,
  UNIQUE (paciente_id, unidade_id, desde)
);

CREATE TABLE public.auditoria (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  autor_id uuid NOT NULL REFERENCES public.perfis(id),
  unidade_id uuid NOT NULL REFERENCES public.unidades(id),
  paciente_id uuid NOT NULL REFERENCES public.pacientes(id),
  acao text NOT NULL,
  criado_em timestamptz NOT NULL DEFAULT now()
);

CREATE FUNCTION public.minha_unidade()
RETURNS uuid LANGUAGE sql STABLE SECURITY DEFINER SET search_path = ''
AS $$
  SELECT p.unidade_id FROM public.perfis AS p WHERE p.id = auth.uid()
$$;

CREATE FUNCTION public.eh_admin()
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = ''
AS $$
  SELECT COALESCE((SELECT p.papel = 'admin'::public.papel
                   FROM public.perfis AS p WHERE p.id = auth.uid()), false)
$$;

CREATE FUNCTION public.abrir_prontuario(p_paciente uuid)
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
    WHERE v.paciente_id = p_paciente AND v.unidade_id = unidade
      AND v.desde <= CURRENT_DATE
      AND (v.ate IS NULL OR v.ate > CURRENT_DATE)
  ) THEN
    SELECT p.* INTO paciente FROM public.pacientes AS p WHERE p.id = p_paciente;
    IF FOUND THEN
      INSERT INTO public.auditoria (autor_id, unidade_id, paciente_id, acao)
      VALUES (usuario, unidade, p_paciente, 'abrir_prontuario');
      RETURN paciente;
    END IF;
  END IF;
  IF EXISTS (SELECT 1 FROM public.pacientes AS p WHERE p.id = p_paciente) THEN
    INSERT INTO public.auditoria (autor_id, unidade_id, paciente_id, acao)
    VALUES (usuario, unidade, p_paciente, 'acesso_negado');
  END IF;
  RETURN NULL;
END
$$;

CREATE FUNCTION public.buscar_pacientes(p_texto text DEFAULT NULL)
RETURNS TABLE (id uuid, nome text, sexo public.sexo, data_nascimento date, cns_final text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = ''
AS $$
  SELECT p.id, p.nome, p.sexo, p.data_nascimento,
         CASE WHEN p.cns IS NULL THEN NULL ELSE right(p.cns, 4) END
  FROM public.pacientes AS p
  WHERE EXISTS (
    SELECT 1 FROM public.vinculos AS v
    WHERE v.paciente_id = p.id AND v.unidade_id = public.minha_unidade()
      AND v.desde <= CURRENT_DATE
      AND (v.ate IS NULL OR v.ate > CURRENT_DATE)
  )
    AND (NULLIF(btrim(p_texto), '') IS NULL
         OR p.nome ILIKE '%' || btrim(p_texto) || '%'
         OR p.cns = btrim(p_texto))
$$;

CREATE FUNCTION public.cadastrar_paciente(
  p_nome text, p_cns text, p_sexo public.sexo, p_data_nascimento date,
  p_motivo text, p_origem public.origem_vinculo
)
RETURNS uuid LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE
  usuario uuid := auth.uid();
  unidade uuid := public.minha_unidade();
  v_paciente_id uuid;
  acao text;
BEGIN
  IF NOT public.eh_admin() THEN RAISE EXCEPTION 'Apenas admin' USING ERRCODE = '42501'; END IF;
  p_cns := NULLIF(btrim(p_cns), '');
  IF p_cns IS NOT NULL THEN
    SELECT p.id INTO v_paciente_id FROM public.pacientes AS p WHERE p.cns = p_cns;
  END IF;
  IF v_paciente_id IS NULL THEN
    INSERT INTO public.pacientes (nome, cns, sexo, data_nascimento)
    VALUES (p_nome, p_cns, p_sexo, p_data_nascimento) RETURNING id INTO v_paciente_id;
    acao := 'cadastrar_paciente';
  ELSE
    acao := 'criar_vinculo';
  END IF;
  INSERT INTO public.vinculos (paciente_id, unidade_id, motivo, origem, criado_por, desde)
  VALUES (v_paciente_id, unidade, p_motivo, p_origem, usuario, CURRENT_DATE)
  ON CONFLICT (paciente_id, unidade_id, desde)
  DO UPDATE SET motivo = EXCLUDED.motivo,
                origem = EXCLUDED.origem,
                criado_por = EXCLUDED.criado_por,
                ate = NULL;
  INSERT INTO public.auditoria (autor_id, unidade_id, paciente_id, acao)
  VALUES (usuario, unidade, v_paciente_id, acao);
  RETURN v_paciente_id;
END
$$;

CREATE FUNCTION public.vincular_paciente(
  p_paciente uuid, p_motivo text, p_origem public.origem_vinculo
)
RETURNS uuid LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE
  usuario uuid := auth.uid();
  unidade uuid := public.minha_unidade();
  vinculo_id uuid;
BEGIN
  IF NOT public.eh_admin() THEN RAISE EXCEPTION 'Apenas admin' USING ERRCODE = '42501'; END IF;
  INSERT INTO public.vinculos (paciente_id, unidade_id, motivo, origem, criado_por, desde)
  VALUES (p_paciente, unidade, p_motivo, p_origem, usuario, CURRENT_DATE)
  ON CONFLICT (paciente_id, unidade_id, desde)
  DO UPDATE SET motivo = EXCLUDED.motivo,
                origem = EXCLUDED.origem,
                criado_por = EXCLUDED.criado_por,
                ate = NULL
  RETURNING id INTO vinculo_id;
  INSERT INTO public.auditoria (autor_id, unidade_id, paciente_id, acao)
  VALUES (usuario, unidade, p_paciente, 'criar_vinculo');
  RETURN vinculo_id;
END
$$;

CREATE FUNCTION public.encerrar_vinculo(p_vinculo uuid)
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE
  usuario uuid := auth.uid();
  unidade uuid := public.minha_unidade();
  paciente uuid;
BEGIN
  IF NOT public.eh_admin() THEN RAISE EXCEPTION 'Apenas admin' USING ERRCODE = '42501'; END IF;
  UPDATE public.vinculos AS v SET ate = CURRENT_DATE
  WHERE v.id = p_vinculo AND v.unidade_id = unidade
  RETURNING v.paciente_id INTO paciente;
  IF paciente IS NULL THEN RAISE EXCEPTION 'Vínculo não encontrado nesta unidade' USING ERRCODE = '42501'; END IF;
  INSERT INTO public.auditoria (autor_id, unidade_id, paciente_id, acao)
  VALUES (usuario, unidade, paciente, 'encerrar_vinculo');
END
$$;

ALTER TABLE public.unidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.perfis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pacientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vinculos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auditoria ENABLE ROW LEVEL SECURITY;

CREATE POLICY unidades_leitura_unidade ON public.unidades
  FOR SELECT TO authenticated USING (id = public.minha_unidade());
CREATE POLICY perfis_leitura_proprios_ou_unidade ON public.perfis
  FOR SELECT TO authenticated USING (id = auth.uid() OR unidade_id = public.minha_unidade());
CREATE POLICY perfis_admin_altera_unidade ON public.perfis
  FOR UPDATE TO authenticated USING (
    public.eh_admin() AND unidade_id = public.minha_unidade() AND id <> auth.uid()
  ) WITH CHECK (
    public.eh_admin() AND unidade_id = public.minha_unidade()
  );
CREATE POLICY auditoria_admin_leitura_unidade ON public.auditoria
  FOR SELECT TO authenticated USING (public.eh_admin() AND unidade_id = public.minha_unidade());

REVOKE ALL ON TABLE public.unidades, public.perfis, public.pacientes,
  public.vinculos, public.auditoria FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.unidades TO authenticated;
GRANT SELECT, UPDATE ON public.perfis TO authenticated;
GRANT SELECT ON public.auditoria TO authenticated;

REVOKE ALL ON FUNCTION public.minha_unidade() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.eh_admin() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.abrir_prontuario(uuid) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.buscar_pacientes(text) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.cadastrar_paciente(text, text, public.sexo, date, text, public.origem_vinculo) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.vincular_paciente(uuid, text, public.origem_vinculo) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.encerrar_vinculo(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.minha_unidade(), public.eh_admin(),
  public.abrir_prontuario(uuid), public.buscar_pacientes(text),
  public.cadastrar_paciente(text, text, public.sexo, date, text, public.origem_vinculo),
  public.vincular_paciente(uuid, text, public.origem_vinculo),
  public.encerrar_vinculo(uuid) TO authenticated;
