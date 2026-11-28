"""Rodada 2 (emenda §8.2 do protocolo): ordem sorteada (seed 240025) dos 57 homens não sorteados na rodada 1 e
download só das máscaras do protocolo, por HTTP Range no zip do Zenodo. Executado pelo revisor (o agente não tem rede)."""
import csv, hashlib, io, json, random, sys, zipfile
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
from baixar_mascaras import RemoteFile, URL, MASKS, EXT  # noqa: E402

restantes = sorted(r['id'] for r in csv.DictReader((AQUI / 'casos.csv').open(encoding='utf-8-sig'))
                   if r['pool'] == 'male_control' and r['selection'] == 'not_selected')
assert len(restantes) == 57, len(restantes)
ordem = random.Random(240025).sample(restantes, len(restantes))
(AQUI / 'homens_r2_ordem.json').write_text(json.dumps({'seed': 240025, 'ordem': ordem}, indent=2), encoding='utf-8')

rf = RemoteFile(URL)
z = zipfile.ZipFile(io.BufferedReader(rf, buffer_size=1 << 16))
por_nome = {i.filename: i for i in z.infolist()}
manifesto = []
for cid in ordem:
    for nome in MASKS:
        info = por_nome.get(f'Totalsegmentator_dataset_v300/{cid}/segmentations/{nome}.nii.gz')
        if info is None:
            manifesto.append({'id': cid, 'mask': nome, 'ausente': True}); continue
        dados = z.read(info)
        destino = EXT / cid / 'segmentations' / f'{nome}.nii.gz'
        destino.parent.mkdir(parents=True, exist_ok=True); destino.write_bytes(dados)
        manifesto.append({'id': cid, 'mask': nome, 'bytes': len(dados), 'sha256': hashlib.sha256(dados).hexdigest()})
(AQUI / 'homens_r2_manifesto.json').write_text(json.dumps({'range_bytes_transferidos': rf.baixado, 'mascaras': manifesto}, indent=2), encoding='utf-8')
print('homens:', len(ordem), '| máscaras:', sum('bytes' in m for m in manifesto), '| ausentes:', sum('ausente' in m for m in manifesto), '| transferido:', rf.baixado)
