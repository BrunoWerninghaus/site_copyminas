# Migração de catálogo — Site 2 → Site 3

## Fonte autoritativa

A estrutura e os registros de catálogo desta etapa vêm do dump MySQL do **Site 2**, banco `main_bd`, fornecido pelo proprietário.

O Site 1 (`/old`) não é usado como substituto silencioso para esses dados.

## Estrutura encontrada no Site 2

Tabelas relevantes:
- `categorias`: 10 categorias;
- `produtos`: 25 registros no dump, IDs até 26;
- `contatos`: estrutura de leads/formulário.

O registro existente em `contatos` no dump tem conteúdo claramente de teste e **não foi migrado**.

## Produtos publicados no Site 3

Somente registros com `ativo = 1`:
- 14 — Computador Desktop Intel Core i3-3220 12GB RAM SSD 128GB
- 15 — Computador Desktop Intel Core i3-3220 8GB RAM SSD 128GB
- 16 — Computador Desktop Intel Core i3-2100 8GB RAM SSD 128GB
- 19 — Brother DCP-8157DN
- 21 — Samsung ProXpress SL-M4070FR
- 22 — Samsung ProXpress SL-M4080FX
- 23 — Brother MFC-8912DW
- 24 — Epson EcoTank L6490
- 25 — Brother DCP-L5652DN
- 26 — Cabo de Rede CAT6 — 10 metros

## Registros excluídos da publicação

Os IDs 1–13, 17 e 20 estavam inativos no dump. O ID 20 também duplica o modelo Samsung SL-M4070FR que permanece ativo no ID 21.

Eles não são apagados da história do Site 2; apenas não entram no catálogo público do Site 3.

## Quantidade

O campo `qtd` é preservado como `source_quantity` para rastreabilidade.

Ele **não é exibido como estoque público** até que o proprietário confirme a semântica e a regra de atualização desse campo.

## Imagens

Os caminhos originais do Site 2 são preservados em `source_image_path`.

Os binários das imagens ainda precisam ser copiados do pacote do Site 2 para os assets do Site 3. Até essa cópia, a interface mostra um slot técnico em vez de gerar URL quebrada ou buscar uma imagem arbitrária na internet.

## Normalização e verificação

O conteúdo original do Site 2 foi mantido para os produtos que já tinham descrição e especificações.

Dois registros que estavam sem conteúdo técnico foram enriquecidos com fontes oficiais:
- ID 24: `EPSON 6490` foi normalizado para **Epson EcoTank L6490** com base na página oficial Epson Brasil.
- ID 25: **Brother DCP-L5652DN** recebeu descrição e ficha básica a partir da página oficial Brother Brasil.

As fichas Samsung SL-M4070FR e SL-M4080FX foram comparadas com páginas oficiais Samsung e os principais dados do Site 2 são compatíveis.

## Modelo do Site 3

O arquivo `src/copyminas/data/catalog_site2.json` é a camada de migração versionada.

Ele preserva:
- `source_id`;
- `source_name`;
- `category_id`;
- `source_image_path`;
- `source_quantity`.

A aplicação pública consome esse arquivo por `src/copyminas/catalog.py`.

Quando a camada persistente definitiva do Site 3 for introduzida, esse JSON pode funcionar como seed/migration fixture sem perder a rastreabilidade com o Site 2.
