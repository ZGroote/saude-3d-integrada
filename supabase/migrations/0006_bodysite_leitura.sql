-- Etapa 6: o mapa bodySite (SNOMED) -> estrutura é dado de referência, como cid10.
-- O servidor (sessão do admin) precisa lê-lo para montar a âncora; ninguém grava.
CREATE POLICY bodysite_leitura_authenticated ON public.bodysite_estrutura
  FOR SELECT TO authenticated USING (true);
GRANT SELECT ON TABLE public.bodysite_estrutura TO authenticated;
