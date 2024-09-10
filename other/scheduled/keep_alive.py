import http.client
import sched
import time
from threading import Thread

scheduler = sched.scheduler(time.monotonic, time.sleep)
PING_INTERVAL = 12 * 60  # 12 minutes


def ping_server():
    conn = http.client.HTTPSConnection("briscola-qbbv.onrender.com")
    try:
        conn.request("GET", "/keep-alive")
        response = conn.getresponse()
        if response.status != 200:
            print(f"Ping failed with status code {response.status}")
    except Exception as e:
        print(f"Error during ping: {e}")
    finally:
        conn.close()

    scheduler.enter(PING_INTERVAL, 1, ping_server)


def start_scheduler():
    scheduler.enter(0, 1, ping_server)
    scheduler.run()


def keep_alive():
    scheduler_thread = Thread(target=start_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
