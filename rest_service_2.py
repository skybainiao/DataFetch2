from flask import Flask, jsonify
import threading
import time
from scraper import init_driver, login, navigate_to_football, fetch_data  # 从scraper.py导入

app = Flask(__name__)

# 用于缓存抓取到的数据
cached_data = []
data_lock = threading.Lock()

def scraping_loop():
    """
    持续抓取数据并更新缓存。
    """
    driver = init_driver()
    try:
        if login(driver) and navigate_to_football(driver):
            while True:
                start_time = time.time()
                data = fetch_data(driver)  # 使用 scraper.py 中的 fetch_data 方法
                if data:
                    with data_lock:
                        cached_data.clear()
                        cached_data.extend(data)
                else:
                    print("未抓取到数据。")

                # 控制抓取频率
                elapsed_time = time.time() - start_time
                if elapsed_time < 1:
                    time.sleep(1 - elapsed_time)
    except Exception as e:
        print(f"抓取过程中出现错误: {e}")
    finally:
        driver.quit()
        print("浏览器已关闭。")

@app.route('/matches', methods=['GET'])
def get_matches():
    """
    获取抓取到的比赛数据。
    """
    with data_lock:
        return jsonify(cached_data)

if __name__ == '__main__':
    # 启动抓取线程
    threading.Thread(target=scraping_loop, daemon=True).start()
    # 启动Flask RESTful服务
    app.run(host='0.0.0.0', port=5001)
