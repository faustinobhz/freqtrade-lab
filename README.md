# Freqtrade Lab

Base inicial da ideia de Alison Faustino: executar e observar o Freqtrade com uma instalação simples, dados reais de mercado e nenhuma ordem real.

**Estado: fase 1 — observação e validação da infraestrutura.** O pacote inicial passou pelos testes unitários locais. A execução da imagem Docker, o painel e a conexão com a corretora ainda precisam ser validados no computador de destino. Não é um produto pronto para operar dinheiro real.

## Arquitetura

Um container oficial do Freqtrade fornece motor, API autenticada e FreqUI. O histórico fica no SQLite do próprio bot, persistido no volume Docker `bot_data`. O host publica somente `127.0.0.1:8080`. Python no host serve apenas para configurar e verificar a instalação.

O painel PHP antigo e seus instaladores não são incorporados. A interface personalizada será uma próxima etapa, após validar o núcleo. Não há MySQL, cadastro público, armazenamento de chaves de corretora, FreqAI ou acesso remoto nesta fase.

## O que você precisa

- Linux com Docker Engine + Compose, ou Windows com WSL2 Ubuntu e Docker Desktop integrado ao WSL.
- Python 3.10 ou superior e Git.
- Como orçamento inicial do laboratório: 8 GB de RAM no computador, cerca de 4 GB disponíveis ao Docker, 2 núcleos e 15–20 GB livres. São estimativas de trabalho, não mínimos oficiais nem garantia de desempenho.
- Internet para baixar a imagem e acessar os dados públicos da Binance. Se a rede/região bloquear a corretora, a inicialização poderá falhar; não use contornos de restrição, escolha uma corretora disponível e revise pares/configuração.
- Sem conta de corretora, depósito, API Key, cartão, GPU, VPS ou domínio para esta fase.

No Windows, execute os comandos no terminal Ubuntu/WSL e guarde o projeto em `~/projetos/freqtrade-lab`, não em `/mnt/c`. No Linux, use seu usuário comum com acesso ao Docker, sem executar o projeto inteiro com sudo.

## Primeira execução

Clone o repositório e abra a pasta do projeto:

```bash
git clone https://github.com/faustinobhz/freqtrade-lab.git
cd freqtrade-lab
```

Se usar o ZIP, extraia-o e abra a pasta `freqtrade-lab`.

```bash
python3 scripts/lab.py doctor
python3 -m unittest discover -s tests -v
python3 scripts/lab.py init
python3 scripts/lab.py check
python3 scripts/lab.py start
```

`init` baixa a imagem oficial `stable` disponível naquele momento e fixa seu digest exato em `.env`. Assim, reiniciar não troca silenciosamente a versão. Esse arquivo não contém senhas. Guarde o digest junto ao registro dos testes; instalações novas podem selecionar uma versão diferente. Não há atualização automática.

As credenciais ficam em `.private/config.json`, fora do Git. `init` não sobrescreve configurações existentes. Se for interrompido e deixar arquivos parciais, confira esses dois arquivos antes de mover/remover qualquer coisa e repetir. Não apague bancos para resolver uma falha de inicialização.

Abra **http://127.0.0.1:8080**. Para consultar seu login local:

```bash
python3 scripts/lab.py credentials
```

Não envie a saída de `credentials`, o arquivo de configuração ou imagens mostrando a senha. O login inicial é `alison`; a senha é aleatória e diferente em cada instalação. Não há 2FA acrescentado por este projeto; nesta fase o acesso é somente local e depende também da proteção da sua conta no computador.

Após o bot ficar disponível:

```bash
python3 scripts/lab.py smoke
docker compose ps
```

O teste `smoke` verifica ping, rejeição de acesso anônimo, rejeição de senha errada, login Basic, consulta com JWT, dry-run efetivo, estratégia esperada e ausência de posições abertas. Ele não envia comandos de compra/venda nem testa rentabilidade.

No FreqUI, confirme o nome da estratégia `ObserveStrategy`, modo dry-run e os pares BTC/USDT e ETH/USDT. Observe a atualização dos candles após pelo menos um intervalo de 5 minutos. Zero operações é esperado: esta estratégia não emite entradas.

## Comandos úteis

```bash
# Diagnóstico sem senhas: esta saída pode ser enviada para suporte.
python3 scripts/lab.py doctor
# Logs podem conter informações operacionais: revise antes de compartilhar.
docker compose logs --tail=80
# Parar e preservar arquivos locais.
python3 scripts/lab.py stop
# Iniciar novamente com validação.
python3 scripts/lab.py start
```

Não abra portas no roteador e não altere `127.0.0.1` para permitir acesso externo. Publicar o código no GitHub não hospeda o bot: ele continua executando no seu computador. A API dentro do container escuta em `0.0.0.0` para o encaminhamento do Docker; somente a porta local do host é publicada.

O container usa o usuário `ftuser` da imagem oficial. Dados, logs e bancos ficam no volume Docker, enquanto o código da estratégia é montado somente para leitura. `stop` preserva os dados; não execute `docker compose down -v`, que remove o volume. A pasta `user_data` do repositório contém apenas a estratégia, não uma cópia do banco em execução.

## Verificações e limites

- `tests/test_lab.py`: testes locais com respostas simuladas, sem Docker e sem mercado.
- GitHub Actions: testes unitários, validação do Compose e carregamento de estratégia dentro da imagem oficial. Consulte o resultado de cada execução na aba Actions do repositório; o sucesso dos testes locais não substitui a validação do container.
- `smoke`: teste contra o bot efetivamente rodando no seu computador.
- [docs/TESTES.md](docs/TESTES.md): critérios de aceite e próximos testes.
- [docs/ROADMAP.md](docs/ROADMAP.md): evolução até estratégias e painel próprio.
- [SECURITY.md](SECURITY.md): limites e tratamento de segredos.

O healthcheck verifica apenas a disponibilidade do HTTP; não prova atualização dos candles, segurança completa nem funcionamento de uma estratégia de negociação. As travas deste laboratório evitam erros acidentais, mas não protegem contra alguém que tenha controle administrativo do host ou altere os arquivos.

## Repositório e contribuições

Código: [faustinobhz/freqtrade-lab](https://github.com/faustinobhz/freqtrade-lab).
Testes: [GitHub Actions](https://github.com/faustinobhz/freqtrade-lab/actions).

Antes de enviar alterações, execute os testes e revise `git diff --cached`.
Nunca adicione `.private`, bancos, logs ou credenciais ao repositório.
Use branches e pull requests para mudanças futuras.

Nenhuma licença de redistribuição foi escolhida para o código próprio nesta etapa.
O Freqtrade é obtido separadamente e mantém sua licença original.

## Referências

- [Docker e FreqUI oficiais](https://www.freqtrade.io/en/stable/docker_quickstart/)
- [API e autenticação](https://www.freqtrade.io/en/stable/rest-api/)
- [Configuração](https://www.freqtrade.io/en/stable/configuration/)
- [Estratégias](https://www.freqtrade.io/en/stable/strategy-customization/)
