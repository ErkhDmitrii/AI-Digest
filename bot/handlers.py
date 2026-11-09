"""Обработчики Telegram-бота — модерация и публикация."""
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from config.settings import settings
from db.repository import (get_digest_by_id, get_next_issue_number,
                           mark_digest_published, save_digest,
                           update_digest_decision)

log = logging.getLogger("bot.handlers")

session = AiohttpSession()
bot = Bot(token=settings.BOT_TOKEN, session=session)
dp = Dispatcher()

# Хранилище ID последнего черновика для callback
_pending_digests: dict = {}  # {message_id: digest_id}


async def send_draft_to_admin(digest_text: str):
    """Отправляет черновик дайджеста всем админам из списка с inline-кнопками."""
    from digest.postprocess import split_for_telegram

    parts = split_for_telegram(digest_text)

    # Сохраняем в БД
    issue_number = await get_next_issue_number()
    digest_id = await save_digest(issue_number, digest_text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать",
                                 callback_data=f"pub:{digest_id}"),
            InlineKeyboardButton(text="✏️ Редактировать",
                                 callback_data=f"edit:{digest_id}"),
            InlineKeyboardButton(text="❌ Отклонить",
                                 callback_data=f"rej:{digest_id}"),
        ]
    ])

    # ЦИКЛ ПО ВСЕМ АДМИНАМ
    for admin_id in settings.ADMIN_CHAT_IDS:
        try:
            # Отправляем первую часть с кнопками
            msg = await bot.send_message(
                chat_id=admin_id,
                text=parts[0],
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

            _pending_digests[msg.message_id] = digest_id


            for part in parts[1:]:
                await bot.send_message(
                    chat_id=admin_id,
                    text=part,
                    parse_mode="Markdown",
                )
        except Exception as e:
            log.error(f"Не удалось отправить дайджест админу {admin_id}: {e}")

    log.info("Черновик #%d отправлен всем админам", issue_number)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🤖 AI-Дайджест бот\n\n"
        "Я собираю новости Грузии, фильтрую через AI и отправляю черновик дайджеста "
        "для модерации. Подписка на рассылку — в канале."
    )


@dp.callback_query(F.data.startswith("pub:"))
async def cb_publish(callback: CallbackQuery):
    """Публикация дайджеста в целевой канал."""
    digest_id = int(callback.data.split(":")[1])

    digest = await get_digest_by_id(digest_id)
    if not digest:
        await callback.answer("Дайджест не найден", show_alert=True)
        return
        
    if digest.status == "published":
        await callback.answer("Этот дайджест уже был опубликован!", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return

    from digest.postprocess import split_for_telegram

    text_to_publish = digest.final_text if digest.final_text else digest.content
    parts = split_for_telegram(text_to_publish)

    try:
        for part in parts:
            await bot.send_message(
                chat_id=settings.TARGET_CHANNEL_ID,
                text=part,
                parse_mode="Markdown",
            )

        await mark_digest_published(digest_id)
        await update_digest_decision(digest_id, "published")
        await callback.answer("✅ Опубликовано в канал!")
        await callback.message.edit_reply_markup(reply_markup=None)
        log.info("Дайджест #%d опубликован в канал", digest.issue_number)

    except Exception as e:
        log.error("Ошибка публикации: %s", e)
        await callback.answer(f"Ошибка: {e}", show_alert=True)


@dp.callback_query(F.data.startswith("edit:"))
async def cb_edit(callback: CallbackQuery):
    """Редактирование дайджеста — ждём новый текст от админа."""
    digest_id = int(callback.data.split(":")[1])
    _pending_digests[f"edit_{callback.from_user.id}"] = digest_id

    await callback.answer()
    await callback.message.answer(
        "✏️ Отправьте исправленный текст дайджеста следующим сообщением."
    )


@dp.callback_query(F.data.startswith("rej:"))
async def cb_reject(callback: CallbackQuery):
    """Отклонение дайджеста."""
    digest_id = int(callback.data.split(":")[1])
    
    digest = await get_digest_by_id(digest_id)

    # Защита: если уже обработан, не отклоняем повторно
    if digest and digest.status in ["published", "decided"]:
        await callback.answer("Этот дайджест уже обработан!", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return

    await update_digest_decision(digest_id, "rejected")
    await callback.answer("❌ Отклонён")
    await callback.message.edit_reply_markup(reply_markup=None)
    log.info("Дайджест #%d отклонён", digest_id)


@dp.message(F.chat.type == "private", F.text)
async def handle_edited_text(message: Message):
    key = f"edit_{message.from_user.id}"
    if key not in _pending_digests:

        await message.answer("⚠️ Я не жду от вас текст для редактирования. Нажмите кнопку «✏️ Редактировать» под нужным черновиком заново.")
        return

    digest_id = _pending_digests.pop(key)
    
    try:
        await update_digest_decision(digest_id, "edited", final_text=message.text)
        log.info(f"Текст дайджеста ID {digest_id} успешно обновлен")
    except Exception as e:
        log.error(f"Ошибка при обновлении БД: {e}")
        await message.answer(f"Ошибка при сохранении: {e}")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"pub:{digest_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"rej:{digest_id}"),
        ]
    ])

    await message.answer(
        "Текст сохранён. Проверьте и опубликуйте:",
        reply_markup=keyboard,
    )
