"""Baixa só um paciente do subconjunto do TotalSegmentator (CC BY 4.0), lendo o zip remoto por partes.

Uso: python baixar_caso.py <pasta_destino> [listar | <prefixo_do_caso>]
"""
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://zenodo.org/api/records/10047263/files/Totalsegmentator_dataset_small_v201.zip/content"


class ZipRemoto(io.RawIOBase):
    """Arquivo somente leitura sobre HTTP Range, para o zipfile buscar só o que precisa."""

    def __init__(self, url):
        self.url, self.pos = url, 0
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req) as r:
            self.url = r.url  # segue o redirecionamento uma vez
            self.tamanho = int(r.headers["Content-Length"])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.tamanho + off}[whence]
        return self.pos

    def read(self, n=-1):
        if n < 0:
            n = self.tamanho - self.pos
        if n == 0 or self.pos >= self.tamanho:
            return b""
        fim = min(self.pos + n, self.tamanho) - 1
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{fim}"})
        with urllib.request.urlopen(req) as r:
            dados = r.read()
        self.pos += len(dados)
        return dados

    def readinto(self, b):
        dados = self.read(len(b))
        b[: len(dados)] = dados
        return len(dados)


def main():
    destino = Path(sys.argv[1])
    alvo = sys.argv[2] if len(sys.argv) > 2 else "listar"
    z = zipfile.ZipFile(io.BufferedReader(ZipRemoto(URL), buffer_size=1 << 20))
    nomes = z.namelist()
    if alvo == "listar":
        casos = sorted({n.split("/")[1] for n in nomes if n.count("/") >= 2})
        print(len(nomes), "arquivos;", len(casos), "casos; primeiros:", casos[:5])
        print("exemplo:", [n for n in nomes if casos[0] in n][:8])
        return
    for n in nomes:
        if alvo in n and not n.endswith("/"):
            saida = destino / n
            saida.parent.mkdir(parents=True, exist_ok=True)
            saida.write_bytes(z.read(n))
    print("ok:", sum(1 for n in nomes if alvo in n), "arquivos de", alvo)


if __name__ == "__main__":
    main()
