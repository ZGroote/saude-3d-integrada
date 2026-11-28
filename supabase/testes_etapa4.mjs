import assert from 'node:assert/strict';
import { emails, login, rpc } from './etapa4_comum.mjs';

const mariaId='30000000-0000-4000-8000-000000000001';
const demostracao=[
  {obs:'ETAPA4-DEMO-CARDIO',cid:'I10',autor:'Profissional Cardiologia',unidade:'Ambulatório de Cardiologia'},
  {obs:'ETAPA4-DEMO-ORTOPEDIA',cid:'M54.5',autor:'Profissional Ortopedia',unidade:'UBS Centro',sistema:'esqueletico',estrutura:'UBERON:0004620'},
  {obs:'ETAPA4-DEMO-OBSTETRICIA',cid:'Z34.0',autor:'Profissional Obstetrícia',unidade:'Maternidade Municipal',sistema:'urogenital',estrutura:'UBERON:0009853'},
];

for (const [papel,email] of Object.entries({cardiologia:emails.cardiologia,ortopedia:emails.ortopedia,obstetricia:emails.obstetricia})) {
  const cliente=await login(email);
  const pacientes=await rpc(cliente,'buscar_pacientes',{p_texto:'Maria Fictícia'});
  assert.ok(pacientes.some((p)=>p.id===mariaId),`${papel}: Maria não apareceu na lista`);
  const achados=await rpc(cliente,'listar_achados',{p_paciente:mariaId});
  for (const esperado of demostracao) {
    const row=achados.find((a)=>a.observacao===esperado.obs);
    assert.ok(row,`${papel}: não vê ${esperado.obs}`);
    assert.equal(row.cid10,esperado.cid);
    assert.equal(row.autor_nome,esperado.autor);
    assert.equal(row.unidade_nome,esperado.unidade);
    if (esperado.sistema) {
      assert.equal(row.ancora.atlas,'hra-f');
      assert.equal(row.ancora.atlas_versao,'1.10-1');
      assert.equal(row.ancora.sistema,esperado.sistema);
      assert.equal(row.ancora.estrutura,esperado.estrutura);
      assert.ok(row.ancora.posicao_local.every(Number.isFinite));
      assert.ok(Number.isInteger(row.ancora.triangulo));
      assert.deepEqual(row.ancora.baricentricas,[1,0,0]);
    }
  }
  const restrito=achados.filter((a)=>a.observacao==='ETAPA4-DEMO-RESTRITO-CARDIO');
  if (email===emails.cardiologia) {
    assert.equal(restrito.length,1);
    assert.equal(restrito[0].cid10,'F32.9');
    assert.equal(restrito[0].nivel_sigilo,'restrito');
  } else {
    assert.deepEqual(restrito,[]);
    assert.equal(achados.some((a)=>a.cid10==='F32.9'),false);
  }
  console.log(`✔ ${papel}: Maria listada; 3 achados de referência corretos; ${email===emails.cardiologia?'restrito visível só à unidade autora':'F32.9 de outra unidade oculto'}`);
}

const cardio=await login(emails.cardiologia);
const lista=await rpc(cardio,'buscar_pacientes',{p_texto:'Paciente Carga Fictícia'});
const carga=lista.find((p)=>p.nome==='Paciente Carga Fictícia');
assert.ok(carga,'Paciente Carga Fictícia não aparece para cardiologia');
const achadosCarga=await rpc(cardio,'listar_achados',{p_paciente:carga.id});
const cargaEtapa4=achadosCarga.filter((a)=>/^ETAPA4-CARGA-\d{3}$/.test(a.observacao??''));
assert.equal(cargaEtapa4.length,200,'a carga deve ter exatamente 200 achados vigentes');
assert.equal(new Set(cargaEtapa4.map((a)=>a.observacao)).size,200,'observações da carga não podem duplicar');
assert.ok(cargaEtapa4.every((a)=>a.nivel_sigilo==='normal'),'a carga não pode conter CID restrito');
assert.ok(cargaEtapa4.every((a)=>a.ancora?.atlas==='hra-f' && a.ancora?.atlas_versao==='1.10-1'
  && Number.isInteger(a.ancora?.triangulo) && a.ancora?.posicao_local?.length===3),
  'cada achado de carga precisa de âncora HRA com geometria real');
const sistemas=new Set(cargaEtapa4.map((a)=>a.ancora.sistema));
assert.ok(sistemas.size>=8,`esperados >=8 sistemas anatômicos, recebidos ${sistemas.size}`);
assert.ok(new Set(cargaEtapa4.map((a)=>a.cid10)).size>=8,'esperados CIDs variados');
console.log(`✔ carga: ${cargaEtapa4.length} vigentes, ${sistemas.size} sistemas, ${new Set(cargaEtapa4.map((a)=>a.cid10)).size} CIDs não restritos`);
console.log('Etapa 4: todos os testes de homologação passaram');
