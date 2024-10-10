import json
import logging
import threading
import re
import traceback
from logging.handlers import QueueHandler
from venv import logger

import ddddocr
import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, NoSuchWindowException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# for embedding
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG
from type import BrowserDriver, Notify, DummyEvent
from utils import selenium_get_img, countdown, init_list, wait_if_paused


class TicketSoldOutError(Exception):
    pass


class Tixcraft(BrowserDriver):
    def __init__(
        self,
        continue_event: threading.Event,
        pause_flag: threading.Event,
        end_flag: threading.Event,
        logger: logging.Logger,
        event_url: str,
        session_index_list: list[int] = None,
        keyword_list: list[str] = None,
        requested_tickets: int = 1,
    ):
        super().__init__()
        self.continue_event = continue_event
        self.pause_flag = pause_flag
        self.end_flag = end_flag
        self.event_url = event_url
        self.keyword_list = init_list(keyword_list)
        self.requested_tickets = requested_tickets
        self.session_index_list = init_list(session_index_list)
        self.session_url_list = []
        self.ocr = ddddocr.DdddOcr()
        self.notify = Notify()
        self.LOGIN_URL = "https://tixcraft.com/login/google"
        self.CHECKOUT_URL = "https://tixcraft.com/ticket/checkout"
        self.logger = logger

    def login(self):
        if not CONFIG["AUTO_LOGIN"]:
            self.driver.get(self.event_url)
            self.logger.warning("confirm_login")
            self.continue_event.wait()
            self.continue_event.clear()
            return

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

        logger.info("自動選擇 Google 登入")
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

    def __fill_ticket_form(self):
        self.driver.execute_script("document.body.style.zoom='70%'")
        ticket_num_selector = "[id^='TicketForm_ticketPrice_']"
        ticket_select = WebDriverWait(
            self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]
        ).until(EC.presence_of_element_located((By.CSS_SELECTOR, ticket_num_selector)))
        ticket_select.location_once_scrolled_into_view  # scroll into view
        ticket_select.send_keys(str(self.requested_tickets))
        agree_checkbox = WebDriverWait(
            self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]
        ).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#TicketForm_agree")))
        agree_checkbox.location_once_scrolled_into_view  # scroll into view
        agree_checkbox.click()

        verify_code_input = WebDriverWait(
            self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]
        ).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#TicketForm_verifyCode"))
        )
        verify_code_input.location_once_scrolled_into_view  # scroll into view
        if not CONFIG["AUTO_INPUT_CAPTCHA"]:
            self.driver.execute_script("arguments[0].focus();", verify_code_input)
            return

        image = selenium_get_img(self.driver, "#TicketForm_verifyCode-image")
        result = self.ocr.classification(image)
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
        submit_button.click()

    def __get_form_result(self):
        while True:
            try:
                alert = WebDriverWait(self.driver, 0.5).until(EC.alert_is_present())
                alert_text = alert.text
                alert.accept()
                print("警報內容:", alert_text)
                if "驗證碼" in alert_text:
                    return False
                if "已售完" in alert_text or "已無足夠" in alert_text:
                    raise TicketSoldOutError(alert_text)
            except TimeoutException:
                pass
            except TicketSoldOutError as e:
                raise e

            current_url = self.driver.current_url
            if current_url == self.CHECKOUT_URL:
                self.logger.info(f"頁面已跳轉至 {current_url}")
                check_detail = WebDriverWait(
                    self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]
                ).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#cartList")))
                check_detail.location_once_scrolled_into_view  # scroll into view
                self.logger.info("正在截圖購票結果，請稍候...")
                os.makedirs(CONFIG["SCREENSHOT_DIR"], exist_ok=True)
                check_detail.screenshot(CONFIG["TICKET_DETAIL_IMG_PATH"])
                return True

    def fill_ticket_form(self):
        while True:
            wait_if_paused(self.pause_flag, self.continue_event, self.logger)
            self.logger.info("填寫購票表單")
            self.__fill_ticket_form()
            if self.__get_form_result():
                return

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
        print(events)
        return events

    def __refresh_session_links(self):
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

    def refresh_session_links(self):
        self.logger.info("更新場次購票連結")
        self.session_url_list.clear()
        self.__refresh_session_links()
        while len(self.session_url_list) == 0:
            self.__refresh_session_links()

    def __area_is_available_for_purchase(self, row_text: str) -> bool:
        # check if the row contains any keyword
        if not any(keyword in row_text for keyword in self.keyword_list):
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

    def find_available_ticket(self, event_url: str) -> bool:
        self.logger.info(f"尋找 {event_url} 是否有可購票區域")
        response = requests.get(event_url)
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select('[id^="group_"] > li')
        for row in rows:
            row_text = str(row)
            if self.__area_is_available_for_purchase(row_text):
                match = re.search(r'a id="([^"]+)"', row_text)
                id = match.group(1)
                area_url_list = self.__get_area_url_list(response.text)
                if not area_url_list:
                    return False
                self.driver.get(area_url_list[id])
                self.logger.info(f"選購: {row.text}")
                self.logger.info(f"購票連結: {area_url_list[id]}")
                return True
        return False

    def purchase_one_session(self, event_url: str) -> bool:
        while True:
            if not self.find_available_ticket(event_url):
                return False
            try:
                self.fill_ticket_form()
                return True
            except TicketSoldOutError as e:
                self.logger.info(e)
                continue

    def purchase(self):
        self.refresh_session_links()
        wait_if_paused(self.pause_flag, self.continue_event, self.logger)
        for event_url in self.session_url_list:
            wait_if_paused(self.pause_flag, self.continue_event, self.logger)
            if self.purchase_one_session(event_url):
                return True
        return False

    def run(self):
        """
        infinite loop until tickets are purchased
        if error occurs:
            TRY_AGAIN_WHEN_ERROR=True: re-login and try again
            TRY_AGAIN_WHEN_ERROR=False: end infinite loop
        """
        self.login()
        countdown(CONFIG["TARGET_TIME"], self.logger)
        while True:
            try:
                if self.purchase():
                    self.notify.send(
                        f"{CONFIG["NOTIFY_PREFIX"]} {CONFIG["SUCCESS_MESSAGE"]}",
                        CONFIG["TICKET_DETAIL_IMG_PATH"],
                    )
                    break
                else:
                    self.logger.info("無可購票區域，重新嘗試...")
            except SystemExit as e:
                raise e
            except NoSuchWindowException:
                self.logger.error("瀏覽器視窗已關閉，強制停止腳本")
                return
            except Exception:
                self.logger.error(traceback.format_exc())
                if not CONFIG["TRY_AGAIN_WHEN_ERROR"]:
                    break
        self.logger.info("腳本結束，等待手動關閉...")
        self.end_flag.set()
        self.continue_event.wait()

    def cleanup(self):
        self.end_flag.clear()
        self.pause_flag.clear()
        self.continue_event.clear()
        self.logger.info("關閉瀏覽器")
        self.driver.quit()

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
    pause_flag: threading.Event = None,
    end_flag: threading.Event = None,
    log_queue=None,
):
    print("Config id tixcraft:", id(CONFIG), CONFIG)

    if not continue_event:
        continue_event = DummyEvent()
    if not pause_flag:
        pause_flag = DummyEvent()
    if not end_flag:
        end_flag = DummyEvent()
        
    logger = __get_logger(log_queue)
    try:
        logger.info("開啟瀏覽器")
        ticket_bot = Tixcraft(
            continue_event=continue_event,
            pause_flag=pause_flag,
            end_flag=end_flag,
            logger=logger,
            event_url=CONFIG["TIXCRAFT_EVENT_URL"],
            session_index_list=CONFIG["TIXCRAFT_SESSION_INDEX_LIST"],
            keyword_list=CONFIG["KEYWORD_LIST"],
            requested_tickets=CONFIG["REQUEST_TICKETS"],
        )
        ticket_bot.run()
    except SystemExit:
        logger.info("強制停止腳本")
    ticket_bot.cleanup()
    del ticket_bot


if __name__ == "__main__":
    main()
