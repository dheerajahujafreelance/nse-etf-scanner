# NSE ETF Scanner 📊

Automated ETF scanner that fetches live data from Yahoo Finance and sends top losers to Telegram at market hours.

## 🚀 Features

- Fetches live ETF data from Yahoo Finance (no NSE scraping required)
- Identifies top losers sorted from highest loss to lowest loss
- Sends automated updates to Telegram channel
- Runs at 12:00 PM, 2:00 PM, and 3:00 PM IST on market days
- Configurable ETF symbols via CSV file
- Comprehensive logging and error handling

## 📋 Prerequisites

- Python 3.10 or higher
- Telegram Bot Token
- Telegram Channel/Group Chat ID

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/nse-etf-scanner.git
cd nse-etf-scanner
