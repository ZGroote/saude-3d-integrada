// Demo: clicar no corpo devolve a âncora; cada clique vira um marcador clicável.
import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { CORES_SISTEMA, carregarPacote, MotorAnatomico, type Marcador, type Pacote } from '../src';

const ATLAS = 'bp3d-m';
const VERSAO = '4.0-1';

// ?ancora=<json> reabre uma âncora gravada (inclusive de outra atlas_versao, que o motor reprojeta)
const gravada = new URLSearchParams(location.search).get('ancora');
const INICIAIS: Marcador[] = gravada
  ? [{ id: 'gravada', ancora: JSON.parse(gravada), cor: '#e07b00', tamanho: 0.012 }]
  : [];

function Demo() {
  const [pacote, setPacote] = useState<Pacote | null>(null);
  const [erro, setErro] = useState('');
  const [sistemas, setSistemas] = useState(['esqueletico']);
  const [marcadores, setMarcadores] = useState<Marcador[]>(INICIAIS);
  const [selecionado, setSelecionado] = useState<string | null>(null);
  const [semPosicao, setSemPosicao] = useState<string[] | null>(null);
  const ultima = marcadores.find((m) => m.id === selecionado)?.ancora;
  const entrada = pacote?.indice.find((e) => e.malha === ultima?.malha);

  useEffect(() => {
    carregarPacote('', ATLAS, VERSAO).then(setPacote, (e: Error) =>
      setErro(`${e.message}. Gere o atlas: python bodyparts3d/publicar_atlas.py`));
  }, []);

  return (
    <main>
      <aside>
        <h1 style={{ fontSize: 16 }}>Motor anatômico</h1>
        {erro && <p role="alert">{erro}</p>}
        {pacote?.manifesto.sistemas.map((s) => (
          <label key={s.id}>
            <input
              type="checkbox"
              value={s.id}
              checked={sistemas.includes(s.id)}
              onChange={(e) =>
                setSistemas((atual) => (e.target.checked ? [...atual, s.id] : atual.filter((id) => id !== s.id)))}
            />{' '}
            <span style={{ color: CORES_SISTEMA[s.id] }}>■</span> {s.id} ({s.estruturas})
          </label>
        ))}
        <p id="nome">
          {entrada ? `${entrada.nome_pt || entrada.nome_en}` : 'Clique numa estrutura'}
          {entrada?.nome_pt && entrada.validacao === 'pendente' && <small> — tradução não revisada</small>}
        </p>
        <p>Marcador selecionado: <output id="selecionado">{selecionado ?? 'nenhum'}</output></p>
        <p>Marcadores: <output id="total">{marcadores.length}</output></p>
        <p>Sem posição: <output id="sem-posicao">{semPosicao ? semPosicao.join(', ') || 'nenhum' : '…'}</output></p>
        <button type="button" onClick={() => { setMarcadores([]); setSelecionado(null); }}>Limpar marcadores</button>
        <h2 style={{ fontSize: 14 }}>Âncora</h2>
        <pre id="ancora">{ultima ? JSON.stringify(ultima, null, 2) : ''}</pre>
      </aside>
      <section>
        <MotorAnatomico
          atlas={ATLAS}
          versao={VERSAO}
          baseUrl=""
          sistemasVisiveis={sistemas}
          marcadores={marcadores}
          selecionado={selecionado}
          onEscolherPonto={(ancora) => {
            const id = `m${marcadores.length + 1}`;
            setMarcadores([...marcadores, { id, ancora, cor: '#12b24a', tamanho: 0.012 }]);
            setSelecionado(id);
          }}
          onSelecionarMarcador={setSelecionado}
          onMarcadoresSemPosicao={setSemPosicao}
        />
      </section>
    </main>
  );
}

createRoot(document.getElementById('raiz')!).render(<StrictMode><Demo /></StrictMode>);
