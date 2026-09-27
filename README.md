# 🛰️ Radar de Freelas

Robô em Python que procura **projetos novos** no **99Freelas** e no **Workana**, filtra pelas palavras-chave que me interessam e me avisa no **Telegram**. Roda sozinho 3 vezes por dia no **GitHub Actions**, com custo zero.

## O que ele faz

1. Lê as páginas de projetos das duas plataformas (`requests` + `BeautifulSoup`)
   - 99Freelas: extrai os projetos direto do HTML
   - Workana: lê o JSON que a própria página carrega
2. Filtra por palavra inteira, sem acento e sem diferenciar maiúsculas (`config.json`)
3. Guarda os projetos já vistos em `vistos.json` para nunca avisar duas vezes
4. Envia cada projeto novo para o Telegram com título, orçamento, descrição e link

## Tecnologias

Python 3.12 · requests · BeautifulSoup4 · API de bots do Telegram · GitHub Actions (cron)

## Como usar

### 1. Rodar no seu computador (modo teste)

```bash
pip install -r requirements.txt
python buscador.py --teste
```

O modo teste só mostra os projetos no terminal. Não envia nada nem salva o `vistos.json`.

### 2. Criar o bot do Telegram (grátis)

1. No Telegram, abra uma conversa com **@BotFather** e mande `/newbot`
2. Escolha um nome. Ele te devolve um **token**, parecido com `123456:ABC-...`
3. Rode `python configurar_telegram.py`, cole o token e siga as instruções. O script confere o token, descobre o seu **chat id** e manda uma mensagem de teste

### 3. Colocar para rodar sozinho no GitHub

1. Crie um repositório **público** no GitHub (o Actions é gratuito em repositório público) e suba estes arquivos
2. Em **Settings → Secrets and variables → Actions → New repository secret**, crie:
   - `TELEGRAM_TOKEN`: o token do BotFather
   - `TELEGRAM_CHAT_ID`: o seu chat id
3. Na aba **Actions**, abra "Radar de Freelas" e clique em **Run workflow** para testar na hora

Depois disso ele roda sozinho às 8h, 14h e 20h (horário de Brasília).

> ⚠️ Nunca coloque o token direto no código. Como o repositório é público, qualquer pessoa veria.

## Personalizando

Tudo fica no `config.json`:

| Campo | Para que serve |
|---|---|
| `palavras_incluir` | Avisa se **qualquer** uma aparecer no título, na descrição ou nas habilidades |
| `palavras_excluir` | Descarta o projeto se **qualquer** uma aparecer |
| `paginas` | Quantas páginas ler em cada site por execução |
| `ativo` | `false` desliga uma das plataformas |
| `maximo_por_execucao` | Limite de mensagens por rodada, para não lotar o Telegram |

## Boas práticas

- Consulta poucas páginas, poucas vezes por dia, com pausa de 2 segundos entre elas
- Lê só páginas públicas, sem login, e respeita o `robots.txt` dos dois sites
- **Não envia propostas automaticamente.** O robô encontra os projetos, e quem lê e escreve a proposta sou eu

## Próximos passos

- [ ] Gerar um rascunho de proposta com IA (API gratuita do Gemini)
- [ ] Filtrar por orçamento mínimo
- [ ] Testes automatizados com `pytest` para os leitores de página
