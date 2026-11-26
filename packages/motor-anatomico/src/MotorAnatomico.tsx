'use client';
// Motor 3D (SPEC §5.4). Não sabe o que é paciente: recebe atlas e marcadores, desenha e devolve geometria.
import { Canvas, useFrame, useThree, type ThreeEvent } from '@react-three/fiber';
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import {
  BackSide, Box3, DirectionalLight, DoubleSide, InstancedMesh, Matrix4, Mesh, MeshStandardMaterial, Vector3,
  type Intersection, type Raycaster,
} from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { ancoraDeIntersecao, candidatas, precisaDeGeometria, situarMarcador } from './ancora';
import { carregarPacote, carregarSistema, descartarSistema, urlDoPacote, type Pacote, type Sistema } from './pacote';
import type { Ancora, EntradaIndice, Marcador, Vetor3 } from './tipos';
import { COR_PADRAO, CORES_SISTEMA, distanciaDeEnquadramento } from './visual';

export type MotorAnatomicoProps = {
  atlas: string;
  versao: string;
  /** pasta (URL) que contém <atlas>/<versao>/; "" = raiz do site */
  baseUrl: string;
  sistemasVisiveis: string[];
  marcadores?: Marcador[];
  /** id do marcador em destaque */
  selecionado?: string | null;
  onEscolherPonto?: (ancora: Ancora) => void;
  onSelecionarMarcador?: (id: string) => void;
  /** lista completa dos marcadores que não dá para desenhar; chamada quando muda (pode voltar vazia) */
  onMarcadoresSemPosicao?: (ids: string[]) => void;
};

const PELE = 'tegumentar';

/** Ocupa 100% do elemento pai, que precisa ter altura. */
export function MotorAnatomico(props: MotorAnatomicoProps) {
  // trocar de atlas ou versão recomeça do zero: nada de um corpo vaza para o outro
  const chave = urlDoPacote(props.baseUrl, props.atlas, props.versao);
  return <Motor key={chave} {...props} />;
}

type Carga = { sistema?: Sistema; erro?: string };

/** Marcador desenhado por cima de tudo também ganha o clique: entra no raycast com distância zero. */
function raycastNaFrente(this: InstancedMesh, raio: Raycaster, acertos: Intersection[]) {
  const antes = acertos.length;
  InstancedMesh.prototype.raycast.call(this, raio, acertos);
  for (const acerto of acertos.slice(antes)) acerto.distance = 0;
}

type Posicionado = Marcador & { posicao: Vetor3; estrutural: boolean };

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
 * Baixa cada sistema uma vez, quando fica visível ou quando um marcador precisa da geometria dele.
 * Uma falha é repetida quando o sistema é ligado de novo ou deixa de ser pedido.
 */
function useSistemas(base: string, pacote: Pacote | null, visiveis: string[], dosMarcadores: string[]) {
  const cache = useRef(new Map<string, Carga>());
  const visiveisAntes = useRef<string[]>([]);
  const [revisao, setRevisao] = useState(0);
  const pedidos = [...new Set([...visiveis, ...dosMarcadores])];
  const chave = `${visiveis.join(',')}|${dosMarcadores.join(',')}`;

  useEffect(() => {
    if (!pacote) return;
    const avisar = () => setRevisao((n) => n + 1);
    for (const [id, carga] of cache.current) {
      const religado = visiveis.includes(id) && !visiveisAntes.current.includes(id);
      if (carga.erro && (religado || !pedidos.includes(id))) cache.current.delete(id);
    }
    visiveisAntes.current = visiveis;
    for (const id of pedidos) {
      const definicao = pacote.manifesto.sistemas.find((s) => s.id === id);
      if (!definicao || cache.current.has(id)) continue;
      const carga: Carga = {};
      cache.current.set(id, carga);
      const porMalha = new Map(pacote.indice.filter((e) => e.glb === definicao.glb).map((e) => [e.malha, e]));
      const material = new MeshStandardMaterial({
        color: CORES_SISTEMA[id] ?? COR_PADRAO, roughness: 0.55, metalness: 0, side: DoubleSide,
      });
      carregarSistema(`${base}/${definicao.glb}`, porMalha, material).then(
        (sistema) => {
          if (cache.current.get(id) !== carga) return descartarSistema(sistema); // o motor saiu da tela
          carga.sistema = sistema;
          avisar();
        },
        (erro: unknown) => {
          console.error(erro);
          carga.erro = erro instanceof Error ? erro.message : String(erro);
          avisar();
        },
      );
    }
    avisar();
  }, [pacote, chave]);

  useEffect(() => {
    const atual = cache.current;
    return () => {
      for (const { sistema } of atual.values()) if (sistema) descartarSistema(sistema);
      atual.clear();
    };
  }, []);

  return { cache: cache.current, revisao };
}

function Motor({
  atlas, versao, baseUrl, sistemasVisiveis, marcadores = [], selecionado,
  onEscolherPonto, onSelecionarMarcador, onMarcadoresSemPosicao,
}: MotorAnatomicoProps) {
  const base = urlDoPacote(baseUrl, atlas, versao);
  const [pacote, setPacote] = useState<Pacote | null>(null);
  const [falha, setFalha] = useState('');

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

  const { cache, revisao } = useSistemas(base, pacote, sistemasVisiveis, dosMarcadores);
  const prontos = sistemasVisiveis.filter((id) => cache.get(id)?.sistema);
  const carregando = sistemasVisiveis.filter((id) => cache.has(id) && !cache.get(id)!.sistema && !cache.get(id)!.erro);
  const aviso = [
    falha,
    !pacote && !falha ? 'Carregando atlas…' : '',
    ...sistemasVisiveis.map((id) => (cache.get(id)?.erro ? `Falha ao carregar ${id}: ${cache.get(id)!.erro}` : '')),
    carregando.length ? `Carregando ${carregando.join(', ')}…` : '',
  ].filter(Boolean).join(' ');

  const { posicionados, semPosicao, pendentes } = useMemo(() => {
    const obter = (entrada: EntradaIndice) => {
      if (!pacote?.manifesto.sistemas.some((s) => s.id === entrada.sistema)) return null;
      const carga = cache.get(entrada.sistema);
      if (carga?.sistema) return carga.sistema.malhas.get(entrada.malha)?.geometry ?? null;
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

  const escolher = (evento: ThreeEvent<MouseEvent>) => {
    if (evento.delta > 5) return; // arrasto gira a câmera, não escolhe ponto
    const { name: malha, userData } = evento.object;
    const { sistema, estrutura } = userData;
    // pele translúcida deixa o clique passar para o que houver atrás (estrutura ou marcador)
    if (peleTranslucida && sistema === PELE && evento.intersections.some((i) => i.object.userData.sistema !== PELE))
      return;
    evento.stopPropagation(); // só a superfície mais próxima
    onEscolherPonto?.(ancoraDeIntersecao(evento, { atlas, atlas_versao: versao, sistema, estrutura, malha }));
  };

  return (
    <div
      style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}
      data-motor
      data-carregados={prontos.join(' ')}
      data-marcadores={posicionados.length}
      data-pele={peleTranslucida ? 'translucida' : 'opaca'}
    >
      <Canvas
        flat
        camera={{ fov: 35, near: 0.005, far: 50, position: [0, 0, 4] }}
        dpr={[1, 2]}
        onCreated={({ raycaster }) => { raycaster.firstHitOnly = true; }}
        aria-label="Corpo em 3D"
      >
        <Camera alvo={prontos.length ? cache.get(prontos[0]!)!.sistema! : null} />
        <hemisphereLight args={[0xffffff, 0x444444, 2.2]} />
        {/* ponytail: uma chamada de desenho por estrutura; BatchedMesh se ficar lento com tudo ligado */}
        {prontos.map((id) => (
          <primitive key={id} object={cache.get(id)!.sistema!.grupo} onClick={escolher} />
        ))}
        {grupos.map(([chave, itens]) => (
          <Instancias key={chave} itens={itens} destaque={itens[0]!.id === selecionado} onSelecionar={onSelecionarMarcador} />
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

/** Órbita, luz presa à câmera e enquadramento do primeiro sistema que chegar. */
function Camera({ alvo }: { alvo: Sistema | null }) {
  const camera = useThree((s) => s.camera);
  const cena = useThree((s) => s.scene);
  const tela = useThree((s) => s.gl.domElement);
  const tamanho = useThree((s) => s.size);
  const controles = useRef<OrbitControls | null>(null);
  const enquadrado = useRef(false);

  useLayoutEffect(() => {
    // o lado que se olha fica sempre iluminado
    const luz = new DirectionalLight(0xffffff, 1.4);
    luz.position.set(0.5, 1, 1);
    camera.add(luz);
    cena.add(camera);
    const orbita = new OrbitControls(camera, tela);
    orbita.enableDamping = true;
    controles.current = orbita;
    return () => {
      orbita.dispose();
      camera.remove(luz);
      cena.remove(camera);
    };
  }, [camera, cena, tela]);

  useLayoutEffect(() => {
    if (!alvo || enquadrado.current || !controles.current) return;
    enquadrado.current = true;
    const caixa = new Box3().setFromObject(alvo.grupo);
    const centro = caixa.getCenter(new Vector3());
    const distancia = distanciaDeEnquadramento(caixa, 35, tamanho.width / tamanho.height);
    controles.current.target.copy(centro);
    camera.position.set(centro.x, centro.y, centro.z + distancia);
    controles.current.update();
  }, [alvo, camera, tamanho]);

  useFrame(() => controles.current?.update());
  return null;
}
