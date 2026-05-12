"""
Utility functions for ETF scanner
"""

import pandas as pd
import logging
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import pytz

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/scanner.log')
        ]
    )

def load_etf_symbols(csv_file: Path) -> List[str]:
    """Load ETF symbols from CSV file"""
    
    try:
        if not csv_file.exists():
            # Create default CSV file
            create_default_etf_csv(csv_file)
        
        df = pd.read_csv(csv_file)
        
        # Check for symbol column
        if 'symbol' in df.columns:
            symbols = df['symbol'].tolist()
        elif 'SYMBOL' in df.columns:
            symbols = df['SYMBOL'].tolist()
        else:
            # Try first column
            symbols = df.iloc[:, 0].tolist()
        
        # Clean symbols (add .NS if missing)
        cleaned_symbols = []
        for symbol in symbols:
            symbol = str(symbol).strip()
            if symbol and not symbol.endswith('.NS'):
                symbol = f"{symbol}.NS"
            cleaned_symbols.append(symbol)
        
        logging.info(f"Loaded {len(cleaned_symbols)} symbols from {csv_file}")
        return cleaned_symbols
        
    except Exception as e:
        logging.error(f"Error loading symbols from {csv_file}: {e}")
        return []

def create_default_etf_csv(csv_file: Path):
    """Create default ETF symbols CSV file"""
    
    default_etfs = [
        "NIFTYBEES",
        "GOLDBEES",
        "SILVERBEES",
        "BANKBEES",
        "JUNIORBEES",
        "MON100",
        "ITBEES",
        "PHARMABEES",
        "PSUBNKBEES",
        "MOMENTUM"
    ]
    
    df = pd.DataFrame({'symbol': default_etfs, 'name': default_etfs})
    df.to_csv(csv_file, index=False)
    logging.info(f"Created default ETF CSV at {csv_file}")

def save_log(logs_dir: Path, log_type: str, data: dict):
    """Save log data to JSON file"""
    
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y%m%d')
    log_file = logs_dir / f"{log_type}_{timestamp}.json"
    
    try:
        # Load existing logs
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Append new log
        logs.append(data)
        
        # Save back
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2, default=str)
            
    except Exception as e:
        logging.error(f"Error saving log: {e}")

def is_market_hours() -> bool:
    """Check if market is open (9:15 AM - 3:30 PM IST)"""
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.time()
    
    market_open = current_time.hour >= 9 and current_time.minute >= 15
    market_close = current_time.hour < 15 or (current_time.hour == 15 and current_time.minute <= 30)
    
    return market_open and market_close
