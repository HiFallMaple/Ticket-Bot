import getpass
import json
import os
from datetime import datetime, timedelta
from typing import TypedDict

from utils import get_project_dir


STORE_KEY = [
    "TARGET_TIME_STR",
    "NOTIFY_PREFIX",
    "SUCCESS_MESSAGE",
    "REQUEST_TICKETS",
    "KEYWORD_LIST",
    "TRY_AGAIN_WHEN_ERROR",
    "TIXCRAFT_EVENT_URL",
    "TIXCRAFT_SESSION_INDEX_LIST",
    "TG_TOKEN",
    "TG_CHAT_ID",
    "LINE_NOTIFY_TOKEN",
]


class Config(TypedDict):
    CHROME_DRIVER_PATH: str
    CHROME_USER_DIR_PATH: str
    SELENIUM_WAIT_TIMEOUT: int
    NOTIFY_PREFIX: str
    SUCCESS_MESSAGE: str
    TG_TOKEN: str
    TG_CHAT_ID: int
    LINE_NOTIFY_TOKEN: str
    TARGET_TIME_STR: str
    TARGET_TIME: datetime
    READY_TIME: str
    SCREENSHOT_DIR: str
    TICKET_DETAIL_IMG_PATH: str
    KEYWORD_LIST: list[str]
    REQUEST_TICKETS: int
    TRY_AGAIN_WHEN_ERROR: bool
    TIXCRAFT_EVENT_URL: str
    TIXCRAFT_SESSION_INDEX_LIST: list[int]


PROJ_DIR = get_project_dir()
FRONTEND_PATH = os.path.join(PROJ_DIR, "frontend", "dist")

def load_config():
    with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
        j = json.load(f)
        for k, v in j.items():
            CONFIG[k] = v


def get_stored_config() -> dict:
    tmp_dict = dict()
    for key in STORE_KEY:
        tmp_dict[key] = CONFIG[key]
    return tmp_dict


def save_config():
    tmp_dict = get_stored_config()
    with open(CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(tmp_dict, f, ensure_ascii=False, indent=4)


CONFIG_JSON_PATH = os.path.join(PROJ_DIR, "config.json")
CONFIG = Config()
load_config()


CONFIG["CHROME_DRIVER_PATH"] = os.path.join(PROJ_DIR, "chromedriver.exe")
CONFIG["CHROME_USER_DIR_PATH"] = (
    f"C:\\Users\\{getpass.getuser()}\\AppData\\Local\\Google\\Chrome\\User Data"
)
CONFIG["SELENIUM_WAIT_TIMEOUT"] = 10

CONFIG["TARGET_TIME"] = datetime.strptime(
    CONFIG["TARGET_TIME_STR"], "%Y/%m/%d %H:%M:%S.%f"
)
CONFIG["READY_TIME"] = CONFIG["TARGET_TIME"] - timedelta(minutes=1)

CONFIG["SCREENSHOT_DIR"] = os.path.join(PROJ_DIR, "screenshots")
CONFIG["TICKET_DETAIL_IMG_PATH"] = os.path.join(
    CONFIG["SCREENSHOT_DIR"], "ticket_detail.png"
)
