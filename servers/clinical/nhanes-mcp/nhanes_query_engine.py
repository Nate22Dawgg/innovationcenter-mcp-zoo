#!/usr/bin/env python3
"""
NHANES Query Engine

Provides query interface for NHANES data stored in SQLite database.
Supports filtering, variable selection, aggregations, and percentile calculations.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


def get_db_path(data_dir: Path) -> Path:
    """Get path to SQLite database."""
    return data_dir / "nhanes.db"


def get_table_name(cycle: str, file_prefix: str) -> str:
    """Get SQLite table name for a dataset."""
    # Import here to avoid circular imports
    try:
        from nhanes_data_loader import get_cycle_code
        cycle_code = get_cycle_code(cycle)
    except ImportError:
        # Fallback cycle code mapping
        cycle_map = {
            "2017-2018": "P",
            "2019-2020": "Q",
            "2021-2022": "R"
        }
        cycle_code = cycle_map.get(cycle, cycle)
    return f"{file_prefix}_{cycle_code}"


def list_datasets(cycle: str, config_path: Path) -> List[Dict]:
    """
    List available datasets for a cycle.
    
    Args:
        cycle: Data cycle (e.g., "2017-2018")
        config_path: Path to datasets.json config file
    
    Returns:
        List of dataset dictionaries
    """
    # Import here to avoid circular imports
    try:
        from nhanes_data_loader import get_available_datasets
        return get_available_datasets(cycle, config_path)
    except ImportError:
        # Fallback: read config directly
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


def get_dataset_info(dataset_id: str, cycle: str, config_path: Path) -> Dict[str, Any]:
    """
    Get information about a specific dataset.
    
    Args:
        dataset_id: Dataset ID from config
        cycle: Data cycle
        config_path: Path to datasets.json config file
    
    Returns:
        Dataset information dictionary
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    if dataset_id not in config:
        raise ValueError(f"Dataset '{dataset_id}' not found in config")
    
    dataset = config[dataset_id]
    
    if cycle not in dataset.get("cycles", []):
        raise ValueError(f"Dataset '{dataset_id}' not available for cycle '{cycle}'")
    
    return {
        "id": dataset_id,
        "name": dataset["name"],
        "file_prefix": dataset["file_prefix"],
        "data_type": dataset["data_type"],
        "description": dataset["description"],
        "key_variables": dataset.get("key_variables", []),
        "cycle": cycle,
        "table_name": get_table_name(cycle, dataset["file_prefix"])
    }


def build_filter_clause(filters: Optional[Dict[str, Any]]) -> tuple:
    """
    Build SQL WHERE clause from filters dictionary.
    
    Args:
        filters: Dictionary of filter conditions (e.g., {"RIDAGEYR": {"min": 18, "max": 65}})
    
    Returns:
        Tuple of (WHERE clause string, parameter list)
    """
    if not filters:
        return "", []
    
    conditions = []
    params = []
    
    for var, condition in filters.items():
        if isinstance(condition, dict):
            if "min" in condition:
                conditions.append(f"{var} >= ?")
                params.append(condition["min"])
            if "max" in condition:
                conditions.append(f"{var} <= ?")
                params.append(condition["max"])
            if "equals" in condition:
                conditions.append(f"{var} = ?")
                params.append(condition["equals"])
            if "in" in condition:
                placeholders = ",".join(["?"] * len(condition["in"]))
                conditions.append(f"{var} IN ({placeholders})")
                params.extend(condition["in"])
        else:
            # Simple equality
            conditions.append(f"{var} = ?")
            params.append(condition)
    
    where_clause = " AND ".join(conditions)
    return where_clause, params


def query_data(
    dataset_id: str,
    cycle: str,
    filters: Optional[Dict[str, Any]] = None,
    variables: Optional[List[str]] = None,
    limit: Optional[int] = None,
    data_dir: Path = None,
    config_path: Path = None
) -> Dict[str, Any]:
    """
    Query NHANES data with optional filters and variable selection.
    
    Args:
        dataset_id: Dataset ID from config
        cycle: Data cycle
        filters: Optional filter dictionary
        variables: Optional list of variables to select
        limit: Optional limit on number of rows
        data_dir: Data directory path
        config_path: Config file path
    
    Returns:
        Dictionary with query results
    """
    if data_dir is None:
        data_dir = Path(__file__).parent / "data"
    if config_path is None:
        config_path = Path(__file__).parent / "config" / "datasets.json"
    
    # Get dataset info
    dataset_info = get_dataset_info(dataset_id, cycle, config_path)
    table_name = dataset_info["table_name"]
    db_path = get_db_path(data_dir)
    
    # Ensure dataset is loaded
    from nhanes_data_loader import ensure_dataset_loaded
    ensure_dataset_loaded(
        cycle,
        dataset_info["file_prefix"],
        dataset_info["data_type"],
        data_dir,
        db_path
    )
    
    # Build query
    if variables:
        var_list = ", ".join(variables)
    else:
        var_list = "*"
    
    where_clause, params = build_filter_clause(filters)
    
    query = f"SELECT {var_list} FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"
    if limit:
        query += f" LIMIT {limit}"
    
    # Execute query
    conn = sqlite3.connect(str(db_path))
    try:
        df = pd.read_sql_query(query, conn, params=params)
        
        # Convert to list of dictionaries
        results = df.to_dict('records')
        
        # Convert numpy types to native Python types
        for row in results:
            for key, value in row.items():
                if pd.isna(value):
                    row[key] = None
                elif isinstance(value, (pd.Int64Dtype, pd.Float64Dtype)):
                    row[key] = float(value) if pd.isna(value) else int(value) if value == int(value) else float(value)
                elif hasattr(value, 'item'):
                    row[key] = value.item()
        
        return {
            "dataset": dataset_id,
            "cycle": cycle,
            "count": len(results),
            "limit": limit,
            "filters": filters or {},
            "variables": variables or "all",
            "data": results
        }
    finally:
        conn.close()


def get_variable_info(
    dataset_id: str,
    variable: str,
    cycle: str,
    data_dir: Path = None,
    config_path: Path = None
) -> Dict[str, Any]:
    """
    Get information about a specific variable in a dataset.
    
    Args:
        dataset_id: Dataset ID
        variable: Variable name
        cycle: Data cycle
        data_dir: Data directory path
        config_path: Config file path
    
    Returns:
        Variable information dictionary
    """
    if data_dir is None:
        data_dir = Path(__file__).parent / "data"
    if config_path is None:
        config_path = Path(__file__).parent / "config" / "datasets.json"
    
    # Get dataset info
    dataset_info = get_dataset_info(dataset_id, cycle, config_path)
    table_name = dataset_info["table_name"]
    db_path = get_db_path(data_dir)
    
    # Ensure dataset is loaded
    from nhanes_data_loader import ensure_dataset_loaded
    ensure_dataset_loaded(
        cycle,
        dataset_info["file_prefix"],
        dataset_info["data_type"],
        data_dir,
        db_path
    )
    
    # Query variable statistics
    conn = sqlite3.connect(str(db_path))
    try:
        # Check if variable exists
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        if variable not in columns:
            raise ValueError(f"Variable '{variable}' not found in dataset '{dataset_id}'")
        
        # Get basic statistics
        query = f"""
            SELECT 
                COUNT(*) as count,
                COUNT({variable}) as non_null_count,
                MIN({variable}) as min_value,
                MAX({variable}) as max_value,
                AVG({variable}) as mean_value,
                COUNT(DISTINCT {variable}) as distinct_count
            FROM {table_name}
        """
        
        cursor.execute(query)
        stats = cursor.fetchone()
        
        # Get sample values
        sample_query = f"SELECT {variable} FROM {table_name} WHERE {variable} IS NOT NULL LIMIT 10"
        cursor.execute(sample_query)
        sample_values = [row[0] for row in cursor.fetchall()]
        
        return {
            "variable": variable,
            "dataset": dataset_id,
            "cycle": cycle,
            "count": stats[0],
            "non_null_count": stats[1],
            "min_value": stats[2],
            "max_value": stats[3],
            "mean_value": stats[4],
            "distinct_count": stats[5],
            "sample_values": sample_values[:10]
        }
    finally:
        conn.close()


def calculate_percentile(
    variable: str,
    value: float,
    dataset_id: str,
    cycle: str,
    filters: Optional[Dict[str, Any]] = None,
    data_dir: Path = None,
    config_path: Path = None
) -> Dict[str, Any]:
    """
    Calculate percentile rank of a value for a variable.
    
    Args:
        variable: Variable name
        value: Value to calculate percentile for
        dataset_id: Dataset ID
        cycle: Data cycle
        filters: Optional filters to apply
        data_dir: Data directory path
        config_path: Config file path
    
    Returns:
        Dictionary with percentile rank and statistics
    """
    if data_dir is None:
        data_dir = Path(__file__).parent / "data"
    if config_path is None:
        config_path = Path(__file__).parent / "config" / "datasets.json"
    
    # Get dataset info
    dataset_info = get_dataset_info(dataset_id, cycle, config_path)
    table_name = dataset_info["table_name"]
    db_path = get_db_path(data_dir)
    
    # Ensure dataset is loaded
    from nhanes_data_loader import ensure_dataset_loaded
    ensure_dataset_loaded(
        cycle,
        dataset_info["file_prefix"],
        dataset_info["data_type"],
        data_dir,
        db_path
    )
    
    # Build filter clause
    where_clause, params = build_filter_clause(filters)
    base_where = f"{variable} IS NOT NULL"
    if where_clause:
        full_where = f"{base_where} AND {where_clause}"
    else:
        full_where = base_where
        params = []
    
    # Query data
    conn = sqlite3.connect(str(db_path))
    try:
        query = f"SELECT {variable} FROM {table_name} WHERE {full_where}"
        df = pd.read_sql_query(query, conn, params=params)
        
        if len(df) == 0:
            return {
                "variable": variable,
                "value": value,
                "dataset": dataset_id,
                "cycle": cycle,
                "error": "No data available after applying filters"
            }
        
        values = df[variable].dropna().tolist()
        
        # Calculate percentile
        values_sorted = sorted(values)
        count_below = sum(1 for v in values_sorted if v < value)
        count_equal = sum(1 for v in values_sorted if v == value)
        percentile = (count_below + count_equal / 2) / len(values_sorted) * 100
        
        # Calculate statistics
        import numpy as np
        mean_val = np.mean(values_sorted)
        median_val = np.median(values_sorted)
        std_val = np.std(values_sorted)
        
        # Calculate percentiles
        p25 = np.percentile(values_sorted, 25)
        p50 = np.percentile(values_sorted, 50)
        p75 = np.percentile(values_sorted, 75)
        p90 = np.percentile(values_sorted, 90)
        p95 = np.percentile(values_sorted, 95)
        p99 = np.percentile(values_sorted, 99)
        
        return {
            "variable": variable,
            "value": value,
            "dataset": dataset_id,
            "cycle": cycle,
            "percentile": round(percentile, 2),
            "sample_size": len(values_sorted),
            "statistics": {
                "mean": float(mean_val),
                "median": float(median_val),
                "std": float(std_val),
                "min": float(min(values_sorted)),
                "max": float(max(values_sorted)),
                "p25": float(p25),
                "p50": float(p50),
                "p75": float(p75),
                "p90": float(p90),
                "p95": float(p95),
                "p99": float(p99)
            }
        }
    finally:
        conn.close()


def get_demographics_summary(
    cycle: str,
    data_dir: Path = None,
    config_path: Path = None
) -> Dict[str, Any]:
    """
    Get summary statistics for demographics data.
    
    Args:
        cycle: Data cycle
        data_dir: Data directory path
        config_path: Config file path
    
    Returns:
        Demographics summary dictionary
    """
    if data_dir is None:
        data_dir = Path(__file__).parent / "data"
    if config_path is None:
        config_path = Path(__file__).parent / "config" / "datasets.json"
    
    # Query demographics data
    demo_data = query_data(
        "demographics",
        cycle,
        limit=10000,  # Get enough data for summary
        data_dir=data_dir,
        config_path=config_path
    )
    
    if not demo_data.get("data"):
        return {
            "cycle": cycle,
            "error": "No demographics data available"
        }
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(demo_data["data"])
    
    summary = {
        "cycle": cycle,
        "total_records": len(df),
        "age_distribution": {},
        "gender_distribution": {},
        "race_ethnicity_distribution": {}
    }
    
    # Age distribution
    if "RIDAGEYR" in df.columns:
        age_col = df["RIDAGEYR"].dropna()
        summary["age_distribution"] = {
            "mean": float(age_col.mean()),
            "median": float(age_col.median()),
            "min": int(age_col.min()),
            "max": int(age_col.max()),
            "std": float(age_col.std())
        }
    
    # Gender distribution
    if "RIAGENDR" in df.columns:
        gender_counts = df["RIAGENDR"].value_counts().to_dict()
        summary["gender_distribution"] = {
            "1": int(gender_counts.get(1, 0)),  # Male
            "2": int(gender_counts.get(2, 0))   # Female
        }
    
    # Race/ethnicity distribution
    if "RIDRETH3" in df.columns:
        race_counts = df["RIDRETH3"].value_counts().to_dict()
        summary["race_ethnicity_distribution"] = {
            str(k): int(v) for k, v in race_counts.items()
        }
    
    return summary

