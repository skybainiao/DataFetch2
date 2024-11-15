# scraper.py

import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import csv
import traceback
import os

# 配置部分，请替换为您的实际用户名和密码
ACCOUNTS = [
    {'username': 'dtyc0lDM0', 'password': 'dddd1111DD'},
    {'username': 'dtyc23DM1', 'password': 'dddd1111DD'},
    {'username': 'dtyc6yDM2', 'password': 'dddd1111DD'},
]
BASE_URL = 'https://123.108.119.156/'  # 登录页面的URL

# 定义要抓取的市场类型及其对应的按钮ID
MARKET_TYPES = {
    'HDP_OU': 'tab_rnou',   # 请根据实际情况替换为正确的按钮ID
    'CORNERS': 'tab_cn'      # 请根据实际情况替换为正确的按钮ID
}

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=chrome_options)
    # 隐藏webdriver属性以防被检测
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        '''
    })
    return driver

def login(driver, username, password):
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 30)
    try:
        # 选择语言
        lang_field = wait.until(EC.visibility_of_element_located((By.ID, 'lang_en')))
        lang_field.click()
        # 输入用户名和密码
        username_field = wait.until(EC.visibility_of_element_located((By.ID, 'usr')))
        password_field = wait.until(EC.visibility_of_element_located((By.ID, 'pwd')))
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)
        # 点击登录按钮
        login_button = wait.until(EC.element_to_be_clickable((By.ID, 'btn_login')))
        login_button.click()
        # 处理可能的弹窗
        try:
            popup_wait = WebDriverWait(driver, 5)
            no_button = popup_wait.until(EC.element_to_be_clickable((By.ID, 'C_no_btn')))
            no_button.click()
        except:
            pass  # 如果没有弹窗，继续执行
        # 等待导航到足球页面
        wait.until(EC.visibility_of_element_located((By.XPATH, '//div[span[text()="Soccer"]]')))
        print(f"{username} 登录成功")
        return True
    except Exception as e:
        print(f"{username} 登录失败: {e}")
        traceback.print_exc()
        return False

def navigate_to_football(driver):
    wait = WebDriverWait(driver, 30)
    try:
        # 点击足球按钮
        football_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[span[text()="Soccer"]]')))
        football_button.click()
        # 等待页面加载完成
        wait.until(EC.visibility_of_element_located((By.ID, 'div_show')))
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'btn_title_le')))
        print("导航到足球页面成功")
        return True
    except Exception as e:
        print(f"导航到足球页面失败: {e}")
        traceback.print_exc()
        return False

def get_market_data(driver):
    try:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        return soup
    except Exception as e:
        print(f"获取页面数据失败: {e}")
        traceback.print_exc()
        return None

def parse_market_data(soup, market_type):
    data = []
    league_sections = soup.find_all('div', class_='btn_title_le')
    for league_section in league_sections:
        league_name_tag = league_section.find('tt', id='lea_name')
        league_name = league_name_tag.get_text(strip=True) if league_name_tag else 'Unknown League'
        # 获取该联赛下的所有比赛
        match_container = league_section.find_next_sibling()
        while match_container and 'box_lebet' in match_container.get('class', []):
            match_info = extract_match_info(match_container, league_name, market_type)
            if match_info:
                data.append(match_info)
            match_container = match_container.find_next_sibling()
    return data





def extract_match_info(match_container, league_name, market_type):
    try:
        # 提取主客队名称
        home_team_div = match_container.find('div', class_='box_team teamH')
        away_team_div = match_container.find('div', class_='box_team teamC')

        if home_team_div:
            home_team_tag = home_team_div.find('span', class_='text_team')
            home_team = home_team_tag.get_text(strip=True) if home_team_tag else 'Unknown'
        else:
            home_team = 'Unknown'

        if away_team_div:
            away_team_tag = away_team_div.find('span', class_='text_team')
            away_team = away_team_tag.get_text(strip=True) if away_team_tag else 'Unknown'
        else:
            away_team = 'Unknown'

        # 提取比分
        score_container = match_container.find('div', class_='box_score')
        if score_container:
            score_tags = score_container.find_all('span', class_='text_point')
            if score_tags and len(score_tags) >= 2:
                home_score = score_tags[0].get_text(strip=True)
                away_score = score_tags[1].get_text(strip=True)
            else:
                home_score = away_score = '0'
        else:
            home_score = away_score = '0'

        # 提取比赛时间
        match_time_tag = match_container.find('tt', class_='text_time')
        if match_time_tag:
            icon_info = match_time_tag.find('i', id='icon_info')
            match_time = icon_info.get_text(strip=True) if icon_info else 'Unknown Time'
        else:
            match_time = 'Unknown Time'

        # 初始化数据字典
        match_info = {
            'league': league_name,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'match_time': match_time,
        }

        # 提取赔率信息
        odds = {}
        if market_type == 'HDP_OU':
            desired_bet_types = ['Handicap', 'Goals O/U']

            # 提取全场（FT）赔率信息
            odds_sections_ft = match_container.find_all('div', class_='form_lebet_hdpou hdpou_ft')
            for odds_section in odds_sections_ft:
                bet_type_tag = odds_section.find('div', class_='head_lebet').find('span')
                bet_type = bet_type_tag.get_text(strip=True) if bet_type_tag else 'Unknown Bet Type'
                if bet_type in desired_bet_types:
                    odds.update(extract_odds_hdp_ou(odds_section, bet_type, 'FT'))

            # 提取上半场（1H）赔率信息
            odds_sections_1h = match_container.find_all('div', class_='form_lebet_hdpou hdpou_1h')
            for odds_section in odds_sections_1h:
                bet_type_tag = odds_section.find('div', class_='head_lebet').find('span')
                bet_type = bet_type_tag.get_text(strip=True) if bet_type_tag else 'Unknown Bet Type'
                if bet_type in desired_bet_types:
                    odds.update(extract_odds_hdp_ou(odds_section, bet_type, '1H'))

        elif market_type == 'CORNERS':
            odds_sections = match_container.find_all('div', class_='box_lebet_odd')
            for odds_section in odds_sections:
                odds.update(extract_odds_corners(odds_section))

        match_info.update(odds)
        return match_info

    except Exception as e:
        print(f"提取比赛信息失败: {e}")
        traceback.print_exc()
        return None







def extract_odds_hdp_ou(odds_section, bet_type, time_indicator):
    odds = {}
    # 找到所有的赔率列
    labels = odds_section.find_all('div', class_='col_hdpou')
    for label in labels:
        # 提取主队赔率
        home_odds_div = label.find('div', id=lambda x: x and (x.endswith('_REH') or x.endswith('_ROUH')))
        if home_odds_div and 'lock' not in home_odds_div.get('class', []):
            handicap_tag = home_odds_div.find('tt', class_='text_ballhead')
            odds_tag = home_odds_div.find('span', class_='text_odds')
            handicap = handicap_tag.get_text(strip=True) if handicap_tag else ''
            odds_value = odds_tag.get_text(strip=True) if odds_tag else ''
            # 过滤掉包含占位符的数据
            if '*' in handicap or '*' in odds_value or not handicap or not odds_value:
                continue
            # 正确映射 'O' 为 'Over'，'U' 为 'Under'
            team_info_tag = home_odds_div.find('tt', class_='text_ballou')
            team_info = team_info_tag.get_text(strip=True) if team_info_tag else ''
            over_under = 'Over' if team_info == 'O' else 'Under'
            if bet_type == 'Handicap':
                key_home = f"SPREAD_{time_indicator}_{handicap}_HomeOdds"
            elif bet_type == 'Goals O/U':
                key_home = f"TOTAL_POINTS_{time_indicator}_{handicap}_{over_under}Odds"
            else:
                continue
            odds[key_home] = odds_value

        # 提取客队赔率
        away_odds_div = label.find('div', id=lambda x: x and (x.endswith('_REC') or x.endswith('_ROUC')))
        if away_odds_div and 'lock' not in away_odds_div.get('class', []):
            handicap_tag = away_odds_div.find('tt', class_='text_ballhead')
            odds_tag = away_odds_div.find('span', class_='text_odds')
            handicap = handicap_tag.get_text(strip=True) if handicap_tag else ''
            odds_value = odds_tag.get_text(strip=True) if odds_tag else ''
            # 过滤掉包含占位符的数据
            if '*' in handicap or '*' in odds_value or not handicap or not odds_value:
                continue
            # 正确映射 'O' 为 'Over'，'U' 为 'Under'
            team_info_tag = away_odds_div.find('tt', class_='text_ballou')
            team_info = team_info_tag.get_text(strip=True) if team_info_tag else ''
            over_under = 'Over' if team_info == 'O' else 'Under'
            if bet_type == 'Handicap':
                key_away = f"SPREAD_{time_indicator}_{handicap}_AwayOdds"
            elif bet_type == 'Goals O/U':
                key_away = f"TOTAL_POINTS_{time_indicator}_{handicap}_{over_under}Odds"
            else:
                continue
            odds[key_away] = odds_value
    return odds







def extract_odds_corners(odds_section):
    odds = {}
    # 提取时间指示符（FT 或 1H）
    head_lebet = odds_section.find('div', class_='head_lebet')
    time_indicator_tag = head_lebet.find('tt')
    if time_indicator_tag:
        time_indicator = time_indicator_tag.get_text(strip=True)
    else:
        time_indicator = 'FT'

    # 提取投注类型，例如 'O/U'，'HDP' 等
    bet_type_span = head_lebet.find('span')
    bet_type = bet_type_span.get_text(strip=True) if bet_type_span else 'Unknown Bet Type'

    # 处理每个赔率按钮
    buttons = odds_section.find_all('div', class_='btn_lebet_odd')
    for btn in buttons:
        odds_tag = btn.find('span', class_='text_odds')
        odds_value = odds_tag.get_text(strip=True) if odds_tag else ''
        # 过滤掉无效数据
        if not odds_value or '*' in odds_value:
            continue

        # 根据按钮的 ID 判断类型
        btn_id = btn.get('id', '')
        if '_H' in btn_id:
            team = 'Home'
        elif '_C' in btn_id:
            team = 'Away'
        elif '_O' in btn_id:
            team = 'Odd'
        elif '_E' in btn_id:
            team = 'Even'
        else:
            team = ''

        # 提取盘口或其他信息
        handicap_tag = btn.find('tt', class_='text_ballhead')
        handicap = handicap_tag.get_text(strip=True) if handicap_tag else ''

        team_info_tag = btn.find('tt', class_='text_ballou')
        team_info = team_info_tag.get_text(strip=True) if team_info_tag else ''

        # 构建键名
        if bet_type == 'HDP':
            key = f"SPREAD_{time_indicator}_{handicap}_{team}Odds"
        elif bet_type == 'O/U':
            over_under = 'Over' if team_info == 'O' else 'Under'
            key = f"TOTAL_POINTS_{time_indicator}_{handicap}_{over_under}Odds"
        elif bet_type == 'Next Corner':
            key = f"NEXT_CORNER_{time_indicator}_{team_info}_{team}Odds"
        elif bet_type == 'O/E':
            key = f"ODD_EVEN_{time_indicator}_{team}Odds"
        else:
            key = f"{bet_type}_{time_indicator}_{team_info}_{handicap}_{team}Odds"

        odds[key] = odds_value

    return odds




def click_all_1h_buttons(driver):
    try:
        # 等待比赛列表加载完成
        time.sleep(2)
        # 查找所有的 1H 按钮
        one_h_buttons = driver.find_elements(By.XPATH, "//div[contains(@class, 'rnou_btn rnou_btn_1H')]")
        print(f"找到 {len(one_h_buttons)} 个 1H 按钮")
        for button in one_h_buttons:
            try:
                if button.is_displayed() and button.is_enabled() and 'off' not in button.get_attribute('class'):
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(0.1)  # 短暂等待，避免过快点击
            except Exception as e:
                print(f"点击 1H 按钮时发生错误: {e}")
    except Exception as e:
        print(f"点击所有 1H 按钮时发生错误: {e}")
        traceback.print_exc()


def save_to_csv(data, filename):
    if not data:
        print(f"没有数据保存到 {filename}")
        return
    # 定义固定的字段名
    fixed_fields = ['league', 'match_time', 'home_team', 'away_team', 'home_score', 'away_score', 'home_corners', 'away_corners']
    # 收集所有赔率类型
    odds_fields = set()
    for item in data:
        odds_fields.update(item.keys() - set(fixed_fields))
    # 定义最终的字段名，固定字段在前，赔率字段排序后追加
    fieldnames = fixed_fields + sorted(odds_fields)
    # 保存数据，覆盖模式
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # 仅包含定义的字段
            clean_row = {k: v for k, v in row.items() if k in fieldnames}
            writer.writerow(clean_row)
    print(f"数据保存到 {filename}")

def run_scraper(account, market_type, filename):
    driver = init_driver()
    try:
        if login(driver, account['username'], account['password']):
            if navigate_to_football(driver):
                # 点击指定的市场类型按钮
                try:
                    button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, MARKET_TYPES[market_type]))
                    )
                    button.click()
                    print(f"{account['username']} 已点击 {market_type} 按钮")
                except Exception as e:
                    print(f"{account['username']} 点击 {market_type} 按钮失败: {e}")
                    traceback.print_exc()
                # 等待页面加载
                time.sleep(5)
                # 进入数据抓取循环
                while True:
                    try:
                        soup = get_market_data(driver)
                        if soup:
                            data = parse_market_data(soup, market_type)
                            save_to_csv(data, filename)
                            print(f"{account['username']} 成功获取并保存数据")
                        else:
                            print(f"{account['username']} 未获取到数据")
                    except Exception as e:
                        print(f"{account['username']} 抓取数据时发生错误: {e}")
                        traceback.print_exc()
                    time.sleep(1)  # 每秒获取一次数据
    except Exception as e:
        print(f"{account['username']} 运行过程中发生错误: {e}")
        traceback.print_exc()
    finally:
        driver.quit()
        print(f"{account['username']} 已关闭浏览器")




if __name__ == "__main__":
    # 创建线程列表
    threads = []
    # 第一个线程，获取 HDP & O/U 数据（同时包含全场和上半场）
    thread1 = threading.Thread(target=run_scraper, args=(ACCOUNTS[0], 'HDP_OU', 'hdp_ou_data.csv'))
    threads.append(thread1)
    # 第二个线程，获取 CORNERS 数据
    thread2 = threading.Thread(target=run_scraper, args=(ACCOUNTS[1], 'CORNERS', 'corners_data.csv'))
    threads.append(thread2)
    # 启动线程
    for thread in threads:
        thread.start()
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    print("所有数据抓取完成")



