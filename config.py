import json
import os
import platform
from dotenv import load_dotenv

load_dotenv()

def get_default_masscan_path():
    if platform.system() == "Windows":
        return "masscan.exe"
    return "masscan"

CONFIG = {
    "MASSCAN_PATH": os.getenv("MASSCAN_PATH", get_default_masscan_path()),
    "SCAN_RATE": int(os.getenv("SCAN_RATE", 1000)),
    "THREADS": int(os.getenv("THREADS", 10)),
    "PROXY_LIST": os.getenv("PROXY_LIST", "proxies.txt"),
    "USE_REDIS": os.getenv("USE_REDIS", "false").lower() == "true",
    "REDIS_HOST": os.getenv("REDIS_HOST", "localhost"),
    "REDIS_PORT": int(os.getenv("REDIS_PORT", 6379)),
    "WEBHOOK_URL": os.getenv("WEBHOOK_URL", ""),
    "CONCURRENCY_LIMIT": int(os.getenv("CONCURRENCY_LIMIT", 50)),
    "PROXY_API_URL": os.getenv("PROXY_API_URL", "https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http,https&timeout=6000&country=all&ssl=all&anonymity=all"),
    "TARGET_PLAYER_MAX": 8,
    "SERVER_PLAYER_CAP": 60,
    "WHITELIST_CHECK_TIMEOUT": 30
}
