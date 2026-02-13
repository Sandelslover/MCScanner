import requests
from bs4 import BeautifulSoup
import logging
import re
from proxy_manager import ProxyManager
from config import CONFIG

class ServerScraper:
    def __init__(self, proxy_manager: ProxyManager = None):
        self.proxy_manager = proxy_manager
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def _get_request(self, url):
        """Helper to handle requests with proxy rotation on failure/slowness/rate-limiting"""
        proxies = self.proxy_manager.get_proxy() if self.proxy_manager else None
        try:
            response = requests.get(url, headers=self.headers, proxies=proxies, timeout=10)
            
            # Explicit check for Rate Limiting (HTTP 429)
            if response.status_code == 429:
                logging.warning(f"Rate limited (429) on {url} with proxy {proxies.get('http') if proxies else 'None'}. Rotating...")
                if self.proxy_manager:
                    self.proxy_manager.mark_failed() # Discard rate-limited proxy
                return self._get_request(url) # Recursive retry with new proxy

            response.raise_for_status()
            return response
        except (requests.RequestException, requests.Timeout) as e:
            logging.warning(f"Request to {url} failed with proxy {proxies.get('http') if proxies else 'None'}: {e}")
            if self.proxy_manager:
                self.proxy_manager.mark_failed()
            # Try once more with a new proxy
            proxies = self.proxy_manager.get_proxy() if self.proxy_manager else None
            try:
                response = requests.get(url, headers=self.headers, proxies=proxies, timeout=15)
                if response.status_code == 429:
                    if self.proxy_manager: self.proxy_manager.mark_failed()
                    return None
                response.raise_for_status()
                return response
            except Exception as retry_e:
                logging.error(f"Retry to {url} also failed: {retry_e}")
                return None

    def scrape_minecraft_list_org(self):
        """Example: Scrape minecraft-list.org (hypothetical target for small servers)"""
        servers = []
        url = "https://minecraft-list.org/servers/players"
        response = self._get_request(url)
        if not response:
            return servers

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            # This is a generic logic, would need adjustment per site
            for row in soup.select(".server-row"):
                players_text = row.select_one(".players").text.strip()
                match = re.search(r'(\d+)\s*/\s*(\d+)', players_text)
                if match:
                    online = int(match.group(1))
                    max_players = int(match.group(2))
                    
                    if 0 <= online <= 10 and max_players <= 50:
                        ip = row.select_one(".ip").text.strip()
                        servers.append({
                            "ip": ip,
                            "port": 25565,
                            "online": online,
                            "max_online": max_players
                        })
        except Exception as e:
            logging.error(f"Error parsing minecraft-list.org: {e}")
        return servers

    def scrape_topg_org(self):
        """Scrape topg.org for small servers"""
        servers = []
        url = "https://topg.org/minecraft-servers/"
        response = self._get_request(url)
        if not response:
            return servers

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            for row in soup.select(".server-list-item"):
                players_div = row.select_one(".players")
                if players_div:
                    match = re.search(r'(\d+)\s*/\s*(\d+)', players_div.text)
                    if match:
                        online = int(match.group(1))
                        max_p = int(match.group(2))
                        if 0 <= online <= 10 and max_p <= 50:
                            ip_btn = row.select_one(".copy-ip")
                            if ip_btn and ip_btn.get("data-ip"):
                                servers.append({
                                    "ip": ip_btn["data-ip"],
                                    "port": 25565,
                                    "online": online,
                                    "max_online": max_p
                                })
        except Exception as e:
            logging.error(f"Error parsing topg.org: {e}")
        return servers

    def scrape_minecraft_server_list_com(self):
        """Scrape minecraft-server-list.com for small servers"""
        servers = []
        url = "https://minecraft-server-list.com/filter/players/1/"
        response = self._get_request(url)
        if not response:
            return servers

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            for row in soup.select("tr"):
                ip_tag = row.select_one(".ip")
                player_tag = row.select_one(".players")
                
                if ip_tag and player_tag:
                    ip = ip_tag.text.strip()
                    players_text = player_tag.text.strip()
                    match = re.search(r'(\d+)\s*/\s*(\d+)', players_text)
                    if match:
                        online = int(match.group(1))
                        max_p = int(match.group(2))
                        if 0 <= online <= 10 and max_p <= 60:
                            servers.append({
                                "ip": ip,
                                "port": 25565,
                                "online": online,
                                "max_online": max_p
                            })
        except Exception as e:
            logging.error(f"Error parsing minecraft-server-list.com: {e}")
        return servers

    def scrape_all(self):
        all_found = []
        
        # Sources list with logging
        sources = [
            ("topg.org", self.scrape_topg_org),
            ("minecraft-server-list.com", self.scrape_minecraft_server_list_com),
            ("minecraft-list.org", self.scrape_minecraft_list_org)
        ]

        for name, func in sources:
            logging.info(f"Scraping {name}...")
            try:
                found = func()
                all_found.extend(found)
                logging.info(f"Source {name} returned {len(found)} results.")
            except Exception as e:
                logging.error(f"Failed to scrape {name}: {e}")
        
        # Deduplicate results
        unique = {}
        for s in all_found:
            key = f"{s['ip']}:{s['port']}"
            unique[key] = s
        
        logging.info(f"Scraping complete. Total unique servers found: {len(unique)}")
        return list(unique.values())
