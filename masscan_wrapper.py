import subprocess
import json
import os
import logging
import asyncio
from config import CONFIG

class MasscanWrapper:
    def __init__(self):
        self.masscan_path = CONFIG["MASSCAN_PATH"]
        self.rate = CONFIG["SCAN_RATE"]
        self.last_status = {}
        self.status_task = None

    async def _monitor_masscan(self, process):
        """Read masscan stderr and log status every 30 seconds"""
        async def read_stderr():
            try:
                buffer = b""
                while True:
                    char = await process.stderr.read(1)
                    if not char:
                        break
                    
                    if char in (b'\r', b'\n'):
                        line = buffer.decode('utf-8', errors='ignore').strip()
                        buffer = b""
                        if not line:
                            continue
                        
                        # Log every distinct line for debugging
                        logging.debug(f"[MASSCAN-STDERR] {line}")
                        
                        # Masscan status lines often look like:
                        # rate: 100.00-kpps, 1.23% done, 0:01:23 remaining, 123 hits
                        if any(key in line.lower() for key in ["rate:", "done", "remaining", "hits:"]):
                            self.last_status["latest"] = line
                    else:
                        buffer += char
            except Exception as e:
                logging.debug(f"Error reading masscan stderr: {e}")

        # Start a task to read the lines
        reader_task = asyncio.create_task(read_stderr())
        
        try:
            # Poll more frequently at the start to catch the first status
            for _ in range(30):
                if reader_task.done():
                    break
                await asyncio.sleep(1)
                if "latest" in self.last_status:
                    logging.info(f"[MASSCAN] {self.last_status['latest']}")
                    break
            
            # Then continue with the 30s reporting loop
            while not reader_task.done():
                await asyncio.sleep(30)
                if "latest" in self.last_status:
                    logging.info(f"[MASSCAN] {self.last_status['latest']}")
        except asyncio.CancelledError:
            reader_task.cancel()
            raise
        finally:
            if not reader_task.done():
                reader_task.cancel()

    async def scan_range(self, ip_range, port="25565"):
        """
        Runs masscan on a given IP range.
        Output is parsed from JSON.
        """
        output_file = "masscan_out.json"
        cmd = [
            self.masscan_path,
            ip_range,
            "-p", port,
            "--max-rate", str(self.rate),
            "-oJ", output_file,
            "--wait", "0",
            "--status"
        ]
        
        try:
            logging.info(f"Starting masscan on {ip_range}...")
            # Use asyncio.create_subprocess_exec for non-blocking execution
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Start monitoring task
            self.status_task = asyncio.create_task(self._monitor_masscan(process))
            
            # Wait for process to finish
            await process.wait()
            
            if self.status_task:
                self.status_task.cancel()
                try:
                    await self.status_task
                except asyncio.CancelledError:
                    pass
                self.status_task = None
            
            if not os.path.exists(output_file):
                return []

            with open(output_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                # Masscan JSON output can sometimes be missing the closing bracket if interrupted
                if not content.endswith(']'):
                    content += ']'
                data = json.loads(content)
            
            os.remove(output_file)
            
            results = []
            for entry in data:
                ip = entry.get("ip")
                for p in entry.get("ports", []):
                    results.append((ip, p.get("port")))
            return results

        except subprocess.CalledProcessError as e:
            logging.error(f"Masscan error: {e.stderr.decode()}")
            return []
        except Exception as e:
            logging.error(f"Error running masscan: {e}")
            return []
