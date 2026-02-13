# MCScanner - Minecraft Server Discovery Agent

A high-performance Minecraft Java Edition server discovery agent designed to find small, private, or hidden servers.

## Features
- **Cross-Platform**: Support for Windows and Linux.
- **Fast Discovery**: Uses `masscan` for rapid port scanning (25565).
- **Deep Verification**: Uses `mcstatus` for initial ping and `mineflayer` (Node.js) for join tests.
- **Whitelist Detection**: Automatically identifies whitelisted vs open servers.
- **Plugin Capture**: Captures server plugins upon successful join.
- **Proxy Support**: Dynamic proxy fetching from ProxyScrape API with automatic rotation and health checks.
- **Scalable**: Redis-backed task queue support for horizontal scaling.
- **Real-time Monitoring**: Periodic progress reporting and a dashboard view.
- **Notifications**: Discord Webhook integration for "Prime Targets".

## Requirements
- **Python 3.12+**
- **Node.js** (for Whitelist/Plugin detection)
- **Masscan**: 
  - Windows: `masscan.exe` (included or in PATH)
  - Linux: `sudo apt install masscan`
- **Redis** (Optional, for multi-worker scaling)

## Installation

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/Sandelslover/MCScanner.git
cd MCScanner
pip install -r requirements.txt
npm install
```

### 2. Run Setup
Use the interactive setup script to configure your environment variables:
```bash
python setup.py
```

## Usage

### Discovery Mode (Scrape + Scan)
```bash
python main.py --mode discovery --range 73.0.0.0/8
```

### Worker Mode (Process found servers)
```bash
python main.py --mode worker --workers 5
```

### Full Mode (Everything)
```bash
python main.py --mode full --range 73.0.0.0/8 --workers 5
```

### Run without Proxies
```bash
python main.py --mode full --range 1.2.3.0/24 --no-proxy
```

## Configuration (.env)
- `MASSCAN_PATH`: Path to the masscan executable.
- `SCAN_RATE`: Packets per second for masscan.
- `PROXY_LIST`: Path to your proxy file.
- `WEBHOOK_URL`: Discord webhook for alerts.
- `USE_REDIS`: Set to `true` to use Redis for task management.

## Disclaimer
This tool is for educational and research purposes only. Ensure you have permission to scan network ranges and comply with Minecraft's EULA and local laws.

Also a work in progress. Redis management has not been tested but everything else should be working atp.
