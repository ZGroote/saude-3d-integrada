# Metodologia Científica

Todo experimento (`EXP-XXXX`) conduzido neste projeto segue rigorosamente oito etapas sequenciais:

1. **Problema:** formulação objetiva da questão técnica, geométrica ou clínica a ser respondida.
2. **Hipótese:** proposição testável antes da execução.
3. **Protocolo:** definição prévia de métodos, algoritmos, datasets, versões, parâmetros, seeds e **critérios de sucesso definidos antes da execução**. Critérios não devem ser alterados após observar os resultados sem registro explícito da mudança.
4. **Execução:** rodagem reprodutível com registro de ambiente (hardware, SO, bibliotecas, comandos) e preservação de logs.
5. **Resultados:** registro fiel das métricas e saídas obtidas, sem omissão nem modificação posterior; experimentos malsucedidos ou inválidos são preservados integralmente.
6. **Validação:** verificação contra critérios independentes (*holdout*), testes sintéticos ou revisão por pares (separando explicitamente teste sintético de dado real e validação técnica de validação clínica).
7. **Conclusão:** classificação explícita da hipótese como **sustentada**, **rejeitada** ou **inconclusiva**, separando o que foi observado diretamente do que é interpretação.
8. **Próximo experimento:** encaminhamento derivado da conclusão.
