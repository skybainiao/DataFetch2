# app.py

from flask import Flask, jsonify
import threading
import time
from scraper import init_driver, login, navigate_to_football, fetch_data

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import logging

app = Flask(__name__)

# 配置日志，仅输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 用于缓存抓取到的数据
cached_data = {
    "count": 0,
    "fixtures": []
}
data_lock = threading.Lock()

# 全局 WebDriver 对象
driver = None
driver_lock = threading.Lock()  # 用于保护 WebDriver 对象的访问

# 定义一个事件，用于优雅地关闭后台线程
stop_event = threading.Event()

# 添加刷新状态标志和条件变量
is_refreshing = False
refresh_condition = threading.Condition()  # 用于协调刷新状态

# 定义最大重试次数
MAX_RETRIES = 3


def initialize_driver():
    global driver
    with driver_lock:
        driver = init_driver()
        if not login(driver):
            logging.error("登录失败，程序退出。")
            driver.quit()
            exit(1)
        if not navigate_to_football(driver):
            logging.error("导航到足球页面失败，程序退出。")
            driver.quit()
            exit(1)
        logging.info("WebDriver 初始化并登录成功。")


def keep_session_alive():
    """
    Periodically perform actions to keep the session alive.
    Simulate user scrolling every minute.
    If scrolling fails, perform re-login and navigate to football.
    """
    global is_refreshing
    while not stop_event.is_set():
        with refresh_condition:
            is_refreshing = True
            refresh_condition.notify_all()  # 通知所有等待的线程

        with driver_lock:
            try:
                logging.info("尝试通过滚动页面保持会话活跃。")

                # 模拟用户向下滚动
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                logging.info("已向下滚动页面。")

                # 等待一段时间，确保滚动完成
                time.sleep(2)

                # 可选：向上滚动回顶部
                driver.execute_script("window.scrollTo(0, 0);")
                logging.info("已向上滚动页面回顶部。")

                # 等待一段时间
                time.sleep(2)

                # 验证会话是否仍然有效
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'btn_title_le'))
                    )
                    logging.info("会话仍然有效。")
                except:
                    logging.warning("会话可能已失效，需要重新登录。")
                    raise Exception("Session might be inactive.")

            except Exception as e:
                logging.error(f"保持会话活跃时发生错误: {e}")
                try:
                    logging.info("尝试重新登录以恢复会话。")

                    # 重新登录
                    if login(driver):
                        logging.info("重新登录成功。")
                        # 重新导航到足球页面
                        if navigate_to_football(driver):
                            logging.info("重新导航到足球页面成功。")
                        else:
                            logging.error("重新导航到足球页面失败。")
                    else:
                        logging.error("重新登录失败。")
                except Exception as inner_e:
                    logging.error(f"重新登录时发生错误: {inner_e}")
            finally:
                with refresh_condition:
                    is_refreshing = False
                    refresh_condition.notify_all()  # 通知所有等待的线程

        # 等待1分钟后再次执行
        logging.info("等待 1 分钟后再次保持会话活跃。")
        stop_event.wait(60)  # 60秒 = 1分钟


@app.route('/matches', methods=['GET'])
def get_matches():
    """
    获取抓取到的比赛数据。
    """
    global driver, is_refreshing
    try:
        with refresh_condition:
            while is_refreshing:
                logging.info("当前正在刷新数据，等待刷新完成。")
                refresh_condition.wait()  # 等待刷新完成

        with driver_lock:
            # 检查 WebDriver 是否仍然有效
            try:
                _ = driver.title  # 访问一个属性以检查会话是否有效
            except Exception as e:
                logging.error(f"WebDriver 会话无效: {e}")
                logging.info("尝试点击主页按钮回到主页。")
                try:
                    home_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, 'home_page'))
                    )
                    home_button.click()
                    logging.info("已点击主页按钮。")
                    if navigate_to_football(driver):
                        logging.info("重新导航到足球页面成功。")
                    else:
                        logging.error("重新导航到足球页面失败。")
                except Exception as inner_e:
                    logging.error(f"处理 WebDriver 会话无效时发生错误: {inner_e}")
                    return jsonify({"message": "数据不可用，请稍后再试。"}), 503

            # 抓取数据
            data = fetch_data(driver)
            with data_lock:
                cached_data['dataSource'] = 2  # 根据你的需求，更新数据来源
                cached_data['count'] = data['count']
                cached_data['fixtures'] = data['fixtures']
            logging.info(f"返回数据: {data['count']} 场比赛")
            return jsonify(cached_data)
    except Exception as e:
        logging.error(f"处理请求时发生错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点。
    """
    global driver
    try:
        with driver_lock:
            _ = driver.title  # 检查 WebDriver 会话
        return jsonify({"status": "healthy"}), 200
    except Exception:
        return jsonify({"status": "unhealthy"}), 500


@app.route('/', methods=['GET'])
def root():
    """
    根路径，重定向到 /matches 端点。
    """
    return jsonify({
        "message": "欢迎使用比赛数据API。请访问 /matches 获取今日比赛数据。"
    }), 200


def run_flask():
    app.run(host='0.0.0.0', port=5001, threaded=True)


if __name__ == '__main__':
    # 初始化 WebDriver, 登录并导航
    initialize_driver()

    # 启动后台线程以保持会话活跃
    keep_alive_thread = threading.Thread(target=keep_session_alive, daemon=True)
    keep_alive_thread.start()

    try:
        # 启动Flask RESTful服务
        logging.info("启动 Flask RESTful 服务...")
        run_flask()
    except KeyboardInterrupt:
        logging.info("接收到退出信号，关闭浏览器。")
    finally:
        # 停止后台线程
        stop_event.set()
        keep_alive_thread.join(timeout=5)

        # 关闭 WebDriver
        with driver_lock:
            if driver:
                driver.quit()
                logging.info("浏览器已关闭。")
