# scraper.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import USERNAME, PASSWORD, BASE_URL, DATA_URL

import time

def init_driver():
    chrome_options = Options()
    # 移除无头模式，便于观察浏览器行为
    # chrome_options.add_argument('--headless')  # 调试时可以取消注释
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    # 忽略 SSL 证书错误
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login(driver):
    driver.get(BASE_URL)

    try:
        wait = WebDriverWait(driver, 30)  # 增加等待时间到30秒

        # 调试：打印用户名和密码
        print(f"Attempting login with USERNAME: {USERNAME}, PASSWORD: {PASSWORD}")

        # 等待并找到用户名输入框
        username_field = wait.until(EC.visibility_of_element_located((By.ID, 'usr')))
        password_field = wait.until(EC.visibility_of_element_located((By.ID, 'pwd')))

        # 输入用户名和密码
        username_field.clear()
        username_field.send_keys(USERNAME)
        password_field.clear()
        password_field.send_keys(PASSWORD)

        # 等待登录按钮可点击并点击
        login_button = wait.until(EC.element_to_be_clickable((By.ID, 'btn_login')))
        login_button.click()

        # 等待登录完成，确认登录成功
        # 示例：登录后 URL 包含 '/dashboard'
        wait.until(EC.url_changes(BASE_URL))

        print("登录成功")
        return True
    except Exception as e:
        print(f"登录失败: {e}")
        # 保存截图以便调试
        driver.save_screenshot('login_failure.png')
        print("已保存登录失败的截图为 'login_failure.png'")
        return False

def fetch_data(driver):
    driver.get(DATA_URL)

    try:
        wait = WebDriverWait(driver, 30)  # 增加等待时间到30秒
        # 等待数据页面加载完成，具体条件根据实际情况调整
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'match-info')))  # 根据实际情况调整

        # 抓取数据
        matches = driver.find_elements(By.CLASS_NAME, 'match-info')
        data = []
        for match in matches:
            try:
                league = match.find_element(By.CLASS_NAME, 'league').text.strip()
                home_team = match.find_element(By.CLASS_NAME, 'home-team').text.strip()
                away_team = match.find_element(By.CLASS_NAME, 'away-team').text.strip()
                odds = match.find_element(By.CLASS_NAME, 'odds').text.strip()
                data.append({
                    'league': league,
                    'home_team': home_team,
                    'away_team': away_team,
                    'odds': odds
                })
            except Exception as inner_e:
                print(f"数据解析错误: {inner_e}")

        print("抓取到的数据:")
        for item in data:
            print(f"{item['league']}: {item['home_team']} vs {item['away_team']} - Odds: {item['odds']}")

        return data
    except Exception as e:
        print(f"抓取数据失败: {e}")
        return []

def save_to_csv(data, filename='matches.csv'):
    import csv
    if not data:
        print("没有数据可保存。")
        return
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    print(f"数据已保存到 {filename}")

def run_scraper():
    driver = init_driver()
    try:
        if login(driver):
            '''
            data = fetch_data(driver)
            save_to_csv(data)
            '''
    finally:
        driver.quit()
