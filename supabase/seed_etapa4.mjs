import assert from 'node:assert/strict';
import { emails, login, rpc } from './etapa4_comum.mjs';
import { criarAncorasSeed } from './ancoras_seed.mjs';

const { indice: atlas, sistemas, carregarGlb, ancora, lado } = criarAncorasSeed('hra-f', '1.10-1');
const emailNome = new Map([
  [emails.cardiologia,'Profissional Cardiologia'], [emails.ortopedia,'Profissional Ortopedia'],
  [emails.obstetricia,'Profissional Obstetrícia'],
]);
async function lista(cliente, paciente) {
  return await rpc(cliente,'listar_achados',{p_paciente:paciente}) ?? [];
}
async function garantir(cliente, registros, autor, registro) {
  if (registros.some((r)=>r.autor_nome===autor && r.observacao===registro.observacao)) return false;
  const id = await rpc(cliente,'registrar_achado',{
    p_paciente:registro.paciente, p_ancora:registro.ancora, p_cid10:registro.cid10,
    p_categoria:registro.categoria, p_lado:registro.lado, p_status:'ativo',
    p_inicio:'2026-01-01', p_observacao:registro.observacao, p_substitui:null,
  });
  if (!id) throw new Error(`registrar_achado devolveu null: ${registro.observacao}`);
  registros.push({ autor_nome:autor, observacao:registro.observacao, cid10:registro.cid10 });
  return true;
}

const cardio = await login(emails.cardiologia);
const ortho = await login(emails.ortopedia);
const obst = await login(emails.obstetricia);
const admin = await login(emails.adminCardio);
const mariaResult = await rpc(cardio,'buscar_pacientes',{p_texto:'Maria Fictícia'});
const maria = mariaResult.find((p)=>p.nome==='Maria Fictícia');
if (!maria) throw new Error('Maria Fictícia não encontrada pela busca autenticada da Cardiologia');

const l4 = atlas.find((e)=>e.malha==='VH_F_lumbar_vertebra_4');
const utero = atlas.find((e)=>e.malha==='VH_F_body_of_uterus');
assert.ok(l4 && utero, 'índice precisa conter L4 e corpo do útero');
await carregarGlb(l4.glb);
await carregarGlb(utero.glb);
const ancoras = { lombar: ancora(l4,'posterior'), utero: ancora(utero,'centro') };

const demo = [
  { cliente:cardio, email:emails.cardiologia, cid10:'I10', categoria:'doenca', lado:'nao_se_aplica', ancora:null, observacao:'ETAPA4-DEMO-CARDIO' },
  { cliente:ortho, email:emails.ortopedia, cid10:'M54.5', categoria:'sintoma', lado:'nao_se_aplica', ancora:ancoras.lombar, observacao:'ETAPA4-DEMO-ORTOPEDIA' },
  { cliente:obst, email:emails.obstetricia, cid10:'Z34.0', categoria:'doenca', lado:'nao_se_aplica', ancora:ancoras.utero, observacao:'ETAPA4-DEMO-OBSTETRICIA' },
  { cliente:cardio, email:emails.cardiologia, cid10:'F32.9', categoria:'doenca', lado:'nao_se_aplica', ancora:null, observacao:'ETAPA4-DEMO-RESTRITO-CARDIO' },
];
for (const r of demo) await rpc(r.cliente,'buscar_cid10',{p_texto:r.cid10,p_limite:100}).then((rows)=>{
  if (!rows.some((c)=>c.codigo===r.cid10)) throw new Error(`CID ausente na homologação: ${r.cid10}`);
});
for (const r of demo) {
  const achados = await lista(r.cliente,maria.id);
  const criado = await garantir(r.cliente,achados,emailNome.get(r.email),{...r,paciente:maria.id});
  console.log(`${criado?'criado':'já existia'} Maria: ${r.observacao} (${r.cid10})`);
}

const cnsCarga = '700000000000003';
const cargaId = await rpc(admin,'cadastrar_paciente',{
  p_nome:'Paciente Carga Fictícia', p_cns:cnsCarga, p_sexo:'feminino', p_data_nascimento:'1994-01-01',
  p_motivo:'Demonstração de desempenho Etapa 4', p_origem:'importacao',
});
if (!cargaId) throw new Error('cadastrar_paciente não retornou ID para Paciente Carga Fictícia');

// Load/decode every indexed HRA system once, then choose usable meshes across at least eight systems.
const porSistema = new Map();
for (const e of atlas) if (e.estrutura && e.triangulos > 0) {
  if (!porSistema.has(e.sistema)) porSistema.set(e.sistema,[]);
  porSistema.get(e.sistema).push(e);
}
for (const [sistema, entradas] of porSistema) {
  const glbs = new Set(entradas.map((e)=>e.glb));
  for (const glb of glbs) await carregarGlb(glb);
  porSistema.set(sistema,entradas.filter((e)=>sistemas.get(e.glb).porMalha.has(e.malha))
    .sort((a,b)=>b.triangulos-a.triangulos || a.malha.localeCompare(b.malha)));
}
const grupos = [...porSistema.entries()].filter(([,e])=>e.length).map(([sistema,e])=>({sistema,entradas:e}));
if (grupos.length < 8) throw new Error(`Só ${grupos.length} sistemas têm malhas decodificadas`);
const entradasCarga = [];
for (let profundidade=0;entradasCarga.length<200;profundidade++) {
  let adicionou=false;
  for (const g of grupos) {
    if (entradasCarga.length===200) break;
    if (profundidade<g.entradas.length) { entradasCarga.push(g.entradas[profundidade]); adicionou=true; }
  }
  if (!adicionou) for (const g of grupos) {
    if (entradasCarga.length===200) break;
    entradasCarga.push(g.entradas[profundidade % g.entradas.length]);
  }
}
// dois caracteres: com uma letra só, buscar_cid10 também casa a descrição e os 100 primeiros não começam pelo prefixo
const prefixos = ['A0','C5','D5','E1','G4','H1','I1','J4','K2','L2','M5','N3','R1','S8','Z0'];
const cids = [];
for (const prefixo of prefixos) {
  const rows = await rpc(cardio,'buscar_cid10',{p_texto:prefixo,p_limite:100});
  const achado = rows.find((c)=>c.codigo.startsWith(prefixo) && !/^(F|B2[0-4]|Z21|T74|Y05|Y07|O0[4-7])/.test(c.codigo));
  if (achado && !cids.some((c)=>c.codigo===achado.codigo)) cids.push(achado);
}
if (cids.length < 8) throw new Error(`Preciso de 8 CIDs normais variados; só encontrei ${cids.length}`);
const jaExistentes = await lista(cardio,cargaId);
const observacoes = new Set(jaExistentes.filter((r)=>r.autor_nome===emailNome.get(emails.cardiologia))
  .map((r)=>r.observacao));
let prontos = 0;
const pendentes = [];
for (let i=0;i<200;i++) {
  const observacao=`ETAPA4-CARGA-${String(i+1).padStart(3,'0')}`;
  if (observacoes.has(observacao)) { prontos++; continue; }
  const entry=entradasCarga[i];
  const a=ancora(entry,'dispersa',i);
  pendentes.push({
    p_paciente:cargaId,p_ancora:a,p_cid10:cids[i%cids.length].codigo,
    p_categoria:i%4===0?'sintoma':'doenca',p_lado:lado(entry),p_status:'ativo',
    p_inicio:'2026-01-01',p_observacao:observacao,p_substitui:null,
  });
}
let criados=0;
let cursor=0;
async function worker() {
  while (cursor<pendentes.length) {
    const item=pendentes[cursor++];
    const id=await rpc(cardio,'registrar_achado',item);
    if (!id) throw new Error(`Falha ao gravar ${item.p_observacao}`);
    criados++;
    if (criados%50===0) console.log(`carga: ${criados}/${pendentes.length} novos`);
  }
}
await Promise.all(Array.from({length:5},worker));
const finais=await lista(cardio,cargaId);
const marcados=finais.filter((r)=>r.autor_nome===emailNome.get(emails.cardiologia)
  && /^ETAPA4-CARGA-\d{3}$/.test(r.observacao ?? ''));
const sistemasUsados=new Set(marcados.map((r)=>r.ancora?.sistema).filter(Boolean));
if (marcados.length!==200) throw new Error(`Esperava 200 achados de carga vigentes; obtive ${marcados.length}`);
if (sistemasUsados.size<8) throw new Error(`Esperava 8 sistemas; obtive ${sistemasUsados.size}`);
if (marcados.some((r)=>r.nivel_sigilo!=='normal')) throw new Error('A carga incluiu CID restrito');

console.log(`Maria=${maria.id}; pontos reais: L4 posterior ${ancoras.lombar.triangulo} ${JSON.stringify(ancoras.lombar.posicao_local)}, útero ${ancoras.utero.triangulo} ${JSON.stringify(ancoras.utero.posicao_local)}`);
console.log(`carga=${cargaId}; vigentes=${marcados.length}; sistemas=${[...sistemasUsados].join(',')}; CIDs_normais=${cids.map((c)=>c.codigo).join(',')}; novos=${criados}; existentes=${prontos}`);
