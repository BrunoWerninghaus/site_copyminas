# Copy Minas — Site vNext

Nova geração do site institucional e catálogo da Copy Minas.

## Estado

O projeto está sendo reconstruído do zero.

- `/old`: snapshot integral do site anterior, preservado apenas como histórico.
- `/src/copyminas`: nova aplicação.
- `/docs`: contratos e decisões da nova geração.
- O ZIP de desenvolvimento analisado anteriormente é referência funcional/visual, não fonte de código.

## Rotas atuais

- `/` — Home pública;
- `/home` — mesma Home pública;
- `/solucoes` — áreas de atuação;
- `/produtos` — catálogo migrado do Site 2;
- `/produtos/<slug>` — ficha individual do produto;
- `/empresa` — identidade e dados institucionais;
- `/contato` — contato e localização.

## Contrato de conteúdo

O site usa somente informações confirmadas pela autoridade de conteúdo definida no projeto e não inventa informações comerciais.

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


## Gerações

- **Site 1**: snapshot histórico em `/old`.
- **Site 2**: fonte de dados do catálogo migrado.
- **Site 3**: aplicação atual.

A rastreabilidade da migração do catálogo está documentada em `docs/SITE2_CATALOG_MIGRATION.md`.


## Testes rápidos

Os testes públicos usam apenas `unittest` da biblioteca padrão:

```bash
python -m unittest discover -s tests -v
```
