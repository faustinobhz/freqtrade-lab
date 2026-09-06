# Evolução do projeto

1. **Infraestrutura local (este pacote):** Freqtrade/FreqUI oficial, SQLite, imagem fixada, autenticação local, observação e teste de conexão. Aceite pendente no ambiente do usuário.
2. **Estratégia de estudo:** definir hipótese de entrada/saída e risco, implementar testes, baixar histórico, fazer backtest e análises de vieses, acompanhar dry-run. Nenhuma alegação de rentabilidade.
3. **Painel personalizado da ideia original:** definir telas com o usuário, começar por leitura da API, dados reais e indicação explícita de indisponibilidade. Manter o histórico do bot como fonte principal para evitar dupla sincronização.
4. **Controles adicionais:** caso necessários, comandos autenticados e autorizados, proteção CSRF quando houver cookies, registro de ações, tratamento de erros e testes ponta a ponta. Evitar reimplementar autenticação sem necessidade.
5. **Operação contínua e acesso remoto:** avaliar máquina dedicada, backups, recuperação, VPN e requisitos de acesso. Escopo separado da instalação local.
6. **Operações reais:** decisão futura explícita, após revisão técnica e validação da estratégia. Não contempladas nesta base.

Raspberry Pi e FreqAI serão avaliados conforme hardware e necessidade. A primeira versão visa reduzir dependências e descobrir problemas com facilidade. Requisitos multiusuário e múltiplos bots precisam de definição antes de modificar a arquitetura.
