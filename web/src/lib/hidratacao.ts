import { useSyncExternalStore } from "react";

const nunca = () => () => {};

/**
 * false no HTML do servidor e até o React assumir a página. Antes disso um controle aceita o toque, mas
 * ninguém o ouve (um filtro mostraria uma escolha sem filtrar): deixe-o desabilitado.
 */
export const useHidratado = () => useSyncExternalStore(nunca, () => true, () => false);
