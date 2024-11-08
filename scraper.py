# scraper.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup
import time
import csv
import threading
import requests  # 用于发送数据到其他服务器

# 配置部分
USERNAME = 'dtycDM1'          # 替换为您的实际用户名
PASSWORD = 'dddd1111DD'       # 替换为您的实际密码
BASE_URL = 'https://123.108.119.156/'  # 登录页面的URL

# 目标服务器的URL（用于发送数据）
TARGET_SERVER_URL = 'https://yourserver.com/receive_data'  # 替换为您的目标服务器URL

def init_driver():
    chrome_options = Options()
    # 取消无头模式，便于观察浏览器行为
    # chrome_options.add_argument('--headless')  # 调试完成后可取消注释
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
    print("WebDriver 初始化完成")
    return driver

def login(driver):
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 30)

    try:
        # 打印登录尝试信息
        print(f"尝试使用用户名: {USERNAME} 和密码: {PASSWORD} 登录")

        # 等待并找到用户名输入框
        username_field = wait.until(EC.visibility_of_element_located((By.ID, 'usr')))
        password_field = wait.until(EC.visibility_of_element_located((By.ID, 'pwd')))
        print("找到用户名和密码输入框")

        # 输入用户名和密码
        username_field.clear()
        username_field.send_keys(USERNAME)
        password_field.clear()
        password_field.send_keys(PASSWORD)
        print("已输入用户名和密码")

        # 等待登录按钮可点击并点击
        login_button = wait.until(EC.element_to_be_clickable((By.ID, 'btn_login')))
        login_button.click()
        print("已点击登录按钮")

        # 处理可能出现的 passcode 弹窗
        try:
            popup_wait = WebDriverWait(driver, 5)  # 设置较短的等待时间
            no_button = popup_wait.until(EC.element_to_be_clickable((By.ID, 'C_no_btn')))
            no_button.click()
            print("已点击 'NO' 按钮，关闭 passcode 弹窗")
        except:
            print("未发现 passcode 弹窗，继续执行")

        # 等待足球按钮出现，确认登录成功
        wait.until(EC.visibility_of_element_located((By.XPATH, '//div[span[text()="Soccer"]]')))
        print("登录成功")
        return True
    except Exception as e:
        print(f"登录失败: {e}")
        return False

def navigate_to_football(driver):
    wait = WebDriverWait(driver, 30)
    try:
        # 使用文本内容定位足球按钮
        football_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[span[text()="Soccer"]]')))
        football_button.click()
        print("已点击足球按钮，正在导航到足球页面")

        # 等待比赛列表容器加载完成
        wait.until(EC.visibility_of_element_located((By.ID, 'div_show')))
        print("比赛列表容器已加载")

        # 等待联赛列表加载完成
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'btn_title_le')))
        print("联赛列表已加载")

        return True
    except Exception as e:
        print(f"导航到足球页面失败: {e}")
        return False

def fetch_data(driver):
    try:
        # 不刷新页面，直接获取最新的页面元素
        # 等待比赛列表容器加载完成
        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of_element_located((By.ID, 'div_show')))

        # 获取比赛列表容器
        matches_container = driver.find_element(By.ID, 'div_show')
        inner_html = matches_container.get_attribute('innerHTML')
        soup = BeautifulSoup(inner_html, 'html.parser')

        data = []

        # 找到所有联赛容器
        league_containers = soup.find_all('div', class_='btn_title_le')

        for league_container in league_containers:
            # 获取联赛名称
            league_name_tag = league_container.find('tt', id='lea_name')
            if league_name_tag:
                current_league = league_name_tag.get_text(strip=True)
                # print(f"找到联赛: {current_league}")
            else:
                # 尝试其他方式获取联赛名称
                league_name_tag = league_container.find('span', class_='text_league')
                if league_name_tag:
                    current_league = league_name_tag.get_text(strip=True)
                    # print(f"找到联赛: {current_league}")
                else:
                    current_league = "Unknown League"
                    # print("未找到联赛名称，使用默认值")

            # 从联赛容器开始，遍历其后面的兄弟元素，直到下一个联赛容器
            next_sibling = league_container.find_next_sibling()
            while next_sibling:
                # 如果遇到下一个联赛，停止处理当前联赛
                if 'btn_title_le' in next_sibling.get('class', []):
                    break
                elif 'box_lebet' in next_sibling.get('class', []):
                    match_container = next_sibling

                    # 提取主队和客队名称
                    home_team_tag = match_container.find('div', class_='teamH')
                    away_team_tag = match_container.find('div', class_='teamC')

                    if home_team_tag and away_team_tag:
                        home_team_name_tag = home_team_tag.find('span', class_='text_team')
                        home_team = home_team_name_tag.get_text(strip=True) if home_team_name_tag else "Unknown"

                        away_team_name_tag = away_team_tag.find('span', class_='text_team')
                        away_team = away_team_name_tag.get_text(strip=True) if away_team_name_tag else "Unknown"

                        # print(f"找到比赛: {home_team} vs {away_team}")

                        # 提取比分和比赛时间等信息
                        match_info = {}

                        # 比赛时间
                        time_tag = match_container.find('i', id='icon_info')
                        match_time = time_tag.get_text(strip=True) if time_tag else "Unknown Time"
                        match_info['match_time'] = match_time

                        # 比分
                        score_tags = match_container.find_all('span', class_='text_point')
                        if score_tags and len(score_tags) >= 2:
                            home_score = score_tags[0].get_text(strip=True)
                            away_score = score_tags[1].get_text(strip=True)
                        else:
                            home_score = away_score = "0"
                        match_info['home_score'] = home_score
                        match_info['away_score'] = away_score

                        # 提取赔率信息
                        odds = {}
                        # 找到所有赔率部分
                        odds_sections = match_container.find_all('div', class_='box_lebet_odd')

                        for odds_section in odds_sections:
                            # 获取盘口类型
                            bet_type_tag = odds_section.find('div', class_='head_lebet')
                            bet_type = bet_type_tag.get_text(strip=True) if bet_type_tag else "Unknown Bet Type"

                            # 获取所有赔率按钮
                            odds_buttons = odds_section.find_all('div', class_='btn_lebet_odd')
                            for btn in odds_buttons:
                                # 获取盘口详情
                                bet_detail_tag = btn.find(['tt', 'span'], class_=lambda x: x and ('text_ballhead' in x or 'text_ballou' in x))
                                bet_detail = bet_detail_tag.get_text(strip=True) if bet_detail_tag else "Unknown Bet Detail"

                                # 获取赔率值
                                odd_value_tag = btn.find('span', class_='text_odds')
                                odd_value = odd_value_tag.get_text(strip=True) if odd_value_tag else ""

                                if odd_value:
                                    full_bet_type = f"{bet_type} - {bet_detail}"
                                    odds[full_bet_type] = odd_value
                                    # print(f"找到赔率 - {full_bet_type}: {odd_value}")

                        # 合并比赛信息和赔率信息
                        match_info.update({
                            'league': current_league,
                            'home_team': home_team,
                            'away_team': away_team,
                            'odds': odds
                        })

                        data.append(match_info)
                    else:
                        print("未能找到主队或客队名称，跳过此比赛")

                # 继续遍历下一个兄弟元素
                next_sibling = next_sibling.find_next_sibling()

        return data

    except Exception as e:
        print(f"抓取数据失败: {e}")
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

    # 定义CSV的表头，添加比分和比赛时间
    keys = ['league', 'match_time', 'home_team', 'away_team', 'home_score', 'away_score'] + all_odds_types
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        for item in data:
            row = {
                'league': item['league'],
                'match_time': item['match_time'],
                'home_team': item['home_team'],
                'away_team': item['away_team'],
                'home_score': item['home_score'],
                'away_score': item['away_score']
            }
            # 填充赔率
            for bet_type in all_odds_types:
                row[bet_type] = item['odds'].get(bet_type, '')
            dict_writer.writerow(row)
    print(f"数据已保存到 {filename}")

def send_data_to_server(data):
    try:
        # 将数据转换为JSON格式
        json_data = {'matches': data}
        response = requests.post(TARGET_SERVER_URL, json=json_data)
        if response.status_code == 200:
            print("数据已成功发送到服务器")
        else:
            print(f"发送数据失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"发送数据时发生错误: {e}")

def run_scraper():
    driver = init_driver()
    try:
        if login(driver):
            if navigate_to_football(driver):
                while True:
                    start_time = time.time()
                    data = fetch_data(driver)
                    if data:
                        # 打印抓取的比赛数量
                        print(f"抓取到 {len(data)} 场比赛的数据")
                        # 保存到CSV
                        save_to_csv(data)
                        # 发送数据到服务器
                        send_data_to_server(data)
                    else:
                        print("未抓取到任何数据")

                    # 计算抓取和处理时间
                    elapsed_time = time.time() - start_time
                    # 如果抓取时间小于1秒，等待剩余时间
                    if elapsed_time < 1:
                        time.sleep(1 - elapsed_time)
    except KeyboardInterrupt:
        print("停止抓取")
    finally:
        driver.quit()
        print("已关闭浏览器")

if __name__ == "__main__":
    run_scraper()
