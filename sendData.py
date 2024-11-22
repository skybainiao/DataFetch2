import threading
from scraper1 import send_csv_as_json

if __name__ == "__main__":

    threads = []

    # 使用 lambda 延迟调用 send_csv_as_json
    thread3 = threading.Thread(
        target=lambda: send_csv_as_json('hdp_ou_data.csv', 'http://localhost:8080/api/odds/matches', 0.5, "normal"))
    threads.append(thread3)

    thread4 = threading.Thread(
        target=lambda: send_csv_as_json('corners_data.csv', 'http://localhost:8080/api/odds/corner-matches', 0.5, "corner"))
    threads.append(thread4)

    # 启动线程
    for thread in threads:
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()
