from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from decouple import config
import time


options = webdriver.ChromeOptions()
options.binary_location = "/usr/bin/chromium-browser"
options.add_argument("--start-maximized")

service = Service(ChromeDriverManager(driver_version="128.0.6613.137").install())

USER_PF = config("USER_PATHFINDER")
PASS_PF = config("PASSWORD_PATHFINDER")
USER_SALES = config("USER_SALES")
PASS_SALES = config("PASSWORD_SALES")
URL_LOGIN = (
    "https://pathfinder.automationanywhere.com/challenges/salesorder-applogin.html#"
)
URL_SALES = (
    "https://pathfinder.automationanywhere.com/challenges/salesorder-applist.html"
)


class RoboTrack:
    def __init__(self):
        self.webdriver = webdriver.Chrome(service=service, options=options)

    def open_url(self, url):
        self.webdriver.get(url)

    def login_pf(self):
        # clica no botao de aceitar cookies
        accept_button = self.webdriver.find_element(
            By.ID, "onetrust-accept-btn-handler"
        )
        accept_button.click()

        # clica no botao de login community
        login_button = self.webdriver.find_element(
            By.ID, "button_modal-login-btn__iPh6x"
        )
        login_button.click()

        # espera o input de preencher email renderizar e preenche o email
        email_input = WebDriverWait(self.webdriver, 10).until(
            EC.presence_of_element_located((By.ID, "43:2;a"))
        )
        email_input.send_keys(USER_PF)

        # clica no botão next
        next_button = WebDriverWait(self.webdriver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
        )
        next_button.click()

        # digita a senha
        pass_input = WebDriverWait(self.webdriver, 3).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Password']")
            )
        )
        pass_input.send_keys(PASS_PF)

        # envia o login
        send_login_button = WebDriverWait(self.webdriver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Log in')]")
            )
        )
        send_login_button.click()

    def login_sales(self):
        # digitando email
        email_input = WebDriverWait(self.webdriver, 10).until(
            EC.presence_of_element_located((By.ID, "salesOrderInputEmail"))
        )
        email_input.send_keys(USER_SALES)

        # digitndo a senha
        pass_input = WebDriverWait(self.webdriver, 10).until(
            EC.presence_of_element_located((By.ID, "salesOrderInputPassword"))
        )
        pass_input.send_keys(PASS_SALES)

        # enviando o login
        self.webdriver.execute_script("authLogin();")

    def set_sales_limit_page(self, limit):

        select_element = WebDriverWait(self.webdriver, 10).until(
            EC.presence_of_element_located((By.NAME, "salesOrderDataTable_length"))
        )
        select = Select(select_element)
        select.select_by_value(str(limit))

    def handle_sales(self):

        WebDriverWait(self.webdriver, 10).until(
            EC.presence_of_element_located((By.ID, "salesOrderDataTable"))
        )

        rows = self.webdriver.find_elements(
            By.CSS_SELECTOR, "#salesOrderDataTable tbody tr"
        )

        # passa por todas os orders
        for row in rows:
            # Captura o status da linha
            status = row.find_elements(By.TAG_NAME, "td")[4].text

            if status in ["Confirmed", "Delivery Outstanding"]:
                # abre o detalhe do order
                control_cell = row.find_element(By.CLASS_NAME, "dt-control")
                control_cell.click()

                time.sleep(1)
                new_row = row.find_element(By.XPATH, "following-sibling::tr[1]")
                html = new_row.get_attribute("innerHTML")

                # resgata os tracking numbers
                tracking_numbers = self.get_tracking_numbers(html)

                status_delivery = self.check_delivery(tracking_numbers)

                print("olha o status deste order %s " % status_delivery)

    # resgata os tracking numbers em list
    def get_tracking_numbers(self, html):

        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="sales-order-items")

        tracking_numbers = []

        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) > 1:
                tracking_numbers.append(cells[1].text)

        for tracking_number in tracking_numbers:
            print(tracking_number)

        print(f"Total de trackings {len(tracking_numbers)}")

        return tracking_numbers

    def check_delivery(self, tracking_numbers):

        self.webdriver.execute_script("window.open('');")
        self.webdriver.switch_to.window(self.webdriver.window_handles[-1])

        delivery_url = "https://pathfinder.automationanywhere.com/challenges/salesorder-tracking.html"
        self.webdriver.get(delivery_url)

        status = True

        for tracking_number in tracking_numbers:
            tracking_input = WebDriverWait(self.webdriver, 10).until(
                EC.presence_of_element_located((By.ID, "inputTrackingNo"))
            )
            tracking_input.clear()
            tracking_input.send_keys(tracking_number)

            track_button = WebDriverWait(self.webdriver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnCheckStatus"))
            )
            track_button.click()

            WebDriverWait(self.webdriver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "(//tbody[@id='shipmentStatus']/tr)[last()]")
                )
            )

            status_deliver = self.webdriver.find_element(
                By.XPATH, "(//tbody[@id='shipmentStatus']/tr)[last()]/td[last()]"
            ).text

            if status_deliver != "Delivered":
                status = False
                break

            time.sleep(1.5)

        time.sleep(3)

        self.webdriver.close()

        self.webdriver.switch_to.window(self.webdriver.window_handles[0])

        return status


if __name__ == "__main__":
    bot = RoboTrack()
    bot.open_url(URL_LOGIN)
    time.sleep(3)
    bot.login_pf()
    time.sleep(5)
    bot.login_sales()
    time.sleep(3)
    bot.open_url(URL_SALES)
    time.sleep(3)
    bot.set_sales_limit_page(50)
    time.sleep(3)
    bot.handle_sales()
