# Radar de Freelas — contexto para o Claude Code

## O que é
Robô em Python que busca projetos novos no **99Freelas** e no **Workana**, filtra por palavras-chave (`config.json`) e avisa no **Telegram**. Deve rodar de graça no **GitHub Actions** (`.github/workflows/radar.yml`, 3x/dia: 8h, 14h e 20h de Brasília).

## Sobre o usuário
- Está começando em programação: estudou lógica em Python/JS/HTML e um pouco de SQL, e faz um curso de Python na Udemy.
- Objetivo: começar como freelancer e usar este projeto como **primeira peça de portfólio no GitHub**.
- Explique as coisas de forma didática, em português, e deixe ele entender cada passo, sem só entregar pronto.
- Prioridade: **custo zero** (sem APIs pagas).

## Como os sites foram mapeados (26/09/2026, inspecionando no navegador)
- **99Freelas**: `https://www.99freelas.com.br/projects?categoria=web-mobile-e-software&page=N`. O HTML vem do servidor, com 10 projetos por página, cada um em `li.result-item` (atributo `data-id`). Título/link em `h1.title a`, descrição em `.description` (tem os links "Expandir"/"Esconder", que o código remove), info em `.information` e habilidades em `a.habilidade`. A ordem é mais recentes primeiro, com os projetos em destaque no topo.
- **Workana**: `https://www.workana.com/jobs?category=it-programming&language=pt&page=N`. Os projetos NÃO estão no HTML visível: ficam como JSON no atributo `:results-initials` da tag `<search>`. Campos usados: `slug`, `title` (HTML; o título completo está no atributo `title` do `<span>`), `description` (HTML), `budget`, `publishedDate`, `totalBids`, `skills[].anchorText`. Link: `https://www.workana.com/job/{slug}`.
- robots.txt dos dois sites não bloqueia essas páginas. O código espera 2s entre as páginas.

## Estado atual
- [x] `buscador.py` com leitores dos dois sites, filtro por palavra inteira sem acento (ex.: "sap" não casa com "whatsapp"), deduplicação via `vistos.json` e envio ao Telegram (HTML)
- [x] Leitores e filtro testados com amostras reais das páginas
- [x] Testado baixando as páginas de verdade (26/09/2026): 99Freelas 20 projetos (2 págs.), Workana 23 (3 págs., vêm de 7 a 9 por página), sem 403. As datas do 99Freelas vêm vazias no HTML (timestamp em ms no atributo `cp-datetime`, que um JS preenche no navegador); agora `preencher_datas_99freelas` converte isso em Python.
- [x] Bot criado no @BotFather e chat id obtido com `configurar_telegram.py` (mensagem de teste chegou). O token foi trocado com `/revoke` porque vazou no histórico do PowerShell.
- [x] `radar.yml` movido para `.github/workflows/` (estava na raiz, e o Actions não acharia)
- [x] Repositório público https://github.com/b4rao-dg/radar-freelas criado com o `gh` (instalado via .zip em `%LOCALAPPDATA%\Programs\gh\bin`, já que não há winget) e secrets `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` cadastrados
- [x] Workflow rodado manualmente em 27/09/2026: mensagens chegaram no Telegram e o `vistos.json` foi salvo pelo robô. **Antes de mexer no código, rode `git pull`**, porque o robô faz commits sozinho.
- Obs.: nos terminais do usuário, `python`, `git` e `gh` às vezes não são achados no PATH. Passe o caminho completo (ex.: `& "C:\Users\barao\AppData\Local\Programs\Python\Python312\python.exe"`).

## Ideias para depois
- Rascunho de proposta com IA gratuita (Gemini / Google AI Studio, cota grátis). Nunca enviar propostas automaticamente.
- Filtro por orçamento mínimo
- ~~Testes com `pytest`~~ feito em 27/09/2026: `tests/test_buscador.py` (23 testes), com HTMLs inventados mas de estrutura fiel em `tests/exemplos/` (não salvar páginas reais: têm conteúdo de terceiros). CI em `.github/workflows/testes.yml`. Se o site mudar de estrutura, atualize primeiro o exemplo e depois o leitor.
- Caprichar no README para o portfólio (print da mensagem no Telegram, GIF)
