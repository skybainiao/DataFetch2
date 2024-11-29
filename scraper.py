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


# 配置部分
USERNAME = 'dtycj0DM4'  # 替换为您的实际用户名
PASSWORD = 'dddd1111DD'  # 替换为您的实际密码
BASE_URL = 'https://123.108.119.156/'  # 登录页面的URL


def init_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 启用无头模式
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('--disable-extensions')
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
    wait = WebDriverWait(driver, 60)

    try:
        print("正在登录")

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

        # 处理可能出现的 passcode 弹窗
        try:
            popup_wait = WebDriverWait(driver, 10)  # 设置较长的等待时间
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
    wait = WebDriverWait(driver, 60)
    try:
        # 点击 TODAY 按钮
        today_button = wait.until(EC.element_to_be_clickable((By.ID, 'today_page')))
        today_button.click()
        print("已点击 TODAY 按钮")

        # 等待页面刷新后，body_loading 消失
        wait.until(EC.invisibility_of_element_located((By.ID, 'body_loading')))
        print("TODAY 页面加载完成")

        # 点击 ALL 按钮
        all_button = wait.until(EC.element_to_be_clickable((By.ID, 'league_tab_mix')))
        all_button.click()
        print("已点击 ALL 按钮")

        # 再次等待 body_loading 消失
        wait.until(EC.invisibility_of_element_located((By.ID, 'body_loading')))
        print("ALL 页面加载完成")

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
        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of_element_located((By.ID, 'div_show')))

        # 获取比赛列表容器
        matches_container = driver.find_element(By.ID, 'div_show')
        inner_html = matches_container.get_attribute('innerHTML')
        soup = BeautifulSoup(inner_html, 'html.parser')

        fixtures = []

        # 找到所有联赛容器
        league_containers = soup.find_all('div', class_='btn_title_le')

        for league_container in league_containers:
            # 获取联赛名称
            league_name_tag = league_container.find('tt', id='lea_name')
            if league_name_tag:
                current_league = league_name_tag.get_text(strip=True)
            else:
                # 尝试其他方式获取联赛名称
                league_name_tag = league_container.find('span', class_='text_league')
                if league_name_tag:
                    current_league = league_name_tag.get_text(strip=True)
                else:
                    current_league = "Unknown League"

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

                        fixture = {
                            'league': current_league,
                            'home_team': home_team,
                            'away_team': away_team
                        }

                        fixtures.append(fixture)
                    else:
                        print("未能找到主队或客队名称，跳过此比赛")

                # 继续遍历下一个兄弟元素
                next_sibling = next_sibling.find_next_sibling()

        scraped_data = {
            "count": len(fixtures),
            "fixtures": fixtures
        }

        return scraped_data

    except Exception as e:
        print(f"抓取数据失败: {e}")
        return {
            "count": 0,
            "fixtures": []
        }
