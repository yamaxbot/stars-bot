import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient, functions, types
import time
from aiogram import Bot

from config import GOLDEN_KEY, gifts_id, API_ID, API_HASH, TELEGRAM_BOT_TOKEN, USER_TELEGRAM_ID


client = TelegramClient('session_name', API_ID, API_HASH, device_model='Samsung Galaxy S20 FE, running Android 13', system_version='4.16.30-vxCUSTOM')

async def send_gift(total_stars, username, total_order, bot):
        receiver = await client.get_input_entity(username)
        gift_id = gifts_id[total_stars]

        for i in range(total_order):
            # Создаем инвойс на отправку подарка
            invoice = types.InputInvoiceStarGift(
                hide_name=False,
                peer=receiver,
                gift_id=gift_id,
                include_upgrade=False)

            # 4. Оплачиваем инвойс с баланса Telegram Stars аккаунта
            try:
                form = await client(functions.payments.GetPaymentFormRequest(invoice=invoice))
                result = await client(functions.payments.SendStarsFormRequest(
                    form_id=form.form_id,
                    invoice=invoice
                ))
            except Exception as e:
                await bot.send_message(f"Пользователю {username} не получилось отправить подарок", chat_id=USER_TELEGRAM_ID)



async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await client.start()
    print("Запущен")
    while True:
        time.sleep(10)
        headers = {
        'Cookie': f'golden_key={GOLDEN_KEY}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        }

        chats = requests.get("https://funpay.com/chat/", headers=headers)
        src = chats.text
        src = BeautifulSoup(src, "lxml")
        unread_chats = src.find_all("a", class_="contact-item unread")
        if len(unread_chats) == 0:
            continue

        for chat in unread_chats:
            href = chat.get("href")
            read_chat = requests.get(href, headers=headers)
            read_chat = BeautifulSoup(read_chat.text, "lxml")
            message = read_chat.find_all("div", class_="chat-message")[-2]

            if "FunPay" in str(message.find("div", class_="media-user-name")) and "оповещение" in str(message.find("div", class_="media-user-name")) and "Telegram, Звёзды" in str(message.find("div", class_="chat-msg-text")) and "Подарком" in str(message.find("div", class_="chat-msg-text")) and "оплатил" in str(message.find("div", class_="chat-msg-text")) and "заказ" in str(message.find("div", class_="chat-msg-text")):
                text = str(message.find("div", class_="chat-msg-text")).replace("<a", "///").replace("</a>", "///")
                data = list(text.split("///"))[4].split(", ")

                total_stars = int(list(data[2].split())[0])
                username = data[-1][:-2]
                total_order = 1

                if len(data) == 6:
                    total_order = int(list(data[-2].split())[0])
                user_stars = await client(functions.payments.GetStarsStatusRequest(peer=types.InputPeerSelf()))

                if int(user_stars.balance.amount) >= total_order*total_stars:
                    await send_gift(total_stars, username, total_order, bot)
                else:
                    await bot.send_message(text=f"Не хватает звёзд для клиента {href}", chat_id=USER_TELEGRAM_ID)
            time.sleep(2)



if __name__ == "__main__":
    client.loop.run_until_complete(main())
