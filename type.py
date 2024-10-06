import asyncio
import logging
import multiprocessing
import os
from enum import Enum
from typing import Literal, Optional

import requests
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from telegram import Bot, InputFile
from telegram.error import TelegramError

from config import CONFIG


class BrowserDriver:
    def __init__(self):
        service = Service(executable_path=CONFIG["CHROME_DRIVER_PATH"])
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-data-dir={CONFIG["CHROME_USER_DIR_PATH"]}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        self.driver = webdriver.Chrome(service=service, options=options)


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


class QueueHandler(logging.Handler):
    def __init__(self, queue: multiprocessing.Queue):
        super().__init__()
        self.queue: multiprocessing.Queue = queue

    def emit(self, record):
        msg = self.format(record)
        self.queue.put(msg)


class ActionRequest(BaseModel):
    action: Literal["run", "stop"]


class ProgramStatusEnum(Enum):
    RUNNING = "running"
    STOPPED = "stopped"


class BotStatus(BaseModel):
    status: ProgramStatusEnum


class ConfigSchema(BaseModel):
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
