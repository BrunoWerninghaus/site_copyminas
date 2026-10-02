# Copy Minas — Site vNext

Nova geração do site institucional e catálogo da Copy Minas.

## Estado

O projeto está sendo reconstruído do zero.

- `/old`: snapshot integral do site anterior, preservado apenas como histórico.
- `/src/copyminas`: nova aplicação.
- `/docs`: contratos e decisões da nova geração.
- O ZIP de desenvolvimento analisado anteriormente é referência funcional/visual, não fonte de código.

## Rotas atuais

- `/` — entrada imersiva Copy Minas;
- `/home` — Home institucional.

## Contrato de conteúdo

Enquanto textos e imagens definitivos não forem fornecidos, o site usa placeholders explícitos e não inventa informações comerciais.

Leia `docs/SITE_CONTRACT.md`.

## Executar em desenvolvimento

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python app.py
```

A configuração local deve ficar em `.env`, nunca versionado.
