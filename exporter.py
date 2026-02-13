import sqlite3
import csv
import json
import logging
from datetime import datetime

class DataExporter:
    def __init__(self, db_path="servers.db"):
        self.db_path = db_path

    def _fetch_all(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM servers WHERE is_whitelisted = 0")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching data for export: {e}")
            return []

    def export_csv(self, filename="discovered_servers.csv"):
        data = self._fetch_all()
        if not data:
            return
        
        keys = data[0].keys()
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
            logging.info(f"Exported {len(data)} servers to {filename}")
        except Exception as e:
            logging.error(f"CSV Export error: {e}")

    def export_json(self, filename="discovered_servers.json"):
        data = self._fetch_all()
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, default=str)
            logging.info(f"Exported {len(data)} servers to {filename}")
        except Exception as e:
            logging.error(f"JSON Export error: {e}")
