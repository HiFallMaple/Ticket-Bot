import asyncio
import os
from enum import Enum
import threading
from typing import Literal, Optional

import requests
from pydantic import BaseModel

from telegram import Bot, InputFile
from telegram.error import TelegramError

from config import CONFIG


class TicketSoldOutError(Exception):
    pass


class Notify:
    def __init__(self):
        self.send_method = []
        if CONFIG["TG_TOKEN"] and CONFIG["TG_CHAT_ID"]:
            self.send_method.append(self.telegram_bot_send)
            self.bot = Bot(token=CONFIG["TG_TOKEN"])

        if CONFIG["LINE_NOTIFY_TOKEN"]:
            self.send_method.append(self.line_notify_send)

    def send(self, message: str, image_path: str = None):
        if not os.path.exists(image_path):
            print(f"Image path: {image_path} not exists.")
            image_path = None
        for method in self.send_method:
            method(message, image_path)
        return

    def telegram_bot_send(self, message: str, image_path: str = None):
        asyncio.run(self.__telegram_bot_send(message, image_path))

    async def __telegram_bot_send(self, message: str, image_path: str = None):
        try:
            if image_path:
                with open(image_path, "rb") as image_file:
                    await self.bot.send_photo(
                        chat_id=CONFIG["TG_CHAT_ID"],
                        caption=message,
                        photo=InputFile(image_file),
                    )
            else:
                await self.bot.send_message(chat_id=CONFIG["TG_CHAT_ID"], text=message)
            print("Message sent successfully!")
        except TelegramError as e:
            print(f"Failed to send message: {e}")

    def line_notify_send(self, message: str, image_path: str = None):
        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": f"Bearer {CONFIG["LINE_NOTIFY_TOKEN"]}"}
        data = {"message": message}
        files = {"imageFile": open(image_path, "rb")} if image_path else None
        print(f"Sending message: {message}")
        print(f"Sending files: {files}")
        response = requests.post(url, headers=headers, data=data, files=files)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")
            print(response.text)


class ProgramStatusEnum(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    ENDED = "ended"
    STOPPED = "stopped"


class ActionRequest(BaseModel):
    action: Literal["run", "stop", "pause", "continue"]


class BotStatus(BaseModel):
    status: ProgramStatusEnum


class ConfigSchema(BaseModel):
    CHROME_PROFILE_DIR_PATH: Optional[str] = None
    AUTO_LOGIN: Optional[bool] = None
    AUTO_INPUT_CAPTCHA: Optional[bool] = None
    NOTIFY_PREFIX: Optional[str] = None
    SUCCESS_MESSAGE: Optional[str] = None
    TG_TOKEN: Optional[str] = None
    TG_CHAT_ID: Optional[int] = None
    LINE_NOTIFY_TOKEN: Optional[str] = None
    TARGET_TIME_STR: Optional[str] = None
    KEYWORD_LIST: Optional[list[str]] = None
    REQUEST_TICKETS: Optional[int] = None
    TRY_AGAIN_WHEN_ERROR: Optional[bool] = None
    TIXCRAFT_EVENT_URL: Optional[str] = None
    TIXCRAFT_SESSION_INDEX_LIST: Optional[list[int]] = None


class SessionInfo(BaseModel):
    performance_time: str
    event_name: str
    venue: str
    purchase_status: str
    id: int


class DummyEvent(threading.Event):
    def __init__(self):
        pass

    def set(self):
        pass

    def clear(self):
        pass

    def wait(self, timeout=None):
        input("Press Enter to continue...")

    def is_set(self):
        return False
