import logging
import random
import threading
import time
import traceback
from datetime import datetime

import ddddocr
from selenium.common.exceptions import NoSuchWindowException

# for embedding
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATE_FORMAT
from type import Notify, TicketSoldOutError
from utils import countdown, init_list, wait_if_paused, get_webdriver


class Bot:
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
        keyword_list: list[str] = None,
        auto_login: bool = False,
        auto_input_captcha: bool = False,
        try_again_when_error: bool = False,
        notify_prefix: str = None,
        success_message: str = None,
        ticket_detail_img_path: str = None,
        target_time_str: str = None,
    ):
        super().__init__()
        self.continue_event = continue_event
        self.wait_login_flag = wait_login_flag
        self.wait_captcha_flag = wait_captcha_flag
        self.pause_flag = pause_flag
        self.end_flag = end_flag
        self.event_url = event_url
        self.keyword_list = init_list(keyword_list)
        self.retry_delay = retry_delay
        self.requested_tickets = requested_tickets
        self.notify_prefix = notify_prefix
        self.success_message = success_message
        self.try_again_when_error = try_again_when_error
        self.ticket_detail_img_path = ticket_detail_img_path
        self.auto_login = auto_login
        self.auto_input_captcha = auto_input_captcha
        self.session_index_list = init_list(session_index_list)
        self.ocr = ddddocr.DdddOcr()
        self.notify = Notify()
        self.driver = get_webdriver(
            user_data_dir=chrome_user_data_dir,
            profile_dir=chrome_profile_dir_path,
        )
        self.target_time = datetime.strptime(target_time_str, DATE_FORMAT)
        self.logger = logger
        self.session_url_list = list()

    def __del__(self):
        self.cleanup()

    def check_cookie_banner(self):
        raise NotImplementedError

    def login(self):
        """Subclass should implement this method."""
        raise NotImplementedError

    def __login(self):
        self.driver.get(self.event_url)
        self.check_cookie_banner()
        if not self.auto_login:
            self.wait_login_flag.set()
            self.continue_event.wait()
            self.continue_event.clear()
            self.wait_login_flag.clear()
            return
        self.login()

    def _fill_ticket_form(self):
        raise NotImplementedError

    def _get_form_result(self):
        raise NotImplementedError

    def _screen_shot_ticket_detail(self):
        raise NotImplementedError

    def fill_ticket_form(self, ticket_url: str):
        """Fill in the ticket form and check the result."""
        while True:
            wait_if_paused(self.pause_flag, self.continue_event, self.logger)
            self.logger.info(f"填寫購票表單 {ticket_url}")
            self.driver.get(ticket_url)
            self._fill_ticket_form()
            if self._get_form_result():
                return

    def get_session_info(event_url) -> list:
        """Get session info from the event page."""
        pass

    def refresh_session_links(self):
        """Get all session links from the event page and store them in session_url_list"""
        raise NotImplementedError

    def find_available_ticket(self, session_url: str) -> list:
        """Find available tickets in the session page."""
        raise NotImplementedError

    def purchase_session(self, session_url: str) -> bool:
        self.logger.info(f"尋找 {session_url} 是否有可購票區域")
        for ticket_url in self.find_available_ticket(session_url):
            try:
                self.fill_ticket_form(ticket_url)
                return True
            except TicketSoldOutError as e:
                self.logger.info(e)
                continue
        return False

    def purchase(self):
        self.logger.info("更新場次購票連結")
        self.refresh_session_links()
        wait_if_paused(self.pause_flag, self.continue_event, self.logger)
        for session_url in self.session_url_list:
            wait_if_paused(self.pause_flag, self.continue_event, self.logger)
            if self.purchase_session(session_url):
                return True
        return False

    def run(self):
        """
        infinite loop until tickets are purchased
        if error occurs:
            TRY_AGAIN_WHEN_ERROR=True: re-login and try again
            TRY_AGAIN_WHEN_ERROR=False: end infinite loop
        """
        self.__login()
        if self.target_time:
            countdown(self.target_time, self.logger)
        while True:
            try:
                if self.purchase():
                    if not self.notify.need_notify():
                        break
                    self._screen_shot_ticket_detail()
                    self.notify.send(
                        f"{self.notify_prefix} {self.success_message}",
                        self.ticket_detail_img_path,
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
                if not self.try_again_when_error:
                    break
            # random delay retry_delay
            random_delay = random.randint(0, self.retry_delay)
            self.logger.info(f"等待 {random_delay} 秒後重試")
            time.sleep(random_delay)

        self.logger.info("腳本結束，等待手動關閉...")
        self.end_flag.set()
        self.continue_event.wait()

    def cleanup(self):
        self.end_flag.clear()
        self.pause_flag.clear()
        self.continue_event.clear()
        self.logger.info("關閉瀏覽器")
        self.driver.quit()
