import json
import logging
import multiprocessing
import re
import traceback
from logging.handlers import QueueHandler

import ddddocr
import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# for embedding
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG
from type import BrowserDriver, Notify
from utils import selenium_get_img, countdown, init_list


class TicketSoldOutError(Exception):
    pass


class Tixcraft(BrowserDriver):
    def __init__(
        self,
        wait_event: multiprocessing.Event,
        log_handler: logging.StreamHandler,
        event_url: str,
        session_index_list: list[int] = None,
        keyword_list: list[str] = None,
        requested_tickets: int = 1,
    ):
        super().__init__()
        self.wait_event = wait_event
        self.event_url = event_url
        self.keyword_list = init_list(keyword_list)
        self.requested_tickets = requested_tickets
        self.session_index_list = init_list(session_index_list)
        self.session_url_list = []
        self.ocr = ddddocr.DdddOcr()
        self.notify = Notify()
        self.LOGIN_URL = "https://tixcraft.com/login/google"
        self.CHECKOUT_URL = "https://tixcraft.com/ticket/checkout"
        self.logger = self.__init_logger(log_handler)

    def __init_logger(self, log_handler: logging.StreamHandler):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(log_handler)
        return logger

    def login(self):
        if not CONFIG["AUTO_LOGIN"]:
            self.driver.get(self.event_url)
            self.logger.warning("confirm_login")
            self.wait_event.wait()
            self.wait_event.clear()
            return
        
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
        self.logger.info("使用 Google 登入")
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
        image = selenium_get_img(self.driver, "#TicketForm_verifyCode-image")
        result = self.ocr.classification(image)
        verify_code_input = WebDriverWait(
            self.driver, CONFIG["SELENIUM_WAIT_TIMEOUT"]
        ).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#TicketForm_verifyCode"))
        )
        verify_code_input.location_once_scrolled_into_view  # scroll into view
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
            except TicketSoldOutError as e:
                raise e
            except TimeoutException:
                pass

            current_url = self.driver.current_url
            if current_url == self.CHECKOUT_URL:
                self.logger.info(f"頁面已跳轉至 {self.event_url}")
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

    def find_available_ticket(self, event_url: str) -> bool:
        self.logger.info(f"尋找 {event_url} 是否有可購票區域")
        response = requests.get(event_url)
        pattern = r"var areaUrlList = (\{.*?\});"
        match = re.search(pattern, response.text, re.DOTALL)
        if not match:
            return False
        area_url_list = json.loads(match.group(1))
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select('[id^="group_"] > li')
        for row in rows:
            row_text = str(row)
            if self.__area_is_available_for_purchase(row_text):
                match = re.search(r'a id="([^"]+)"', row_text)
                id = match.group(1)
                self.driver.get(area_url_list[id])
                self.logger.info(f"選購: {row.text}")
                self.logger.info(f"購票連結: {area_url_list[id]}")
                return True
        return False

    def check_all_events_and_purchase_tickets(self):
        for event_url in self.session_url_list:
            if self.find_available_ticket(event_url):
                self.fill_ticket_form()
                self.notify.send(
                    f"{CONFIG["NOTIFY_PREFIX"]} {CONFIG["SUCCESS_MESSAGE"]}",
                    CONFIG["TICKET_DETAIL_IMG_PATH"],
                )
                return True
        return False

    def loop(self):
        try:
            self.login()
            countdown(CONFIG["TARGET_TIME"], self.logger)
            while True:
                self.refresh_session_links()
                if self.check_all_events_and_purchase_tickets():
                    return True
                self.logger.info("無可購票區域，重新嘗試...")
        except Exception:
            self.logger.error(traceback.format_exc())
            self.driver.refresh()
        return not CONFIG["TRY_AGAIN_WHEN_ERROR"]

    def start(self):
        while not self.loop():
            pass
        self.logger.info("腳本結束，等待手動關閉...")
        self.wait_event.wait()


def main(log_queue=None, wait_event=None):
    if log_queue:
        log_handler = QueueHandler(log_queue)
    else:
        log_handler = logging.StreamHandler(sys.stdout)

    if not wait_event:
        wait_event = multiprocessing.Event()

    formatter = logging.Formatter("%(asctime)s - :%(levelname)s - %(message)s")
    log_handler.setFormatter(formatter)

    ticket_bot = Tixcraft(
        wait_event=wait_event,
        log_handler=log_handler,
        event_url=CONFIG["TIXCRAFT_EVENT_URL"],
        session_index_list=CONFIG["TIXCRAFT_SESSION_INDEX_LIST"],
        keyword_list=CONFIG["KEYWORD_LIST"],
        requested_tickets=CONFIG["REQUEST_TICKETS"],
    )
    ticket_bot.start()


if __name__ == "__main__":
    main()
