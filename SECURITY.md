# Segurança — como relatar problemas

## Escopo

Este é um **projeto educacional de portfólio**, mantido sem SLA e sem garantias.
Ele **não** está pronto para produção: não há TLS, segredos centralizados,
rate limit distribuído nem rotação de chaves (ver README, "Fora de escopo").

## Como relatar

**Não abra issue pública com detalhes da vulnerabilidade.** Prefira, nesta ordem:

1. **Private vulnerability reporting** do GitHub (aba Security → Report a vulnerability),
   se habilitado no repositório; ou
2. Mensagem privada ao mantenedor pelo perfil do GitHub.

Inclua: descrição, passos de reprodução, impacto estimado e, se houver, sugestão
de correção. Logs e exemplos devem usar **dados fictícios** (nunca dados reais).

## O que é útil relatar

Falhas de autenticação/autorização, exposição de observações em claro, bypass de
posse de registros, segredos commitados, dependência vulnerável sem correção
documentada.

## Fora de escopo de reporte

- Segredos de desenvolvimento claramente marcados em `.env.example`
  (placeholders locais, nunca usados fora do laboratório).
- Ausência dos controles listados como "fora de escopo" no README.
- Alertas de scanner sem demonstração de impacto (envie o PoC junto).

## Compromisso

Sem prazo garantido (projeto pessoal de estudo), mas todo relato legítimo será
analisado, corrigido se procedente e creditado no histórico, sem exposição de
dados sensíveis no processo.
