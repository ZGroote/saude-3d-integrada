"""Complemento idempotente do seed de HOMOLOGAÇÃO: cria o que existe em supabase/seed.sql
e ainda falta no banco (usuários do Auth, unidades e perfis). Dados fictícios.

Uso (na raiz):  python supabase/seed_homologacao_complemento.py
Lê supabase/.env (senha do banco); acrescenta as senhas novas em supabase/.env.demo (fora do git).
Rodar de novo não duplica nada.
"""
import re, secrets, string, subprocess, sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
REF, POOLER = "zmrxskzokpbedmvikrvc", "aws-0-sa-east-1.pooler.supabase.com:5432"
env = dict(l.split("=", 1) for l in (RAIZ / ".env").read_text().split() if "=" in l)
url = f"postgresql://postgres.{REF}:{env['SUPABASE_DB_PASSWORD']}@{POOLER}/postgres"

seed = (RAIZ / "seed.sql").read_text(encoding="utf-8")
usuarios = re.findall(r"\('([0-9a-f-]{36})', '([^']+@saude3d\.invalid)'\)", seed)
unidades = re.findall(r"\('(10000000-[0-9a-f-]{27})', '([^']+)', '(\d+)', '(\d+)'\)", seed)
perfis = re.findall(r"\('(20000000-[0-9a-f-]{27})', '([^']+)', '(10000000-[0-9a-f-]{27})', (NULL|'[^']+'), '(admin|profissional)'\)", seed)
assert usuarios and unidades and perfis, "não achei os blocos no seed.sql"

demo = RAIZ / ".env.demo"
existentes = dict(l.split("=", 1) for l in demo.read_text().split() if "=" in l) if demo.exists() else {}
alfabeto = string.ascii_letters + string.digits
novas = {email: "".join(secrets.choice(alfabeto) for _ in range(20)) for _, email in usuarios if email not in existentes}

sql = ["DO $c$ BEGIN"]
for uid, nome, cnes, ibge in unidades:
    sql.append(f"INSERT INTO public.unidades (id, nome, cnes, municipio_ibge) VALUES ('{uid}', '{nome}', '{cnes}', '{ibge}') ON CONFLICT (id) DO NOTHING;")
for uid, email in usuarios:
    if email not in novas:
        continue
    sql.append(
        f"IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = '{uid}') THEN "
        "INSERT INTO auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,"
        " raw_app_meta_data, raw_user_meta_data, created_at, updated_at, confirmation_token, email_change,"
        " email_change_token_new, recovery_token) VALUES ("
        f"'00000000-0000-0000-0000-000000000000', '{uid}', 'authenticated', 'authenticated', '{email}',"
        f" extensions.crypt('{novas[email]}', extensions.gen_salt('bf')), now(),"
        " '{\"provider\":\"email\",\"providers\":[\"email\"]}', '{}', now(), now(), '', '', '', '');"
        " INSERT INTO auth.identities (id, user_id, provider_id, identity_data, provider, last_sign_in_at, created_at, updated_at)"
        f" VALUES (gen_random_uuid(), '{uid}', '{uid}', jsonb_build_object('sub', '{uid}', 'email', '{email}', 'email_verified', true),"
        " 'email', now(), now(), now()); END IF;")
for uid, nome, unidade, esp, papel in perfis:
    sql.append(f"INSERT INTO public.perfis (id, nome, unidade_id, especialidade, papel) VALUES ('{uid}', '{nome}', '{unidade}', {esp}, '{papel}') ON CONFLICT (id) DO NOTHING;")
sql.append("END $c$;")

with tempfile.TemporaryDirectory() as tmp:
    arq = Path(tmp) / "complemento.sql"
    arq.write_text("\n".join(sql), encoding="utf-8")
    r = subprocess.run(["npx", "-y", "supabase@latest", "db", "query", f"--remote={url}", "--yes", "-f", str(arq)],
                       capture_output=True, text=True, shell=sys.platform == "win32")
if r.returncode != 0:
    sys.exit("falhou:\n" + (r.stdout + r.stderr).replace(env["SUPABASE_DB_PASSWORD"], "***")[-2000:])
if novas:
    with demo.open("a") as f:
        f.writelines(f"{email}={senha}\n" for email, senha in novas.items())
print(f"ok: {len(unidades)} unidades, {len(perfis)} perfis conferidos; usuários novos: {', '.join(novas) or 'nenhum'}")
