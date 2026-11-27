"""Lê só o meta.csv de dentro do zip remoto do TotalSegmentator V3 (Zenodo 22688904) por HTTP Range.
Baixa apenas o diretório central do zip e o trecho do meta.csv (<= 50 MB pela regra do EXP-0023)."""
import hashlib, io, sys, urllib.request, zipfile
from pathlib import Path

URL = "https://zenodo.org/api/records/22688904/files/Totalsegmentator_dataset_v300.zip/content"
SAIDA = Path(__file__).parent / "metadados" / "S1_totalsegmentator"
LIMITE = 50 * 1024 * 1024


class RemoteFile(io.RawIOBase):
    def __init__(self, url):
        self.url, self.pos, self.baixado = url, 0, 0
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=60) as r:
            self.size = int(r.headers["Content-Length"])
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos
    def readinto(self, b):
        n = min(len(b), self.size - self.pos)
        if n <= 0: return 0
        self.baixado += n
        if self.baixado > LIMITE: sys.exit("limite de 50 MB atingido; abortado")
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{self.pos + n - 1}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            if r.status != 206: sys.exit(f"servidor não aceitou Range (HTTP {r.status}); abortado")
            data = r.read()
        b[:len(data)] = data
        self.pos += len(data)
        return len(data)


rf = RemoteFile(URL)
z = zipfile.ZipFile(io.BufferedReader(rf, buffer_size=1 << 20))
metas = [i for i in z.infolist() if i.filename.lower().endswith("meta.csv")]
print("tamanho do zip:", rf.size, "| entradas:", len(z.infolist()), "| meta.csv:", [(i.filename, i.file_size) for i in metas])
for i in metas:
    dados = z.read(i)
    destino = SAIDA / Path(i.filename).name
    destino.write_bytes(dados)
    print(destino.name, len(dados), "bytes, sha256", hashlib.sha256(dados).hexdigest())
print("bytes baixados via Range:", rf.baixado)
