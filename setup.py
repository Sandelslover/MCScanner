import os
import sys

def setup():
    print("=== MCScanner Setup Wizard ===")
    
    # Check for .env or create it
    env_content = []
    
    # 1. Masscan Path
    default_masscan = "masscan.exe" if sys.platform == "win32" else "masscan"
    masscan_path = input(f"Enter Masscan path (default: {default_masscan}): ").strip() or default_masscan
    env_content.append(f"MASSCAN_PATH={masscan_path}")
    
    # 2. Scan Rate
    scan_rate = input("Enter Scan Rate (packets per second, default: 1000): ").strip() or "1000"
    env_content.append(f"SCAN_RATE={scan_rate}")
    
    # 3. Threads
    threads = input("Enter Threads for pinging (default: 10): ").strip() or "10"
    env_content.append(f"THREADS={threads}")
    
    # 4. Proxies
    proxy_list = input("Enter Proxy list filename (default: proxies.txt): ").strip() or "proxies.txt"
    env_content.append(f"PROXY_LIST={proxy_list}")
    
    # 5. Redis
    use_redis = input("Use Redis for scaling? (y/N): ").strip().lower() == 'y'
    env_content.append(f"USE_REDIS={'true' if use_redis else 'false'}")
    if use_redis:
        redis_host = input("Redis Host (default: localhost): ").strip() or "localhost"
        redis_port = input("Redis Port (default: 6379): ").strip() or "6379"
        env_content.append(f"REDIS_HOST={redis_host}")
        env_content.append(f"REDIS_PORT={redis_port}")
    
    # 6. Discord Webhook
    webhook = input("Enter Discord Webhook URL (optional): ").strip()
    env_content.append(f"WEBHOOK_URL={webhook}")
    
    # 7. Concurrency
    concurrency = input("Enter Concurrency Limit (default: 50): ").strip() or "50"
    env_content.append(f"CONCURRENCY_LIMIT={concurrency}")

    with open(".env", "w") as f:
        f.write("\n".join(env_content))
    
    print("\n[+] .env file created successfully!")
    
    # Initialize proxies.txt if it doesn't exist
    if not os.path.exists(proxy_list):
        with open(proxy_list, "w") as f:
            pass
        print(f"[+] Created empty {proxy_list}")

    print("\nSetup complete! You can now run the scanner with:")
    print("python main.py --mode full --range <your_range>")

if __name__ == "__main__":
    setup()
