#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram бот-секретарь (Business Mode)
Запуск: python her.py
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

# ==================== КОНФИГ ====================
BOT_TOKEN = "8721442629:AAHpH3zVd05JnsP-LWisHrIew-ABkn0V_rc"

E_STAR = "✦"

# ==================== БОТ ====================
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# ==================== КЛАВИАТУРЫ ====================
def start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Инструкция по подключению", callback_data="how_to_connect")]
    ])


def connect_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подключить", url="tg://settings/edit")],
        [InlineKeyboardButton(text="Назад", callback_data="back_start")]
    ])


# ==================== /start ====================
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_name = message.from_user.first_name or "друг"

    await message.answer(
        f"{E_STAR} <b>Добро пожаловать, {user_name}!</b> {E_STAR}\n\n"
        f"<b>Я очень рад, что ты решил использовать наш бот!</b>\n\n"
        f"<b>Начни прямо сейчас!</b>",
        reply_markup=start_keyboard()
    )


@dp.callback_query(F.data == "how_to_connect")
async def how_to_connect_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"{E_STAR} <b>Инструкция по добавлению</b>\n\n"
        f"<b>1) Скопируйте юзернейм данного бота</b>\n"
        f"<b>2) Нажмите на кнопку подключить</b>\n"
        f"<b>3) Найдите «Автоматизация чатов»</b>\n"
        f"<b>4) Введите туда юзернейм бота и все готово.</b>",
        reply_markup=connect_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "back_start")
async def back_start_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"{E_STAR} <b>Добро пожаловать!</b> {E_STAR}\n\n"
        f"<b>Я очень рад, что ты решил использовать наш бот!</b>\n\n"
        f"<b>Начни прямо сейчас!</b>",
        reply_markup=start_keyboard()
    )
    await callback.answer()


# ==================== ХЕЛПЕРЫ ====================
async def send_status(chat_id, bcid, text):
    """Отправляет бизнес-сообщение, возвращает message или None."""
    try:
        msg = await bot.send_message(
            chat_id=chat_id,
            business_connection_id=bcid,
            text=text
        )
        return msg
    except Exception as e:
        logging.error(f"send_status error: {e}")
        return None


async def delete_msg(chat_id, msg_id, bcid):
    """Удаляет сообщение. Ждёт завершения."""
    try:
        await bot.delete_business_messages(
            business_connection_id=bcid,
            message_ids=[msg_id]
        )
        return True
    except Exception as e:
        logging.warning(f"delete error: {e}")
        return False


# ==================== КОМАНДА .snos ====================
@dp.business_message(F.text.lower() == ".snos")
async def snos_command(message: types.Message):
    """Мгновенная реакция: удаляем + цепочка сообщений (с удалением предыдущего)."""
    chat_id = message.chat.id
    bcid = message.business_connection_id

    # Имя собеседника
    target_name = "пользователь"
    try:
        target = await bot.get_chat(chat_id)
        target_name = target.first_name or target.username or "пользователь"
    except Exception:
        pass

    # 1. Мгновенно удаляем сообщение пользователя (.snos)
    await delete_msg(chat_id, message.message_id, bcid)

    # 2. Цепочка статусов
    stages = [
        (f"<b>Идет удаление аккаунта {target_name}....</b>", 1.0),
        ("<b>Сбор информации...</b>", 0.15),
        ("<b>Отправка заявки...</b>", 0.15),
        ("<b>Отправка жалоб....</b>", 0.15),
        ("<b>Отправка 154 жалобы на аккаунт....</b>", 0.15),
    ]

    prev_msg = None
    for text, delay in stages:
        # Удаляем предыдущее сообщение (если есть)
        if prev_msg:
            await delete_msg(chat_id, prev_msg.message_id, bcid)
            prev_msg = None

        # Отправляем новое
        prev_msg = await send_status(chat_id, bcid, text)

        # Ждём
        await asyncio.sleep(delay)

    # 3. Визуальная загрузка 0→100%
    if prev_msg:
        await delete_msg(chat_id, prev_msg.message_id, bcid)
        prev_msg = None

    bar_length = 15
    steps = 40
    delay = 0.08  # 40 * 0.08 = ~3.2 сек

    for i in range(steps + 1):
        percent = int((i / steps) * 100)
        filled = int((i / steps) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        if percent < 30:
            tail = "▰▱▱▱▱"
        elif percent < 60:
            tail = "▰▰▰▱▱"
        elif percent < 90:
            tail = "▰▰▰▰▱"
        else:
            tail = "▰▰▰▰▰"

        if percent < 100:
            text = f"<b>Загрузка [{bar}] {percent}%</b>\n{tail}"
        else:
            text = f"<b>Загрузка [{bar}] 100%</b>\n✅ <b>Готово!</b>"

        # Удаляем предыдущее сообщение
        if prev_msg:
            await delete_msg(chat_id, prev_msg.message_id, bcid)

        # Отправляем новое
        prev_msg = await send_status(chat_id, bcid, text)

        await asyncio.sleep(delay)

    # 4. Финал — удаляем последний прогресс и шлём итог
    if prev_msg:
        await delete_msg(chat_id, prev_msg.message_id, bcid)

    await send_status(
        chat_id, bcid,
        f"<b>✅ Процесс завершен!</b>\n\n"
        f"<b>Заявка на удаление аккаунта {target_name} отправлена.</b>"
    )


# ==================== ЗАПУСК ====================
async def main():
    print("=" * 50)
    print("БОТ-СЕКРЕТАРЬ ЗАПУЩЕН!")
    print("=" * 50)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())