# Contrato do Site — Copy Minas vNext

Status: APROVADO PARA IMPLEMENTAÇÃO INICIAL

Este documento governa a construção da nova geração do site Copy Minas.

## 1. Regra de conteúdo

Enquanto o conteúdo comercial definitivo não for fornecido, a interface deve usar somente conteúdo provisório explicitamente genérico.

É proibido inventar:
- números;
- clientes;
- anos de mercado;
- garantias;
- certificações;
- marcas atendidas;
- áreas de cobertura;
- vantagens competitivas;
- preços;
- prazos;
- depoimentos;
- endereços;
- telefones;
- estatísticas.

Títulos provisórios devem indicar função, não fazer afirmações comerciais. Exemplos:
- "Título institucional"
- "Título da seção de soluções"
- "Título da seção de produtos"

Descrições provisórias devem indicar o conteúdo esperado. Exemplo:
- "Descrição institucional a definir."

## 2. Regra de imagens

Toda imagem ainda não fornecida deve possuir um slot visual explícito.

Cada slot deve informar sua finalidade no código/interface, por exemplo:
- imagem principal;
- imagem institucional;
- imagem de solução;
- imagem de produto;
- imagem de localização.

A ausência de uma imagem nunca deve quebrar o layout.

A nova logo cromada Copy Minas é a referência oficial de marca. Até o arquivo original ser incorporado ao repositório, a aplicação pode usar uma representação temporária claramente tratada como placeholder técnico.

## 3. Arquitetura pública inicial

### `/` — Entrada

Página imersiva de entrada.

Contrato visual:
- viewport inteiro;
- fundo escuro;
- globo parcialmente cortado na metade esquerda;
- marca Copy Minas na metade direita;
- pouca ou nenhuma informação adicional;
- sem catálogo, cards ou conteúdo institucional nessa tela.

Contrato de interação:
- clique na tela avança para `/home`;
- scroll para baixo avança para `/home`;
- Enter, Espaço, ArrowDown ou PageDown avançam para `/home`;
- gesto de swipe para cima em dispositivos touch avança para `/home`;
- transição deve respeitar `prefers-reduced-motion`.

O globo mostrado nessa página possui um mount dedicado. A primeira fundação pode usar fallback visual; o módulo geográfico definitivo entra sem alterar a anatomia da página.

### `/home` — Home

Página institucional principal.

A Home nasce com áreas independentes e substituíveis:
1. hero institucional;
2. soluções;
3. produtos em destaque;
4. bloco institucional;
5. localização/globo;
6. contato/orçamento;
7. rodapé.

Nenhum desses blocos depende do conteúdo definitivo para existir.

## 4. Globo — contrato final

O globo definitivo deve respeitar:
- mundo/continentes: branco ou prata;
- Brasil: vermelho;
- Minas Gerais: amarelo/dourado;
- Elói Mendes / Copy Minas: azul;
- versão compacta e versão ampliada;
- clique na versão compacta abre a experiência ampliada;
- clique no ponto azul abre a localização oficial no Google Maps;
- coordenada e URL do Google Maps não podem ser inventadas;
- dados geográficos de produção devem preferencialmente ser locais/pré-processados;
- não executar milhões de testes geoespaciais no navegador a cada visita.

## 5. Separação de responsabilidades

- `templates/public/intro.html`: entrada.
- `templates/public/home.html`: Home.
- `static/css/base.css`: tokens e estrutura global.
- `static/css/pages/intro.css`: somente entrada.
- `static/css/pages/home.css`: somente Home.
- `static/js/intro.js`: somente interação da entrada.
- módulos futuros do globo devem viver separados da navegação da página.

Uma página não deve importar CSS específico de outra página.

## 6. Identidade inicial

Base visual:
- preto / azul-preto;
- branco / prata;
- vermelho Copy Minas;
- azul como acento tecnológico;
- amarelo/dourado para Minas no sistema geográfico.

A interface deve evitar excesso de efeitos. Logo e globo são os elementos visuais dominantes.

## 7. Rotas futuras previstas, não implementadas por este contrato

- catálogo completo;
- produto individual;
- contato/orçamento dedicado;
- administração.

Essas rotas serão adicionadas em etapas próprias e não devem ser simuladas com páginas falsas.
