import logging
import threading
import traceback

import ddddocr
from selenium.common.exceptions import NoSuchWindowException

# for embedding
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from type import Notify, TicketSoldOutError
from utils import countdown, init_list, wait_if_paused, get_webdriver


class Bot:
    def __init__(
        self,
        continue_event: threading.Event,
        pause_flag: threading.Event,
        end_flag: threading.Event,
        logger: logging.Logger,
        event_url: str,
        chrome_user_data_dir: str,
        chrome_profile_dir_path: str,
        requested_tickets: int = 1,
        session_index_list: list[int] = None,
        keyword_list: list[str] = None,
        auto_login: bool = False,
        try_again_when_error: bool = False,
        notify_prefix: str = None,
        success_message: str = None,
        ticket_detail_img_path: str = None,
        target_time: str = None,
    ):
        super().__init__()
        self.continue_event = continue_event
        self.pause_flag = pause_flag
        self.end_flag = end_flag
        self.event_url = event_url
        self.keyword_list = init_list(keyword_list)
        self.requested_tickets = requested_tickets
        self.target_time = target_time
        self.notify_prefix = notify_prefix
        self.success_message = success_message
        self.try_again_when_error = try_again_when_error
        self.ticket_detail_img_path = ticket_detail_img_path
        self.auto_login = auto_login
        self.session_index_list = init_list(session_index_list)
        self.ocr = ddddocr.DdddOcr()
        self.notify = Notify()
        self.driver = get_webdriver(
            user_data_dir=chrome_user_data_dir,
            profile_dir=chrome_profile_dir_path,
        )
        self.logger = logger
        self.session_url_list = list()

    def login(self):
        """Subclass should implement this method."""
        raise NotImplementedError

    def __login(self):
        if not self.auto_login:
            self.driver.get(self.event_url)
            self.logger.warning("confirm_login")
            self.continue_event.wait()
            self.continue_event.clear()
            return
        self.login()

    def __fill_ticket_form(self):
        raise NotImplementedError

    def __get_form_result(self):
        raise NotImplementedError

    def fill_ticket_form(self):
        """Fill in the ticket form and check the result."""
        while True:
            wait_if_paused(self.pause_flag, self.continue_event, self.logger)
            self.logger.info("填寫購票表單")
            self.__fill_ticket_form()
            if self.__get_form_result():
                return

    def get_session_info(event_url) -> list:
        """Get session info from the event page."""
        pass

    def refresh_session_links(self):
        """Get all session links from the event page and store them in session_url_list"""
        raise NotImplementedError

    def find_available_ticket(self, session_url: str) -> bool:
        """Find available tickets in the session page."""
        raise NotImplementedError

    def purchase_session(self, session_url: str) -> bool:
        while True:
            self.logger.info(f"尋找 {session_url} 是否有可購票區域")
            if not self.find_available_ticket(session_url):
                return False
            try:
                self.fill_ticket_form()
                return True
            except TicketSoldOutError as e:
                self.logger.info(e)
                continue

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
        self.logger.info("腳本結束，等待手動關閉...")
        self.end_flag.set()
        self.continue_event.wait()

    def cleanup(self):
        self.end_flag.clear()
        self.pause_flag.clear()
        self.continue_event.clear()
        self.logger.info("關閉瀏覽器")
        self.driver.quit()