"""Carga de demonstração no Supabase de HOMOLOGAÇÃO (dados fictícios).

Uso (na raiz do repositório):  python supabase/seed_homologacao.py
Lê:    supabase/.env  (SUPABASE_DB_PASSWORD; fora do git)
Gera:  supabase/.env.demo  (e-mail e senha de cada usuário fictício; fora do git)

Cria os usuários de supabase/seed.sql no Auth (com senha e identidade de e-mail)
e aplica o resto do seed.sql. Roda uma vez: se os usuários já existem, para.
"""
import re, secrets, string, subprocess, sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
REF = "zmrxskzokpbedmvikrvc"
POOLER = "aws-0-sa-east-1.pooler.supabase.com:5432"

env = dict(l.split("=", 1) for l in (RAIZ / ".env").read_text().split() if "=" in l)
url = f"postgresql://postgres.{REF}:{env['SUPABASE_DB_PASSWORD']}@{POOLER}/postgres"

seed = (RAIZ / "seed.sql").read_text(encoding="utf-8")
bloco_auth = re.search(r"INSERT INTO auth\.users \(id, email\) VALUES(.*?);\n", seed, re.S)
usuarios = re.findall(r"\('([0-9a-f-]{36})', '([^']+)'\)", bloco_auth.group(1))
assert len(usuarios) == 7, usuarios
resto = seed.replace(bloco_auth.group(0), "")

alfabeto = string.ascii_letters + string.digits
senhas = {email: "".join(secrets.choice(alfabeto) for _ in range(20)) for _, email in usuarios}

# o CLI executa um comando por vez: tudo vai num único bloco DO (atômico)
sql = ["DO $seed$ BEGIN",
       "IF EXISTS (SELECT 1 FROM auth.users WHERE email LIKE '%@saude3d.invalid') "
       "THEN RAISE EXCEPTION 'seed de homologação já aplicado'; END IF;"]
for uid, email in usuarios:
    sql.append(
        "INSERT INTO auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,"
        " raw_app_meta_data, raw_user_meta_data, created_at, updated_at, confirmation_token, email_change,"
        " email_change_token_new, recovery_token) VALUES ("
        f"'00000000-0000-0000-0000-000000000000', '{uid}', 'authenticated', 'authenticated', '{email}',"
        f" extensions.crypt('{senhas[email]}', extensions.gen_salt('bf')), now(),"
        " '{\"provider\":\"email\",\"providers\":[\"email\"]}', '{}', now(), now(), '', '', '', '');")
    sql.append(
        "INSERT INTO auth.identities (id, user_id, provider_id, identity_data, provider, last_sign_in_at, created_at, updated_at)"
        f" VALUES (gen_random_uuid(), '{uid}', '{uid}',"
        f" jsonb_build_object('sub', '{uid}', 'email', '{email}', 'email_verified', true), 'email', now(), now(), now());")
sql += [resto, "END $seed$;"]

with tempfile.TemporaryDirectory() as tmp:
    arq = Path(tmp) / "seed.sql"
    arq.write_text("\n".join(sql), encoding="utf-8")
    r = subprocess.run(["npx", "-y", "supabase@latest", "db", "query", f"--remote={url}", "--yes", "-f", str(arq)],
                       capture_output=True, text=True, shell=sys.platform == "win32")
saida = (r.stdout + r.stderr).replace(env["SUPABASE_DB_PASSWORD"], "***")
if r.returncode != 0:
    sys.exit("falhou:\n" + saida[-2000:])

(RAIZ / ".env.demo").write_text("".join(f"{email}={senhas[email]}\n" for _, email in usuarios))
print(f"ok: {len(usuarios)} usuários, unidades, perfis, pacientes e vínculos. Senhas em supabase/.env.demo")
