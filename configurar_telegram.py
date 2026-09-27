"""
Ajudante para configurar o Telegram (rode uma vez só)
----------------------------------------------------
1. Pede o token do bot (ele não aparece na tela enquanto você cola)
2. Descobre o seu chat id lendo a última mensagem que você mandou para o bot
3. Manda uma mensagem de teste para confirmar que está tudo certo

Uso:
    python configurar_telegram.py
"""

from getpass import getpass

import requests


def main() -> None:
    token = getpass("Cole o token do BotFather e aperte Enter (não vai aparecer nada): ").strip()
    api = f"https://api.telegram.org/bot{token}"

    # getMe confirma se o token é válido e devolve o @ do bot
    resposta = requests.get(f"{api}/getMe", timeout=30).json()
    if not resposta.get("ok"):
        raise SystemExit("Token inválido. Confira se copiou ele inteiro no BotFather.")
    usuario_bot = resposta["result"]["username"]

    input(f"\nToken OK! Agora abra o Telegram, mande um 'oi' para @{usuario_bot} e aperte Enter aqui...")

    # getUpdates devolve as mensagens que o bot recebeu; cada uma diz de qual chat veio
    atualizacoes = requests.get(f"{api}/getUpdates", timeout=30).json().get("result", [])
    chats = [a["message"]["chat"] for a in atualizacoes if "message" in a]
    if not chats:
        raise SystemExit(f"Não achei nenhuma mensagem. Mande um 'oi' para @{usuario_bot} e rode de novo.")
    chat = chats[-1]  # a mais recente
    chat_id = chat["id"]

    requests.post(
        f"{api}/sendMessage",
        data={"chat_id": chat_id, "text": "🛰️ Radar de Freelas conectado! As vagas vão chegar aqui."},
        timeout=30,
    ).raise_for_status()

    print(f"\nPronto, {chat.get('first_name', '')}! Chegou uma mensagem de teste no seu Telegram.")
    print(f"Seu TELEGRAM_CHAT_ID é: {chat_id}")
    print("Guarde esse número (ele não é segredo como o token) para cadastrar no GitHub.")


if __name__ == "__main__":
    main()
