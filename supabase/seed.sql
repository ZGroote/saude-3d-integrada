-- Carga de demonstração fictícia para desenvolvimento e testes locais.
INSERT INTO public.unidades (id, nome, cnes, municipio_ibge) VALUES
  ('10000000-0000-4000-8000-000000000001', 'UBS Centro', '1111111', '3550308'),
  ('10000000-0000-4000-8000-000000000002', 'Ambulatório de Cardiologia', '2222222', '3550308'),
  ('10000000-0000-4000-8000-000000000003', 'Maternidade Municipal', '3333333', '3550308');

INSERT INTO auth.users (id, email) VALUES
  ('20000000-0000-4000-8000-000000000001', 'admin@saude3d.invalid'),
  ('20000000-0000-4000-8000-000000000002', 'cardiologia@saude3d.invalid'),
  ('20000000-0000-4000-8000-000000000003', 'ortopedia@saude3d.invalid'),
  ('20000000-0000-4000-8000-000000000004', 'obstetricia@saude3d.invalid'),
  ('20000000-0000-4000-8000-000000000005', 'admin-cardiologia@saude3d.invalid'),
  ('20000000-0000-4000-8000-000000000006', 'admin-maternidade@saude3d.invalid'),
  ('20000000-0000-4000-8000-000000000007', 'admin-ubs-substituto@saude3d.invalid');

INSERT INTO public.perfis (id, nome, unidade_id, especialidade, papel) VALUES
  ('20000000-0000-4000-8000-000000000001', 'Admin UBS Centro', '10000000-0000-4000-8000-000000000001', NULL, 'admin'),
  ('20000000-0000-4000-8000-000000000002', 'Profissional Cardiologia', '10000000-0000-4000-8000-000000000002', 'cardiologia', 'profissional'),
  ('20000000-0000-4000-8000-000000000003', 'Profissional Ortopedia', '10000000-0000-4000-8000-000000000001', 'ortopedia', 'profissional'),
  ('20000000-0000-4000-8000-000000000004', 'Profissional Obstetrícia', '10000000-0000-4000-8000-000000000003', 'obstetricia', 'profissional'),
  ('20000000-0000-4000-8000-000000000005', 'Admin Cardiologia', '10000000-0000-4000-8000-000000000002', NULL, 'admin'),
  ('20000000-0000-4000-8000-000000000006', 'Admin Maternidade', '10000000-0000-4000-8000-000000000003', NULL, 'admin'),
  ('20000000-0000-4000-8000-000000000007', 'Admin UBS substituto', '10000000-0000-4000-8000-000000000001', NULL, 'admin');

-- Dados sintéticos aplicados como proprietário durante a instalação do seed.
-- A aplicação não recebe esses privilégios: suas escritas passam pelas funções.
INSERT INTO public.pacientes (id, nome, cns, sexo, data_nascimento, municipio_ibge) VALUES
  ('30000000-0000-4000-8000-000000000001', 'Maria Fictícia', '700000000000001', 'feminino', CURRENT_DATE - INTERVAL '32 years', '3550308'),
  ('30000000-0000-4000-8000-000000000002', 'João Fictício', '700000000000002', 'masculino', DATE '1990-01-01', '3550308');

INSERT INTO public.vinculos
  (paciente_id, unidade_id, motivo, origem, criado_por, desde)
VALUES
  ('30000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', 'Atendimento de atenção primária', 'atendimento', '20000000-0000-4000-8000-000000000001', CURRENT_DATE),
  ('30000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000002', 'Acompanhamento cardiológico', 'encaminhamento', '20000000-0000-4000-8000-000000000005', CURRENT_DATE),
  ('30000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000003', 'Acompanhamento obstétrico', 'atendimento', '20000000-0000-4000-8000-000000000006', CURRENT_DATE),
  ('30000000-0000-4000-8000-000000000002', '10000000-0000-4000-8000-000000000001', 'Atendimento de atenção primária', 'atendimento', '20000000-0000-4000-8000-000000000001', CURRENT_DATE);

INSERT INTO public.auditoria (autor_id, unidade_id, paciente_id, acao) VALUES
  ('20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', '30000000-0000-4000-8000-000000000002', 'seed_demonstracao');
