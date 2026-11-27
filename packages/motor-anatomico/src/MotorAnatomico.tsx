'use client';
// Motor 3D (SPEC §5.4). Não sabe o que é paciente: recebe atlas e marcadores, desenha e devolve geometria.
import { Canvas, useFrame, useThree, type ThreeEvent } from '@react-three/fiber';
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import {
  BackSide, Box3, DirectionalLight, DoubleSide, InstancedMesh, Matrix4, Mesh, MeshStandardMaterial, Quaternion, Sphere, Vector3,
  type Camera as ThreeCamera, type Intersection, type Raycaster,
} from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { ancoraDeIntersecao, candidatas, criarBVH, precisaDeGeometria, reprojetar, situarMarcador } from './ancora';
import {
  carregarPacote, carregarSistema, descartarSistema, doisQuadros, montarBVHs, urlDoPacote, type Pacote, type Sistema,
} from './pacote';
import type { Ancora, ComandoCamera, EntradaIndice, Marcador, NomeVista, Vetor3, VistaCamera } from './tipos';
import { binningCamadas, limparMapaForaDeUso, montarVistaCamera, COR_PADRAO, CORES_SISTEMA, distanciaDeEnquadramento } from './visual';

export type MotorAnatomicoProps = {
  atlas: string;
  versao: string;
  /** pasta (URL) que contém <atlas>/<versao>/; "" = raiz do site */
  baseUrl: string;
  sistemasVisiveis: string[];
  marcadores?: Marcador[];
  /**
   * true = os marcadores ainda vão chegar. Quando informado, os sistemas visíveis só são baixados depois
   * que isto for false e um quadro com os marcadores tiver sido desenhado. Omitido = baixa de imediato.
   */
  marcadoresPendentes?: boolean;
  /** chamada uma vez, depois do primeiro quadro com os marcadores; só quando `marcadoresPendentes` é informado */
  onMarcadoresDesenhados?: () => void;
  /** id do marcador em destaque */
  selecionado?: string | null;
  onEscolherPonto?: (ancora: Ancora) => void;
  onSelecionarMarcador?: (id: string) => void;
  /** lista completa dos marcadores que não dá para desenhar; chamada quando muda (pode voltar vazia) */
  onMarcadoresSemPosicao?: (ids: string[]) => void;
  comandoCamera?: ComandoCamera;
  onVista?: (vista: Omit<VistaCamera, 'sistemas'>) => void;
  ocultas?: string[];
  isoladas?: string[] | null;
  transparencia?: boolean;
  camadasRemovidas?: number;
  onCamadas?: (total: number) => void;
};

const PELE = 'tegumentar';
const UP_PADRAO: Vetor3 = [0, 1, 0];
const EIXO_VERTICAL = new Vector3(0, 1, 0);
/** Fração da distância de enquadramento abaixo da qual a vista conta como ampliada. */
const AMPLIADO = 0.6;

/** Ocupa 100% do elemento pai, que precisa ter altura. */
export function MotorAnatomico(props: MotorAnatomicoProps) {
  // trocar de atlas ou versão recomeça do zero: nada de um corpo vaza para o outro
  const chave = urlDoPacote(props.baseUrl, props.atlas, props.versao);
  return <Motor key={chave} {...props} />;
}

type Carga = {
  /** o que está em uso: a versão leve ou a completa */
  sistema?: Sistema;
  completo?: boolean;
  erro?: string;
  pedindoLeve?: boolean;
  pedidoCompleto?: Promise<Sistema>;
};

/** Marcador desenhado por cima de tudo também ganha o clique: entra no raycast com distância zero. */
function raycastNaFrente(this: InstancedMesh, raio: Raycaster, acertos: Intersection[]) {
  const antes = acertos.length;
  InstancedMesh.prototype.raycast.call(this, raio, acertos);
  for (const acerto of acertos.slice(antes)) acerto.distance = 0;
}

type Posicionado = Marcador & { posicao: Vetor3; estrutural: boolean };

type OrbitControlsComEixo = OrbitControls & { _quat: Quaternion; _quatInverse: Quaternion };

/** OrbitControls fixa seus quaternions a partir de object.up no construtor; acompanhe alterações posteriores. */
function atualizarEixoOrbitacao(camera: ThreeCamera, orbit: OrbitControls, up: Vetor3) {
  camera.up.fromArray(up);
  const controle = orbit as OrbitControlsComEixo;
  controle._quat.setFromUnitVectors(camera.up, EIXO_VERTICAL);
  controle._quatInverse.copy(controle._quat).invert();
}

/** Marcadores iguais no material (cor e se ficam por cima de tudo): uma chamada de desenho para todos. */
function Instancias({ itens, destaque = false, onSelecionar }: {
  itens: Posicionado[];
  destaque?: boolean;
  onSelecionar?: (id: string) => void;
}) {
  const malha = useRef<InstancedMesh>(null);
  const { cor, estrutural } = itens[0]!;

  useLayoutEffect(() => {
    const atual = malha.current!;
    const matriz = new Matrix4();
    itens.forEach(({ posicao, tamanho }, i) =>
      atual.setMatrixAt(i, matriz.makeScale(tamanho, tamanho, tamanho).setPosition(...posicao)));
    atual.instanceMatrix.needsUpdate = true;
    atual.computeBoundingSphere(); // fica em cache: sem isto o clique e o recorte usariam as posições antigas
  }, [itens]);

  return (
    <instancedMesh
      // a quantidade de instâncias é fixa na criação
      key={itens.length}
      ref={malha}
      args={[undefined, undefined, itens.length]}
      renderOrder={estrutural ? 1 : 0}
      raycast={estrutural ? raycastNaFrente : InstancedMesh.prototype.raycast}
      onClick={(evento) => {
        if (evento.delta > 5) return;
        evento.stopPropagation();
        const marcador = itens[evento.instanceId!];
        if (marcador) onSelecionar?.(marcador.id);
      }}
    >
      <sphereGeometry args={[1, 24, 16]} />
      <meshStandardMaterial color={cor} emissive={cor} emissiveIntensity={destaque ? 0.6 : 0.15} depthTest={!estrutural} />
    </instancedMesh>
  );
}

/**
 * Baixa cada sistema quando fica visível ou quando alguém precisa da geometria completa (`completos`,
 * `obterCompleto`). Se o pacote tiver versão leve, o sistema visível abre por ela e a completa vem em
 * segundo plano, assim que a leve aparece. Cada versão é baixada uma vez.
 * Uma falha é repetida quando o sistema é ligado de novo ou deixa de ser pedido.
 */
function useSistemas(base: string, pacote: Pacote | null, visiveis: string[], completos: string[]) {
  const [cache] = useState(() => new Map<string, Carga>());
  const visiveisAntes = useRef<string[]>([]);
  const substituidos = useRef<Sistema[]>([]);
  const [revisao, setRevisao] = useState(0);
  const pedidos = [...new Set([...visiveis, ...completos])];
  const chave = `${visiveis.join(',')}|${completos.join(',')}`;
  const avisar = () => setRevisao((n) => n + 1);
  const mensagem = (erro: unknown) => (erro instanceof Error ? erro.message : String(erro));

  const carga = (id: string) => {
    let atual = cache.get(id);
    if (!atual) cache.set(id, (atual = {}));
    return atual;
  };

  const baixar = (id: string, glb: string) => {
    // o índice cita o GLB completo; a versão leve tem os mesmos nomes de nó
    const completo = pacote!.manifesto.sistemas.find((s) => s.id === id)!.glb;
    const porMalha = new Map(pacote!.indice.filter((e) => e.glb === completo).map((e) => [e.malha, e]));
    const material = new MeshStandardMaterial({
      color: CORES_SISTEMA[id] ?? COR_PADRAO, roughness: 0.55, metalness: 0, side: DoubleSide,
    });
    return carregarSistema(`${base}/${glb}`, porMalha, material);
  };

  const usar = (alvo: Carga, sistema: Sistema, completo: boolean) => {
    // o anterior só é descartado depois que a tela deixar de desenhá-lo
    if (alvo.sistema) substituidos.current.push(alvo.sistema);
    Object.assign(alvo, { sistema, completo, erro: undefined });
    void montarBVHs(sistema);
    avisar();
  };

  const obterCompleto = (id: string): Promise<Sistema> => {
    const definicao = pacote?.manifesto.sistemas.find((s) => s.id === id);
    if (!definicao) return Promise.reject(new Error(`sistema desconhecido: ${id}`));
    const alvo = carga(id);
    if (alvo.completo) return Promise.resolve(alvo.sistema!);
    if (alvo.pedidoCompleto) return alvo.pedidoCompleto;
    alvo.pedidoCompleto = baixar(id, definicao.glb).then(
      (sistema) => {
        if (cache.get(id) !== alvo) {
          descartarSistema(sistema); // o motor saiu da tela
          throw new Error('carga descartada');
        }
        usar(alvo, sistema, true);
        return sistema;
      },
      (erro: unknown) => {
        console.error(erro);
        alvo.pedidoCompleto = undefined;
        // com a versão leve na tela, a falha do detalhe não apaga o sistema
        if (!alvo.sistema) alvo.erro = mensagem(erro);
        avisar();
        throw erro;
      },
    );
    avisar();
    return alvo.pedidoCompleto;
  };

  useEffect(() => {
    if (!pacote) return;
    for (const [id, atual] of cache) {
      const religado = visiveis.includes(id) && !visiveisAntes.current.includes(id);
      if (atual.erro && (religado || !pedidos.includes(id))) cache.delete(id);
    }
    visiveisAntes.current = visiveis;
    const semPropagar = () => {}; // a falha já fica registrada na carga
    for (const id of pedidos) {
      const definicao = pacote.manifesto.sistemas.find((s) => s.id === id);
      if (!definicao || cache.get(id)?.erro) continue;
      const alvo = carga(id);
      const { glb_leve: leve } = definicao;
      if (leve && visiveis.includes(id) && !alvo.sistema && !alvo.pedindoLeve) {
        alvo.pedindoLeve = true;
        baixar(id, leve).then(
          (sistema) => {
            if (cache.get(id) !== alvo || alvo.completo) return descartarSistema(sistema);
            usar(alvo, sistema, false);
            // com o corpo na tela, a versão completa vem em segundo plano
            void doisQuadros().then(() => {
              if (cache.get(id) === alvo) obterCompleto(id).catch(semPropagar);
            });
          },
          (erro: unknown) => {
            console.error(erro); // sem a versão leve, tenta a completa
            if (cache.get(id) === alvo) obterCompleto(id).catch(semPropagar);
          },
        );
      }
      if (!leve || completos.includes(id)) {
        void Promise.resolve().then(() => obterCompleto(id)).catch(semPropagar);
      }
    }
    queueMicrotask(avisar);
  }, [pacote, chave]);

  useEffect(() => {
    for (const sistema of substituidos.current.splice(0)) descartarSistema(sistema);
  }, [revisao]);

  useEffect(() => {
    const atual = cache;
    const velhos = substituidos.current;
    return () => {
      for (const { sistema } of atual.values()) if (sistema) descartarSistema(sistema);
      for (const sistema of velhos.splice(0)) descartarSistema(sistema);
      atual.clear();
    };
  }, []);

  return { cache, revisao, obterCompleto };
}

/** Avisa depois que um quadro com o conteúdo atual da cena foi desenhado. */
function AposDesenhar({ avisar }: { avisar: () => void }) {
  const quadros = useRef(0);
  // useFrame roda antes do desenho: na segunda chamada o primeiro quadro já saiu
  useFrame(() => { if (++quadros.current === 2) avisar(); });
  return null;
}

function Motor({
  atlas, versao, baseUrl, sistemasVisiveis, marcadores = [], marcadoresPendentes, onMarcadoresDesenhados, selecionado,
  onEscolherPonto, onSelecionarMarcador, onMarcadoresSemPosicao, comandoCamera, onVista,
  ocultas = [], isoladas = null, transparencia = false, camadasRemovidas = 0, onCamadas,
}: MotorAnatomicoProps) {
  const base = urlDoPacote(baseUrl, atlas, versao);
  const [pacote, setPacote] = useState<Pacote | null>(null);
  const [falha, setFalha] = useState('');
  const [vistaAtual, setVistaAtual] = useState<NomeVista | 'livre'>('anterior');
  const [cameraAtual, setCameraAtual] = useState<{ posicao: Vetor3; alvo: Vetor3; up: Vetor3 } | null>(null);

  useEffect(() => {
    const cancelar = new AbortController();
    carregarPacote(baseUrl, atlas, versao, cancelar.signal).then(setPacote, (erro: Error) => {
      if (!cancelar.signal.aborted) setFalha(`Não foi possível abrir o atlas: ${erro.message}`);
    });
    return () => cancelar.abort();
  }, [baseUrl, atlas, versao]);

  // de quais malhas cada marcador depende (undefined = índice ainda não chegou)
  const plano = useMemo(
    () =>
      marcadores.map((marcador) => {
        const { ancora } = marcador;
        let entradas: EntradaIndice[] | undefined = [];
        if (ancora.atlas === atlas && precisaDeGeometria(ancora, versao) && !falha) {
          try {
            entradas = pacote ? candidatas(ancora, pacote.indice) : undefined;
          } catch (erro) {
            console.warn(`marcador ${marcador.id}:`, erro);
          }
        }
        return { marcador, entradas };
      }),
    [marcadores, pacote, falha, atlas, versao],
  );
  const dosMarcadores = [...new Set(plano.flatMap((p) => p.entradas?.map((e) => e.sistema) ?? []))].sort();

  const [liberado, setLiberado] = useState(marcadoresPendentes === undefined);
  const [ampliado, setAmpliado] = useState(false);
  const liberados = liberado ? sistemasVisiveis : [];
  const doSelecionado = marcadores.find((m) => m.id === selecionado)?.ancora;
  // geometria completa: para posicionar marcadores, para o sistema do marcador selecionado e na vista ampliada
  const completos = [...new Set([
    ...dosMarcadores,
    ...(ampliado ? liberados : []),
    ...(doSelecionado?.atlas === atlas && liberados.includes(doSelecionado.sistema) ? [doSelecionado.sistema] : []),
    ...(liberados.includes('muscular') ? [PELE, 'muscular'] : []),
  ])].sort();

  const { cache, revisao, obterCompleto } = useSistemas(base, pacote, liberados, completos);
  const prontos = sistemasVisiveis.filter((id) => cache.get(id)?.sistema);
  const carregando = sistemasVisiveis.filter((id) => cache.has(id) && !cache.get(id)!.sistema && !cache.get(id)!.erro);
  const detalhando = sistemasVisiveis.filter((id) => {
    const c = cache.get(id);
    return c?.sistema && !c.completo && c.pedidoCompleto;
  });
  const aviso = [
    falha,
    !pacote && !falha ? 'Carregando atlas…' : '',
    ...sistemasVisiveis.map((id) => (cache.get(id)?.erro ? `Falha ao carregar ${id}: ${cache.get(id)!.erro}` : '')),
    carregando.length ? `Carregando ${carregando.join(', ')}…` : '',
    detalhando.length ? `Carregando detalhe de ${detalhando.join(', ')}…` : '',
  ].filter(Boolean).join(' ');

  const { posicionados, semPosicao, pendentes } = useMemo(() => {
    const obter = (entrada: EntradaIndice) => {
      if (!pacote?.manifesto.sistemas.some((s) => s.id === entrada.sistema)) return null;
      const carga = cache.get(entrada.sistema);
      // marcador só se posiciona na geometria completa
      if (carga?.completo) return carga.sistema!.malhas.get(entrada.malha)?.geometry ?? null;
      return carga?.erro ? null : undefined;
    };
    const posicionados: Posicionado[] = [];
    const semPosicao: string[] = [];
    let pendentes = false;
    for (const { marcador, entradas } of plano) {
      let posicao: Vetor3 | 'pendente' | null = null;
      try {
        posicao = situarMarcador(marcador.ancora, atlas, versao, entradas, obter);
      } catch (erro) {
        console.warn(`marcador ${marcador.id}:`, erro); // um marcador ruim não derruba o corpo
      }
      if (posicao === 'pendente') pendentes = true;
      else if (!posicao) semPosicao.push(marcador.id);
      else posicionados.push({ ...marcador, posicao, estrutural: !marcador.ancora.posicao_local });
    }
    return { posicionados, semPosicao, pendentes };
  }, [plano, pacote, atlas, versao, revisao]);

  // o selecionado vai num grupo só dele, que brilha mais
  const grupos = useMemo(() => {
    const porMaterial = new Map<string, Posicionado[]>();
    for (const m of posicionados) {
      const chave = JSON.stringify([m.cor, m.estrutural, m.id === selecionado]);
      const grupo = porMaterial.get(chave);
      if (grupo) grupo.push(m);
      else porMaterial.set(chave, [m]);
    }
    return [...porMaterial];
  }, [posicionados, selecionado]);
  const emDestaque = posicionados.find((m) => m.id === selecionado);

  const informarCamera = useCallback((posicao: Vetor3, alvo: Vetor3, up: Vetor3, vista?: NomeVista) => {
    setVistaAtual(vista ?? 'livre');
    setCameraAtual({ posicao, alvo, up });
    onVista?.({ atlas, atlas_versao: versao, posicao, alvo, up });
  }, [atlas, versao, onVista]);

  const camadas = useMemo(() => {
    const muscle = cache.get('muscular');
    const skin = cache.get(PELE);
    if (!sistemasVisiveis.includes('muscular') || !muscle?.completo || !muscle.sistema || !skin?.completo || !skin.sistema)
      return { total: 0, porMalha: {} };
    const pele = [...skin.sistema.malhas.values()];
    const bvhPorMalha = new Map<Mesh, ReturnType<typeof criarBVH>>();
    for (const m of pele) {
      const atual = m.geometry.boundsTree as ReturnType<typeof criarBVH> | null;
      const bvh = atual ?? criarBVH(m.geometry);
      m.geometry.boundsTree = bvh;
      bvhPorMalha.set(m, bvh);
    }
    const profundidades = [...muscle.sistema.malhas.values()].map((malha) => {
      if (!malha.geometry.boundingBox) malha.geometry.computeBoundingBox();
      const centro = malha.geometry.boundingBox!.getCenter(new Vector3());
      const distancia = Math.min(...pele.map((p) => bvhPorMalha.get(p)!.closestPointToPoint(centro)?.distance ?? Number.POSITIVE_INFINITY));
      return { malha: malha.name, profundidade: distancia };
    });
    return binningCamadas(profundidades);
  }, [cache, revisao, sistemasVisiveis]);

  useEffect(() => { onCamadas?.(camadas.total); }, [camadas.total, onCamadas]);

  // Guarda os materiais e raycasts originais para filtrar por malha sem alterar o GLB/cache.
  const visuaisOriginais = useRef(new Map<Mesh, { material: Mesh['material']; raycast: Mesh['raycast']; translucido?: MeshStandardMaterial }>());
  const wrapperMotor = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const malhasEmUso = new Set<Mesh>();
    for (const id of prontos) {
      for (const malha of cache.get(id)?.sistema?.malhas.values() ?? []) malhasEmUso.add(malha);
    }
    limparMapaForaDeUso(visuaisOriginais.current, malhasEmUso, (original, malha) => {
      malha.material = original.material;
      malha.raycast = original.raycast;
      malha.visible = true;
      original.translucido?.dispose();
    });
    for (const id of prontos) {
      const sistema = cache.get(id)?.sistema;
      if (!sistema) continue;
      for (const malha of sistema.malhas.values()) {
        let original = visuaisOriginais.current.get(malha);
        if (!original) {
          original = { material: malha.material, raycast: malha.raycast };
          visuaisOriginais.current.set(malha, original);
        }
        const daCamadaRemovida = id === 'muscular' && (camadas.porMalha[malha.name] ?? -1) < camadasRemovidas;
        const desenhar = !ocultas.includes(malha.name) && (isoladas === null || isoladas.includes(malha.name)) && !daCamadaRemovida;
        malha.visible = desenhar;
        malha.raycast = desenhar ? original.raycast : (() => []);
        const tornarTranslucida = transparencia && id !== 'esqueletico' && id !== 'articular' && id !== PELE
          && !isoladas?.includes(malha.name);
        if (tornarTranslucida) {
          const baseMaterial = Array.isArray(original.material) ? original.material[0] : original.material;
          if (baseMaterial instanceof MeshStandardMaterial) {
            original.translucido ??= baseMaterial.clone();
            original.translucido.opacity = 0.3;
            original.translucido.transparent = true;
            original.translucido.depthWrite = false;
            original.translucido.needsUpdate = true;
            malha.material = original.translucido;
          }
        } else malha.material = original.material;
      }
    }
    wrapperMotor.current?.setAttribute('data-visuais', String(visuaisOriginais.current.size));
  }, [cache, revisao, prontos.join(','), ocultas.join(','), isoladas?.join(',') ?? 'null', transparencia, camadas.porMalha, camadasRemovidas]);

  useEffect(() => () => {
    for (const [malha, original] of visuaisOriginais.current) {
      malha.material = original.material;
      malha.raycast = original.raycast;
      malha.visible = true;
      original.translucido?.dispose();
    }
    visuaisOriginais.current.clear();
  }, []);

  const relatado = useRef<string | null>(null);
  const chaveSemPosicao = JSON.stringify(semPosicao);
  useEffect(() => {
    // o primeiro aviso vazio espera tudo resolver, para não dizer "todos posicionados" cedo demais
    if (relatado.current === null && pendentes && !semPosicao.length) return;
    if (relatado.current === chaveSemPosicao) return;
    relatado.current = chaveSemPosicao;
    onMarcadoresSemPosicao?.(semPosicao);
  }, [chaveSemPosicao, pendentes]);

  // SPEC §7.2: com qualquer sistema interno ligado, a pele fica translúcida
  const peleTranslucida = sistemasVisiveis.some(
    (id) => id !== PELE && pacote?.manifesto.sistemas.some((s) => s.id === id),
  );
  useLayoutEffect(() => {
    const material = cache.get(PELE)?.sistema?.malhas.values().next().value?.material as MeshStandardMaterial | undefined;
    if (!material) return;
    material.transparent = peleTranslucida;
    material.opacity = peleTranslucida ? 0.2 : 1;
    material.depthWrite = !peleTranslucida;
    material.needsUpdate = true;
  }, [peleTranslucida, revisao]);

  // só o último clique vale enquanto o detalhe carrega
  const ultimoClique = useRef(0);
  useEffect(() => () => { ultimoClique.current++; }, []);

  const escolher = (evento: ThreeEvent<MouseEvent>) => {
    if (evento.delta > 5) return; // arrasto gira a câmera, não escolhe ponto
    const { name: malha, userData } = evento.object;
    const { sistema, estrutura } = userData;
    // pele translúcida deixa o clique passar para o que houver atrás (estrutura ou marcador)
    if (peleTranslucida && sistema === PELE && evento.intersections.some((i) => i.object.userData.sistema !== PELE))
      return;
    evento.stopPropagation(); // só a superfície mais próxima
    const clique = ++ultimoClique.current;
    const contexto = { atlas, atlas_versao: versao, sistema, estrutura, malha };
    const ancora = ancoraDeIntersecao(evento, contexto);
    // o que foi clicado pode ainda ser a versão leve, mesmo com a completa recém-chegada
    const atual = cache.get(sistema);
    if (atual?.completo && atual.sistema!.malhas.get(malha) === evento.object) return onEscolherPonto?.(ancora);
    // clique na versão leve: a âncora (ponto, triângulo, baricêntricas) é a da geometria completa
    const entregar = (a: Ancora) => { if (clique === ultimoClique.current) onEscolherPonto?.(a); };
    obterCompleto(sistema).then(
      (completo) => {
        const geometria = completo.malhas.get(malha)?.geometry;
        if (!geometria) return console.error(`malha ${malha} não está na versão completa de ${sistema}`);
        geometria.boundsTree ??= criarBVH(geometria);
        const { distancia: distanciaProjecao, ...projecao } = reprojetar(ancora, geometria);
        void distanciaProjecao;
        entregar({ ...contexto, ...projecao });
      },
      // sem a versão completa, o ponto vale, mas triângulo e baricêntricas não
      () => entregar({ ...ancora, triangulo: null, baricentricas: null }),
    );
  };
  const selecionarMarcador = (id: string) => {
    ultimoClique.current++;
    onSelecionarMarcador?.(id);
  };

  return (
    <div
      ref={wrapperMotor}
      style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}
      data-motor
      data-carregados={prontos.join(' ')}
      data-completos={prontos.filter((id) => cache.get(id)!.completo).join(' ')}
      data-marcadores={posicionados.length}
      data-pele={peleTranslucida ? 'translucida' : 'opaca'}
      data-vista={vistaAtual}
      data-camera={cameraAtual ? JSON.stringify(cameraAtual) : undefined}
      data-isoladas={isoladas === null ? 0 : 1}
      data-ocultas={ocultas.length}
      data-camadas-total={camadas.total}
    >
      <Canvas
        flat
        camera={{ fov: 35, near: 0.005, far: 50, position: [0, 0, 4] }}
        dpr={[1, 2]}
        onCreated={({ raycaster }) => { raycaster.firstHitOnly = true; }}
        role="group"
        aria-label="Corpo em 3D"
      >
        <Camera
          atlas={atlas} versao={versao} comando={comandoCamera}
          alvo={prontos.length ? cache.get(prontos[0]!)!.sistema! : null}
          selecionado={emDestaque?.posicao ?? null} selecionadoId={emDestaque?.id ?? null}
          onCamera={informarCamera} onAmpliar={() => setAmpliado(true)}
        />
        {!liberado && marcadoresPendentes === false && <AposDesenhar avisar={() => { setLiberado(true); onMarcadoresDesenhados?.(); }} />}
        <hemisphereLight args={[0xffffff, 0x444444, 2.2]} />
        {/* ponytail: uma chamada de desenho por estrutura; BatchedMesh se ficar lento com tudo ligado */}
        {prontos.map((id) => (
          <primitive key={cache.get(id)!.sistema!.grupo.uuid} object={cache.get(id)!.sistema!.grupo} onClick={escolher} />
        ))}
        {grupos.map(([chave, itens]) => (
          <Instancias key={chave} itens={itens} destaque={itens[0]!.id === selecionado} onSelecionar={selecionarMarcador} />
        ))}
        {emDestaque && (
          // contorno: casca maior vista por dentro; não intercepta cliques
          <mesh
            position={emDestaque.posicao}
            scale={emDestaque.tamanho * 1.45}
            raycast={() => null}
            renderOrder={emDestaque.estrutural ? 1 : 0}
          >
            <sphereGeometry args={[1, 24, 16]} />
            <meshBasicMaterial color="#111111" side={BackSide} depthTest={!emDestaque.estrutural} />
          </mesh>
        )}
      </Canvas>
      <div role="status" style={{ position: 'absolute', top: 8, left: 8, right: 8, fontSize: 13, pointerEvents: 'none' }}>
        {aviso}
      </div>
      {pacote && (
        // atribuição exigida pela licença do atlas (SPEC §10)
        <small style={{ position: 'absolute', left: 8, right: 8, bottom: 4, fontSize: 11, textAlign: 'center', pointerEvents: 'none' }}>
          {pacote.manifesto.atribuicao}
        </small>
      )}
    </div>
  );
}

/** Órbita, comandos de câmera, foco e enquadramento do primeiro sistema que chegar. */
function Camera({ atlas, versao, comando, alvo, selecionado, selecionadoId, onCamera, onAmpliar }: {
  atlas: string;
  versao: string;
  comando?: ComandoCamera;
  alvo: Sistema | null;
  selecionado: Vetor3 | null;
  selecionadoId: string | null;
  onCamera: (posicao: Vetor3, alvo: Vetor3, up: Vetor3, vista?: NomeVista) => void;
  onAmpliar: () => void;
}) {
  const camera = useThree((s) => s.camera);
  const cena = useThree((s) => s.scene);
  const tela = useThree((s) => s.gl.domElement);
  const tamanho = useThree((s) => s.size);
  const controles = useRef<OrbitControls | null>(null);
  const enquadrado = useRef(false);
  const ampliadoAvisado = useRef(false);
  const distanciaReferencia = useRef(0);
  const ultimoSeq = useRef(0);
  const comandoPendente = useRef<ComandoCamera | null>(null);
  const ultimaSelecao = useRef<string | null>(null);
  const onCameraAtual = useRef(onCamera);
  useEffect(() => { onCameraAtual.current = onCamera; }, [onCamera]);
  const animacao = useRef<{
    inicio: number; posicaoInicial: Vector3; posicaoFinal: Vector3; alvoInicial: Vector3; alvoFinal: Vector3; amortecimento: boolean;
  } | null>(null);

  const cancelarAnimacao = () => {
    if (animacao.current && controles.current) controles.current.enableDamping = animacao.current.amortecimento;
    animacao.current = null;
  };

  const enviarVista = (nome?: NomeVista) => {
    const orbit = controles.current;
    if (!orbit) return;
    onCameraAtual.current(camera.position.toArray() as Vetor3, orbit.target.toArray() as Vetor3,
      camera.up.toArray() as Vetor3, nome);
  };

  const dadosEnquadramento = () => {
    if (!alvo) return null;
    const caixa = new Box3().setFromObject(alvo.grupo);
    const centro = caixa.getCenter(new Vector3());
    const distanciaCaixa = distanciaDeEnquadramento(caixa, 35, tamanho.width / tamanho.height);
    const raio = caixa.getBoundingSphere(new Sphere()).radius;
    const semiVertical = Math.PI * 35 / 360;
    const semiHorizontal = Math.atan(Math.tan(semiVertical) * (tamanho.width / tamanho.height));
    const distanciaEsfera = raio / Math.sin(Math.min(semiVertical, semiHorizontal));
    return { centro, distancia: Math.max(distanciaCaixa, distanciaEsfera) };
  };

  const enquadrar = () => {
    const data = dadosEnquadramento();
    const orbit = controles.current;
    if (!data || !orbit) return false;
    cancelarAnimacao();
    camera.position.set(data.centro.x, data.centro.y, data.centro.z + data.distancia);
    atualizarEixoOrbitacao(camera, orbit, UP_PADRAO);
    orbit.target.copy(data.centro);
    orbit.update();
    distanciaReferencia.current = data.distancia;
    return true;
  };

  const moverAlvo = (alvoNovo: Vector3, animar: boolean) => {
    const orbit = controles.current;
    if (!orbit) return false;
    const alvoAtual = orbit.target.clone();
    const posAtual = camera.position.clone();
    const deslocamento = posAtual.clone().sub(alvoAtual);
    const limite = distanciaReferencia.current * 0.5;
    if (limite > 0 && deslocamento.length() > limite) deslocamento.setLength(limite);
    const posicaoFinal = alvoNovo.clone().add(deslocamento);
    const reduzido = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!animar || reduzido) {
      cancelarAnimacao();
      orbit.target.copy(alvoNovo);
      camera.position.copy(posicaoFinal);
      orbit.update();
      return true;
    }
    const amortecimento = orbit.enableDamping;
    orbit.enableDamping = false;
    animacao.current = { inicio: performance.now(), posicaoInicial: posAtual, posicaoFinal,
      alvoInicial: alvoAtual, alvoFinal: alvoNovo.clone(), amortecimento };
    return true;
  };

  const executar = (cmd: ComandoCamera) => {
    if (cmd.seq <= ultimoSeq.current) return;
    const orbit = controles.current;
    if (!orbit || !enquadrado.current) { comandoPendente.current = cmd; return; }
    if (comandoPendente.current?.seq === cmd.seq || comandoPendente.current?.seq === -1) comandoPendente.current = null;
    ultimoSeq.current = cmd.seq;
    if (cmd.acao === 'restaurar') {
      if (cmd.vista.atlas !== atlas || cmd.vista.atlas_versao !== versao) return;
      cancelarAnimacao();
      orbit.target.fromArray(cmd.vista.alvo);
      camera.position.fromArray(cmd.vista.posicao);
      atualizarEixoOrbitacao(camera, orbit, cmd.vista.up ?? UP_PADRAO);
      orbit.update();
      enviarVista();
      return;
    }
    if (cmd.acao === 'enquadrar') {
      if (enquadrar()) enviarVista('anterior');
      return;
    }
    if (cmd.acao === 'vista') {
      const data = dadosEnquadramento();
      if (!data) return;
      const vista = montarVistaCamera(cmd.vista, atlas, versao, data.centro.toArray() as Vetor3, data.distancia, []);
      cancelarAnimacao();
      camera.position.fromArray(vista.posicao);
      atualizarEixoOrbitacao(camera, orbit, vista.up ?? UP_PADRAO);
      orbit.target.fromArray(vista.alvo);
      distanciaReferencia.current = data.distancia;
      orbit.update();
      enviarVista(cmd.vista);
      return;
    }
    if (selecionado) {
      moverAlvo(new Vector3(...selecionado), true);
      if (animacao.current) comandoPendente.current = { seq: -1, acao: 'focar' };
      else enviarVista();
      return;
    }
  };

  useLayoutEffect(() => {
    const luz = new DirectionalLight(0xffffff, 1.4);
    luz.position.set(0.5, 1, 1);
    camera.add(luz);
    cena.add(camera);
    const orbit = new OrbitControls(camera, tela);
    orbit.enableDamping = true;
    const terminou = () => {
      const atual = controles.current;
      if (atual) onCameraAtual.current(camera.position.toArray() as Vetor3, atual.target.toArray() as Vetor3,
        camera.up.toArray() as Vetor3);
    };
    orbit.addEventListener('end', terminou);
    controles.current = orbit;
    return () => {
      orbit.removeEventListener('end', terminou);
      orbit.dispose();
      camera.remove(luz);
      cena.remove(camera);
    };
  }, [camera, cena, tela]);

  useLayoutEffect(() => {
    if (!alvo || enquadrado.current || !controles.current) return;
    enquadrado.current = true;
    enquadrar();
  }, [alvo, camera, tamanho]);

  useEffect(() => {
    if (!comando) return;
    if (!alvo || !enquadrado.current) comandoPendente.current = comando;
    else executar(comando);
  }, [comando, alvo, atlas, versao]);

  useEffect(() => {
    if (!selecionadoId || !selecionado) return;
    if (comando?.acao === 'restaurar'
      && comando.vista.atlas === atlas && comando.vista.atlas_versao === versao) {
      ultimaSelecao.current = selecionadoId;
      return;
    }
    if (ultimaSelecao.current === selecionadoId) return;
    ultimaSelecao.current = selecionadoId;
    if (moverAlvo(new Vector3(...selecionado), true)) {
      if (animacao.current) comandoPendente.current = { seq: -1, acao: 'focar' };
      else enviarVista();
    }
  }, [selecionadoId, selecionado, comando, atlas, versao]);

  useFrame(() => {
    const orbit = controles.current;
    if (!orbit) return;
    const movimento = animacao.current;
    if (movimento) {
      const t = Math.min(1, (performance.now() - movimento.inicio) / 400);
      const suave = t * t * (3 - 2 * t);
      camera.position.lerpVectors(movimento.posicaoInicial, movimento.posicaoFinal, suave);
      orbit.target.lerpVectors(movimento.alvoInicial, movimento.alvoFinal, suave);
      orbit.update();
      if (t >= 1) {
        animacao.current = null;
        orbit.enableDamping = movimento.amortecimento;
        const pendente = comandoPendente.current;
        comandoPendente.current = null;
        if (pendente?.acao === 'focar') enviarVista();
      }
    } else orbit.update();
    if (!ampliadoAvisado.current && distanciaReferencia.current > 0 && camera.position.distanceTo(orbit.target) < distanciaReferencia.current * AMPLIADO) {
      ampliadoAvisado.current = true;
      onAmpliar();
    }
    if (comandoPendente.current && comandoPendente.current.acao !== 'focar' && enquadrado.current) {
      const pendente = comandoPendente.current;
      comandoPendente.current = null;
      executar(pendente);
    }
  });
  return null;
}
