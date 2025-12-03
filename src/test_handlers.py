"""
Unit tests for SAP Price Updater handlers.
Tests cover extreme cases and edge conditions.
"""
import unittest
import pandas as pd
import numpy as np
from io import StringIO
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from handlers import (
    normalize_article_code,
    normalize_code_column,
    parse_clipboard_data,
    prepare_sap_from_clipboard,
    merge_data,
    prepare_result,
)


class TestNormalizeArticleCode(unittest.TestCase):
    """Test normalize_article_code function with extreme cases."""
    
    def test_integer_code(self):
        """Test integer codes are converted to string."""
        self.assertEqual(normalize_article_code(123), "123")
        self.assertEqual(normalize_article_code(0), "0")
        self.assertEqual(normalize_article_code(999999999), "999999999")
    
    def test_float_whole_number(self):
        """Test floats that are whole numbers lose the decimal."""
        self.assertEqual(normalize_article_code(123.0), "123")
        self.assertEqual(normalize_article_code(456.00), "456")
        self.assertEqual(normalize_article_code(0.0), "0")
    
    def test_float_with_decimal(self):
        """Test floats with meaningful decimals are preserved."""
        self.assertEqual(normalize_article_code(123.5), "123.5")
        self.assertEqual(normalize_article_code(0.123), "0.123")
    
    def test_string_code(self):
        """Test string codes are returned stripped."""
        self.assertEqual(normalize_article_code("ABC123"), "ABC123")
        self.assertEqual(normalize_article_code("  ABC123  "), "ABC123")
        self.assertEqual(normalize_article_code("A-B-C"), "A-B-C")
    
    def test_string_numeric(self):
        """Test string representations of numbers."""
        self.assertEqual(normalize_article_code("123"), "123")
        self.assertEqual(normalize_article_code("123.0"), "123")
        self.assertEqual(normalize_article_code("  456.00  "), "456")
    
    def test_scientific_notation(self):
        """Test scientific notation is converted to regular number."""
        self.assertEqual(normalize_article_code("1.23E+05"), "123000")
        self.assertEqual(normalize_article_code("1.23e+05"), "123000")
        self.assertEqual(normalize_article_code(1.23e5), "123000")
        self.assertEqual(normalize_article_code("5E+02"), "500")
        self.assertEqual(normalize_article_code("1E+06"), "1000000")
    
    def test_none_value(self):
        """Test None returns empty string."""
        self.assertEqual(normalize_article_code(None), "")
    
    def test_nan_value(self):
        """Test NaN returns empty string."""
        self.assertEqual(normalize_article_code(np.nan), "")
        self.assertEqual(normalize_article_code(float('nan')), "")
    
    def test_pandas_na(self):
        """Test pandas NA returns empty string."""
        self.assertEqual(normalize_article_code(pd.NA), "")
    
    def test_string_nan(self):
        """Test string 'nan' or 'NaN' returns empty string."""
        self.assertEqual(normalize_article_code("nan"), "")
        self.assertEqual(normalize_article_code("NaN"), "")
        self.assertEqual(normalize_article_code("NAN"), "")
    
    def test_string_none(self):
        """Test string 'none' or 'None' returns empty string."""
        self.assertEqual(normalize_article_code("none"), "")
        self.assertEqual(normalize_article_code("None"), "")
    
    def test_empty_string(self):
        """Test empty string returns empty string."""
        self.assertEqual(normalize_article_code(""), "")
        self.assertEqual(normalize_article_code("   "), "")
    
    def test_large_numbers(self):
        """Test large numbers (within safe integer range)."""
        # Note: Very large integers beyond float precision may lose precision
        # This tests realistic article code sizes
        self.assertEqual(normalize_article_code(1234567890), "1234567890")
        self.assertEqual(normalize_article_code("1234567890123456"), "1234567890123456")
    
    def test_negative_numbers(self):
        """Test negative numbers (edge case, unlikely for article codes)."""
        self.assertEqual(normalize_article_code(-123), "-123")
        self.assertEqual(normalize_article_code(-123.0), "-123")
    
    def test_leading_zeros_string(self):
        """Test leading zeros in strings are preserved."""
        self.assertEqual(normalize_article_code("00123"), "123")  # Numeric string loses leading zeros
        self.assertEqual(normalize_article_code("ABC00123"), "ABC00123")  # Non-numeric preserves


class TestNormalizeCodeColumn(unittest.TestCase):
    """Test normalize_code_column function."""
    
    def test_mixed_types_column(self):
        """Test column with mixed types."""
        series = pd.Series([123, 456.0, "789", "ABC", np.nan, None, 1.23e5])
        result = normalize_code_column(series)
        expected = pd.Series(["123", "456", "789", "ABC", "", "", "123000"])
        pd.testing.assert_series_equal(result, expected)
    
    def test_empty_series(self):
        """Test empty series."""
        series = pd.Series([], dtype=object)
        result = normalize_code_column(series)
        self.assertEqual(len(result), 0)
    
    def test_all_nan_series(self):
        """Test series with all NaN values."""
        series = pd.Series([np.nan, None, pd.NA])
        result = normalize_code_column(series)
        expected = pd.Series(["", "", ""])
        pd.testing.assert_series_equal(result, expected)


class TestParseClipboardData(unittest.TestCase):
    """Test parse_clipboard_data function."""
    
    def test_simple_table(self):
        """Test parsing simple tab-separated table."""
        clipboard = "Col1\tCol2\tCol3\nA\tB\tC\n1\t2\t3"
        result = parse_clipboard_data(clipboard)
        self.assertEqual(list(result.columns), ["Col1", "Col2", "Col3"])
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0, 0], "A")
    
    def test_with_numero_articulo(self):
        """Test parsing table with required column."""
        clipboard = "Número de artículo\tDescripción\n123\tProducto A\n456\tProducto B"
        result = parse_clipboard_data(clipboard)
        self.assertIn("Número de artículo", result.columns)
        self.assertEqual(result["Número de artículo"].iloc[0], "123")
    
    def test_empty_clipboard(self):
        """Test empty clipboard raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            parse_clipboard_data("")
        self.assertIn("No hay datos", str(ctx.exception))
    
    def test_only_headers(self):
        """Test clipboard with only headers raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            parse_clipboard_data("Col1\tCol2\tCol3")
        self.assertIn("al menos una fila de encabezados y una fila de datos", str(ctx.exception))
    
    def test_uneven_columns(self):
        """Test table with uneven columns is handled."""
        clipboard = "Col1\tCol2\tCol3\nA\tB"  # Missing third column
        result = parse_clipboard_data(clipboard)
        self.assertEqual(len(result.columns), 3)
        self.assertEqual(result.iloc[0, 2], "")  # Padded with empty string
    
    def test_extra_columns(self):
        """Test table with extra columns is handled."""
        clipboard = "Col1\tCol2\nA\tB\tC\tD"  # Extra columns
        result = parse_clipboard_data(clipboard)
        self.assertEqual(len(result.columns), 2)  # Truncated to header count
    
    def test_whitespace_handling(self):
        """Test whitespace in data is handled."""
        clipboard = "  Col1  \tCol2\n  Value  \tOther"
        result = parse_clipboard_data(clipboard)
        self.assertEqual(result.columns[0], "Col1")  # Headers stripped
        self.assertEqual(result.iloc[0, 0], "  Value  ")  # Data not stripped (user responsibility)
    
    def test_empty_lines_ignored(self):
        """Test empty lines are ignored."""
        clipboard = "Col1\tCol2\nA\tB\n\n\nC\tD\n"
        result = parse_clipboard_data(clipboard)
        self.assertEqual(len(result), 2)  # Only 2 data rows


class TestPrepareSapFromClipboard(unittest.TestCase):
    """Test prepare_sap_from_clipboard function."""
    
    def test_valid_dataframe(self):
        """Test valid DataFrame is processed correctly."""
        df = pd.DataFrame({
            "Número de artículo": [123.0, 456, "789"],
            "Descripción": ["A", "B", "C"]
        })
        result = prepare_sap_from_clipboard(df)
        self.assertEqual(result["Número de artículo"].iloc[0], "123")
        self.assertEqual(result["Número de artículo"].iloc[1], "456")
    
    def test_missing_column(self):
        """Test missing required column raises ValueError."""
        df = pd.DataFrame({
            "Articulo": [123, 456],  # Wrong column name
            "Descripción": ["A", "B"]
        })
        with self.assertRaises(ValueError) as ctx:
            prepare_sap_from_clipboard(df)
        self.assertIn("Número de artículo", str(ctx.exception))


class TestMergeData(unittest.TestCase):
    """Test merge_data function."""
    
    def test_exact_match(self):
        """Test exact matches between SAP and Cost."""
        df_sap = pd.DataFrame({"Número de artículo": ["123", "456", "789"]})
        df_cost = pd.DataFrame({
            "Artículo": ["123", "456", "789"],
            "Manufactura FC": [10.5, 20.0, 30.0]
        })
        result = merge_data(df_sap, df_cost)
        self.assertEqual(len(result), 3)
        self.assertEqual(result["Manufactura FC"].iloc[0], 10.5)
    
    def test_type_mismatch_resolved(self):
        """Test int vs float vs string matches are resolved."""
        df_sap = pd.DataFrame({"Número de artículo": [123, 456.0, "789"]})
        df_cost = pd.DataFrame({
            "Artículo": ["123", 456, 789.0],
            "Manufactura FC": [10, 20, 30]
        })
        result = merge_data(df_sap, df_cost)
        self.assertEqual(len(result), 3)
        # All should match despite type differences
        self.assertFalse(result["Manufactura FC"].isna().any())
    
    def test_scientific_notation_match(self):
        """Test scientific notation matches regular number."""
        df_sap = pd.DataFrame({"Número de artículo": [1.23e5]})  # 123000
        df_cost = pd.DataFrame({
            "Artículo": ["123000"],
            "Manufactura FC": [100]
        })
        result = merge_data(df_sap, df_cost)
        self.assertEqual(result["Manufactura FC"].iloc[0], 100)
    
    def test_no_match_returns_nan(self):
        """Test non-matching codes get NaN for Manufactura FC."""
        df_sap = pd.DataFrame({"Número de artículo": ["999"]})
        df_cost = pd.DataFrame({
            "Artículo": ["123"],
            "Manufactura FC": [10]
        })
        result = merge_data(df_sap, df_cost)
        self.assertTrue(pd.isna(result["Manufactura FC"].iloc[0]))
    
    def test_preserves_sap_order(self):
        """Test SAP order is preserved in result."""
        df_sap = pd.DataFrame({"Número de artículo": ["C", "A", "B"]})
        df_cost = pd.DataFrame({
            "Artículo": ["A", "B", "C"],
            "Manufactura FC": [1, 2, 3]
        })
        result = merge_data(df_sap, df_cost)
        self.assertEqual(result["Número de artículo"].tolist(), ["C", "A", "B"])
        self.assertEqual(result["Manufactura FC"].tolist(), [3, 1, 2])
    
    def test_duplicate_codes_in_cost(self):
        """Test duplicate codes in cost file (first match used by default)."""
        df_sap = pd.DataFrame({"Número de artículo": ["123"]})
        df_cost = pd.DataFrame({
            "Artículo": ["123", "123"],
            "Manufactura FC": [10, 20]  # Duplicate code with different values
        })
        result = merge_data(df_sap, df_cost)
        # Merge will create two rows due to duplicates
        self.assertEqual(len(result), 2)
    
    def test_empty_sap(self):
        """Test empty SAP DataFrame."""
        df_sap = pd.DataFrame({"Número de artículo": []})
        df_cost = pd.DataFrame({
            "Artículo": ["123"],
            "Manufactura FC": [10]
        })
        result = merge_data(df_sap, df_cost)
        self.assertEqual(len(result), 0)
    
    def test_empty_cost(self):
        """Test empty Cost DataFrame."""
        df_sap = pd.DataFrame({"Número de artículo": ["123"]})
        df_cost = pd.DataFrame({
            "Artículo": [],
            "Manufactura FC": []
        })
        result = merge_data(df_sap, df_cost)
        self.assertEqual(len(result), 1)
        self.assertTrue(pd.isna(result["Manufactura FC"].iloc[0]))


class TestPrepareResult(unittest.TestCase):
    """Test prepare_result function."""
    
    def test_numeric_conversion(self):
        """Test Manufactura FC is converted to numeric."""
        df = pd.DataFrame({
            "Número de artículo": ["123", "456"],
            "Manufactura FC": ["10.5", "20"]
        })
        result = prepare_result(df)
        self.assertEqual(result["Manufactura FC"].dtype, float)
        self.assertEqual(result["Manufactura FC"].iloc[0], 10.5)
    
    def test_nan_filled_with_zero(self):
        """Test NaN values are filled with 0."""
        df = pd.DataFrame({
            "Número de artículo": ["123", "456"],
            "Manufactura FC": [10, np.nan]
        })
        result = prepare_result(df)
        self.assertEqual(result["Manufactura FC"].iloc[1], 0)
    
    def test_invalid_string_becomes_zero(self):
        """Test invalid strings become 0."""
        df = pd.DataFrame({
            "Número de artículo": ["123", "456"],
            "Manufactura FC": [10, "invalid"]
        })
        result = prepare_result(df)
        self.assertEqual(result["Manufactura FC"].iloc[1], 0)
    
    def test_only_required_columns(self):
        """Test result only contains required columns."""
        df = pd.DataFrame({
            "Número de artículo": ["123"],
            "Manufactura FC": [10],
            "Extra Column": ["ignored"]
        })
        result = prepare_result(df)
        self.assertEqual(list(result.columns), ["Número de artículo", "Manufactura FC"])
    
    def test_negative_values_preserved(self):
        """Test negative values are preserved."""
        df = pd.DataFrame({
            "Número de artículo": ["123"],
            "Manufactura FC": [-10.5]
        })
        result = prepare_result(df)
        self.assertEqual(result["Manufactura FC"].iloc[0], -10.5)
    
    def test_zero_values(self):
        """Test zero values are preserved."""
        df = pd.DataFrame({
            "Número de artículo": ["123"],
            "Manufactura FC": [0]
        })
        result = prepare_result(df)
        self.assertEqual(result["Manufactura FC"].iloc[0], 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the full pipeline."""
    
    def test_full_pipeline_with_type_mismatches(self):
        """Test full pipeline handles type mismatches correctly."""
        # Simulate SAP data with mixed types
        df_sap = pd.DataFrame({
            "Número de artículo": [123, 456.0, "789", 1.23e5, np.nan]
        })
        
        # Simulate Cost data with different types for same codes
        df_cost = pd.DataFrame({
            "Artículo": ["123", 456, 789.0, "123000", "999"],
            "Manufactura FC": [10, 20, 30, 40, 50]
        })
        
        merged = merge_data(df_sap, df_cost)
        result = prepare_result(merged)
        
        # Check all matches are correct
        self.assertEqual(result["Manufactura FC"].iloc[0], 10)   # 123 matches "123"
        self.assertEqual(result["Manufactura FC"].iloc[1], 20)   # 456.0 matches 456
        self.assertEqual(result["Manufactura FC"].iloc[2], 30)   # "789" matches 789.0
        self.assertEqual(result["Manufactura FC"].iloc[3], 40)   # 1.23e5 matches "123000"
        self.assertEqual(result["Manufactura FC"].iloc[4], 0)    # NaN doesn't match, becomes 0


if __name__ == "__main__":
    unittest.main(verbosity=2)
