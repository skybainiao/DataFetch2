# app.py

from flask import Flask, jsonify
import threading
import time
from scraper import init_driver, login, navigate_to_football, fetch_data

app = Flask(__name__)

# 用于缓存抓取到的数据
cached_data = {
    "count": 0,
    "fixtures": []
}
data_lock = threading.Lock()

# 全局 WebDriver 对象
driver = None


def initialize_driver():
    global driver
    driver = init_driver()
    if not login(driver):
        print("登录失败，程序退出。")
        driver.quit()
        exit(1)
    if not navigate_to_football(driver):
        print("导航到足球页面失败，程序退出。")
        driver.quit()
        exit(1)
    print("初始化完成，等待API请求...")


@app.route('/matches', methods=['GET'])
def get_matches():
    """
    获取抓取到的比赛数据。
    """
    global driver
    try:
        data = fetch_data(driver)
        with data_lock:
            cached_data['count'] = data['count']
            cached_data['fixtures'] = data['fixtures']
        print(f"返回数据: {data['count']} 场比赛")
        return jsonify(cached_data)
    except Exception as e:
        print(f"处理请求时发生错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


def run_flask():
    app.run(host='0.0.0.0', port=5001)


if __name__ == '__main__':
    # 初始化 WebDriver, 登录并导航
    initialize_driver()

    try:
        # 启动Flask RESTful服务
        print("启动 Flask RESTful 服务...")
        run_flask()
    except KeyboardInterrupt:
        print("接收到退出信号，关闭浏览器。")
    finally:
        if driver:
            driver.quit()
            print("浏览器已关闭。")
