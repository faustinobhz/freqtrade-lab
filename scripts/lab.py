"""CLI local: Python 3.10+, biblioteca padrão; não instala pacotes no host."""
import argparse
import base64
import copy
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "freqtradeorg/freqtrade:stable"
API = "http://127.0.0.1:8080/api/v1"


def build_config(base):
    cfg = copy.deepcopy(base)
    cfg["api_server"].update(username="alison", password=secrets.token_urlsafe(32),
                             jwt_secret_key=secrets.token_hex(32),
                             ws_token=secrets.token_urlsafe(32))
    validate(cfg)
    return cfg


def validate(cfg):
    """Contrato da fase 1: laboratório local, sem chaves de corretora."""
    if cfg.get("dry_run") is not True or cfg.get("force_entry_enable") is not False:
        raise ValueError("Esta base exige dry_run=true e force_entry_enable=false.")
    if cfg.get("trading_mode") != "spot":
        raise ValueError("A fase 1 permite apenas spot.")
    exchange = cfg.get("exchange", {})
    if any(exchange.get(k) for k in ("key", "secret", "password", "uid", "apiKey")):
        raise ValueError("Remova as credenciais de corretora: testes usam dados públicos.")
    api = cfg.get("api_server", {})
    if api.get("CORS_origins") != [] or api.get("listen_port") != 8080:
        raise ValueError("Mantenha a configuração local de API da fase 1.")
    if api.get("enabled") is not True:
        raise ValueError("A API precisa estar habilitada para os testes.")
    for field in ("password", "jwt_secret_key", "ws_token"):
        if len(api.get(field, "")) < 32:
            raise ValueError("Execute init para gerar segredos locais fortes.")


def run(args, capture=False):
    return subprocess.run(args, cwd=ROOT, check=True, text=True,
                          capture_output=capture).stdout


def init():
    target = ROOT / ".private/config.json"
    env = ROOT / ".env"
    if target.exists() or env.exists():
        raise ValueError("Configuração já existe ou inicialização parcial. Não será sobrescrita.")
    if not shutil.which("docker"):
        raise ValueError("Instale/inicie Docker e Docker Compose antes de executar init.")
    run(["docker", "compose", "version"])
    run(["docker", "info", "--format", "{{.OSType}}"], capture=True)
    run(["docker", "pull", IMAGE])
    digests = json.loads(run(["docker", "image", "inspect", IMAGE, "--format",
                              "{{json .RepoDigests}}"], capture=True))
    digest = next((d for d in digests or [] if re.fullmatch(
        r"freqtradeorg/freqtrade@sha256:[0-9a-f]{64}", d)), None)
    if not digest:
        raise ValueError("Não foi possível fixar a imagem oficial por digest.")
    cfg = build_config(json.loads((ROOT / "config/base.json").read_text()))
    target.parent.mkdir(mode=0o700, exist_ok=True)
    # Permite ao UID do container ler o arquivo montado; pasta host é privada (0700).
    # No Windows, use dentro do filesystem do WSL2 para respeitar permissões POSIX.
    with target.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(cfg, indent=2) + "\n")
    target.chmod(0o644)
    with env.open("x", encoding="utf-8") as handle:
        handle.write("FREQTRADE_IMAGE=" + digest + "\n")
    run(["docker", "compose", "run", "--rm", "--entrypoint", "python", "freqtrade", "-c",
         "from pathlib import Path; "
         "[Path('/freqtrade/user_data', name).mkdir(parents=True, exist_ok=True) "
         "for name in ('logs', 'data', 'backtest_results')]"])
    print("Configuração criada. Imagem fixada por digest; segredos não exibidos.")
    print("Execute: python3 scripts/lab.py start")


def local_config():
    cfg = json.loads((ROOT / ".private/config.json").read_text())
    validate(cfg)
    return cfg


def assert_compose():
    model = json.loads(run(["docker", "compose", "config", "--format", "json"], capture=True))
    service = model["services"]["freqtrade"]
    ports = service.get("ports", [])
    if len(ports) != 1 or ports[0].get("host_ip") != "127.0.0.1" or str(ports[0].get("published")) != "8080":
        raise ValueError("Publicação de porta deve permanecer em 127.0.0.1:8080.")
    if str(service.get("environment", {}).get("FREQTRADE__DRY_RUN")).lower() != "true":
        raise ValueError("Compose deve manter a trava de dry_run.")
    if not re.fullmatch(r"freqtradeorg/freqtrade@sha256:[0-9a-f]{64}", service["image"]):
        raise ValueError("A imagem precisa estar fixada por digest oficial.")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(path, authorization=None, method="GET"):
    headers = {"Accept": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    req = urllib.request.Request(API + path, headers=headers, method=method)
    # Não envia senha por proxies do ambiente ou redirecionamentos HTTP.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(req, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, {}


def basic(username, password):
    return "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()


def smoke():
    cfg = local_config()
    status, payload = request("/ping")
    if status != 200 or payload.get("status") != "pong":
        raise ValueError("Ping indisponível. Consulte docker compose logs --tail=80.")
    status, _ = request("/show_config")
    if status not in (401, 403):
        raise ValueError("A API não rejeitou leitura sem autenticação.")
    status, _ = request("/token/login", basic("invalid", secrets.token_hex(16)), "POST")
    if status not in (401, 403):
        raise ValueError("A API não rejeitou credenciais inválidas.")
    api = cfg["api_server"]
    status, payload = request("/token/login", basic(api["username"], api["password"]), "POST")
    if status != 200 or not payload.get("access_token"):
        raise ValueError("Falha no login HTTP Basic. Nenhuma credencial será exibida.")
    auth = "Bearer " + payload["access_token"]
    status, payload = request("/show_config", auth)
    if status != 200 or payload.get("dry_run") is not True:
        raise ValueError("O bot não confirmou dry_run=true.")
    if payload.get("strategy") != "ObserveStrategy":
        raise ValueError("Estratégia inesperada para a fase 1.")
    status, trades = request("/status", auth)
    if status != 200 or not isinstance(trades, list) or trades:
        raise ValueError("A fase de observação exige status válido sem posições abertas.")
    print("PASS: ping, acesso anônimo bloqueado, senha incorreta rejeitada, login e JWT,")
    print("dry_run ativo, ObserveStrategy carregada e nenhuma posição aberta.")
    print("Ainda verificar no FreqUI: candles recebidos e atualização após 5 minutos.")


def doctor():
    print("Python:", sys.version.split()[0], "| plataforma:", sys.platform)
    print("Docker disponível:", bool(shutil.which("docker")))
    if shutil.which("docker"):
        for command in (["docker", "--version"], ["docker", "compose", "version"],
                        ["docker", "info", "--format", "{{.OSType}}"]):
            try:
                print(run(command, capture=True).strip())
            except subprocess.CalledProcessError:
                print("FALHOU:", " ".join(command[:3]))
    free = shutil.disk_usage(ROOT).free // (1024 ** 3)
    print("Espaço livre (GiB):", free)
    print("Configuração local presente:", (ROOT / ".private/config.json").exists())
    print("Este diagnóstico não imprime senhas, tokens ou variáveis de ambiente.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["doctor", "init", "check", "start", "smoke", "credentials", "stop"])
    action = parser.parse_args().action
    try:
        if action == "doctor":
            doctor()
        elif action == "init":
            init()
        elif action in ("check", "start"):
            local_config()
            assert_compose()
            if action == "start":
                run(["docker", "compose", "up", "-d"])
                print("Abra http://127.0.0.1:8080. Aguarde o bot e execute smoke.")
            else:
                print("PASS: configuração local e Compose validados.")
        elif action == "smoke":
            smoke()
        elif action == "credentials":
            api = local_config()["api_server"]
            print("Somente para seu uso local. Não compartilhe esta saída.")
            print("Usuário:", api["username"], "\nSenha:", api["password"])
        elif action == "stop":
            run(["docker", "compose", "down"])
    except (ValueError, OSError, subprocess.CalledProcessError, urllib.error.URLError) as exc:
        # Falhas de JSON/configuração não incluem o conteúdo que pode conter segredos.
        if isinstance(exc, ValueError) and not isinstance(exc, json.JSONDecodeError):
            print("ERRO:", str(exc), file=sys.stderr)
        else:
            print("ERRO: operação não concluída. Verifique Docker, arquivos locais e conectividade.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
