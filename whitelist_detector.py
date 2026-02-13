import subprocess
import json
import logging
from config import CONFIG

class WhitelistDetector:
    def __init__(self):
        self.js_path = "whitelist_check.js"

    def check_server(self, ip: str, port: int) -> dict:
        """
        Runs the Node.js mineflayer bot to check if a server is whitelisted.
        """
        try:
            cmd = ["node", self.js_path, ip, str(port)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=CONFIG["WHITELIST_CHECK_TIMEOUT"])
            
            if result.stdout:
                try:
                    return json.loads(result.stdout.strip())
                except json.JSONDecodeError:
                    return {"status": "error", "message": "Failed to parse Node output"}
            
            return {"status": "offline", "message": "No response from bot"}
            
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "Check timed out"}
        except Exception as e:
            logging.error(f"Error checking whitelist for {ip}:{port}: {e}")
            return {"status": "error", "message": str(e)}
