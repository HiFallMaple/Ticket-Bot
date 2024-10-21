import base64
import ctypes
import logging
import os
import threading
import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc


def countdown(target_time: datetime, logger: logging.Logger | None = None) -> None:
    """Countdown to a specified target time.

    Args:
        target_time (datetime): The target time to count down to.
    """
    # Get the current time
    start_time = time.time()
    # Calculate the remaining time
    remaining_time = target_time.timestamp() - start_time
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.debug(f"start_time:{start_time}, target_time:{target_time}, remaining_time:{remaining_time}")

    # Count down every 0.98 seconds until the remaining time is less than or equal to 1 second
    while remaining_time > 1:
        logger.info(f"Remaining time: {remaining_time:.2f} seconds")
        time.sleep(0.98)  # Sleep for 0.98 seconds before the next update
        remaining_time = target_time.timestamp() - time.time()

    # Enter fast-check mode when remaining time is less than or equal to 1 second
    while remaining_time > 0.0:
        remaining_time = target_time.timestamp() - time.time()
        logger.debug(f"Remaining time: {remaining_time:.8f} seconds")
    logger.info("Time's up!")


def selenium_get_img(driver, image_selector: str) -> bytes:
    """Download captcha image and return it as bytes.

    Args:
        driver: The Selenium WebDriver instance.
        image_selector (str): The CSS selector for the image element.

    Returns:
        bytes: The image in bytes.
    """
    image_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, image_selector))
    )
    image_src = image_element.get_attribute("src")

    if image_src.startswith("data:image"):
        # Get the Base64 encoded part
        base64_image = image_src.split(",")[1]  # Split and get the Base64 part
    else:
        # If not Base64 encoded, handle it differently
        base64_image = driver.execute_script(
            """
            var element = arguments[0];
            var cnv = document.createElement('canvas');
            cnv.width = element.naturalWidth;
            cnv.height = element.naturalHeight;
            cnv.getContext('2d').drawImage(element, 0, 0, element.naturalWidth, element.naturalHeight);
            return cnv.toDataURL().substring(22); // Return Base64 string, removing the prefix
            """,
            image_element,
        )

    return base64.b64decode(base64_image)


def init_list(l: list) -> list | None:  # noqa: E741
    """Initialize a list or return None.

    Args:
        l (list): The input list.

    Returns:
        list: An empty list if the input is None, otherwise the input list.
    """
    return [] if l is None else l


def get_project_dir():
    """Get the project directory.

    Returns:
        str: The project directory path.
    """
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    return curr_dir


def wait_if_paused(
    pause_flag: threading.Event,
    continue_event: threading.Event,
    logger: logging.Logger | None = None,
) -> None:
    if pause_flag.is_set():
        if logger is None:
            logger = logging.getLogger(__name__)
        logger.info("腳本暫停")
        continue_event.wait()
        continue_event.clear()
        pause_flag.clear()
        logger.info("腳本繼續")


def raise_SystemExit_in_thread(thread: threading.Thread) -> None:
    """Raise SystemExit in a thread.

    Args:
        thread (threading.Thread): The thread to raise SystemExit in.
    """
    thread_id = thread.ident
    ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread_id), ctypes.py_object(SystemExit)
    )


def get_webdriver(user_data_dir: str = None, profile_dir: str = None):
    options = uc.ChromeOptions()
    if profile_dir:
        options.add_argument(f"--profile-directory={profile_dir}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9111")
    driver = uc.Chrome(
        user_data_dir=user_data_dir,
        use_subprocess=True,
        options=options,
    )
    driver.maximize_window()
    return driver
