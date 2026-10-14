# Teste dinâmico com OWASP ZAP (laboratório local) — Etapa 11

Escopo: **somente a API local** (`localhost:8000`). Nunca apontar ZAP para
terceiros sem autorização escrita. Scan *baseline* (superfície pública, sem
login); scan autenticado fica como evolução (exige script de auth com refresh).

## Procedimento

```bash
cd ~/projects/dataguard-api
. .venv/bin/activate
uvicorn app.main:app --port 8000 &   # terminal 1

# Conectividade container -> API (via host.docker.internal):
docker run --rm curlimages/curl:8.12.1 -s http://host.docker.internal:8000/health

# Baseline (relatórios em ./zap_out):
mkdir -p zap_out
docker run --name zapbase ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t http://host.docker.internal:8000 \
  -J report.json -r report.html
docker cp zapbase:/zap/report.json zap_out/
docker cp zapbase:/zap/report.html zap_out/
docker rm zapbase
```

`zap_out/` é ignorado pelo git (relatórios locais, não evidência versionada);
o triage vai abaixo, com data e versão da imagem.

## Triagem (execução real)

*Imagem: `ghcr.io/zaproxy/zaproxy:stable` (pull em 2026-10-14).*
*Alvo: `http://host.docker.internal:8000` — API de dev com banco local.*
*Comando com `-I` (warnings não falham); saída completa/console + `report.json`.*

Resultado: **66 PASS, 0 FAIL, 1 WARN Informational.**

| Alerta | Risco | Veredito |
|---|---|---|
| Storable and Cacheable Content [10049] em `/robots.txt` e `/sitemap.xml` (404) | Informational | **Corrigido na causa geral**: respostas 404 sem `Cache-Control`; como o princípio vale para as respostas autenticadas (não devem parar em cache de intermediário), adicionado middleware `SecurityHeadersMiddleware` (`Cache-Control: no-store` + `X-Content-Type-Options: nosniff`) com testes. Reran limpo (ver abaixo) |
| Spider: `/` retorna 404 ("expected 200") | — | **Comportamento correto**: API sem rota raiz por design; `/health` é o endpoint de vida |

Reexecução após o middleware: o `10049-3` sumiu; no lugar, `10049-1 Non-Storable
Content` (Informational) nas 3 URLs — esse é o estado de confirmação da regra
("verificado: não armazenável"), não um problema. Placares: 66 PASS, 0 FAIL,
1 INFO por design. Confirmado ainda que as respostas 404 carregam
`cache-control: no-store` (curl -I) e que o código-fonte da regra (beta, aberto)
só chega ao 10049-3 quando nenhum `no-store` está presente.

Regras do triage: cada alerta vira correção, falso-positivo documentado ou
risco aceito com justificativa — nunca silenciado sem registro.

## Limitações (declaradas)

- Baseline não autentica: cobertura parcial (rotas com JWT não são exercitadas).
- Scanner dinâmico acha sintoma, não prova ausência (mesma ressalva das Etapas 5).
- Não roda no CI de propósito: precisa da app no ar, é lento e tem
  flakiness de rede — CI guarda o determinístico; ZAP é procedimento de bancada.
