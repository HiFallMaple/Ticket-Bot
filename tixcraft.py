import json
import logging
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from logging.handlers import QueueHandler

import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import (
    NoSuchWindowException,
    UnexpectedAlertPresentException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

# for embedding
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CHROME_USER_DATA_PATH, CONFIG
from bot import Bot
from type import DummyEvent, TicketSoldOutError
from utils import selenium_get_img


class Tixcraft(Bot):
    def __init__(
        self,
        continue_event: threading.Event,
        wait_login_flag: threading.Event,
        wait_captcha_flag: threading.Event,
        pause_flag: threading.Event,
        end_flag: threading.Event,
        logger: logging.Logger,
        event_url: str,
        chrome_user_data_dir: str,
        chrome_profile_dir_path: str,
        retry_delay: int = 5,
        requested_tickets: int = 1,
        session_index_list: list[int] = None,
        positive_keyword_list: list[str] = None,
        negative_keyword_list: list[str] = None,
        auto_login: bool = False,
        auto_input_captcha: bool = False,
        try_again_when_error: bool = False,
        notify_prefix: str = None,
        success_message: str = None,
        ticket_detail_img_path: str = None,
        target_time_str: str = None,
    ):
        super().__init__(
            continue_event=continue_event,
            wait_login_flag=wait_login_flag,
            wait_captcha_flag=wait_captcha_flag,
            pause_flag=pause_flag,
            end_flag=end_flag,
            logger=logger,
            event_url=event_url,
            chrome_user_data_dir=chrome_user_data_dir,
            chrome_profile_dir_path=chrome_profile_dir_path,
            retry_delay=retry_delay,
            requested_tickets=requested_tickets,
            session_index_list=session_index_list,
            positive_keyword_list=positive_keyword_list,
            negative_keyword_list=negative_keyword_list,
            auto_login=auto_login,
            auto_input_captcha=auto_input_captcha,
            try_again_when_error=try_again_when_error,
            notify_prefix=notify_prefix,
            success_message=success_message,
            ticket_detail_img_path=ticket_detail_img_path,
            target_time_str=target_time_str,
        )
        self.LOGIN_URL = "https://tixcraft.com/login/google"
        self.CHECKOUT_URL = "https://tixcraft.com/ticket/checkout"

    def check_cookie_banner(self):
        current_time = datetime.now(timezone.utc)  # 获取当前 UTC 时间
        expiration_time = current_time + timedelta(days=365)  # 设置过期时间为1年后
        expiration_str = expiration_time.strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )  # 格式化为类似于 '2024-10-11T10:34:16.080Z' 的格式

        # 设置 Cookie
        cookie = {
            "name": "OptanonAlertBoxClosed",
            "value": "45",  # 你可以根据需要设置值
            "domain": ".tixcraft.com",
            "path": "/",
            "secure": True,
            "httpOnly": False,
            "sameSite": "Lax",
            "expires": expiration_str,  # 使用计算的过期时间
        }

        self.driver.add_cookie(cookie)
        self.driver.refresh()

    def login(self):
        self.logger.info("嘗試登入")
        self.driver.get(self.LOGIN_URL)
        WebDriverWait(self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]).until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
        current_url = self.driver.current_url
        if "tixcraft.com" in current_url:
            self.logger.info("已登入")
            return

        WebDriverWait(self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#yDmH0d"))
        )

        self.logger.info("自動選擇 Google 登入")
        login_button = WebDriverWait(
            self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]
        ).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "div.Anixxd div.HvrJge div > div > ul li:nth-child(1) div",
                )
            )
        )
        login_button.click()
        raise NotImplementedError

    def _fill_ticket_form(self, ticket_url: str):
        self.driver.execute_script("document.body.style.zoom='70%'")
        ticket_num_selector = "[id^='TicketForm_ticketPrice_']"
        ticket_select = WebDriverWait(
            self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]
        ).until(EC.presence_of_element_located((By.CSS_SELECTOR, ticket_num_selector)))
        has_enough_tickets = False
        for option in Select(ticket_select).options:
            if int(option.get_attribute("value")) >= self.requested_tickets:
                has_enough_tickets = True
                break
        if not has_enough_tickets:
            raise TicketSoldOutError("已無足夠票數")
        
        ticket_select.location_once_scrolled_into_view  # scroll into view
        self.logger.info(f"選擇購票張數: {self.requested_tickets}")
        ticket_select.send_keys(str(self.requested_tickets))

        self.logger.info("勾選同意條款")
        agree_checkbox = WebDriverWait(
            self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]
        ).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#TicketForm_agree")))
        while not agree_checkbox.is_selected():
            agree_checkbox.location_once_scrolled_into_view  # scroll into view
            WebDriverWait(self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#TicketForm_agree"))
            )
            agree_checkbox.click()

        verify_code_input = WebDriverWait(
            self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]
        ).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#TicketForm_verifyCode"))
        )
        verify_code_input.location_once_scrolled_into_view  # scroll into view
        if not self.auto_input_captcha:
            self.driver.execute_script("arguments[0].focus();", verify_code_input)
            self.wait_captcha_flag.set()
            self.continue_event.wait()
            self.continue_event.clear()
            self.wait_captcha_flag.clear()
            return

        image = selenium_get_img(self.driver, "#TicketForm_verifyCode-image")
        result = self.ocr.classification(image)
        self.logger.info(f"自動填入驗證碼: {result}")
        verify_code_input.send_keys(result)
        submit_button = WebDriverWait(
            self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]
        ).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "#form-ticket-ticket > div.mgt-32.col-lg-12.col-md-12.col-sm-12.col-xs-12.col-12.text-center > button.btn.btn-primary.btn-green",
                )
            )
        )
        self.logger.info("確認購票")
        submit_button.click()

    def _screen_shot_ticket_detail(self):
        check_detail = WebDriverWait(
            self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]
        ).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#cartList")))
        check_detail.location_once_scrolled_into_view  # scroll into view
        self.logger.info("正在截圖購票結果，請稍候...")
        os.makedirs(CONFIG["SCREENSHOT_DIR"], exist_ok=True)
        check_detail.screenshot(CONFIG["TICKET_DETAIL_IMG_PATH"])

    def _get_form_result(self, ticket_url: str) -> bool:
        while True:
            self.logger.info("等待購票結果")
            alert_text = str()
            try:
                current_url = self.driver.current_url
                if current_url == ticket_url:
                    self.logger.info("未如預期點擊購票，重新填寫表單")
                    return False
                if current_url == self.CHECKOUT_URL:
                    self.logger.info(f"頁面已跳轉至 {current_url}")
                    return True
            except UnexpectedAlertPresentException as e:
                alert_text = e.alert_text

            if alert_text:
                if "驗證碼" in alert_text:
                    return False
                if "已售完" in alert_text or "已無足夠" in alert_text:
                    raise TicketSoldOutError(alert_text)
            time.sleep(0.5)

    def get_session_info(event_url):
        response = requests.get(event_url)
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("#gameList > table > tbody > tr")
        events = list()
        for row in rows:
            if "目前無場次資訊" in row.text.strip():
                return events
            cells = row.find_all("td")
            event = {
                "performance_time": cells[0].get_text(strip=True),
                "event_name": cells[1].get_text(strip=True),
                "venue": cells[2].get_text(strip=True),
                "purchase_status": cells[3].get_text(strip=True),
            }
            events.append(event)
        return events

    def refresh_session_links(self):
        self.logger.info("更新場次購票連結")
        self.session_url_list.clear()
        response = requests.get(self.event_url)
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("#gameList > table > tbody > tr")
        for index in self.session_index_list:
            if index >= len(rows):
                continue
            row = rows[index]
            row_text = row.text.strip()
            self.logger.info(f"取得場次：{row_text}")
            if "Find tickets" in row_text:
                match = re.search(r'data-href="([^"]+)"', str(row))
                event_url = match.group(1)
                self.session_url_list.append(event_url)
                self.logger.info("場次符合條件，已存入待搶清單")

    def __area_is_available_for_purchase(self, row_text: str, keyword: str) -> bool:
        # check if the row contains any keyword
        if keyword not in row_text:
            return False
        for negative_keyword in self.negative_keyword_list:
            if negative_keyword in row_text:
                return False
        # remaining seats
        match = re.search(r"(\d+)\s+seat\(s\)\s+remaining", row_text)
        if match:
            remaining_seats = int(match.group(1))
            return remaining_seats >= self.requested_tickets
        # available
        if "Available" in row_text:
            return True
        return False

    def __get_area_url_list(self, response_text) -> dict | None:
        pattern = r"var areaUrlList = (\{.*?\});"
        match = re.search(pattern, response_text, re.DOTALL)
        if not match:
            return None
        return json.loads(match.group(1))

    def find_available_ticket(self, session_url: str) -> list:
        response = requests.get(session_url)
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select('[id^="group_"] > li')
        match_rows = list()
        for keyword in self.positive_keyword_list:
            for row in rows:
                if (
                    self.__area_is_available_for_purchase(str(row), keyword)
                    and row not in match_rows
                ):
                    match_rows.append(row)
        available_url_list = list()
        area_url_list = self.__get_area_url_list(response.text)
        if not area_url_list:
            return []
        for row in match_rows:
            match = re.search(r'a id="([^"]+)"', str(row))
            if match:
                id = match.group(1)
                self.logger.info(f"可選購: {row.text}")
                self.logger.info(f"購票連結: {area_url_list[id]}")
                available_url_list.append(area_url_list[id])
        return available_url_list


def __get_logger(log_queue):
    if log_queue:
        log_handler = QueueHandler(log_queue)
    else:
        log_handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter("%(asctime)s - :%(levelname)s - %(message)s")
    log_handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    logger.addHandler(log_handler)
    return logger


def main(
    continue_event: threading.Event = None,
    wait_login_flag: threading.Event = None,
    wait_captcha_flag: threading.Event = None,
    pause_flag: threading.Event = None,
    end_flag: threading.Event = None,
    log_queue=None,
):
    if not continue_event:
        continue_event = DummyEvent()
    if not pause_flag:
        pause_flag = DummyEvent()
    if not end_flag:
        end_flag = DummyEvent()
    if not wait_login_flag:
        wait_login_flag = DummyEvent()
    if not wait_captcha_flag:
        wait_captcha_flag = DummyEvent()

    logger = __get_logger(log_queue)
    try:
        logger.info("開啟瀏覽器")
        ticket_bot = Tixcraft(
            continue_event=continue_event,
            wait_login_flag=wait_login_flag,
            wait_captcha_flag=wait_captcha_flag,
            pause_flag=pause_flag,
            end_flag=end_flag,
            logger=logger,
            event_url=CONFIG["TIXCRAFT_EVENT_URL"],
            chrome_user_data_dir=CHROME_USER_DATA_PATH,
            chrome_profile_dir_path=CONFIG["CHROME_PROFILE_DIR_PATH"],
            retry_delay=CONFIG["RETRY_DELAY"],
            requested_tickets=CONFIG["REQUEST_TICKETS"],
            session_index_list=CONFIG["TIXCRAFT_SESSION_INDEX_LIST"],
            positive_keyword_list=CONFIG["POSITIVE_KEYWORD_LIST"],
            negative_keyword_list=CONFIG["NEGATIVE_KEYWORD_LIST"],
            auto_login=CONFIG["AUTO_LOGIN"],
            auto_input_captcha=CONFIG["AUTO_INPUT_CAPTCHA"],
            try_again_when_error=CONFIG["TRY_AGAIN_WHEN_ERROR"],
            notify_prefix=CONFIG["NOTIFY_PREFIX"],
            success_message=CONFIG["SUCCESS_MESSAGE"],
            ticket_detail_img_path=CONFIG["TICKET_DETAIL_IMG_PATH"],
            target_time_str=CONFIG["TARGET_TIME_STR"],
        )
        ticket_bot.run()
    except SystemExit:
        logger.info("強制停止腳本")
    except NoSuchWindowException:
        logger.error("瀏覽器視窗已關閉，結束腳本")
    ticket_bot.cleanup()
    del ticket_bot


if __name__ == "__main__":
    main()
