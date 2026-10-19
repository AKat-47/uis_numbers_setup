from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.action_chains import ActionChains
import os
import random
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException
from dotenv import load_dotenv


def human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.08, 0.25))


def random_mouse(driver, moves=5):
    body = driver.find_element(By.TAG_NAME, "body")
    actions = ActionChains(driver).move_to_element(body)
    for _ in range(moves):
        actions.move_by_offset(random.randint(-50, 50), random.randint(-50, 50))
        actions.pause(random.uniform(0.1, 0.4))
    actions.perform()


def login(driver, wait):
    driver.get(URL)
    time.sleep(5)

    if not driver.find_elements(By.XPATH, "//input[@name='username']"):
        print("Уже залогинены (вход взят из профиля)")
        return True

    print("Нужен вход")
    if HEADLESS:
        print("В фоне войти не получится: может появиться капча.")
        print("Запусти один раз с HEADLESS = False, войди и пройди капчу, потом снова ставь True.")
        return False

    random_mouse(driver)

    login_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='username']")))
    ActionChains(driver).move_to_element(login_field).click().perform()
    login_field.clear()
    human_type(login_field, LOGIN)

    time.sleep(random.uniform(0.5, 1.5))

    password_field = driver.find_element(By.XPATH, "//input[@name='password']")
    ActionChains(driver).move_to_element(password_field).click().perform()
    password_field.clear()
    human_type(password_field, PASSWORD)

    time.sleep(random.uniform(0.5, 1.5))

    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    ActionChains(driver).move_to_element(login_button).click().perform()

    input("Если появилась капча, пройди её. Когда откроется личный кабинет, нажми Enter...")
    return True


def wait_no_mask(driver, timeout=60):
    def no_visible_mask(d):
        for mask in d.find_elements(By.CSS_SELECTOR, ".x-mask"):
            try:
                if mask.is_displayed():
                    return False
            except StaleElementReferenceException:
                pass
        return True
    WebDriverWait(driver, timeout).until(no_visible_mask)


def visible_elements(driver, xpath):
    result = []
    for el in driver.find_elements(By.XPATH, xpath):
        try:
            if el.is_displayed():
                result.append(el)
        except StaleElementReferenceException:
            pass
    return result


def safe_click(driver, wait, xpath, attempts=3):
    for attempt in range(attempts):
        wait_no_mask(driver)
        element = wait.until(lambda d: (visible_elements(d, xpath) or [False])[0])
        try:
            element.click()
            return
        except (ElementClickInterceptedException, StaleElementReferenceException):
            if attempt == attempts - 1:
                raise
            time.sleep(2)


def back_to_list(driver, wait):
    for i in range(2):
        safe_click(driver, wait, "//span[normalize-space()='Назад к списку номеров']")
        time.sleep(3)


def set_scenario(driver, wait, number, scenario):
    print(f'Настраиваем номер {number}')
    wait_no_mask(driver)
    find_num = driver.find_element(By.XPATH, "//input[@placeholder='Укажите номер телефона, рекламную кампанию, график активности, список АОНов, сценарий']")
    find_num.clear()
    find_num.send_keys(number)
    time.sleep(3)

    safe_click(driver, wait, "//img[@data-qtip='Редактировать номер']")
    time.sleep(4)
    wait_no_mask(driver)

    if not visible_elements(driver, "//span[normalize-space()='Создать правило']"):
        print(f'Номер {number} уже настроен — пропускаем')
        back_to_list(driver, wait)
        return

    safe_click(driver, wait, "//span[normalize-space()='Создать правило']")
    time.sleep(2)

    chose_scenario = driver.find_element(By.XPATH, "//input[@placeholder='Выберите сценарий...']")
    chose_scenario.send_keys(scenario)
    time.sleep(2)

    chose_scenario.send_keys(Keys.ARROW_DOWN)
    time.sleep(0.3)
    chose_scenario.send_keys(Keys.ENTER)
    time.sleep(1)

    safe_click(driver, wait, "//span[normalize-space()='Сохранить']")
    time.sleep(2)

    back_to_list(driver, wait)
    return

def add_in_rule(driver, wait, number):

    input_number = driver.find_element(By.XPATH, "//label[contains(normalize-space(), 'Выберите номера')]/following-sibling::div//input")
    input_number.send_keys(number)
    time.sleep(1)

    input_number.send_keys(Keys.ARROW_DOWN)
    time.sleep(0.3)
    input_number.send_keys(Keys.ENTER)
    return

def delete_from_rule(driver, wait, number):
    print(f'Удаляем номер {number} из правила')
    try:
        delete_number = driver.find_element(By.XPATH, f"//div[normalize-space()='{number}']")
        delete_button = delete_number.find_element(By.XPATH, ".//img[@data-action='delete']")
        delete_button.click()
        time.sleep(2)
    except:
        print(f'Нет номера {number}')
    return

def open_rule(driver, wait):
    safe_click(driver, wait, f"//*[normalize-space(text())='{RULE_NAME}']/ancestor::table[1]//img[@action='editRecord']")
    time.sleep(2)


def delete_mode(driver, wait, virtual_numbers):
    open_rules = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[normalize-space()='Правила выбора АОН']")))
    open_rules.click()
    time.sleep(3)

    open_rule(driver, wait)

    for counter, num in enumerate(virtual_numbers, start=1):
        delete_from_rule(driver, wait, num)

        if counter % 10 == 0 and counter < len(virtual_numbers):
            save_butt = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[normalize-space()='Сохранить']")))
            save_butt.click()
            time.sleep(5)

            open_rule(driver, wait)

    save_butt = driver.find_element(By.XPATH, "//span[normalize-space()='Сохранить']")
    save_butt.click()
    time.sleep(5)

def settins_mode(driver, wait, virtual_numbers, scenario):
    virt_tab = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//td[@data-qtip='Виртуальная АТС']")))
    virt_tab.click()
    time.sleep(3)

    virt_numbers = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//span[normalize-space()='Виртуальные номера и правила']")))
    virt_numbers.click()
    time.sleep(5)

    for number in virtual_numbers:
        set_scenario(driver, wait, number, scenario)

    return "cool"

def add_in_rule_mode(driver, wait, numbers):
    open_rules = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[normalize-space()='Правила выбора АОН']")))
    open_rules.click()
    time.sleep(3)

    open_rule(driver, wait)

    for counter, num in enumerate(numbers, start=1):
        print(f'Добавляем номер {num} в правило')
        add_in_rule(driver, wait, num)

        if counter % 10 == 0 and counter < len(numbers):
            save_butt = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[normalize-space()='Сохранить']")))
            save_butt.click()
            time.sleep(5)

            open_rule(driver, wait)

    save_butt = driver.find_element(By.XPATH, "//span[normalize-space()='Сохранить']")
    save_butt.click()
    time.sleep(5)


load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

URL = os.getenv("URL", "https://app.uiscom.ru/")
LOGIN = os.environ["LOGIN"]
PASSWORD = os.environ["PASSWORD"]
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")
virtual_numbers = []
with open('num.txt', 'r', encoding='utf-8') as f:
    virtual_numbers = [line.strip() for line in f if line.strip()]
SCENARIO_NAME = os.environ["SCENARIO_NAME"]
RULE_NAME = os.environ["RULE_NAME"]

print(virtual_numbers)
work_mode = int(input("1 - настройка, 2 - удаление, 3 - добавление в правило: "))

PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")

options = webdriver.ChromeOptions()
options.add_argument(f"--user-data-dir={PROFILE_DIR}")
if HEADLESS:
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
else:
    options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 40)

try:
    if not login(driver, wait):
        raise SystemExit

    time.sleep(5)

    if work_mode == 1:
        result = settins_mode(driver, wait, virtual_numbers, SCENARIO_NAME)
        print(result)
    elif work_mode == 2:
        result = delete_mode(driver, wait, virtual_numbers)
    elif work_mode == 3:
        result = add_in_rule_mode(driver, wait, virtual_numbers)
    else:
        print('Некорректный режим работы')


finally:
    driver.quit()
