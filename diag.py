#!/usr/bin/env python3
"""Debug script: test every layer of the bot pipeline."""
import asyncio
import sys
import traceback

async def test_all():
    errors = []

    # 1. Import check
    print("1️⃣ Testing imports...")
    try:
        from bot import config
        print(f"   BOT_TOKEN: {config.BOT_TOKEN[:10]}...")
        print(f"   OPENROUTER_KEY: {config.OPENROUTER_KEY[:10]}...")
        print(f"   OWNER_ID: {config.OWNER_ID}")
    except Exception as e:
        errors.append(f"config import: {e}")
        print(f"   ❌ {e}")

    # 2. Database check
    print("\n2️⃣ Testing database...")
    try:
        from bot import database as db
        await db.init_db()
        print("   ✅ Database initialized")
    except Exception as e:
        errors.append(f"database: {e}")
        print(f"   ❌ {e}")
        traceback.print_exc()

    # 3. Router check
    print("\n3️⃣ Testing intent router...")
    try:
        from bot.router import detect_intent, detect_lang
        tests = [
            ("سلام خوبی", "chat"),
            ("قیمت دلار", "chat"),
            ("یه عکس بکش", "image"),
            ("این کد رو بنویس", "code"),
            ("solve x+1=5", "reason"),
        ]
        for text, expected in tests:
            result = detect_intent(text)
            status = "✅" if result == expected else "❌"
            print(f"   {status} '{text}' → intent={result} (expected={expected})")
    except Exception as e:
        errors.append(f"router: {e}")
        print(f"   ❌ {e}")

    # 4. Handler registration check
    print("\n4️⃣ Testing handler registration...")
    try:
        from aiogram import Bot, Dispatcher
        from bot.handlers import common, actions, admin, translate, notes, remind
        from bot.handlers import quiz, search, files, extras, groups, panel, tools, media, chat
        from bot.middleware import RateLimitMiddleware, InputValidationMiddleware

        bot = Bot(token=config.BOT_TOKEN)
        dp = Dispatcher()

        dp.message.middleware(InputValidationMiddleware())
        dp.message.middleware(RateLimitMiddleware(max_requests=30, window_seconds=60))
        dp.callback_query.middleware(InputValidationMiddleware())
        dp.callback_query.middleware(RateLimitMiddleware(max_requests=30, window_seconds=60))

        routers = [
            common.router, actions.router, admin.router, translate.router,
            notes.router, remind.router, quiz.router, search.router,
            files.router, extras.router, groups.router, panel.router,
            tools.router, media.router, chat.router,
        ]
        for r in routers:
            dp.include_router(r)

        # Count handlers per router
        for r_name, r in zip(["common","actions","admin","translate","notes","remind","quiz","search","files","extras","groups","panel","tools","media","chat"], routers):
            msg_handlers = len(r.message.handlers)
            cb_handlers = len(r.callback_query.handlers)
            print(f"   {r_name}: {msg_handlers} message + {cb_handlers} callback handlers")

        # Check what chat.router catches
        print("\n   Chat router message filters:")
        for h in chat.router.message.handlers:
            print(f"     filter: {h.filters}")

        print("\n   Panel router message filters:")
        for h in panel.router.message.handlers:
            print(f"     filter: {h.filters}")

        print("\n   Tools router message filters:")
        for h in tools.router.message.handlers:
            print(f"     filter: {h.filters}")

        await bot.session.close()
        print("   ✅ All routers registered")
    except Exception as e:
        errors.append(f"handler registration: {e}")
        print(f"   ❌ {e}")
        traceback.print_exc()

    # 5. OpenRouter API check
    print("\n5️⃣ Testing OpenRouter API...")
    try:
        from bot import openrouter
        messages = [{"role": "user", "content": "Say hi in one word."}]
        reply, usage = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=10),
            timeout=30,
        )
        print(f"   ✅ Reply: {reply[:50]}")
        print(f"   Usage: {usage}")
    except Exception as e:
        errors.append(f"openrouter: {e}")
        print(f"   ❌ {e}")

    # 6. Middleware check
    print("\n6️⃣ Testing middleware with sample message...")
    try:
        from unittest.mock import AsyncMock, MagicMock
        from aiogram.types import Message, User, Chat
        from bot.middleware import RateLimitMiddleware, InputValidationMiddleware

        # Create mock message
        mock_msg = MagicMock(spec=Message)
        mock_msg.text = "سلام خوبی"
        mock_msg.from_user = MagicMock(spec=User)
        mock_msg.from_user.id = 12345
        mock_msg.answer = AsyncMock()

        mock_chat = MagicMock(spec=Chat)
        mock_chat.type = "private"
        mock_msg.chat = mock_chat

        mock_call = MagicMock()
        mock_data = {}

        # Test InputValidation
        iv = InputValidationMiddleware()
        result = await iv(mock_call, mock_msg, mock_data)
        print(f"   InputValidation: {'✅ passed' if result is not None else '❌ BLOCKED!'}")

        # Test RateLimit
        rl = RateLimitMiddleware(max_requests=30, window_seconds=60)
        result = await rl(mock_call, mock_msg, mock_data)
        print(f"   RateLimit: {'✅ passed' if result is not None else '❌ BLOCKED!'}")

    except Exception as e:
        errors.append(f"middleware: {e}")
        print(f"   ❌ {e}")
        traceback.print_exc()

    # 7. process_text check
    print("\n7️⃣ Testing core.process_text import...")
    try:
        from bot.handlers import core
        print(f"   ✅ process_text: {core.process_text}")
    except Exception as e:
        errors.append(f"core import: {e}")
        print(f"   ❌ {e}")
        traceback.print_exc()

    # Summary
    print("\n" + "=" * 50)
    if errors:
        print(f"❌ Found {len(errors)} errors:")
        for e in errors:
            print(f"   • {e}")
    else:
        print("✅ All checks passed!")

if __name__ == "__main__":
    asyncio.run(test_all())
