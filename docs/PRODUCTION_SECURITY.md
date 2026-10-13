# Site 3 — Hardening de produção (P1)

Esta etapa protege sessões, respostas HTTP, SMTP e envio de leads.
Não substitui testes de implantação, política de privacidade ou revisão do Cloudflare.

## Ambiente de produção

- `APP_ENV=production` (não depender de `FLASK_ENV` legado).
- `FLASK_DEBUG=0` e acesso externo somente por HTTPS/Cloudflare Tunnel.
- `SECRET_KEY` exclusiva, imprevisível, >=32 caracteres. Exemplo de geração:
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
  Nunca salvar a chave no Git. A aplicação não inicia em produção sem uma chave forte.
- `SMTP_SECURITY=starttls` (normalmente 587) ou `ssl` (normalmente 465);
  `none` é aceito **somente em DEV** e não inicia em produção.
  Confirme a configuração suportada pelo provedor antes da troca.
- `SESSION_COOKIE_SECURE` é automático em produção (HTTPS no navegador), mais
  HttpOnly/SameSite=Lax. Ao ativar produção usando HTTP local o navegador não
  devolverá o cookie: isso é esperado.
- Respostas incluem CSP, anti-iframe, no-sniff, Referrer-Policy e Permissions-Policy.
  HSTS está ativo em produção, sem includeSubDomains.
- A CSP autoriza temporariamente CDN/IBGE/GitHub usados pelo globo. Remover essas
  exceções quando o componente for local na próxima etapa.

## Contato / proteção anti-abuso

- Honeypot `website` invisível: posts preenchendo-o não chegam ao banco ou SMTP.
- Limite local padrão: 5 POSTs por 900 segundos por identidade; responde 429 +
  `Retry-After`. Mensagens grandes (>32768 bytes) recebem 413.
- Cada processo tem seu próprio estado de rate limit em memória. Reinício,
  múltiplos workers e ataques distribuídos **exigem regra adicional no Cloudflare
  WAF/Rate Limiting** para `POST /contato/enviar`.
- Nunca confiar em `X-Forwarded-For` para identificar clientes. O código usa
  `remote_addr` por padrão.
- Se o site for acessível **somente através do Cloudflare Tunnel** e o processo do
  túnel estiver ligado à origem em loopback, configurar
  `CONTACT_TRUSTED_PROXY_CIDRS=127.0.0.1/32,::1/128` permite usar
  `CF-Connecting-IP` de uma conexão vinda desses peers. Bloqueie acesso direto
  ao origin; caso contrário não habilite essa confiança.
- Ajustes: `CONTACT_RATE_LIMIT_COUNT`, `CONTACT_RATE_WINDOW_SECONDS`,
  `CONTACT_MAX_BYTES`. Não configure contagem zero.

## Verificações

1. Rodar `python -m unittest discover -s tests -v`.
2. Confirmar workflow **Public Gate** (Chromium desktop/tablet/mobile).
3. Com `APP_ENV=production` e sem `SECRET_KEY`, startup deve falhar.
4. Com `APP_ENV=production` e `SMTP_SECURITY=none`, startup deve falhar.
5. Verificar `Set-Cookie: Secure; HttpOnly; SameSite=Lax` no acesso HTTPS do Admin.
6. Validar SMTP STARTTLS/SSL com envio real controlado e verificar ambos e-mails.
7. Enviar mais de 5 POSTs na janela de teste e verificar 429; checar 413 e honeypot.
8. Definir no Cloudflare controle de POST e monitorar eventuais falsos positivos.

Não executar smoke real de SMTP ou WAF automaticamente no CI: requer configuração
privada de produção. Os testes automatizados cobrem os contratos sem credenciais reais.
