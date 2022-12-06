import json
import sys
import time
import traceback
from selenium.common import TimeoutException
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import Config


class LoginError(RuntimeError):
    pass


def log_in(cfg: Config, max_load_time=10) -> None:
    """
    Logs in using headless firefox instance, stores resulting data in the input Config object
    Throws TimeoutException if loading time exceed max_load_time (5 seconds by default).

    :param cfg: Config object
    :param max_load_time: Maximum time to wait for loading to finish
    """
    firefox_options = Options()
    firefox_options.headless = True

    firefox = webdriver.Firefox(options=firefox_options)
    firefox.maximize_window()

    firefox.get("https://zeitwart.hs-osnabrueck.de")
    # Wait until form is loaded
    try:
        WebDriverWait(firefox, max_load_time).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='Ecom_User_ID']")))
        WebDriverWait(firefox, max_load_time).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='Ecom_Password']")))
        WebDriverWait(firefox, max_load_time).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='loginButton2']")))
    except TimeoutException:
        firefox.quit()
        raise
    # Wait an extra second to finish loading
    time.sleep(1)
    # Search for form fields
    username_field = firefox.find_element(By.XPATH, "//*[@id='Ecom_User_ID']")
    username_field.send_keys(cfg.user)
    password_field = firefox.find_element(By.XPATH, "//*[@id='Ecom_Password']")
    password_field.send_keys(cfg.password)
    login_button = firefox.find_element(By.XPATH, "//*[@id='loginButton2']")
    login_button.click()
    # Wait for specific requests
    try:
        request = firefox.wait_for_request("/api/v1/users/current", max_load_time)
        print(request.response.body.decode("utf-8"))
        user_id = json.loads(request.response.body.decode("utf-8"))["data"]["id"]
        request = firefox.wait_for_request("/api/v1/settings/zeitwart", max_load_time)
        x_xsrf_token = request.headers.get("X-XSRF-TOKEN")
    except TimeoutException:
        firefox.quit()
        raise
    cookies = firefox.get_cookies()
    Config.persist_indiv_data(cfg.user,
                              x_xsrf_token,
                              next(x for x in cookies if x["name"] == "zeitwart_session")["value"], user_id)
    firefox.quit()


def try_login(cfg: Config) -> None:
    """
    Tries to log in and, if successful, saves resulting data to config, else raises LoginError
    :return: None
    """
    print("Session expired, logging in...")
    try:
        log_in(cfg)
    except TimeoutException:
        print("Log in Failed, try rebuilding your config", file=sys.stderr)
        if cfg.verbose:
            traceback.print_exc()
        raise LoginError
    print("Success")


if __name__ == "__main__":
    pass
