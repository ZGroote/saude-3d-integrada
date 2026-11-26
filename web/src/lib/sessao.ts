const encoder = new TextEncoder();

function segredoSessao() {
  const segredo = process.env.SESSAO_SEGREDO;
  if (!segredo) throw new Error("Configuração de segurança ausente: defina SESSAO_SEGREDO no servidor.");
  return segredo;
}

async function chaveHmac() {
  return crypto.subtle.importKey(
    "raw", encoder.encode(segredoSessao()), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"],
  );
}

function base64Url(bytes: Uint8Array) {
  let binario = "";
  bytes.forEach((byte) => { binario += String.fromCharCode(byte); });
  return btoa(binario).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

export async function assinarAtividade(timestamp: number) {
  const payload = String(timestamp);
  const assinatura = await crypto.subtle.sign("HMAC", await chaveHmac(), encoder.encode(payload));
  return `${payload}.${base64Url(new Uint8Array(assinatura))}`;
}

export async function atividadeValida(valor: string | undefined, agora: number) {
  if (!valor) return false;
  const partes = valor.split(".");
  if (partes.length !== 2 || !/^\d{13}$/.test(partes[0])) return false;
  const timestamp = Number(partes[0]);
  if (!Number.isSafeInteger(timestamp) || timestamp <= 0 || timestamp > agora) return false;
  try {
    const base64 = partes[1].replace(/-/g, "+").replace(/_/g, "/");
    const assinatura = Uint8Array.from(atob(base64), (caractere) => caractere.charCodeAt(0));
    return await crypto.subtle.verify("HMAC", await chaveHmac(), assinatura, encoder.encode(partes[0]));
  } catch {
    return false;
  }
}
