# Copy Minas — Site vNext

Nova geração do site institucional e catálogo da Copy Minas.

## Estado

Este projeto está sendo reconstruído do zero.

- `/old`: snapshot integral do site anterior, preservado apenas como histórico.
- `/src/copyminas`: nova aplicação.
- `/docs`: decisões e referências da nova geração.
- O ZIP de desenvolvimento analisado anteriormente é referência funcional/visual, não fonte de código.

## Objetivos

- nova identidade visual baseada na marca cromada Copy Minas;
- catálogo de produtos;
- administração simples de produtos;
- contato/orçamento;
- globo 3D interativo:
  - mundo em branco/prata;
  - Brasil em vermelho;
  - Minas Gerais em amarelo/dourado;
  - Copy Minas / Elói Mendes em azul;
  - clique no ponto da empresa abre a localização no Google Maps;
- arquitetura pequena, explícita e testável.

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
