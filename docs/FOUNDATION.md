# Fundação — Copy Minas Site vNext

## Regra principal

A nova geração do site é construída do zero.

O conteúdo anterior do repositório foi preservado integralmente em `/old`.
O ZIP de desenvolvimento analisado serve apenas como referência de comportamento e conteúdo. Nenhum controller, template, CSS ou estrutura antiga deve ser copiado por inércia.

## Autoridades de referência

### Marca

A nova logo cromada Copy Minas é a referência visual principal.

Direção:
- fundo preto / azul-preto;
- branco e prata/cromado;
- vermelho Copy Minas;
- azul como acento tecnológico;
- amarelo/dourado reservado principalmente a Minas Gerais no globo.

### Globo 3D

Referência conceitual aprovada:
- mundo: branco/prata;
- Brasil: vermelho;
- Minas Gerais: amarelo/dourado;
- Elói Mendes / Copy Minas: azul;
- globo pequeno integrado ao site;
- clique abre experiência ampliada;
- clique no ponto azul abre a localização oficial no Google Maps;
- dados geográficos devem ser locais ou pré-processados para produção;
- não executar milhões de testes geoespaciais no navegador a cada visita.

### Produto

O site precisa entregar:
1. presença institucional;
2. catálogo;
3. página individual de produto;
4. contato/orçamento;
5. administração simples do catálogo;
6. experiência de localização pelo globo.

## O que NÃO herdar automaticamente

- login/dashboard do site antigo;
- manutenção/chamados antigos;
- CSS legado;
- templates legados;
- controllers legados;
- schema antigo como autoridade automática;
- arquivos de ambiente, logs, caches ou `.venv`;
- o ZIP como estrutura de projeto.

## Princípios

- complexidade somente quando necessária;
- interface responsiva;
- acessibilidade;
- assets otimizados;
- configuração DEV e produção separadas;
- segredos nunca versionados;
- banco versionado por migrações quando entrar na fase de persistência;
- produto e categoria devem usar estruturas nomeadas, não índices mágicos de tupla.
