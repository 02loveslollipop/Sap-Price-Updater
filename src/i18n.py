"""
Internationalization (i18n) module for SAP Price Updater.
Supports English and Spanish.
"""

TRANSLATIONS = {
    'en': {
        # Window titles
        'app_title': 'SAP Price Updater',
        'paste_dialog_title': 'Paste SAP Data from Clipboard',
        'column_config_title': 'Configure Columns',
        
        # Main UI labels
        'file_selection': 'File Selection',
        'cost_file_label': 'Cost File (COSTO STD PRODUCTOS):',
        'sap_file_label': 'SAP File (or paste from clipboard):',
        'results': 'Results',
        'article_sap': 'Article (SAP)',
        'manufacturing_cost': 'Manufacturing Cost',
        
        # Buttons
        'browse': 'Browse',
        'paste': 'Paste',
        'process_files': 'Process Files',
        'copy_to_clipboard': 'Copy Manufacturing Cost to Clipboard',
        'configure_columns': 'Configure Columns',
        'preview': 'Preview',
        'use_data': 'Use this Data',
        'cancel': 'Cancel',
        'apply': 'Apply',
        
        # Paste dialog
        'paste_instructions': "Paste the SAP table data (Ctrl+V) in the text area.\nData must be tab-separated (copied from Excel).",
        'pasted_data': 'Pasted Data',
        'preview_label': 'Preview',
        
        # Column configuration dialog
        'column_config_instructions': 'Select the columns to use for matching and value extraction:',
        'cost_article_column': 'Cost File - Article Code Column:',
        'cost_value_column': 'Cost File - Value Column:',
        'sap_article_column': 'SAP File - Article Code Column:',
        'load_files_first': 'Load both files first to configure columns.',
        
        # Status messages
        'rows_detected': '{count} rows detected.',
        'column_found': "Column '{column}' found.",
        'column_not_found': "Column '{column}' not found. Please verify the data.",
        'data_loaded_clipboard': '✓ SAP data loaded from clipboard ({count} rows)',
        'columns_configured': '✓ Columns configured: Cost[{cost_col}→{value_col}], SAP[{sap_col}]',
        
        # Error messages
        'missing_cost_file': 'Please select the cost file.',
        'missing_sap_data': 'Please select a SAP file or paste data from clipboard.',
        'missing_file': 'Missing File',
        'missing_sap': 'Missing SAP Data',
        'validation_error': 'Validation Error',
        'file_not_found': 'File Not Found',
        'error': 'Error',
        'error_occurred': 'An error occurred:\n{error}',
        'no_data': 'No Data',
        'process_first': 'Please process the files first.',
        'copied': 'Copied',
        'copy_success': 'Manufacturing Cost values copied to clipboard in SAP file order.',
        'copy_error': 'Error copying:\n{error}',
        'invalid_data': 'Invalid Data',
        'paste_valid_data': "Please paste valid data.",
        'success': 'Success',
        'processed_rows': '{count} rows processed.',
        'no_clipboard_data': 'No data in clipboard.',
        'min_rows_required': 'Data must have at least one header row and one data row.',
        'no_data_rows': 'No data rows found.',
        'column_not_found_file': "Column '{column}' not found in the file.",
        
        # Language selector
        'language': 'Language',
        'english': 'English',
        'spanish': 'Spanish',
    },
    'es': {
        # Window titles
        'app_title': 'SAP Price Updater',
        'paste_dialog_title': 'Pegar Datos SAP desde Portapapeles',
        'column_config_title': 'Configurar Columnas',
        
        # Main UI labels
        'file_selection': 'Selección de Archivos',
        'cost_file_label': 'Archivo de Costos (COSTO STD PRODUCTOS):',
        'sap_file_label': 'Archivo SAP (o pegar desde portapapeles):',
        'results': 'Resultados',
        'article_sap': 'Artículo (SAP)',
        'manufacturing_cost': 'Manufactura FC',
        
        # Buttons
        'browse': 'Examinar',
        'paste': 'Pegar',
        'process_files': 'Procesar Archivos',
        'copy_to_clipboard': 'Copiar Manufactura FC al Portapapeles',
        'configure_columns': 'Configurar Columnas',
        'preview': 'Vista Previa',
        'use_data': 'Usar estos Datos',
        'cancel': 'Cancelar',
        'apply': 'Aplicar',
        
        # Paste dialog
        'paste_instructions': "Pegue los datos de la tabla SAP (Ctrl+V) en el área de texto.\nLos datos deben estar separados por tabulaciones (copiados desde Excel).",
        'pasted_data': 'Datos Pegados',
        'preview_label': 'Vista Previa',
        
        # Column configuration dialog
        'column_config_instructions': 'Seleccione las columnas a usar para el emparejamiento y extracción de valores:',
        'cost_article_column': 'Archivo de Costos - Columna de Código:',
        'cost_value_column': 'Archivo de Costos - Columna de Valor:',
        'sap_article_column': 'Archivo SAP - Columna de Código:',
        'load_files_first': 'Cargue ambos archivos primero para configurar las columnas.',
        
        # Status messages
        'rows_detected': '{count} filas detectadas.',
        'column_found': "Columna '{column}' encontrada.",
        'column_not_found': "Columna '{column}' no encontrada. Verifique los datos.",
        'data_loaded_clipboard': '✓ Datos SAP cargados desde portapapeles ({count} filas)',
        'columns_configured': '✓ Columnas configuradas: Costos[{cost_col}→{value_col}], SAP[{sap_col}]',
        
        # Error messages
        'missing_cost_file': 'Por favor seleccione el archivo de costos.',
        'missing_sap_data': 'Por favor seleccione un archivo SAP o pegue datos desde el portapapeles.',
        'missing_file': 'Archivo Faltante',
        'missing_sap': 'Datos SAP Faltantes',
        'validation_error': 'Error de Validación',
        'file_not_found': 'Archivo No Encontrado',
        'error': 'Error',
        'error_occurred': 'Ocurrió un error:\n{error}',
        'no_data': 'Sin Datos',
        'process_first': 'Por favor procese los archivos primero.',
        'copied': 'Copiado',
        'copy_success': 'Valores de Manufactura FC copiados al portapapeles en el orden del archivo SAP.',
        'copy_error': 'Error al copiar:\n{error}',
        'invalid_data': 'Datos Inválidos',
        'paste_valid_data': "Por favor pegue datos válidos.",
        'success': 'Éxito',
        'processed_rows': 'Se procesaron {count} filas.',
        'no_clipboard_data': 'No hay datos en el portapapeles.',
        'min_rows_required': 'Los datos deben tener al menos una fila de encabezados y una fila de datos.',
        'no_data_rows': 'No se encontraron filas de datos.',
        'column_not_found_file': "La columna '{column}' no se encontró en el archivo.",
        
        # Language selector
        'language': 'Idioma',
        'english': 'Inglés',
        'spanish': 'Español',
    }
}


class I18n:
    """Internationalization helper class."""
    
    def __init__(self, language: str = 'es'):
        self.language = language
        self._translations = TRANSLATIONS.get(language, TRANSLATIONS['es'])
    
    def set_language(self, language: str):
        """Change the current language."""
        self.language = language
        self._translations = TRANSLATIONS.get(language, TRANSLATIONS['es'])
    
    def get(self, key: str, **kwargs) -> str:
        """Get a translated string, with optional format arguments."""
        text = self._translations.get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text
    
    def __call__(self, key: str, **kwargs) -> str:
        """Shorthand for get()."""
        return self.get(key, **kwargs)


# Global instance
i18n = I18n('es')
