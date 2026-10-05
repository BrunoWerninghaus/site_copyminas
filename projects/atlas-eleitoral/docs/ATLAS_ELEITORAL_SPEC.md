# Atlas Eleitoral — Especificação Canônica v0.1

**Status:** DESIGN APPROVED / SPECIFICATION  
**Projeto:** Atlas Eleitoral  
**Local:** `projects/atlas-eleitoral/`  
**Repositório hospedeiro:** `BrunoWerninghaus/site_copyminas`  
**Natureza:** projeto independente; o repositório CopyMinas é apenas o recipiente atual  
**Data da especificação:** 2026-10-05

---

## 1. Propósito

O Atlas Eleitoral é uma aplicação de visualização cívica e eleitoral baseada em fontes públicas oficiais brasileiras.

O produto deve permitir que uma pessoa comum pesquise o Brasil, um estado, um município, uma candidatura, um partido ou um agente político e compreenda, por meio de mapas e fichas objetivas:

1. como ocorreu uma eleição;
2. onde uma candidatura ou partido recebeu votos;
3. quem foi oficialmente eleito;
4. quem ocupa atualmente determinado cargo, quando houver fonte institucional adequada;
5. o histórico eleitoral disponível;
6. a atividade parlamentar publicada por órgãos oficiais;
7. a origem exata de cada informação apresentada.

O Atlas não é veículo de campanha, agregador de opinião ou fonte autônoma de fatos políticos.

### Princípio central

> **O Atlas não cria fatos políticos. Ele organiza, relaciona, agrega e visualiza fatos provenientes de fontes públicas oficiais.**

Toda informação politicamente relevante deve possuir proveniência rastreável.

---

## 2. Contrato de isolamento da CopyMinas

O Atlas Eleitoral é logicamente independente do site CopyMinas.

### 2.1. Proibições

A implementação do Atlas não deve:

- importar módulos de `src/copyminas`;
- utilizar banco de dados ou tabelas da CopyMinas;
- utilizar credenciais, sessões, autenticação ou cookies da CopyMinas;
- registrar rotas na aplicação Flask principal;
- compartilhar modelos de domínio;
- depender do catálogo comercial;
- alterar templates, CSS ou JavaScript do site institucional;
- alterar o fluxo de testes, build ou deploy da CopyMinas sem decisão explícita futura;
- apresentar o Atlas como produto oficial da Justiça Eleitoral ou de qualquer órgão consultado.

### 2.2. Fronteira física

Todo código, documentação, testes, cache e configuração específica do Atlas deve permanecer sob:

```text
projects/atlas-eleitoral/
```

Uma futura extração para repositório próprio deve ser possível sem refatoração do domínio.

---

## 3. Escopo funcional

### 3.1. Mapa eleitoral

O mapa deve permitir navegação por:

- Brasil;
- Unidade da Federação;
- município.

Filtros mínimos:

- ano da eleição;
- turno;
- cargo;
- candidatura;
- partido;
- situação do resultado.

Modos mínimos de visualização:

**Maior votação no território**  
Cada território é colorido segundo a candidatura com maior votação naquele recorte.

**Força de uma candidatura**  
A intensidade representa a participação percentual da candidatura no território selecionado.

**Comparação entre duas candidaturas**  
Exibe diferença de votos ou pontos percentuais sem declarar vencedor fora do estado oficialmente publicado.

**Partido**  
Exibe votação nominal/partidária e eleitos segundo a disponibilidade oficial do cargo e da eleição.

### 3.2. Página do município

Uma página municipal deve reunir, sem misturar conceitos:

- identificação oficial do município;
- resultados eleitorais históricos;
- eleição corrente, quando houver apuração oficial disponível;
- prefeito e vereadores eleitos na última eleição municipal;
- ocupantes atuais de cargos municipais somente quando uma fonte institucional oficial sustentar o estado atual;
- votação local para presidente, governador, senador, deputado federal e deputado estadual nas eleições aplicáveis;
- candidaturas mais votadas por cargo;
- eleitos que receberam votos naquele município;
- links de proveniência.

Deputado federal, deputado estadual e senador não devem ser apresentados como "representantes do município". A interface pode apresentar **votação recebida no município** e o âmbito jurídico correto do mandato.

### 3.3. Página da pessoa

A ficha de uma pessoa pode reunir:

- nome oficial na fonte;
- nome de urna quando aplicável;
- partido e UF no contexto da eleição/mandato;
- cargo disputado;
- situação eleitoral oficial;
- total de votos;
- mapa da votação;
- eleições anteriores disponíveis;
- mandato atual quando sustentado por fonte institucional;
- proposições, comissões, discursos, votações ou outras atividades parlamentares quando publicadas pela instituição responsável;
- links para os registros oficiais utilizados.

A ficha nunca deve fundir pessoas apenas por semelhança de nome. Identificadores oficiais e chaves de relacionamento são obrigatórios quando disponíveis.

### 3.4. Página de partido

Deve permitir:

- votação por eleição e cargo;
- distribuição territorial;
- candidaturas;
- eleitos;
- quantidade de cadeiras por recorte quando derivável de resultados oficiais;
- comparação histórica de cadeiras e votação.

A interface pode calcular diferenças aritméticas, como `+3 cadeiras`, desde que os valores de origem sejam oficiais e a transformação seja reproduzível.

---

## 4. Modelo temporal

O Atlas deve manter quatro conceitos independentes.

### 4.1. Histórico eleitoral

Resultados consolidados de eleições anteriores.

Base inicial:

- Eleições Gerais de 2022;
- Eleições Municipais de 2024.

Esses dados formam o primeiro corpus canônico histórico.

### 4.2. Apuração corrente

Dados oficiais de uma eleição enquanto a totalização está evoluindo.

O Atlas deve mostrar explicitamente:

- eleição;
- turno;
- abrangência;
- percentual/seções totalizadas conforme disponibilizado pela fonte;
- horário da última coleta;
- horário/identificador da geração da fonte quando disponível;
- estado de atualização.

### 4.3. Resultado eleitoral oficial

O resultado eleitoral não é sinônimo de exercício do cargo.

Estados de domínio mínimos:

```text
LIVE
TOTALIZED
OFFICIALLY_ELECTED
NOT_ELECTED
UNKNOWN
```

O Atlas **não deve criar por conta própria um estado "eleito matematicamente"**.

Uma candidatura só recebe `OFFICIALLY_ELECTED` quando a fonte oficial de resultados fornecer indicação compatível.

### 4.4. Exercício do mandato

Exercício é uma dimensão separada da eleição.

Estados mínimos:

```text
ELECTED_NOT_IN_OFFICE
IN_OFFICE
LEFT_OFFICE
SUBSTITUTE_IN_OFFICE
OFFICE_STATUS_UNKNOWN
```

Uma vitória eleitoral não autoriza o Atlas a marcar a pessoa como `IN_OFFICE`.

Para Câmara dos Deputados e Senado, o estado atual deve preferir as APIs institucionais de parlamentares em exercício. Para outras esferas, a fonte institucional oficial correspondente deve ser utilizada quando existir e puder ser integrada de forma confiável.

---

## 5. Fontes de autoridade

### 5.1. Tribunal Superior Eleitoral — autoridade eleitoral

Usos:

- candidaturas;
- partidos no contexto eleitoral;
- votação nominal;
- votação partidária;
- apuração;
- totalização;
- situação eleitoral;
- eleitos.

Fontes iniciais:

- Portal de Dados Abertos — Resultados 2022:  
  https://dadosabertos.tse.jus.br/dataset/resultados-2022
- Portal de Dados Abertos — Resultados 2024:  
  https://dadosabertos.tse.jus.br/dataset/resultados-2024
- Divulgação técnica de resultados 2026:  
  https://www.tse.jus.br/eleicoes/informacoes-tecnicas-sobre-a-divulgacao-de-resultados
- Ambiente oficial de resultados:  
  https://resultados.tse.jus.br

A documentação técnica do TSE para 2026 confirma o uso de arquivos JSON para divulgação, incluindo configuração, acompanhamento, resultado unificado e arquivo de eleitos.

### 5.2. IBGE — autoridade territorial

Usos:

- geocódigos;
- nomes territoriais;
- unidades federativas;
- malhas municipais.

Fonte inicial:

- Malha Municipal Digital:  
  https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/15774-malhas

O Atlas deve preservar o geocódigo oficial como identificador territorial estável e não utilizar apenas nomes de município como chave.

### 5.3. Câmara dos Deputados — autoridade de atividade da Câmara

Usos:

- deputados em exercício;
- detalhes de parlamentar;
- histórico de exercício;
- órgãos;
- eventos;
- despesas quando incluídas no produto;
- discursos;
- proposições;
- tramitações;
- votações;
- votos nominais.

Fonte:

- API Dados Abertos da Câmara:  
  https://dadosabertos.camara.leg.br/swagger/api.html

### 5.4. Senado Federal — autoridade de atividade do Senado

Usos:

- senadores em exercício;
- mandatos;
- filiação;
- cargos;
- comissões;
- votações.

Fontes:

- Senadores em exercício:  
  https://www12.senado.leg.br/dados-abertos/legislativo/parlamentares/senadores-em-exercicio
- Votações do senador:  
  https://www12.senado.leg.br/dados-abertos/legislativo/parlamentares/senadores-em-exercicio/info/webservice-de-votacoes-do-senador

### 5.5. Fontes estaduais e municipais

Assembleias Legislativas, prefeituras e câmaras municipais podem ser integradas somente quando:

1. a origem for oficial;
2. a informação tiver identificador ou contexto suficiente;
3. a atualização puder ser monitorada;
4. a fonte puder ser citada ao usuário;
5. a ausência de integração não for substituída por inferência.

A falta de API municipal não autoriza scraping de fontes não oficiais como se fossem autoridade.

---

## 6. Proveniência obrigatória

Todo conjunto importado deve armazenar metadados de proveniência.

Campos conceituais mínimos:

```text
source_agency
source_dataset
source_url
source_record_id
source_election_id
source_generated_at
fetched_at
etag
last_modified
content_hash
ingestion_version
```

Campos não disponíveis na fonte podem permanecer nulos; não devem ser inventados.

Agregações devem ser reproduzíveis a partir de registros de origem.

A interface deve oferecer "Fonte" ou "Ver origem" em páginas de resultado e pessoa.

---

## 7. Apuração 2026 em tempo real

### 7.1. Estratégia

O navegador não deve bombardear diretamente a infraestrutura do TSE.

Fluxo:

```text
TSE Resultados
    ↓
Coletor Atlas
    ↓
Snapshot bruto imutável
    ↓
Normalização
    ↓
Banco/arquivos derivados
    ↓
API Atlas
    ↓
Frontend
```

### 7.2. Descoberta de configuração

Códigos de eleição, pleito e demais identificadores devem ser obtidos dos arquivos oficiais de configuração quando aplicável.

A implementação não deve depender de números copiados manualmente para funcionar em eleições futuras.

### 7.3. Polling responsável

A documentação 2026 do TSE estabelece limite máximo de 100 requisições por IP por segundo e informa suporte a `ETag`, `Last-Modified` e respostas `304 Not Modified`.

O Atlas deve:

- operar muito abaixo do teto;
- usar requisições condicionais;
- aplicar backoff em erro;
- não repetir URL inválida agressivamente;
- deduplicar geração já processada;
- compartilhar a mesma coleta entre todos os usuários do Atlas.

O limite oficial é um teto de segurança, não um alvo de frequência.

### 7.4. Consistência

Cada snapshot deve conservar:

- URL consultada;
- momento da coleta;
- ETag/Last-Modified quando disponível;
- ID de geração disponibilizado pela fonte;
- hash do corpo;
- eleição/abrangência/cargo;
- resultado da validação.

Uma carga parcial não deve substituir silenciosamente uma carga íntegra anterior.

### 7.5. Arquivo de eleitos

O TSE informa que o arquivo de eleitos é produzido após totalização conforme o processo oficial.

O Atlas só deve promover uma candidatura para `OFFICIALLY_ELECTED` a partir de informação oficial compatível.

---

## 8. Modelo de domínio conceitual

Entidades mínimas:

```text
Election
ElectionRound
Office
Territory
Party
Person
Candidacy
VoteResult
PartyVoteResult
ElectionStatus
ElectedResult
Institution
Mandate
OfficeholderStatus
LegislativeActivity
SourceRecord
SourceSnapshot
```

### 8.1. Identidade

`Person` não deve usar nome como chave.

`Candidacy` pertence a um contexto eleitoral específico.

A mesma pessoa pode possuir várias candidaturas em anos/cargos distintos.

### 8.2. Território

`Territory` deve possuir identificador oficial, tipo e relação hierárquica.

Exemplos:

```text
BRASIL
  └── MG
      └── município
```

A geometria do mapa é derivada da autoridade territorial e não da base eleitoral.

### 8.3. Resultado

`VoteResult` deve separar:

- votos absolutos;
- percentual calculado;
- denominador utilizado;
- abrangência;
- cargo;
- turno;
- candidatura;
- fonte.

Percentuais calculados pelo Atlas devem ser identificáveis como cálculo derivado, mesmo quando coincidirem com percentuais publicados.

---

## 9. Neutralidade e apresentação

O Atlas deve ser descritivo.

Não deve:

- recomendar candidato;
- ordenar candidatos por "melhor" ou "pior";
- produzir score ideológico próprio;
- inferir intenção, caráter ou competência;
- declarar tendência futura como resultado;
- confundir pesquisa eleitoral com apuração;
- apresentar cor partidária sem legenda clara;
- ocultar o estado de totalização.

É permitido:

- ordenar por votos;
- exibir maiores/menores valores como descrição matemática;
- comparar votos, percentuais e cadeiras;
- mostrar histórico;
- mostrar atividade oficial;
- calcular diferenças reproduzíveis.

Cores servem à leitura visual e não devem carregar significado valorativo.

---

## 10. Arquitetura proposta

### 10.1. Ingestion

Responsabilidade única: adquirir e validar fontes oficiais.

Módulos futuros:

```text
ingestion/tse/
ingestion/ibge/
ingestion/camara/
ingestion/senado/
ingestion/local/
```

Cada conector deve poder falhar sem invalidar as demais fontes.

### 10.2. Armazenamento

Primeira arquitetura recomendada:

- snapshots brutos preservados;
- Parquet para conjuntos analíticos;
- DuckDB para consultas e materializações;
- banco relacional adicional somente se a necessidade operacional justificar.

Dados brutos e derivados devem ser distinguíveis.

### 10.3. Backend

Primeira implementação recomendada:

- Python;
- FastAPI;
- serviços de consulta somente leitura para o frontend;
- tarefas de ingestão separadas do processo web.

### 10.4. Frontend

Primeira implementação recomendada:

- React;
- TypeScript;
- MapLibre GL JS ou camada equivalente compatível com GeoJSON/tiles;
- interface responsiva;
- acessibilidade de teclado;
- visualizações que não dependam exclusivamente de cor.

### 10.5. Independência de deploy

O Atlas deve possuir configuração, dependências e comando de execução próprios.

A raiz do site CopyMinas não deve precisar conhecer detalhes internos do Atlas.

---

## 11. API conceitual

A especificação não fixa implementação HTTP final, mas os casos de uso exigem interfaces equivalentes a:

```text
GET /elections
GET /elections/{election}/results
GET /territories/{territory}
GET /territories/{territory}/results
GET /people/{person}
GET /people/{person}/elections
GET /people/{person}/activity
GET /parties/{party}/results
GET /live/{election}/status
GET /sources/{source_record}
```

Toda resposta de dado eleitoral relevante deve permitir chegar à proveniência.

---

## 12. Experiência principal

### 12.1. Entrada

A Home do Atlas deve priorizar:

1. pesquisa de cidade;
2. mapa do Brasil;
3. eleição atual;
4. eleições históricas;
5. busca por pessoa;
6. busca por partido.

### 12.2. Pesquisa de cidade

Busca tolerante a acentos, mas retorno vinculado ao geocódigo.

Exemplo de fluxo:

```text
Pesquisar "Elói Mendes"
→ Elói Mendes · MG
→ página municipal
→ eleições / ocupantes / atividade disponível
```

### 12.3. Estado ao vivo

Durante apuração:

```text
APURAÇÃO OFICIAL EM ANDAMENTO
Última atualização: ...
Seções/percentual conforme fonte oficial
Fonte: Tribunal Superior Eleitoral
```

Não deve existir animação ou copy que sugira certeza além do estado oficial.

---

## 13. Degradação e erros

O sistema deve distinguir:

- fonte indisponível;
- dado ainda não publicado;
- dado não aplicável;
- dado não integrado;
- erro de ingestão;
- registro não encontrado;
- divergência entre fontes.

Nunca transformar ausência em zero.

Exemplo:

```text
"Atividade municipal não integrada"
```

é diferente de:

```text
"0 projetos apresentados"
```

### 13.1. Divergência

Quando duas fontes oficiais legítimas representarem conceitos diferentes, ambas podem ser exibidas com contexto.

Quando representarem o mesmo conceito e divergirem, o Atlas deve:

1. manter os registros;
2. marcar divergência;
3. não escolher silenciosamente um valor;
4. preferir a autoridade definida para aquele domínio;
5. registrar a decisão de normalização.

---

## 14. Segurança e privacidade

O Atlas trabalha prioritariamente com dados públicos institucionais.

Mesmo assim:

- não deve enriquecer perfis com dados pessoais obtidos fora das fontes oficiais do escopo;
- não deve expor credenciais de coleta;
- deve validar conteúdo remoto antes de persistir;
- deve limitar tamanho e tipo de downloads;
- deve tratar arquivos externos como entrada não confiável;
- deve manter logs técnicos sem registrar dados pessoais desnecessários.

---

## 15. Testabilidade

A implementação deve permitir testes determinísticos usando fixtures oficiais preservadas.

Categorias mínimas:

- parse de arquivos TSE;
- normalização territorial;
- identidade de candidatura;
- cálculo de percentual;
- transição de snapshot ao vivo;
- detecção de 304/ETag;
- deduplicação;
- arquivo parcial/corrompido;
- pessoa homônima;
- ausência de fonte municipal;
- separação entre eleito e em exercício;
- proveniência;
- renderização de mapa sem depender só de cor.

Testes do Atlas não devem depender da aplicação CopyMinas.

---

## 16. Critérios de aceitação da primeira versão funcional

Uma primeira versão é considerada funcional quando conseguir, usando apenas fontes oficiais:

1. carregar a malha municipal do Brasil;
2. importar resultados consolidados de 2022;
3. importar resultados municipais de 2024;
4. pesquisar município por nome e identificar pelo geocódigo;
5. abrir um município e exibir resultados por cargo;
6. abrir uma candidatura e mostrar sua distribuição territorial;
7. exibir eleitos sem confundir eleição com exercício;
8. integrar deputados em exercício da Câmara;
9. integrar senadores em exercício do Senado;
10. mostrar fonte e horário de coleta;
11. consumir ao menos um fluxo oficial de resultado 2026 em modo live;
12. atualizar o frontend a partir do cache do Atlas, sem polling por usuário diretamente no TSE;
13. executar sem importar ou modificar código do site CopyMinas.

---

## 17. Fases de produto

A sequência de produto aprovada conceitualmente é:

### Fase A — Fundação e corpus histórico

- isolamento;
- domínio;
- IBGE;
- TSE 2022;
- TSE 2024;
- consultas locais;
- proveniência.

### Fase B — Mapa e navegação

- mapa Brasil/UF/município;
- filtros;
- candidato;
- partido;
- página municipal.

### Fase C — Mandato federal

- Câmara dos Deputados;
- Senado;
- distinção eleito/em exercício;
- atividade parlamentar.

### Fase D — Apuração ao vivo

- configuração oficial;
- snapshots;
- cache;
- ETag/Last-Modified;
- status live;
- promoção somente por estado oficial.

### Fase E — Fontes estaduais e municipais

- integrações selecionadas por disponibilidade e qualidade;
- nunca bloquear o produto nacional por ausência de API local.

Essa enumeração descreve produto e dependências; não substitui o plano de implementação.

---

## 18. Decisões canônicas

As seguintes decisões são parte desta especificação:

1. Atlas Eleitoral é independente da CopyMinas.
2. TSE é autoridade para fatos eleitorais.
3. IBGE é autoridade territorial.
4. Câmara e Senado são autoridades para seu respectivo exercício e atividade parlamentar.
5. Resultado eleitoral e exercício do mandato são entidades diferentes.
6. O Atlas não declara eleito por inferência própria.
7. Ausência de dado não equivale a zero.
8. Toda informação relevante deve ser rastreável à origem.
9. O cliente não consulta o TSE diretamente por usuário durante apuração.
10. Dados brutos devem ser preservados separadamente de dados derivados.
11. Identidade não pode depender apenas de nome.
12. Geocódigo, não nome do município, é a chave territorial.
13. A interface deve ser politicamente neutra e descritiva.
14. Integração municipal é progressiva; falta de API oficial deve ser explicitada.
15. O projeto deve poder sair do repositório CopyMinas no futuro sem depender de sua aplicação.

---

## 19. Fora de escopo nesta fundação

Não fazem parte da primeira fundação:

- comentários de usuários;
- rede social;
- avaliação de políticos;
- score de desempenho;
- recomendação eleitoral;
- previsão de vencedor;
- pesquisas eleitorais como substituto de resultado;
- notícias/editorial;
- doações ou financiamento do projeto;
- autenticação de eleitor;
- integração com dados privados;
- scraping de redes sociais;
- uso de modelos de IA para inferir posição política.

Esses itens exigiriam decisão e contrato próprios antes de qualquer implementação.

---

## 20. Resultado esperado

O Atlas deve permitir uma navegação semelhante a:

```text
BRASIL
  ↓
MINAS GERAIS
  ↓
ELÓI MENDES
  ├── Eleições 2022
  ├── Eleições 2024
  ├── Eleições 2026
  ├── Prefeitura / Câmara municipal quando fonte oficial integrada
  ├── Votação presidencial
  ├── Votação para governador e Senado
  └── Votação para deputados
         ↓
      PESSOA
         ├── eleições
         ├── mapa de votos
         ├── mandato
         ├── atividade oficial disponível
         └── fontes
```

O valor do produto está em tornar dados públicos oficiais mais navegáveis sem alterar seu significado.
