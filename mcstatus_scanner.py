from mcstatus import JavaServer
import logging
import asyncio
from typing import Optional, Dict

class MCStatusScanner:
    def __init__(self):
        self.timeout = 5

    async def scan_server(self, ip: str, port: int = 25565) -> Optional[Dict]:
        try:
            server = JavaServer.lookup(f"{ip}:{port}")
            # Use async status for better performance with many servers
            status = await server.async_status()
            
            return {
                "ip": ip,
                "port": port,
                "online": status.players.online,
                "max_online": status.players.max,
                "motd": status.description if isinstance(status.description, str) else str(status.description),
                "version": status.version.name
            }
        except Exception as e:
            # Common for servers that are actually offline or not MC
            return None

    async def batch_scan(self, targets: list[tuple[str, int]]):
        tasks = [self.scan_server(ip, port) for ip, port in targets]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
