import random
import logging
import time
import os
import requests
from datetime import datetime, timedelta
from config import CONFIG

class ProxyManager:
    def __init__(self, proxy_file, skip_fetch=False):
        self.proxies = []
        self.proxy_file = proxy_file
        self.current_proxy = None
        self.last_rotation_time = datetime.min
        self.rotation_interval = timedelta(minutes=5)
        if not skip_fetch:
            self.fetch_from_api()
        self.load_proxies()

    def fetch_from_api(self):
        """Fetch fresh proxies from ProxyScrape API at startup"""
        logging.info("Fetching fresh proxies from API...")
        try:
            response = requests.get(CONFIG["PROXY_API_URL"], timeout=15)
            response.raise_for_status()
            new_proxies = [p.strip() for p in response.text.splitlines() if p.strip()]
            
            # Merge with existing file (avoid duplicates)
            existing = set()
            if os.path.exists(self.proxy_file):
                with open(self.proxy_file, 'r') as f:
                    existing = {line.strip() for line in f if line.strip()}
            
            all_proxies = existing.union(set(new_proxies))
            
            with open(self.proxy_file, 'w') as f:
                f.write("\n".join(all_proxies))
            
            logging.info(f"API fetch complete. Total proxies in {self.proxy_file}: {len(all_proxies)}")
        except Exception as e:
            logging.error(f"Failed to fetch proxies from API: {e}")

    def load_proxies(self):
        try:
            with open(self.proxy_file, 'r') as f:
                # Handle cases with or without http:// prefix
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if not line.startswith(('http://', 'https://')):
                        line = f"http://{line}"
                    self.proxies.append(line)
            logging.info(f"Loaded {len(self.proxies)} proxies from file.")
        except FileNotFoundError:
            logging.warning(f"Proxy file {self.proxy_file} not found. Running without proxies.")

    def _rotate(self):
        """Force a rotation to a new random proxy"""
        if not self.proxies:
            return None
        
        # Avoid picking the same one if possible
        available = [p for p in self.proxies if p != self.current_proxy]
        self.current_proxy = random.choice(available if available else self.proxies)
        self.last_rotation_time = datetime.now()
        logging.info(f"Proxy rotated to: {self.current_proxy}")
        return self.current_proxy

    def get_proxy(self, force_rotate=False):
        """
        Returns a proxy dictionary for requests.
        Rotates if force_rotate is True or if 5 minutes have passed.
        """
        if not self.proxies:
            return None

        now = datetime.now()
        if force_rotate or not self.current_proxy or (now - self.last_rotation_time) > self.rotation_interval:
            self._rotate()

        return {"http": self.current_proxy, "https": self.current_proxy}

    def mark_failed(self):
        """Discard unusable proxy and force rotation"""
        if self.current_proxy in self.proxies:
            logging.warning(f"Discarding unusable proxy: {self.current_proxy}")
            self.proxies.remove(self.current_proxy)
            # Update the file to remove the dead proxy
            try:
                raw_proxy = self.current_proxy.replace("http://", "").replace("https://", "")
                with open(self.proxy_file, 'r') as f:
                    lines = f.readlines()
                with open(self.proxy_file, 'w') as f:
                    for line in lines:
                        if line.strip() != raw_proxy:
                            f.write(line)
            except Exception as e:
                logging.error(f"Failed to update proxy file: {e}")
                
        self._rotate()
