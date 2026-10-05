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
- `GET /admin/produtos` — listagem administrativa;
- `GET|POST /admin/produtos/novo` — criação;
- `GET|POST /admin/produtos/<id>` — edição;
- `POST /admin/produtos/<id>/status` — ativação/desativação;
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
