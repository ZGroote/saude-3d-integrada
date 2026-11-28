"""Apaga da HOMOLOGAÇÃO os achados criados pelos testes e2e (marcados com "(dado fictício)" na observação).
Os achados da demonstração (seed_etapa4.mjs, observação ETAPA4-*) ficam. Uso (na raiz): python supabase/limpar_testes_homologacao.py
Lê a senha de supabase/.env (fora do git) e nunca a imprime."""
import pathlib, shutil, subprocess, sys, tempfile

env = dict(l.split("=", 1) for l in pathlib.Path("supabase/.env").read_text().splitlines() if "=" in l)
senha = env["SUPABASE_DB_PASSWORD"]
url = f"postgresql://postgres.zmrxskzokpbedmvikrvc:{senha}@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"
# correções de teste apontam para achados de teste: apaga a cadeia de trás para frente
SQL = """with recursive alvo as (
  select id from public.achados where observacao like '%(dado fictício)'
  union select a.id from public.achados a join alvo on a.substitui_id = alvo.id)
delete from public.achados where id in (select id from alvo) returning id;"""
with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False, encoding="utf-8") as f:
    f.write(SQL)
r = subprocess.run([shutil.which("npx") or "npx.cmd", "-y", "supabase@latest", "db", "query", f"--remote={url}", "--yes", "-f", f.name],
                   capture_output=True, text=True, encoding="utf-8")
saida = (r.stdout + r.stderr).replace(senha, "***")
if r.returncode:
    sys.exit("falhou:\n" + saida[-2000:])
print(f"achados de teste apagados: {saida.count('\"id\"')}")
