# Segurança da fase 1

Este laboratório é local, individual e apenas dry-run. Não foi auditado para operação real ou exposição pública.

- Sem chaves de corretora e sem cadastro público. Não reaproveitar credenciais dos protótipos antigos.
- `init` usa aleatoriedade criptográfica para senha, JWT e token WebSocket. Segredos são serializados em JSON, sem geração/interpolação de código executável.
- `.private` tem modo 0700 no Linux/WSL. `config.json` tem 0644 para o UID do container conseguir ler o bind mount; o diretório pai limita leitura no host. Administrador, Docker e processos do próprio usuário continuam podendo acessar. Não compartilhe essa pasta.
- O serviço executa como UID/GID do usuário que rodou `init`. Use um usuário comum. Windows nativo tem outras regras de permissão; o caminho documentado é Ubuntu/WSL.
- Imagem oficial fixada por digest após download. Isso fixa o conteúdo, mas não comprova ausência de vulnerabilidades. Atualizações exigem novos testes e registro do novo digest.
- API somente na interface local do host; sem TLS porque esta fase não permite acesso remoto. Não use ngrok ou encaminhamento de portas.
- O cliente de teste desabilita proxies de ambiente e redirecionamentos para não encaminhar a autenticação local a outro destino.
- Diretórios de dados, bancos, logs, `.env` e `.private` são ignorados pelo Git. Antes de publicar arquivos adicionais, confira `git status` e `git diff --cached` localmente.
- Backups de `user_data` e `.private` devem ser privados. Não enviar para repositório, issue ou artefato de CI.

Se um segredo for publicado, remova a exposição e rotacione o segredo; apagar apenas o arquivo do commit atual não remove cópias e histórico. Não abra issues públicas com senhas ou chaves.

Se no futuro houver acesso remoto: definir VPN/TLS, autenticação adequada, limites de tentativas, atualização de dependências e regras de autorização antes de liberar esse acesso. Não há implementação de 2FA nesta base.
