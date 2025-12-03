"""
Data processing handlers for SAP Price Updater.
All data transformation logic is separated here for testability.
"""
import pandas as pd
import numpy as np
import re
from typing import Optional, Tuple


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


def load_cost_file(file_path: str, sheet_name: str = 'COSTO PROD') -> pd.DataFrame:
    """
    Load the cost file and prepare it for processing.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet to load
    
    Returns:
        DataFrame with normalized 'Artículo' column
    
    Raises:
        ValueError: If required columns are missing
        FileNotFoundError: If file doesn't exist
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Validate required columns
    if 'Artículo' not in df.columns:
        raise ValueError("La columna 'Artículo' no se encontró en el archivo de costos.")
    if 'Manufactura FC' not in df.columns:
        raise ValueError("La columna 'Manufactura FC' no se encontró en el archivo de costos.")
    
    # Normalize the article code column
    df['Artículo'] = normalize_code_column(df['Artículo'])
    
    return df


def load_sap_file(file_path: str) -> pd.DataFrame:
    """
    Load the SAP file and prepare it for processing.
    
    Args:
        file_path: Path to the Excel file
    
    Returns:
        DataFrame with normalized 'Número de artículo' column
    
    Raises:
        ValueError: If required columns are missing
        FileNotFoundError: If file doesn't exist
    """
    df = pd.read_excel(file_path)
    
    # Validate required columns
    if 'Número de artículo' not in df.columns:
        raise ValueError("La columna 'Número de artículo' no se encontró en el archivo SAP.")
    
    # Normalize the article code column
    df['Número de artículo'] = normalize_code_column(df['Número de artículo'])
    
    return df


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


def prepare_sap_from_clipboard(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare a DataFrame from clipboard to be used as SAP data.
    Normalizes the article code column.
    
    Args:
        df: DataFrame parsed from clipboard
    
    Returns:
        DataFrame ready to be used as SAP data
    
    Raises:
        ValueError: If required column is missing
    """
    if 'Número de artículo' not in df.columns:
        raise ValueError("La columna 'Número de artículo' no se encontró en los datos pegados.")
    
    # Normalize the article code column
    df['Número de artículo'] = normalize_code_column(df['Número de artículo'])
    
    return df


def merge_data(df_sap: pd.DataFrame, df_cost: pd.DataFrame) -> pd.DataFrame:
    """
    Merge SAP data with Cost data, preserving SAP order.
    Uses left join to keep all SAP rows.
    
    Args:
        df_sap: DataFrame with SAP data (must have 'Número de artículo' column)
        df_cost: DataFrame with Cost data (must have 'Artículo' and 'Manufactura FC' columns)
    
    Returns:
        Merged DataFrame with SAP article numbers and matched Manufactura FC values
    """
    # Ensure both columns are normalized strings before merging
    df_sap = df_sap.copy()
    df_cost = df_cost.copy()
    
    df_sap['Número de artículo'] = normalize_code_column(df_sap['Número de artículo'])
    df_cost['Artículo'] = normalize_code_column(df_cost['Artículo'])
    
    df_merged = pd.merge(
        df_sap,
        df_cost[['Artículo', 'Manufactura FC']],
        left_on='Número de artículo',
        right_on='Artículo',
        how='left'
    )
    
    return df_merged


def prepare_result(df_merged: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the final result DataFrame.
    Converts Manufactura FC to numeric, fills NaN with 0.
    
    Args:
        df_merged: Merged DataFrame from merge_data()
    
    Returns:
        DataFrame with 'Número de artículo' and 'Manufactura FC' columns,
        where Manufactura FC is numeric with 0 for missing values.
    """
    result = df_merged[['Número de artículo', 'Manufactura FC']].copy()
    
    # Convert to numeric, coercing errors to NaN
    result['Manufactura FC'] = pd.to_numeric(result['Manufactura FC'], errors='coerce')
    
    # Fill NaN with 0
    result['Manufactura FC'] = result['Manufactura FC'].fillna(0)
    
    return result


def process_files(cost_path: str, sap_path: str) -> pd.DataFrame:
    """
    Full processing pipeline for file inputs.
    
    Args:
        cost_path: Path to the cost Excel file
        sap_path: Path to the SAP Excel file
    
    Returns:
        Result DataFrame with matched Manufactura FC values
    """
    df_cost = load_cost_file(cost_path)
    df_sap = load_sap_file(sap_path)
    df_merged = merge_data(df_sap, df_cost)
    result = prepare_result(df_merged)
    return result


def process_with_clipboard_sap(cost_path: str, sap_df: pd.DataFrame) -> pd.DataFrame:
    """
    Full processing pipeline using clipboard data for SAP.
    
    Args:
        cost_path: Path to the cost Excel file
        sap_df: DataFrame from clipboard containing SAP data
    
    Returns:
        Result DataFrame with matched Manufactura FC values
    """
    df_cost = load_cost_file(cost_path)
    sap_df = prepare_sap_from_clipboard(sap_df)
    df_merged = merge_data(sap_df, df_cost)
    result = prepare_result(df_merged)
    return result
