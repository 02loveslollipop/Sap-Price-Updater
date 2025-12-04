"""
Data processing handlers for SAP Price Updater.
All data transformation logic is separated here for testability.
"""
import pandas as pd
import numpy as np
import re
from typing import Optional, Tuple, List


def normalize_article_code(value) -> str:
    """
    Normalize an article code to a clean string format.
    Handles floats (123.0 -> "123"), ints, strings, scientific notation, NaN, None.
    
    Args:
        value: The article code in any format (float, int, str, None, NaN)
    
    Returns:
        A normalized string representation of the code, stripped of whitespace.
        Returns empty string for None/NaN values.
    """
    # Handle None and NaN
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return ""
    if pd.isna(value):
        return ""
    
    # Convert to string first
    str_value = str(value).strip()
    
    # Handle empty strings
    if str_value == "" or str_value.lower() == "nan" or str_value.lower() == "none":
        return ""
    
    # Handle scientific notation (e.g., "1.23E+05" -> "123000")
    if 'e' in str_value.lower() or 'E' in str_value:
        try:
            # Convert scientific notation to regular number
            float_val = float(str_value)
            # If it's effectively an integer, convert to int first to remove decimal
            if float_val == int(float_val):
                return str(int(float_val))
            else:
                return str(float_val)
        except ValueError:
            pass
    
    # Handle float strings like "123.0" or "456.00"
    try:
        float_val = float(str_value)
        # Check if it's effectively an integer (no meaningful decimal part)
        if float_val == int(float_val):
            return str(int(float_val))
        else:
            # Keep the decimal if it's meaningful
            return str(float_val)
    except ValueError:
        # Not a number, return as-is (stripped)
        return str_value


def normalize_code_column(series: pd.Series) -> pd.Series:
    """
    Apply normalize_article_code to an entire pandas Series.
    
    Args:
        series: A pandas Series containing article codes
    
    Returns:
        A new Series with all codes normalized to strings
    """
    return series.apply(normalize_article_code)


def get_excel_columns(file_path: str, sheet_name: str = None) -> List[str]:
    """
    Get the column names from an Excel file without loading all data.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet (optional, uses first sheet if not specified)
    
    Returns:
        List of column names
    """
    if sheet_name:
        df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=0)
    else:
        df = pd.read_excel(file_path, nrows=0)
    return list(df.columns)


def load_cost_file(file_path: str, article_column: str = 'Artículo', 
                   value_column: str = 'Manufactura FC', 
                   sheet_name: str = 'COSTO PROD') -> Tuple[pd.DataFrame, str, str]:
    """
    Load the cost file and prepare it for processing.
    
    Args:
        file_path: Path to the Excel file
        article_column: Name of the column containing article codes
        value_column: Name of the column containing the value to extract
        sheet_name: Name of the sheet to load
    
    Returns:
        Tuple of (DataFrame with normalized article column, article_column name, value_column name)
    
    Raises:
        ValueError: If required columns are missing
        FileNotFoundError: If file doesn't exist
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Validate required columns
    if article_column not in df.columns:
        raise ValueError(f"Column '{article_column}' not found in cost file.")
    if value_column not in df.columns:
        raise ValueError(f"Column '{value_column}' not found in cost file.")
    
    # Normalize the article code column
    df[article_column] = normalize_code_column(df[article_column])
    
    return df, article_column, value_column


def load_sap_file(file_path: str, article_column: str = 'Número de artículo') -> Tuple[pd.DataFrame, str]:
    """
    Load the SAP file and prepare it for processing.
    
    Args:
        file_path: Path to the Excel file
        article_column: Name of the column containing article codes
    
    Returns:
        Tuple of (DataFrame with normalized article column, article_column name)
    
    Raises:
        ValueError: If required columns are missing
        FileNotFoundError: If file doesn't exist
    """
    df = pd.read_excel(file_path)
    
    # Validate required columns
    if article_column not in df.columns:
        raise ValueError(f"Column '{article_column}' not found in SAP file.")
    
    # Normalize the article code column
    df[article_column] = normalize_code_column(df[article_column])
    
    return df, article_column


def parse_clipboard_data(clipboard_text: str) -> pd.DataFrame:
    """
    Parse tab-separated data from clipboard into a DataFrame.
    This handles data pasted from Excel or similar spreadsheet applications.
    
    Args:
        clipboard_text: Raw text from clipboard (tab-separated values)
    
    Returns:
        DataFrame with the parsed data
    
    Raises:
        ValueError: If data cannot be parsed or is empty
    """
    if not clipboard_text or not clipboard_text.strip():
        raise ValueError("No hay datos en el portapapeles.")
    
    # Split into lines
    lines = clipboard_text.strip().split('\n')
    
    if len(lines) < 2:
        raise ValueError("Los datos deben tener al menos una fila de encabezados y una fila de datos.")
    
    # Parse header (first line)
    headers = lines[0].split('\t')
    headers = [h.strip() for h in headers]
    
    # Parse data rows
    data_rows = []
    for line in lines[1:]:
        if line.strip():  # Skip empty lines
            row = line.split('\t')
            # Pad row if it has fewer columns than headers
            while len(row) < len(headers):
                row.append('')
            # Truncate if it has more columns
            row = row[:len(headers)]
            data_rows.append(row)
    
    if not data_rows:
        raise ValueError("No se encontraron filas de datos.")
    
    df = pd.DataFrame(data_rows, columns=headers)
    
    return df


def prepare_sap_from_clipboard(df: pd.DataFrame, article_column: str = 'Número de artículo') -> Tuple[pd.DataFrame, str]:
    """
    Prepare a DataFrame from clipboard to be used as SAP data.
    Normalizes the article code column.
    
    Args:
        df: DataFrame parsed from clipboard
        article_column: Name of the column containing article codes
    
    Returns:
        Tuple of (DataFrame ready to be used as SAP data, article_column name)
    
    Raises:
        ValueError: If required column is missing
    """
    if article_column not in df.columns:
        raise ValueError(f"Column '{article_column}' not found in pasted data.")
    
    # Normalize the article code column
    df[article_column] = normalize_code_column(df[article_column])
    
    return df, article_column


def merge_data(df_sap: pd.DataFrame, df_cost: pd.DataFrame,
               sap_article_col: str = 'Número de artículo',
               cost_article_col: str = 'Artículo',
               value_col: str = 'Manufactura FC') -> Tuple[pd.DataFrame, str, str]:
    """
    Merge SAP data with Cost data, preserving SAP order.
    Uses left join to keep all SAP rows.
    
    Args:
        df_sap: DataFrame with SAP data
        df_cost: DataFrame with Cost data
        sap_article_col: Name of the article column in SAP data
        cost_article_col: Name of the article column in Cost data
        value_col: Name of the value column to extract from Cost data
    
    Returns:
        Tuple of (Merged DataFrame, sap_article_col name, value_col name)
    """
    # Ensure both columns are normalized strings before merging
    df_sap = df_sap.copy()
    df_cost = df_cost.copy()
    
    df_sap[sap_article_col] = normalize_code_column(df_sap[sap_article_col])
    df_cost[cost_article_col] = normalize_code_column(df_cost[cost_article_col])
    
    # Remove duplicate article codes from cost file (keep first occurrence)
    # This prevents the merge from creating extra rows when cost file has duplicates
    df_cost_unique = df_cost[[cost_article_col, value_col]].drop_duplicates(
        subset=[cost_article_col], 
        keep='first'
    )
    
    df_merged = pd.merge(
        df_sap,
        df_cost_unique,
        left_on=sap_article_col,
        right_on=cost_article_col,
        how='left'
    )
    
    return df_merged, sap_article_col, value_col


def prepare_result(df_merged: pd.DataFrame, 
                   article_col: str = 'Número de artículo',
                   value_col: str = 'Manufactura FC') -> pd.DataFrame:
    """
    Prepare the final result DataFrame.
    Converts value column to numeric, fills NaN with 0.
    
    Args:
        df_merged: Merged DataFrame from merge_data()
        article_col: Name of the article column
        value_col: Name of the value column
    
    Returns:
        DataFrame with article and value columns,
        where value is numeric with 0 for missing values.
    """
    result = df_merged[[article_col, value_col]].copy()
    
    # Convert to numeric, coercing errors to NaN
    result[value_col] = pd.to_numeric(result[value_col], errors='coerce')
    
    # Fill NaN with 0
    result[value_col] = result[value_col].fillna(0)
    
    return result


def process_files(cost_path: str, sap_path: str,
                  cost_article_col: str = 'Artículo',
                  cost_value_col: str = 'Manufactura FC',
                  sap_article_col: str = 'Número de artículo') -> pd.DataFrame:
    """
    Full processing pipeline for file inputs.
    
    Args:
        cost_path: Path to the cost Excel file
        sap_path: Path to the SAP Excel file
        cost_article_col: Name of article column in cost file
        cost_value_col: Name of value column in cost file
        sap_article_col: Name of article column in SAP file
    
    Returns:
        Result DataFrame with matched values
    """
    df_cost, _, _ = load_cost_file(cost_path, cost_article_col, cost_value_col)
    df_sap, _ = load_sap_file(sap_path, sap_article_col)
    df_merged, article_col, value_col = merge_data(df_sap, df_cost, sap_article_col, cost_article_col, cost_value_col)
    result = prepare_result(df_merged, article_col, value_col)
    return result


def process_with_clipboard_sap(cost_path: str, sap_df: pd.DataFrame,
                                cost_article_col: str = 'Artículo',
                                cost_value_col: str = 'Manufactura FC',
                                sap_article_col: str = 'Número de artículo') -> pd.DataFrame:
    """
    Full processing pipeline using clipboard data for SAP.
    
    Args:
        cost_path: Path to the cost Excel file
        sap_df: DataFrame from clipboard containing SAP data
        cost_article_col: Name of article column in cost file
        cost_value_col: Name of value column in cost file
        sap_article_col: Name of article column in SAP data
    
    Returns:
        Result DataFrame with matched values
    """
    df_cost, _, _ = load_cost_file(cost_path, cost_article_col, cost_value_col)
    sap_df, _ = prepare_sap_from_clipboard(sap_df, sap_article_col)
    df_merged, article_col, value_col = merge_data(sap_df, df_cost, sap_article_col, cost_article_col, cost_value_col)
    result = prepare_result(df_merged, article_col, value_col)
    return result

