-- Última atividade da sessão Auth, atualizada exclusivamente pelo servidor confiável.
CREATE TABLE public.sessoes_atividade (
  sessao_id uuid PRIMARY KEY REFERENCES auth.sessions(id) ON DELETE CASCADE,
  usuario_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  ultima_atividade timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.sessoes_atividade ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.sessoes_atividade FROM PUBLIC, anon, authenticated, service_role;

CREATE FUNCTION public.registrar_atividade_sessao(p_sessao uuid,p_usuario uuid)
RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE registrada boolean;
BEGIN
  IF p_sessao IS NULL OR p_usuario IS NULL OR NOT EXISTS (
    SELECT 1 FROM auth.sessions AS s WHERE s.id=p_sessao AND s.user_id=p_usuario
      AND (s.not_after IS NULL OR s.not_after>now())
  ) THEN RETURN false; END IF;
  IF EXISTS (
    SELECT 1 FROM public.sessoes_atividade AS a WHERE a.sessao_id=p_sessao
      AND a.ultima_atividade<=now()-interval '32 minutes'
  ) THEN RETURN false; END IF;
  INSERT INTO public.sessoes_atividade(sessao_id,usuario_id,ultima_atividade)
    VALUES(p_sessao,p_usuario,now())
    ON CONFLICT(sessao_id) DO UPDATE SET ultima_atividade=EXCLUDED.ultima_atividade
      WHERE public.sessoes_atividade.usuario_id=EXCLUDED.usuario_id
        AND public.sessoes_atividade.ultima_atividade>now()-interval '32 minutes'
    RETURNING true INTO registrada;
  RETURN COALESCE(registrada,false);
END
$$;
REVOKE ALL ON FUNCTION public.registrar_atividade_sessao(uuid,uuid) FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA public TO service_role;
GRANT EXECUTE ON FUNCTION public.registrar_atividade_sessao(uuid,uuid) TO service_role;

CREATE FUNCTION public.sessao_ativa()
RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = ''
AS $$
DECLARE sessao uuid; usuario uuid;
BEGIN
  BEGIN
    sessao:=NULLIF(auth.jwt()->>'session_id','')::uuid;
    usuario:=auth.uid();
  EXCEPTION WHEN OTHERS THEN
    RETURN false;
  END;
  IF sessao IS NULL OR usuario IS NULL THEN RETURN false; END IF;
  RETURN EXISTS (
    SELECT 1 FROM public.sessoes_atividade AS a WHERE a.sessao_id=sessao
      AND a.usuario_id=usuario AND a.ultima_atividade>now()-interval '32 minutes'
  );
END
$$;
REVOKE ALL ON FUNCTION public.sessao_ativa() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.sessao_ativa() TO authenticated, service_role;

CREATE OR REPLACE FUNCTION public.minha_unidade()
RETURNS uuid LANGUAGE sql STABLE SECURITY DEFINER SET search_path = ''
AS $$
  SELECT p.unidade_id FROM public.perfis AS p
  WHERE public.sessao_ativa() AND p.id=auth.uid()
$$;

CREATE OR REPLACE FUNCTION public.eh_admin()
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = ''
AS $$
  SELECT CASE WHEN public.sessao_ativa() THEN COALESCE((
    SELECT p.papel='admin'::public.papel FROM public.perfis AS p WHERE p.id=auth.uid()
  ),false) ELSE false END
$$;

-- Policies de unidade já passam por minha_unidade/eh_admin. A policy de perfil também
-- permitia leitura do próprio perfil diretamente por auth.uid(), sem checar atividade.
ALTER POLICY unidades_leitura_unidade ON public.unidades
  USING (id=(SELECT public.minha_unidade()));
ALTER POLICY perfis_leitura_proprios_ou_unidade ON public.perfis
  USING ((SELECT public.sessao_ativa()) AND
    (id=(SELECT auth.uid()) OR unidade_id=(SELECT public.minha_unidade())));
ALTER POLICY perfis_admin_altera_unidade ON public.perfis
  USING ((SELECT public.sessao_ativa()) AND (SELECT public.eh_admin())
    AND unidade_id=(SELECT public.minha_unidade()) AND id<>(SELECT auth.uid()))
  WITH CHECK ((SELECT public.sessao_ativa()) AND (SELECT public.eh_admin())
    AND unidade_id=(SELECT public.minha_unidade()));
ALTER POLICY auditoria_admin_leitura_unidade ON public.auditoria
  USING ((SELECT public.sessao_ativa()) AND (SELECT public.eh_admin())
    AND unidade_id=(SELECT public.minha_unidade()));

-- Auditoria 0001–0008:
-- abrir_prontuario, cadastrar_paciente, vincular_paciente, encerrar_vinculo,
-- registrar_achado, listar_achados, historico_achado, RPCs de gestação e FHIR, e
-- funções substituídas em 0008 obtêm a unidade por minha_unidade() ou autorização
-- administrativa por eh_admin(); ambos agora exigem sessao_ativa().
-- buscar_pacientes também filtra pelo retorno de minha_unidade().
-- buscar_cid10 e SELECT em cid10, bodysite_estrutura e atlas_malhas são referências
-- não pessoais e permanecem disponíveis a authenticated, conforme o contrato.
-- a função de trigger calcular_sigilo_condicao_gestacao não lê nem grava por sessão.
