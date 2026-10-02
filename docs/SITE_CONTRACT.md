# Contrato do Site — Copy Minas vNext

Status: APROVADO PARA IMPLEMENTAÇÃO

Este documento governa a construção da nova geração do site Copy Minas.

## 0. Nomenclatura das gerações

- **Site 1**: versão histórica preservada integralmente em `/old`.
- **Site 2**: protótipo/ZIP de desenvolvimento usado como fonte de referência e, especificamente, como fonte dos produtos e dados de catálogo que serão migrados.
- **Site 3**: versão atual em construção na raiz deste repositório.

Regra: código e arquitetura do Site 2 não são copiados por inércia. Produtos, categorias, imagens e relações de banco que forem úteis são migrados para o modelo limpo do Site 3.

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

A nova logo cromada Copy Minas é a referência oficial de marca e deve ser usada como asset real nas superfícies principais. Derivados otimizados para web podem ser gerados a partir do arquivo-fonte, preservando a aparência da marca.

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

O globo da entrada é real e derivado de dados geográficos:
- continentes em branco/prata;
- Brasil em vermelho;
- Minas Gerais em amarelo/dourado;
- Elói Mendes em azul;
- rotação automática;
- sem controles de mouse nessa tela, porque clique e scroll pertencem à navegação da entrada.

Durante a fase DEV, o módulo pode consumir GeoJSON externo conhecido. Antes da produção, os dados e dependências devem ser fixados/localizados ou pré-processados para remover dependência desnecessária de serviços externos em runtime.

### `/home` — Home

Página institucional principal.

A Home nasce com áreas independentes e substituíveis:
1. hero institucional;
2. chamada para Soluções;
3. produtos em destaque;
4. chamada institucional;
5. localização/globo;
6. rodapé.

A Home funciona como capa editorial. Conteúdo completo de Soluções, Produtos, Empresa e Contato vive em rotas próprias.

Nenhum desses blocos depende do conteúdo definitivo para existir.

## 4. Globo e localização — contrato oficial

Hierarquia visual:
- mundo/continentes: branco ou prata;
- Brasil: vermelho;
- Minas Gerais: amarelo/dourado;
- Elói Mendes / Copy Minas: azul.

Localização informada para a Copy Minas:
- Rua Tonico da Serra, 89 - Ludovico Pavoni, Elói Mendes - MG, 37110-000.

O marcador visual do globo representa Elói Mendes em escala planetária. Para isso, usa a coordenada da sede urbana/município:
- latitude: -21.6094;
- longitude: -45.5660.

Essa coordenada não deve ser apresentada como geocodificação da porta do estabelecimento. O clique do marcador usa o endereço comercial exato acima como destino da pesquisa no Google Maps.

Comportamento:
- o globo compacto da Home abre a experiência fullscreen;
- o fullscreen permite rotação por arraste e zoom pela roda do mouse;
- o ponto azul pulsa para permanecer identificável;
- clicar no ponto azul abre o Google Maps em nova aba;
- existe também uma ação textual "Abrir no Google Maps" como alternativa acessível;
- a experiência fullscreen deve ter botão de fechar e responder a Escape pelo comportamento nativo de `dialog`.

Dados e desempenho:
- dados geográficos de produção devem preferencialmente ser locais/pré-processados;
- não executar milhões de testes geoespaciais no navegador a cada visita;
- o motor atual trabalha com amostragem por máscara geográfica e quantidade de pontos adequada a uma interface web.

## 5. Separação de responsabilidades

- `templates/public/intro.html`: entrada.
- `templates/public/home.html`: Home.
- `location.py`: localização oficial e destino Google Maps.
- `static/css/base.css`: tokens e estrutura global.
- `static/css/pages/intro.css`: somente entrada.
- `static/css/pages/home.css`: somente Home.
- `static/js/intro.js`: somente navegação da entrada.
- `static/js/globe.js`: renderização e interação geográfica do globo.

Uma página não deve importar CSS específico de outra página.

## 6. Identidade inicial

Base visual:
- preto / azul-preto;
- branco / prata;
- vermelho Copy Minas;
- azul como acento tecnológico;
- amarelo/dourado para Minas no sistema geográfico;
- blocos quadrados, sem cantos arredondados;
- superfícies claras inspiradas em folhas/fichas técnicas sobre o fundo escuro;
- tipografia monoespaçada com linguagem de máquina de escrever/documento técnico.

A interface deve evitar excesso de efeitos. Logo e globo são os elementos tecnológicos dominantes; as áreas de conteúdo usam a metáfora de papel/ficha técnica sem virar uma estética retrô caricata.

## 7. Rotas públicas

- `/`: entrada imersiva.
- `/home`: Home institucional / capa editorial.
- `/solucoes`: áreas de atuação e soluções.
- `/produtos`: catálogo em página própria.
- `/produtos/<slug>`: ficha individual do produto.
- `/empresa`: ficha institucional.
- `/contato`: contato em página própria.
- administração: etapa posterior.

A Home pode exibir chamadas e produtos em destaque, mas não substitui as páginas dedicadas de Produtos e Contato.

## 8. Fonte de dados do catálogo

O catálogo do Site 3 deve ser populado a partir dos dados reais do **Site 2**.

Regras:
- não usar o banco do Site 1 como substituto silencioso;
- não inventar modelos, preços, estoque, marcas ou especificações;
- preservar os identificadores úteis do Site 2 durante a migração quando isso ajudar rastreabilidade;
- normalizar categorias, imagens e relacionamentos para o modelo do Site 3;
- segredos, credenciais e configuração de desenvolvimento do Site 2 não entram no repositório;
- pesquisa pública pode validar categorias e informações institucionais, mas não substitui a fonte real dos produtos.


## 9. Conteúdo institucional verificado

Informações cadastrais públicas consultadas em 2026 sustentam:
- nome fantasia: Copy Minas;
- razão social: Cristovao Mendes Quintino;
- CNPJ: 97.537.200/0001-10;
- início das atividades: 12/07/2011;
- situação cadastral: ativa;
- sede em Elói Mendes/MG;
- atividade principal cadastrada: fotocópias;
- atividades secundárias relevantes ao Site 3: equipamentos e suprimentos de informática, recarga de cartuchos, equipamentos para escritório, aluguel de máquinas/equipamentos para escritório e reparação/manutenção de computadores e periféricos.

Canais públicos recentes encontrados:
- (35) 98877-6969;
- (35) 99927-9922;
- copyminas@hotmail.com.

Há fontes que ainda exibem o telefone (35) 3491-0201. Ele é mantido como dado legado interno, mas não é apresentado como canal principal no Site 3 até confirmação do proprietário.

O horário de atendimento não foi verificado e deve permanecer como "A confirmar".

Conflito de grafia de bairro:
- endereço informado pelo proprietário: Ludovico Pavoni;
- bases cadastrais públicas: Ludovico Pavone.

O Site 3 preserva o endereço informado diretamente pelo proprietário como fonte prioritária.
