# Copy Minas Site 3 — Contrato da área administrativa

## Objetivo

A área administrativa é uma interface interna e não anunciada no site público para operar o conteúdo persistente do Site 3.

Ela existe sob o prefixo `/admin` e não deve aparecer em menus, rodapés, páginas públicas ou navegação editorial.

A ausência de links públicos é apenas uma decisão de interface. A proteção real é feita por autenticação e sessão.

## Autenticação

Credenciais:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

As credenciais são lidas exclusivamente do ambiente da aplicação.

Regras:
- nenhuma credencial é persistida no banco;
- nenhuma credencial é renderizada no HTML;
- comparação de usuário e senha usa comparação em tempo constante;
- sessão autenticada é necessária para todas as rotas de gestão;
- login e logout usam token CSRF;
- após 5 tentativas inválidas, a sessão de login é temporariamente bloqueada por 60 segundos;
- páginas administrativas usam `noindex,nofollow,noarchive`.

## Rotas

- `GET|POST /admin/login` — autenticação;
- `GET /admin` — painel;
- `GET|POST /admin/home` — configuração da Home pública;
- `POST /admin/home/inicializar` — inicialização explícita do módulo Home no main_bd;
- `GET|POST /admin/home/novidades/nova` — criação de novidade;
- `GET|POST /admin/home/novidades/<id>` — edição de novidade;
- `POST /admin/home/novidades/<id>/status` — publicação/desativação de novidade;
- `GET /admin/produtos` — listagem administrativa;
- `GET|POST /admin/produtos/novo` — criação;
- `GET|POST /admin/produtos/<id>` — edição;
- `POST /admin/produtos/<id>/status` — ativação/desativação;
- `GET /admin/produtos/<id>/imagem/<slot>/editar` — editor não destrutivo da imagem;
- `POST /admin/produtos/<id>/imagem/<slot>/salvar` — salva a versão editada e aplica apenas ao slot escolhido;
- `GET /admin/categorias` — listagem de categorias;
- `GET|POST /admin/categorias/nova` — criação de categoria;
- `GET|POST /admin/categorias/<id>` — edição de categoria;
- `POST /admin/categorias/<id>/status` — ativação/desativação de categoria;
- `GET /admin/contatos` — listagem administrativa de solicitações;
- `GET /admin/contatos/<id>` — ficha interna do contato;
- `POST /admin/contatos/<id>/status` — atualização do status de atendimento;
- `POST /admin/logout` — encerra a sessão.

## Produtos

O módulo administrativo opera diretamente as tabelas existentes do `main_bd`.

Campos administrados:
- `nome`;
- `descricao`;
- `imagem1` a `imagem5`;
- `espec`;
- `ativo`;
- `categoria_id`;
- `qtd`.

Categorias são lidas e administradas na tabela existente `categorias`.

O painel também:
- sinaliza nomes equivalentes como possíveis duplicidades sem alterar ou excluir registros automaticamente;
- mostra miniatura quando `imagem1` aponta para um asset existente;
- oferece link direto para a ficha pública quando o produto está publicável;
- permite upload de PNG, JPG/JPEG e WEBP para `static/images/products`;
- mantém caminhos manuais de `imagem1` a `imagem5` compatíveis com o banco existente.

### Regras de segurança de dados

- não existe exclusão física de produto no painel;
- desativação usa `produtos.ativo`;
- criação e edição usam transações;
- falha de gravação executa rollback;
- queries de escrita são parametrizadas;
- categoria informada deve existir;
- quantidade pode ficar vazia ou ser inteiro maior ou igual a zero;
- nenhuma tabela ou coluna nova é criada pelo módulo.

## Relação com o catálogo público

O catálogo público continua sendo uma leitura própria e separada.

Somente produtos ativos associados a categorias ativas são publicados.

O painel administrativo lista também produtos inativos para permitir recuperação e reativação.

O catálogo público só exibe uma imagem quando o arquivo indicado existe no diretório estático.

O administrador pode informar o caminho manualmente ou enviar um arquivo. Uploads:
- aceitam PNG, JPG/JPEG e WEBP;
- usam nome sanitizado e sufixo aleatório para evitar colisões;
- permanecem dentro de `static/images/products`;
- não apagam automaticamente o arquivo anterior ao substituir um slot;
- respeitam o limite total configurado por `ADMIN_UPLOAD_MAX_MB` (25 MB por padrão).

Caminhos que tentem escapar de `static` são rejeitados.

O campo `qtd` continua administrativo e não é exibido como estoque público.

## Escopo atual

Disponível:
- autenticação;
- dashboard;
- listagem de produtos;
- busca e filtro por status;
- criação e edição de produto;
- ativação/desativação;
- miniaturas e preview da ficha pública;
- aviso de possível duplicidade;
- upload de imagens;
- criação e edição de categorias;
- ativação/desativação de categorias;
- contagem de produtos vinculados por categoria.

Fora do escopo desta etapa:
- delete físico;
- limpeza automática de arquivos de imagem órfãos;
- edição destrutiva do conteúdo original de uma solicitação;
- múltiplos usuários administrativos ou permissões por papel.


## Contatos

O módulo Contatos opera diretamente a tabela existente `main_bd.contatos`.

O painel administrativo pode ler:
- protocolo;
- nome;
- empresa;
- e-mail;
- telefone;
- cidade;
- tipo de serviço;
- quantidade informada;
- preferência de contato;
- mensagem;
- consentimento;
- origem;
- status;
- timestamps.

Esses campos permanecem internos. A existência do módulo administrativo não altera a regra pública que esconde banco, tabela, origem e status técnico do visitante.

### Workflow

Estados aceitos:
- `novo`;
- `em_atendimento`;
- `convertido`;
- `encerrado`;
- `spam`.

O admin pode mover uma solicitação entre esses estados. A atualização:
- exige sessão autenticada;
- exige CSRF;
- usa query parametrizada;
- usa transação;
- não exclui o registro;
- preserva todos os dados originalmente recebidos.

### Interface

A listagem administrativa oferece:
- busca por nome, protocolo, empresa, e-mail, telefone e cidade;
- filtro por status;
- filtro por serviço;
- contadores por etapa do workflow.

A ficha interna oferece:
- dados do cliente;
- dados da solicitação;
- mensagem integral;
- consentimento;
- origem;
- timestamps;
- atualização de status;
- atalhos para e-mail e telefone.

O dashboard mostra também a quantidade de contatos novos e em atendimento.


## Dashboard operacional

A rota `GET /admin` apresenta uma visão operacional baseada exclusivamente em dados já existentes.

Ela não cria trilha de auditoria e não inventa eventos.

### Indicadores

O painel mostra:
- produtos publicados;
- produtos inativos;
- categorias;
- contatos novos;
- contatos em atendimento;
- contatos convertidos;
- disponibilidade das fontes de catálogo e contatos.

### Alertas

Os checks atuais podem sinalizar:
- registros de produto com nome equivalente;
- produtos publicados sem imagem válida no Site 3;
- categorias inativas que ainda possuem produtos marcados como ativos;
- contatos ainda com status `novo`.

Esses alertas são informativos. Nenhuma correção é aplicada automaticamente.

### Atividade recente

`Produtos recentes` é ordenado por `updated_at` e, na ausência dele, `created_at`.

`Últimos contatos` é ordenado por `created_at`.

Essas listas são uma visualização temporal dos registros atuais e não substituem uma trilha de auditoria.

### Ações rápidas

O painel oferece atalhos para:
- novo produto;
- nova categoria;
- contatos;
- catálogo público.

### Degradação parcial

Catálogo e contatos são consultados de forma independente.

Se uma dessas fontes estiver indisponível:
- a outra parte do painel continua funcional;
- indicadores indisponíveis aparecem sem valor;
- o painel informa explicitamente qual fonte está offline.


## Admin Shell 2.0

A área autenticada usa um shell persistente de aplicação.

### Navegação

O shell administrativo contém:
- sidebar fixa no desktop;
- sidebar recolhível com preferência persistida localmente no navegador;
- drawer de navegação no mobile;
- topbar persistente;
- breadcrumb do módulo atual;
- acesso ao Site 3 público em nova aba;
- logout autenticado já existente.

Módulos atuais:
- Visão geral;
- Contatos;
- Produtos;
- Categorias.

O login permanece fora do shell.

### Busca global

A busca global pode ser aberta pelo botão da topbar ou por `Ctrl+K` / `Cmd+K`.

Endpoint:
- `GET /admin/busca?q=<termo>`.

A rota exige sessão administrativa.

A busca consulta:
- produtos;
- categorias;
- contatos.

Campos pesquisáveis incluem, conforme o tipo:
- ID;
- nome;
- categoria;
- descrição;
- protocolo;
- empresa;
- e-mail;
- telefone;
- cidade;
- serviço.

A resposta é limitada a resultados administrativos navegáveis e não expõe segredos de ambiente.

Cada fonte é consultada de forma independente. Se uma fonte estiver indisponível, resultados das demais continuam sendo retornados e a interface informa degradação parcial.

### Segurança da interface de busca

Resultados vindos do banco são inseridos na interface por APIs de DOM com `textContent`, não por interpolação de HTML bruto.

A busca:
- não grava no banco;
- não altera status;
- não executa ações;
- apenas navega para telas administrativas existentes.

### Responsividade

Em desktop a sidebar pode alternar entre expandida e compacta.

Em telas menores:
- o conteúdo volta a ocupar 100% da largura;
- a sidebar vira drawer;
- um backdrop fecha a navegação;
- `Escape` fecha drawer ou busca;
- a busca global ocupa a tela inteira em celulares estreitos.


## Editor de imagem de produto

Produtos já salvos podem abrir um editor próprio para qualquer slot `imagem1` a `imagem5`.

### Editor v1

Ferramentas disponíveis:
- canvas quadrado 1:1;
- saída fixa de 1200 × 1200 pixels;
- arrastar e reposicionar;
- zoom;
- rotação de 90°;
- espelhamento horizontal e vertical;
- fundo transparente ou branco;
- visualização da original;
- ajuste automático ao quadro;
- remoção automática de fundo baseada nas cores conectadas às bordas, com sensibilidade configurável;
- ação `Preparar para catálogo`.

A remoção de fundo v1 é determinística e local no navegador. Ela não é um modelo de segmentação por IA. Fundos complexos podem exigir uma etapa futura de borracha/restauração manual ou segmentação especializada.

### Preservação da original

O editor é não destrutivo.

Na primeira edição:
- a imagem usada como fonte é copiada para `static/images/products/originals`;
- a saída editada é criada em `static/images/products/edited`;
- o banco passa a apontar apenas o slot escolhido para a versão editada;
- a imagem original permanece preservada.

Uma edição posterior de uma versão já editada volta a abrir a original preservada como fonte.

Arquivos auxiliares de metadados registram a relação entre a versão editada e sua original. Eles não contêm credenciais nem dados pessoais.

### Segurança e validação

O salvamento:
- exige autenticação administrativa;
- exige CSRF;
- aceita somente os cinco slots existentes;
- valida a imagem resultante com Pillow;
- exige saída 1200 × 1200;
- limita dimensões e tamanho bruto;
- grava o arquivo antes da atualização transacional do slot;
- remove a nova saída editada se a atualização do banco falhar;
- nunca altera os outros quatro slots do produto.

O editor não cria tabela nem coluna nova no banco.


## Home Manager

A Home pública possui um módulo editorial próprio dentro do mesmo `main_bd`.

Tabelas:
- `site_home_config` — configuração singleton da Home;
- `site_home_news` — novidades e mensagens editoriais.

A criação dessas tabelas é explícita e autenticada através de `POST /admin/home/inicializar`. A aplicação não altera schema durante um GET público.

A migration equivalente está documentada em:
- `migrations/20261005_home_manager.sql`.

### Configuração administrável

O admin pode controlar:
- faixa de mensagem superior;
- rótulo e texto da mensagem;
- link opcional da mensagem;
- kicker, título e resumo do hero;
- dois CTAs do hero;
- até seis produtos em destaque, com ordem explícita;
- visibilidade da seção Soluções;
- visibilidade da seção Empresa;
- visibilidade da seção Localização + globo.

Somente produtos ativos associados a categorias ativas podem ser escolhidos como destaque.

Links editoriais aceitos:
- caminhos internos iniciados por `/`;
- `http://`;
- `https://`;
- `mailto:`;
- `tel:`.

Esquemas de URL executáveis como `javascript:` e `data:` são rejeitados.

### Novidades

Novidades possuem:
- rótulo;
- título;
- conteúdo;
- link opcional;
- ordem;
- status ativo/inativo;
- timestamps.

Não existe delete físico no fluxo administrativo. Uma novidade deixa de aparecer publicamente por `active = 0`.

### Fallback público

Enquanto o Home Manager ainda não estiver inicializado, ou se a configuração editorial estiver indisponível, a Home continua renderizando com:
- headline e resumo canônicos já existentes;
- CTAs para Soluções e Produtos;
- três primeiros produtos públicos como destaques;
- seções Soluções, Empresa e Localização ativas.

Isso evita que a adoção do Home Manager torne a página pública dependente de uma migration já aplicada.

### Entrada pública

A rota `/` não usa mais a antiga tela de entrada com globo.

`/` e `/home` renderizam a Home diretamente.

O globo permanece disponível dentro da seção de Localização da Home e em seu diálogo de exploração.
