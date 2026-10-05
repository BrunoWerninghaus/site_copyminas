# Atlas Eleitoral

Projeto independente de visualização cívica e eleitoral, hospedado temporariamente dentro do repositório `site_copyminas`.

> **Estado atual:** especificação / documentação. Nenhum código de produção do Atlas está integrado ao site CopyMinas.

## Isolamento obrigatório

O Atlas Eleitoral **não é um módulo do site CopyMinas**. O repositório é apenas o recipiente atual.

O Atlas não deve:

- importar código de `src/copyminas`;
- usar banco de dados, tabelas, credenciais ou sessões da CopyMinas;
- registrar rotas dentro da aplicação Flask da CopyMinas;
- depender da identidade visual ou do catálogo comercial da CopyMinas;
- alterar o comportamento de build, teste ou deploy do site principal sem decisão explícita futura.

Quando houver implementação, ela deverá permanecer contida em `projects/atlas-eleitoral/`.

## Objetivo

Transformar dados públicos oficiais do Brasil em uma interface navegável que permita:

- explorar resultados eleitorais por Brasil, UF e município;
- acompanhar apuração oficial quando houver eleição em andamento;
- comparar votação de candidaturas e partidos sem produzir ranking editorial;
- identificar pessoas eleitas e distinguir eleição, diplomação, posse e exercício;
- visualizar histórico eleitoral;
- consultar atividade parlamentar oficial quando a instituição responsável disponibilizar dados;
- manter rastreabilidade até a fonte oficial de cada fato exibido.

## Fontes de autoridade

- Tribunal Superior Eleitoral (TSE): candidaturas, votação, totalização e eleitos.
- Instituto Brasileiro de Geografia e Estatística (IBGE): geocódigos e malhas territoriais.
- Câmara dos Deputados: exercício parlamentar, proposições, votações, órgãos e demais dados legislativos federais publicados pela Câmara.
- Senado Federal: exercício parlamentar, mandatos, comissões e votações publicados pelo Senado.
- Assembleias Legislativas, prefeituras e câmaras municipais: somente quando houver fonte oficial adequada para o dado exibido.

## Regra central

**O Atlas não cria fatos políticos.**

A aplicação pode organizar, relacionar, agregar e visualizar dados. Ela não deve transformar inferência própria em fato oficial. Em especial, uma pessoa só deve aparecer como `ELEITA` quando a fonte eleitoral oficial fornecer esse estado; e uma pessoa só deve aparecer como `EM EXERCÍCIO` quando uma fonte institucional adequada sustentar esse estado.

## Especificação

Leia [docs/ATLAS_ELEITORAL_SPEC.md](docs/ATLAS_ELEITORAL_SPEC.md).

## Estrutura prevista

```text
projects/atlas-eleitoral/
├── README.md
├── docs/
│   └── ATLAS_ELEITORAL_SPEC.md
├── backend/        # futuro
├── frontend/       # futuro
├── ingestion/      # futuro
├── data/           # futuro; dados derivados/cache, nunca segredos
└── tests/          # futuro
```

A presença desses diretórios futuros neste documento não autoriza implementação antes da aprovação do plano correspondente.
