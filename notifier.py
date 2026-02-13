import aiohttp
import json
import logging
from datetime import datetime
from config import CONFIG

class WebhookNotifier:
    def __init__(self):
        self.url = CONFIG.get("WEBHOOK_URL")

    async def notify_discovery(self, server_data: dict):
        if not self.url:
            return

        embed = {
            "title": "💎 Prime Minecraft Server Discovered!",
            "color": 0x00ff00,
            "fields": [
                {"name": "IP:Port", "value": f"`{server_data['ip']}:{server_data['port']}`", "inline": True},
                {"name": "Players", "value": f"{server_data['online']}/{server_data['max_online']}", "inline": True},
                {"name": "Version", "value": server_data['version'], "inline": True},
                {"name": "MOTD", "value": f"```\n{server_data['motd']}\n```"},
                {"name": "Notes", "value": server_data.get('notes', 'N/A')}
            ],
            "timestamp": datetime.now().isoformat()
        }

        payload = {"embeds": [embed]}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload) as resp:
                    if resp.status != 204:
                        logging.warning(f"Discord webhook failed with status {resp.status}")
        except Exception as e:
            logging.error(f"Error sending webhook: {e}")
