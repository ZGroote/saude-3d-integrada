"""Registers a direct-test Supabase Auth session without printing credentials."""
import base64
import json
import urllib.request
from pathlib import Path


WEB = Path(__file__).resolve().parents[1]


def _ambiente():
    valores = {}
    for linha in (WEB / '.env.local').read_text(encoding='utf-8-sig').splitlines():
        chave, separador, valor = linha.partition('=')
        if separador and chave.strip() in {'NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_SECRET_KEY'}:
            valores[chave.strip()] = valor.strip().strip('"').strip("'")
    if not valores.get('NEXT_PUBLIC_SUPABASE_URL') or not valores.get('SUPABASE_SECRET_KEY'):
        raise RuntimeError('missing Supabase session activity configuration')
    return valores


def registrar_atividade(access_token):
    partes = access_token.split('.')
    if len(partes) != 3:
        raise RuntimeError('invalid Auth token')
    payload = partes[1] + '=' * (-len(partes[1]) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload))
    sessao, usuario = claims.get('session_id'), claims.get('sub')
    if not isinstance(sessao, str) or not isinstance(usuario, str):
        raise RuntimeError('Auth token has no session claims')

    ambiente = _ambiente()
    segredo = ambiente['SUPABASE_SECRET_KEY']
    pedido = urllib.request.Request(
        ambiente['NEXT_PUBLIC_SUPABASE_URL'].rstrip('/') + '/rest/v1/rpc/registrar_atividade_sessao',
        data=json.dumps({'p_sessao': sessao, 'p_usuario': usuario}).encode(),
        headers={'apikey': segredo, 'authorization': f'Bearer {segredo}', 'content-type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            ativo = json.loads(resposta.read() or b'false')
    except Exception:
        raise RuntimeError('failed to register Auth session activity') from None
    if ativo is not True:
        raise RuntimeError('Auth session activity was rejected')
