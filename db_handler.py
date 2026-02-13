import sqlite3
import logging
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_path="servers.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS servers (
                    ip TEXT,
                    port INTEGER,
                    online INTEGER,
                    max_online INTEGER,
                    motd TEXT,
                    version TEXT,
                    cracked BOOLEAN,
                    is_whitelisted BOOLEAN,
                    plugins TEXT,
                    last_checked TIMESTAMP,
                    notes TEXT,
                    PRIMARY KEY (ip, port)
                )
            ''')
            conn.commit()

    def save_server(self, data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO servers 
                (ip, port, online, max_online, motd, version, cracked, is_whitelisted, plugins, last_checked, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['ip'], data['port'], data['online'], data['max_online'], 
                data['motd'], data['version'], data.get('cracked'), 
                data.get('is_whitelisted'), data.get('plugins'), datetime.now(), data.get('notes')
            ))
            conn.commit()
