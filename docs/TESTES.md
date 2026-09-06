# Plano de testes

## Registro inicial

Executado no ambiente de preparação: testes unitários Python e compilação sintática. Docker não está disponível nesse ambiente. Não foram executados bot, FreqUI, conexão à Binance, backtest ou testes reais de ordens. A instalação e a estratégia precisam passar pela validação dentro da imagem oficial.

## Aceite da fase 1

| Teste | Como executar | Aprovação |
|---|---|---|
| Ambiente | `python3 scripts/lab.py doctor` | Docker/Compose disponíveis e daemon Linux funcionando |
| Regras locais | `python3 -m unittest discover -s tests -v` | Todos os testes passam |
| Configuração | `python3 scripts/lab.py check` | Digest fixo, localhost e dry-run |
| Imagem/estratégia | `docker compose run --rm freqtrade list-strategies --config /freqtrade/config.json --strategy-path /freqtrade/user_data/strategies` | ObserveStrategy carregada sem erros |
| Inicialização | `python3 scripts/lab.py start` e `docker compose ps` | Serviço permanece ativo e fica saudável |
| Autenticação/API | `python3 scripts/lab.py smoke` | Todos os critérios exibidos como PASS |
| Dados de mercado | Abrir gráficos e aguardar novo candle | Dados de BTC/USDT e ETH/USDT avançam no tempo |
| Reinício | `stop`, `start`, `smoke` | Login continua válido e banco local preservado |
| Operações | Verificar painel | Nenhuma posição: estratégia observacional |
| Rede | Confirmar porta publicada no `docker compose ps` | Apenas 127.0.0.1:8080 |

O teste unitário simula a API para testar o nosso verificador; não substitui o `smoke`. O job de container verifica o carregamento da estratégia, mas não precisa obter dados da corretora nem gera ordens. Registro de sucesso do HTTP não substitui o teste visual de candles.

## O que enviar para ajudar no teste

Sistema operacional, RAM, processador e espaço livre; saída de `doctor`; resultado de `smoke`; nome do erro e trecho revisado dos logs. Não enviar `credentials`, `.private/config.json`, tokens, cookies ou dump completo do ambiente.

## Próxima fase: negociação simulada

Após aceite da infraestrutura, implementar uma estratégia de estudo separada, com testes de sinais, dados históricos, custos, spread, slippage e análise de uso indevido de dados futuros. Validar atualização de operações abertas/fechadas, cálculo de resultados, reinício e perda de conexão. Manter dry-run.

Não interpretar a ausência de operações da ObserveStrategy como validação financeira. Ela intencionalmente não produz sinais de entrada. Lucro, drawdown, quantidade de negócios e desempenho fora da amostra só fazem sentido quando houver uma estratégia de negociação testável.
