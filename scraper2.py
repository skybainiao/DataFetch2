# half_time_scraper.py

import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time
import csv
import traceback
import os

# 配置部分，请替换为您的实际用户名和密码
ACCOUNT = {'username': 'dtyc6yDM3', 'password': 'dddd1111DD'}
BASE_URL = 'https://123.108.119.156/'  # 登录页面的URL

# 定义要抓取的市场类型及其对应的按钮ID
MARKET_TYPE = 'HDP_OU'
MARKET_BUTTON_ID = 'tab_rnou'  # 请根据实际情况替换为正确的按钮ID


def init_driver():
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # 无头模式
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


def switch_to_iframe_containing_buttons(driver):
    """先切换到包含1H按钮的iframe"""
    wait = WebDriverWait(driver, 10)
    try:
        # 先切回主文档
        driver.switch_to.default_content()
        # 等待iframe加载
        iframe = wait.until(EC.presence_of_element_located((By.ID, "content")))  # 替换为实际的iframe ID
        driver.switch_to.frame(iframe)
        return True
    except Exception as e:
        print(f"切换到iframe失败: {e}")
        return False


def click_all_1h_buttons(driver):
    matches_with_1h = []
    try:
        # 等待比赛容器加载
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='right_info_']")))
        print("比赛容器已加载")

        time.sleep(5)  # 确保所有内容加载完成

        # 查找所有比赛容器
        match_containers = driver.find_elements(By.CSS_SELECTOR, "div[id^='right_info_']")
        print(f"找到 {len(match_containers)} 个比赛容器")

        # 收集所有可点击的比赛ID
        active_match_ids = []
        for container in match_containers:
            try:
                match_id = container.get_attribute('id').replace('right_info_', '')
                print(f"处理比赛ID: {match_id}")

                one_h_button = container.find_element(By.CSS_SELECTOR, "div.rnou_btn_1H")

                if not one_h_button.is_displayed() or not one_h_button.is_enabled():
                    print(f"比赛 {match_id} 的1H按钮不可点击（不可见或未启用），跳过")
                    continue

                try:
                    icon = one_h_button.find_element(By.CSS_SELECTOR, f"i#icon_HT_{match_id}")
                    icon_class = icon.get_attribute('class')
                    if 'off' in icon_class:
                        print(f"比赛 {match_id} 的1H按钮被禁用（icon_class: {icon_class}），跳过")
                        continue
                except Exception as e_icon:
                    print(f"获取比赛 {match_id} 的<i>标签时发生错误: {e_icon}，跳过")
                    continue

                active_match_ids.append(match_id)
                print(f"比赛 {match_id} 的1H按钮是可点击的")
            except Exception as e:
                print(f"处理比赛容器时发生错误: {e}")
                traceback.print_exc()
                continue

        print(f"找到 {len(active_match_ids)} 个可点击的1H按钮")

        # 逐一点击并提取数据
        for match_id in active_match_ids:
            retries = 3
            for attempt in range(retries):
                try:
                    print(f"尝试点击比赛 {match_id} 的1H按钮（尝试 {attempt + 1}/{retries}）")

                    container = driver.find_element(By.ID, f"right_info_{match_id}")
                    one_h_button = container.find_element(By.CSS_SELECTOR, "div.rnou_btn_1H")

                    if not (one_h_button.is_displayed() and one_h_button.is_enabled()):
                        print(f"比赛 {match_id} 的1H按钮当前不可点击，跳过")
                        break

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", one_h_button)
                    time.sleep(0.5)

                    # 尝试点击内部的 <i> 标签
                    try:
                        icon = one_h_button.find_element(By.CSS_SELECTOR, f"i#icon_HT_{match_id}")
                        icon.click()
                        print(f"比赛 {match_id} 的1H按钮已点击（点击内部<i>标签）")
                    except Exception as e_click_inner:
                        print(f"比赛 {match_id} 的1H按钮内的<i>标签点击失败，尝试使用 div.click(): {e_click_inner}")
                        # 尝试点击 <div> 本身
                        try:
                            one_h_button.click()
                            print(f"比赛 {match_id} 的1H按钮已点击（点击 div）")
                        except Exception as e_click_div:
                            print(f"比赛 {match_id} 的1H按钮点击失败，尝试使用 JavaScript click: {e_click_div}")
                            # 使用 JavaScript 点击
                            try:
                                driver.execute_script("arguments[0].click();", one_h_button)
                                print(f"比赛 {match_id} 的1H按钮已点击（使用 JavaScript click）")
                            except Exception as e_js_click:
                                print(f"比赛 {match_id} 的1H按钮 JavaScript 点击失败: {e_js_click}")
                                raise e_js_click  # 触发重试

                    # 记录成功点击的比赛ID
                    matches_with_1h.append(match_id)

                    # 等待页面加载数据
                    time.sleep(1)  # 根据实际情况调整

                    # 解析数据
                    data = parse_market_data(driver, match_id)
                    if data:
                        save_to_csv(data)
                        print(f"比赛 {match_id} 的数据已保存到CSV")
                    else:
                        print(f"比赛 {match_id} 的数据为空")

                    # 成功点击并解析，跳出重试循环
                    break

                except Exception as e:
                    print(f"点击或解析比赛 {match_id} 的1H按钮时发生错误: {e}")
                    traceback.print_exc()
                    if attempt < retries - 1:
                        print(f"重试点击比赛 {match_id} 的1H按钮...")
                        time.sleep(1)  # 等待再重试
                    else:
                        print(f"比赛 {match_id} 的1H按钮点击尝试全部失败，跳过")

    except Exception as e:
        print(f"点击1H按钮过程中发生错误: {e}")
        traceback.print_exc()

    print(f"总共成功点击了 {len(matches_with_1h)} 个1H按钮")
    return matches_with_1h



def get_market_data(driver):
    try:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        return soup
    except Exception as e:
        print(f"获取页面数据失败: {e}")
        traceback.print_exc()
        return None


def parse_market_data(driver, match_id):
    try:
        # 假设半场数据加载在一个特定的容器内，例如 "ratioShow_{match_id}"
        ratio_container = driver.find_element(By.ID, f"ratioShow_{match_id}")

        # 解析相关数据
        # 这里需要根据实际的页面结构进行数据提取
        # 以下是一个示例：
        data = {
            'match_id': match_id,
            'handicap': [],
            'goals_over_under': []
        }

        # 解析 Handicap 1H
        handicap_section = ratio_container.find_element(By.ID, f"ratioR_{match_id}")
        handicap_odds = handicap_section.find_elements(By.CSS_SELECTOR, "div.btn_hdpou_odd")
        for odd in handicap_odds:
            ratio = odd.find_element(By.CSS_SELECTOR, "tt.text_ballhead").text.strip()
            odd_value = odd.find_element(By.CSS_SELECTOR, "span.text_odds").text.strip()
            data['handicap'].append({'ratio': ratio, 'odd': odd_value})

        # 解析 Goals O/U 1H
        goals_section = ratio_container.find_element(By.ID, f"ratioOU_{match_id}")
        goals_odds = goals_section.find_elements(By.CSS_SELECTOR, "div.btn_hdpou_odd")
        for odd in goals_odds:
            over_under = odd.find_element(By.CSS_SELECTOR, "tt.text_ballou").text.strip()
            ratio = odd.find_element(By.CSS_SELECTOR, "tt.text_ballhead").text.strip()
            odd_value = odd.find_element(By.CSS_SELECTOR, "span.text_odds").text.strip()
            data['goals_over_under'].append({'over_under': over_under, 'ratio': ratio, 'odd': odd_value})

        return data
    except Exception as e:
        print(f"解析比赛 {match_id} 的半场数据时发生错误: {e}")
        traceback.print_exc()
        return None


def extract_match_info(match_container, league_name):
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
            icon_info = match_time_tag.find('i', id=lambda x: x and x.startswith('icon_info'))
            match_time = icon_info.get_text(strip=True) if icon_info else 'Unknown Time'
        else:
            match_time = 'Unknown Time'

        # 初始化数据字典
        match_info = {
            'league': league_name,
            'match_time': match_time,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
        }

        # 提取半场赔率信息
        odds = {}
        desired_bet_types = ['Handicap', 'Goals O/U']

        # 提取半场（1H）赔率信息
        odds_sections_1h = match_container.find_all('div', class_='form_lebet_hdpou hdpou_1h')
        for odds_section in odds_sections_1h:
            bet_type_tag = odds_section.find('div', class_='head_lebet').find('span')
            bet_type = bet_type_tag.get_text(strip=True) if bet_type_tag else 'Unknown Bet Type'
            if bet_type in desired_bet_types:
                odds.update(extract_odds_hdp_ou(odds_section, bet_type, '1H'))

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
    key_counts = {}  # 用于跟踪键名的出现次数

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

            # 检查键名是否已存在，如果存在，则添加后缀以确保唯一性
            if key_home in odds:
                if key_home not in key_counts:
                    key_counts[key_home] = 1
                key_counts[key_home] += 1
                unique_key = f"{key_home}_{key_counts[key_home]}"
            else:
                unique_key = key_home

            odds[unique_key] = odds_value

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

            # 检查键名是否已存在，如果存在，则添加后缀以确保唯一性
            if key_away in odds:
                if key_away not in key_counts:
                    key_counts[key_away] = 1
                key_counts[key_away] += 1
                unique_key = f"{key_away}_{key_counts[key_away]}"
            else:
                unique_key = key_away

            odds[unique_key] = odds_value
    return odds


def save_to_csv(data):

    file_exists = os.path.isfile('half_time_data.csv')
    with open('half_time_data.csv', 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['match_id', 'type', 'ratio', 'odd']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        # 写入 Handicap 数据
        for handicap in data['handicap']:
            writer.writerow({
                'match_id': data['match_id'],
                'type': 'Handicap 1H',
                'ratio': handicap['ratio'],
                'odd': handicap['odd']
            })

        # 写入 Goals O/U 数据
        for goal in data['goals_over_under']:
            writer.writerow({
                'match_id': data['match_id'],
                'type': 'Goals O/U 1H',
                'ratio': f"{goal['over_under']} {goal['ratio']}",
                'odd': goal['odd']
            })


def run_scraper(account, market_type, filename):
    driver = init_driver()
    try:
        if login(driver, account['username'], account['password']):
            if navigate_to_football(driver):
                # 点击指定的市场类型按钮
                try:
                    button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, MARKET_BUTTON_ID))
                    )
                    button.click()
                    print(f"{account['username']} 已点击 {market_type} 按钮")
                except Exception as e:
                    print(f"{account['username']} 点击 {market_type} 按钮失败: {e}")
                    traceback.print_exc()
                # 点击所有1H按钮并获取有半场数据的比赛索引
                matches_with_1h = click_all_1h_buttons(driver)
                # 如果没有任何比赛的1H按钮被点击，则不获取半场数据
                if not matches_with_1h:
                    print("没有可点击的1H按钮，停止获取半场数据")
                    return
                # 额外等待5秒，确保数据加载完成
                time.sleep(5)
                # 进入数据抓取循环
                while True:
                    try:
                        soup = get_market_data(driver)
                        if soup:
                            data = parse_market_data(soup, matches_with_1h)
                            save_to_csv(data, filename)
                            print(f"{account['username']} 成功获取并保存数据到 {filename}")
                        else:
                            print(f"{account['username']} 未获取到数据")
                    except Exception as e:
                        print(f"{account['username']} 抓取数据时发生错误: {e}")
                        traceback.print_exc()
                    time.sleep(10)  # 每10秒获取一次数据
    except Exception as e:
        print(f"{account['username']} 运行过程中发生错误: {e}")
        traceback.print_exc()
    finally:
        driver.quit()
        print(f"{account['username']} 已关闭浏览器")


if __name__ == "__main__":
    # 账号信息

    MARKET_TYPE = 'HDP_OU'
    MARKET_BUTTON_ID = 'tab_rnou'  # 请根据实际情况替换为正确的按钮ID
    # CSV文件名
    FILENAME = 'half_time_data.csv'
    # 运行爬虫
    run_scraper(ACCOUNT, MARKET_TYPE, FILENAME)
