-- Etapa 7: índices de chaves estrangeiras e avaliação única de contexto nas políticas.
CREATE INDEX IF NOT EXISTS perfis_unidade_id_idx ON public.perfis(unidade_id);
CREATE INDEX IF NOT EXISTS vinculos_unidade_id_idx ON public.vinculos(unidade_id);
CREATE INDEX IF NOT EXISTS vinculos_criado_por_idx ON public.vinculos(criado_por);
CREATE INDEX IF NOT EXISTS auditoria_autor_id_idx ON public.auditoria(autor_id);
CREATE INDEX IF NOT EXISTS auditoria_unidade_id_idx ON public.auditoria(unidade_id);
CREATE INDEX IF NOT EXISTS auditoria_paciente_id_idx ON public.auditoria(paciente_id);
CREATE INDEX IF NOT EXISTS achados_autor_id_idx ON public.achados(autor_id);
CREATE INDEX IF NOT EXISTS achados_unidade_id_idx ON public.achados(unidade_id);
CREATE INDEX IF NOT EXISTS achados_cid10_idx ON public.achados(cid10);
CREATE INDEX IF NOT EXISTS gestacoes_mae_id_idx ON public.gestacoes(mae_id);
CREATE INDEX IF NOT EXISTS gestacoes_autor_id_idx ON public.gestacoes(autor_id);
CREATE INDEX IF NOT EXISTS gestacoes_unidade_id_idx ON public.gestacoes(unidade_id);
CREATE INDEX IF NOT EXISTS condicoes_gestacao_gestacao_id_idx ON public.condicoes_gestacao(gestacao_id);
CREATE INDEX IF NOT EXISTS condicoes_gestacao_cid10_idx ON public.condicoes_gestacao(cid10);
CREATE INDEX IF NOT EXISTS condicoes_gestacao_autor_id_idx ON public.condicoes_gestacao(autor_id);
CREATE INDEX IF NOT EXISTS condicoes_gestacao_unidade_id_idx ON public.condicoes_gestacao(unidade_id);
CREATE INDEX IF NOT EXISTS nascimentos_gestacao_id_idx ON public.nascimentos(gestacao_id);
CREATE INDEX IF NOT EXISTS nascimentos_autor_id_idx ON public.nascimentos(autor_id);
CREATE INDEX IF NOT EXISTS nascimentos_unidade_id_idx ON public.nascimentos(unidade_id);
CREATE INDEX IF NOT EXISTS importacoes_fhir_autor_id_idx ON public.importacoes_fhir(autor_id);
CREATE INDEX IF NOT EXISTS importacoes_fhir_unidade_id_idx ON public.importacoes_fhir(unidade_id);
CREATE INDEX IF NOT EXISTS eventos_clinicos_unidade_id_idx ON public.eventos_clinicos(unidade_id);
CREATE INDEX IF NOT EXISTS eventos_clinicos_importacao_id_idx ON public.eventos_clinicos(importacao_id);
CREATE INDEX IF NOT EXISTS paciente_fhir_paciente_id_idx ON public.paciente_fhir(paciente_id);

ALTER POLICY unidades_leitura_unidade ON public.unidades
  USING (id = (SELECT public.minha_unidade()));
ALTER POLICY perfis_leitura_proprios_ou_unidade ON public.perfis
  USING (id = (SELECT auth.uid()) OR unidade_id = (SELECT public.minha_unidade()));
ALTER POLICY perfis_admin_altera_unidade ON public.perfis
  USING ((SELECT public.eh_admin()) AND unidade_id = (SELECT public.minha_unidade())
    AND id <> (SELECT auth.uid()))
  WITH CHECK ((SELECT public.eh_admin()) AND unidade_id = (SELECT public.minha_unidade()));
ALTER POLICY auditoria_admin_leitura_unidade ON public.auditoria
  USING ((SELECT public.eh_admin()) AND unidade_id = (SELECT public.minha_unidade()));
