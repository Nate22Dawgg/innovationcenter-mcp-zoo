#!/usr/bin/env python3
"""
NHANES Data Loader

Downloads and converts NHANES XPT files to SQLite database for efficient querying.
Handles data download, XPT file reading, and database conversion.
"""

import json
import os
import sqlite3
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

# Try to import pyreadstat for XPT reading (better than pandas for XPT)
try:
    import pyreadstat
    PYREADSTAT_AVAILABLE = True
except ImportError:
    PYREADSTAT_AVAILABLE = False
    print("Warning: pyreadstat not available. Using pandas for XPT files (may have limitations).")


# NHANES base URL
NHANES_BASE_URL = "https://wwwn.cdc.gov/Nchs/Nhanes"
NHANES_DATA_URL = "https://wwwn.cdc.gov/Nchs/Nhanes"


def get_available_cycles() -> List[str]:
    """
    Get list of available NHANES data cycles.
    
    Returns:
        List of cycle strings (e.g., ["2017-2018", "2019-2020", "2021-2022"])
    """
    # Common cycles - can be extended
    return [
        "2017-2018",
        "2019-2020",
        "2021-2022"
    ]


def get_cycle_code(cycle: str) -> str:
    """
    Convert cycle string to NHANES cycle code.
    
    Args:
        cycle: Cycle string (e.g., "2017-2018")
    
    Returns:
        Cycle code (e.g., "P")
    """
    cycle_map = {
        "2017-2018": "P",
        "2019-2020": "Q",
        "2021-2022": "R"
    }
    return cycle_map.get(cycle, cycle)


def get_data_type_path(data_type: str) -> str:
    """
    Get URL path segment for data type.
    
    Args:
        data_type: Data type (demographics, examination, laboratory, questionnaire)
    
    Returns:
        URL path segment
    """
    type_map = {
        "demographics": "Demographics",
        "examination": "Examination",
        "laboratory": "Laboratory",
        "questionnaire": "Questionnaire"
    }
    return type_map.get(data_type.lower(), data_type)


def download_nhanes_data(cycle: str, file_prefix: str, data_type: str, data_dir: Path) -> Optional[Path]:
    """
    Download NHANES XPT file.
    
    Args:
        cycle: Data cycle (e.g., "2017-2018")
        file_prefix: File prefix (e.g., "DEMO", "BMX")
        data_type: Data type (demographics, examination, laboratory, questionnaire)
        data_dir: Directory to save downloaded files
    
    Returns:
        Path to downloaded file, or None if download failed
    """
    cycle_code = get_cycle_code(cycle)
    data_type_path = get_data_type_path(data_type)
    
    # Construct URL
    filename = f"{file_prefix}_{cycle_code}.XPT"
    url = f"{NHANES_DATA_URL}/{cycle}/{data_type_path}/{filename}"
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Local file path
    local_file = data_dir / filename
    
    # Skip if file already exists
    if local_file.exists():
        print(f"File already exists: {local_file}")
        return local_file
    
    try:
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, local_file)
        print(f"Downloaded: {local_file}")
        return local_file
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None


def read_xpt_file(xpt_file: Path) -> pd.DataFrame:
    """
    Read XPT file into pandas DataFrame.
    
    Args:
        xpt_file: Path to XPT file
    
    Returns:
        pandas DataFrame
    """
    if PYREADSTAT_AVAILABLE:
        # Use pyreadstat for better XPT support
        try:
            df, meta = pyreadstat.read_xport(str(xpt_file))
            return df
        except Exception as e:
            print(f"Error reading XPT with pyreadstat: {e}, trying pandas...")
    
    # Fallback to pandas
    try:
        df = pd.read_sas(str(xpt_file), format='xport')
        return df
    except Exception as e:
        raise ValueError(f"Error reading XPT file {xpt_file}: {e}")


def convert_xpt_to_sqlite(xpt_file: Path, db_path: Path, table_name: str) -> None:
    """
    Convert XPT file to SQLite table.
    
    Args:
        xpt_file: Path to XPT file
        db_path: Path to SQLite database
        table_name: Name for SQLite table
    """
    print(f"Converting {xpt_file} to SQLite table {table_name}...")
    
    # Read XPT file
    df = read_xpt_file(xpt_file)
    
    # Create database connection
    conn = sqlite3.connect(str(db_path))
    
    try:
        # Write to SQLite
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"Converted {len(df)} rows to table {table_name}")
    finally:
        conn.close()


def load_dataset(cycle: str, file_prefix: str, data_type: str, data_dir: Path, db_path: Path) -> bool:
    """
    Download and load a dataset into SQLite.
    
    Args:
        cycle: Data cycle (e.g., "2017-2018")
        file_prefix: File prefix (e.g., "DEMO", "BMX")
        data_type: Data type (demographics, examination, laboratory, questionnaire)
        data_dir: Directory for downloaded files
        db_path: Path to SQLite database
    """
    # Download XPT file
    xpt_file = download_nhanes_data(cycle, file_prefix, data_type, data_dir)
    if not xpt_file:
        return False
    
    # Create table name: {file_prefix}_{cycle_code}
    cycle_code = get_cycle_code(cycle)
    table_name = f"{file_prefix}_{cycle_code}"
    
    # Convert to SQLite
    try:
        convert_xpt_to_sqlite(xpt_file, db_path, table_name)
        return True
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return False


def get_available_datasets(cycle: str, config_path: Path) -> List[Dict]:
    """
    Get list of available datasets for a cycle from config.
    
    Args:
        cycle: Data cycle (e.g., "2017-2018")
        config_path: Path to datasets.json config file
    
    Returns:
        List of dataset dictionaries
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    available = []
    for key, dataset in config.items():
        if cycle in dataset.get("cycles", []):
            available.append({
                "id": key,
                "name": dataset["name"],
                "file_prefix": dataset["file_prefix"],
                "data_type": dataset["data_type"],
                "description": dataset["description"],
                "key_variables": dataset.get("key_variables", [])
            })
    
    return available


def ensure_dataset_loaded(cycle: str, file_prefix: str, data_type: str, data_dir: Path, db_path: Path) -> bool:
    """
    Ensure a dataset is loaded in the database. Download and convert if needed.
    
    Args:
        cycle: Data cycle
        file_prefix: File prefix
        data_type: Data type
        data_dir: Data directory
        db_path: Database path
    
    Returns:
        True if dataset is available, False otherwise
    """
    cycle_code = get_cycle_code(cycle)
    table_name = f"{file_prefix}_{cycle_code}"
    
    # Check if table exists
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            if cursor.fetchone():
                return True
        finally:
            conn.close()
    
    # Load dataset if not found
    return load_dataset(cycle, file_prefix, data_type, data_dir, db_path)


if __name__ == "__main__":
    # Test script
    import sys
    
    data_dir = Path(__file__).parent / "data"
    db_path = data_dir / "nhanes.db"
    config_path = Path(__file__).parent / "config" / "datasets.json"
    
    if len(sys.argv) > 1:
        cycle = sys.argv[1]
        file_prefix = sys.argv[2] if len(sys.argv) > 2 else "DEMO"
        data_type = sys.argv[3] if len(sys.argv) > 3 else "demographics"
        
        print(f"Loading {file_prefix} for cycle {cycle}...")
        load_dataset(cycle, file_prefix, data_type, data_dir, db_path)
    else:
        print("Usage: python nhanes_data_loader.py <cycle> [file_prefix] [data_type]")
        print("Example: python nhanes_data_loader.py 2017-2018 DEMO demographics")

