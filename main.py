import asyncio
import logging
import sys
import argparse
from datetime import datetime
from db_handler import DatabaseHandler
from scraper import ServerScraper
from masscan_wrapper import MasscanWrapper
from mcstatus_scanner import MCStatusScanner
from whitelist_detector import WhitelistDetector
from config import CONFIG

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.FileHandler("scanner.log"), logging.StreamHandler(sys.stdout)]
)

from queue_manager import TaskQueue
from notifier import WebhookNotifier
from colorama import Fore, Style, init

init(autoreset=True)

from proxy_manager import ProxyManager

class MCDiscoveryAgent:
    def __init__(self, use_proxies=True):
        self.db = DatabaseHandler()
        self.use_proxies = use_proxies
        self.proxy_manager = ProxyManager(CONFIG["PROXY_LIST"], skip_fetch=not use_proxies) if use_proxies else None
        self.scraper = ServerScraper(proxy_manager=self.proxy_manager)
        self.masscan = MasscanWrapper()
        self.mc_scanner = MCStatusScanner()
        self.whitelist_checker = WhitelistDetector()
        self.queue = TaskQueue(
            use_redis=CONFIG["USE_REDIS"], 
            host=CONFIG["REDIS_HOST"], 
            port=CONFIG["REDIS_PORT"]
        )
        self.notifier = WebhookNotifier()
        self.semaphore = asyncio.Semaphore(CONFIG["CONCURRENCY_LIMIT"])
        self.total_found = 0
        self.start_time = datetime.now()

    async def report_stats(self):
        """Periodically report scanning statistics"""
        while True:
            q_size = await self.queue.get_queue_size()
            uptime = datetime.now() - self.start_time
            logging.info(f"{Fore.BLUE}{Style.BRIGHT}--- DASHBOARD ---")
            logging.info(f"Uptime: {uptime} | Queue Size: {q_size} | Total Prime Targets: {self.total_found}")
            logging.info(f"{Fore.BLUE}{Style.BRIGHT}-----------------")
            await asyncio.sleep(60)

    async def process_potential_server(self, server_data):
        """Deep check and save if promising"""
        async with self.semaphore:
            ip = server_data['ip']
            port = server_data['port']
            
            logging.info(f"{Fore.CYAN}Deep checking {ip}:{port}...")
            check_result = self.whitelist_checker.check_server(ip, port)
            
            if check_result['status'] == 'success':
                self.total_found += 1
                server_data['is_whitelisted'] = False
                server_data['cracked'] = True
                server_data['plugins'] = check_result.get('plugins', 'None')
                server_data['notes'] = f"Join Success: Likely cracked/no-whitelist. Plugins: {server_data['plugins']}"
                logging.info(f"{Fore.GREEN}{Style.BRIGHT}PRIME TARGET: {ip}:{port} | {server_data['online']}/{server_data['max_online']} | Plugins: {server_data['plugins']}")
                
                self.db.save_server(server_data)
                await self.notifier.notify_discovery(server_data)
                
            elif check_result['status'] == 'whitelisted':
                logging.debug(f"Server {ip}:{port} is whitelisted.")
            else:
                logging.debug(f"Server {ip}:{port} check result: {check_result['status']}")

    async def worker(self):
        """Worker loop to process tasks from Redis with health monitoring"""
        worker_id = f"worker_{id(self)}_{asyncio.current_task().get_name()}"
        logging.info(f"{Fore.YELLOW}Worker {worker_id} started. Waiting for tasks...")
        
        consecutive_errors = 0
        while True:
            try:
                task = await self.queue.dequeue()
                if task:
                    await self.process_potential_server(task)
                    consecutive_errors = 0  # Reset on success
                else:
                    await asyncio.sleep(5)
            except Exception as e:
                consecutive_errors += 1
                logging.error(f"{Fore.RED}Worker {worker_id} error ({consecutive_errors}): {e}")
                if consecutive_errors > 5:
                    logging.error(f"{Fore.RED}Worker {worker_id} experienced too many consecutive errors. Restarting worker logic in 10s...")
                    await asyncio.sleep(10)
                    consecutive_errors = 0
                else:
                    await asyncio.sleep(2)

    async def run_discovery_cycle(self, ip_ranges=None):
        # 1. Scrape known lists
        logging.info(f"{Fore.MAGENTA}Starting scraper...")
        scraped_servers = self.scraper.scrape_all()
        if scraped_servers:
            await self.queue.enqueue_batch(scraped_servers)
        
        # 2. Run masscan if ranges provided
        if ip_ranges:
            for ip_range in ip_ranges:
                discovered = await self.masscan.scan_range(ip_range)
                # Convert to dict format for queue
                tasks = [{"ip": ip, "port": port} for ip, port in discovered]
                await self.queue.enqueue_batch(tasks)

    async def ping_and_filter(self):
        """Intermediate step: take raw IP:port from queue, ping it, and re-queue if promising"""
        while True:
            task = await self.queue.dequeue()
            if not task:
                await asyncio.sleep(5)
                continue
                
            # If it already has online info, it's ready for deep check
            if 'online' in task:
                await self.process_potential_server(task)
                continue

            # Otherwise, it's a raw IP:port from masscan
            res = await self.mc_scanner.scan_server(task['ip'], task['port'])
            if res and res['online'] <= CONFIG["TARGET_PLAYER_MAX"] and res['max_online'] <= CONFIG["SERVER_PLAYER_CAP"]:
                await self.queue.enqueue_batch([res])

import argparse

async def main():
    parser = argparse.ArgumentParser(description="MCScanner - Minecraft Server Discovery Agent")
    parser.add_argument("--mode", choices=["discovery", "worker", "full"], default="full", 
                        help="discovery: scrape/scan and enqueue; worker: process queue; full: do both")
    parser.add_argument("--range", help="IPv4 range for masscan (e.g., 1.2.3.0/24)")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker tasks to spawn in worker/full mode")
    parser.add_argument("--no-proxy", action="store_true", help="Disable proxy usage for scraping")
    
    args = parser.parse_args()
    agent = MCDiscoveryAgent(use_proxies=not args.no_proxy)

    tasks = []
    
    if args.mode in ["discovery", "full"]:
        ip_ranges = [args.range] if args.range else None
        tasks.append(agent.run_discovery_cycle(ip_ranges))
        tasks.append(agent.ping_and_filter())
        tasks.append(agent.report_stats())

    if args.mode in ["worker", "full"]:
        for _ in range(args.workers):
            tasks.append(agent.worker())
        if args.mode == "worker":
            tasks.append(agent.report_stats())

    if not tasks:
        parser.print_help()
        return

    logging.info(f"{Fore.BLUE}{Style.BRIGHT}MCScanner started in '{args.mode}' mode with {args.workers} worker(s).")
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
