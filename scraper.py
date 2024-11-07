# scraper.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import USERNAME, PASSWORD, BASE_URL

import time
import csv
from bs4 import BeautifulSoup

def init_driver():
    chrome_options = Options()
    # 取消无头模式，便于观察浏览器行为
    # chrome_options.add_argument('--headless')  # 调试时可取消注释
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    # 忽略 SSL 证书错误
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')
    # 禁用扩展，避免干扰
    chrome_options.add_argument('--disable-extensions')
    # 禁用自动化控制提示
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # 防止被检测为自动化工具
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver

def login(driver):
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 30)  # 增加等待时间到30秒

    try:
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

        # 等待足球按钮出现，确认登录成功
        wait.until(EC.visibility_of_element_located((By.XPATH, '//div[span[text()="Soccer"]]')))

        print("登录成功")
        return True
    except Exception as e:
        print(f"登录失败: {e}")
        # 保存截图以便调试
        driver.save_screenshot('login_failure.png')
        print("已保存登录失败的截图为 'login_failure.png'")
        return False

def navigate_to_football(driver):
    wait = WebDriverWait(driver, 30)
    try:
        # 使用文本内容定位足球按钮
        football_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[span[text()="Soccer"]]')))
        football_button.click()
        print("导航到足球页面成功")
        # 等待比赛列表容器加载完成
        wait.until(EC.visibility_of_element_located((By.ID, 'div_show')))
        # 等待额外的时间以确保所有动态内容加载
        time.sleep(5)
        return True
    except Exception as e:
        print(f"导航到足球页面失败: {e}")
        driver.save_screenshot('navigate_failure.png')
        print("已保存导航失败的截图为 'navigate_failure.png'")
        return False

def fetch_data(driver):
    wait = WebDriverWait(driver, 30)
    try:
        # 等待比赛列表容器加载完成
        wait.until(EC.visibility_of_element_located((By.ID, 'div_show')))
        matches_container = driver.find_element(By.ID, 'div_show')

        # 获取并打印 innerHTML
        inner_html = matches_container.get_attribute('innerHTML')
        with open('div_show_innerHTML.html', 'w', encoding='utf-8') as f:
            f.write(inner_html)
        print("已保存 div_show 的 innerHTML 为 'div_show_innerHTML.html'")

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(inner_html, 'html.parser')

        data = []
        current_league = ""

        # 遍历所有直接子元素
        for child in soup.find_all(recursive=False):
            # 检查是否为联赛名称的div
            if 'btn_title_le' in child.get('class', []):
                league_tag = child.find('tt', id='lea_name')
                if league_tag:
                    current_league = league_tag.get_text(strip=True)
                    print(f"Found league: {current_league}")
                else:
                    print("未找到联赛名称")
                    current_league = ""
            # 检查是否为比赛信息的div
            elif 'bet_type_8' in child.get('class', []):
                if not current_league:
                    print("未找到对应的联赛名称，跳过此比赛")
                    continue
                # 获取主队名称
                home_team_tag = child.select_one('div.teamH .text_team')
                home_team = home_team_tag.get_text(strip=True) if home_team_tag else "Unknown"
                print(f"Found home team: {home_team}")

                # 获取客队名称
                away_team_tag = child.select_one('div.teamC .text_team')
                away_team = away_team_tag.get_text(strip=True) if away_team_tag else "Unknown"
                print(f"Found away team: {away_team}")

                # 获取赔率信息
                odds = {}
                for odd_div in child.find_all('div', class_='btn_lebet_odd'):
                    bet_type_tag = odd_div.find('tt', class_='text_ballhead')
                    odd_value_tag = odd_div.find('span', class_='text_odds')
                    bet_type = bet_type_tag.get_text(strip=True) if bet_type_tag else "Unknown"
                    odd_value = odd_value_tag.get_text(strip=True) if odd_value_tag else "Unknown"
                    odds[bet_type] = odd_value
                    print(f"Found odds - {bet_type}: {odd_value}")

                data.append({
                    'league': current_league,
                    'home_team': home_team,
                    'away_team': away_team,
                    'odds': odds
                })
            else:
                # 其他类型的div，可能是广告、脚本等，跳过
                continue

        if not data:
            print("抓取到的数据: 没有数据可保存。")
        else:
            print("抓取到的数据:")
            for item in data:
                print(f"{item['league']}: {item['home_team']} vs {item['away_team']} - Odds: {item['odds']}")

        return data
    except Exception as e:
        print(f"抓取数据失败: {e}")
        driver.save_screenshot('fetch_failure.png')
        print("已保存抓取失败的截图为 'fetch_failure.png'")
        return []

def save_to_csv(data, filename='matches.csv'):
    if not data:
        print("没有数据可保存。")
        return
    # 获取所有赔率类型
    all_odds_types = set()
    for item in data:
        all_odds_types.update(item['odds'].keys())
    all_odds_types = sorted(all_odds_types)

    # 定义CSV的表头
    keys = ['league', 'home_team', 'away_team'] + all_odds_types
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        for item in data:
            row = {
                'league': item['league'],
                'home_team': item['home_team'],
                'away_team': item['away_team']
            }
            # 填充赔率
            for bet_type in all_odds_types:
                row[bet_type] = item['odds'].get(bet_type, '')
            dict_writer.writerow(row)
    print(f"数据已保存到 {filename}")

def run_scraper():
    driver = init_driver()
    try:
        if login(driver):
            if navigate_to_football(driver):
                data = fetch_data(driver)
                save_to_csv(data)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_scraper()
