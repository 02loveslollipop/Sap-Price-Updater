import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os

from handlers import (
    normalize_code_column,
    load_cost_file,
    load_sap_file,
    parse_clipboard_data,
    prepare_sap_from_clipboard,
    merge_data,
    prepare_result,
    get_excel_columns,
)
from i18n import i18n


class ColumnConfigDialog:
    """Dialog for configuring which columns to use for matching."""
    
    def __init__(self, parent, cost_columns, sap_columns, current_config):
        self.parent = parent
        self.cost_columns = cost_columns
        self.sap_columns = sap_columns
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(i18n('column_config_title'))
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Variables with current values
        self.cost_article_var = tk.StringVar(value=current_config.get('cost_article', ''))
        self.cost_value_var = tk.StringVar(value=current_config.get('cost_value', ''))
        self.sap_article_var = tk.StringVar(value=current_config.get('sap_article', ''))
        
        self.create_widgets()
        
    def create_widgets(self):
        # Instructions
        instructions = ttk.Label(
            self.dialog,
            text=i18n('column_config_instructions'),
            padding=(10, 10),
            wraplength=480
        )
        instructions.pack(fill="x")
        
        # Configuration frame
        config_frame = ttk.Frame(self.dialog, padding=(20, 10))
        config_frame.pack(fill="both", expand=True)
        
        # Cost file - Article column
        ttk.Label(config_frame, text=i18n('cost_article_column')).grid(
            row=0, column=0, sticky="w", pady=5
        )
        cost_article_combo = ttk.Combobox(
            config_frame, 
            textvariable=self.cost_article_var,
            values=self.cost_columns,
            state="readonly",
            width=30
        )
        cost_article_combo.grid(row=0, column=1, sticky="ew", pady=5, padx=10)
        
        # Cost file - Value column
        ttk.Label(config_frame, text=i18n('cost_value_column')).grid(
            row=1, column=0, sticky="w", pady=5
        )
        cost_value_combo = ttk.Combobox(
            config_frame,
            textvariable=self.cost_value_var,
            values=self.cost_columns,
            state="readonly",
            width=30
        )
        cost_value_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=10)
        
        # SAP file - Article column
        ttk.Label(config_frame, text=i18n('sap_article_column')).grid(
            row=2, column=0, sticky="w", pady=5
        )
        sap_article_combo = ttk.Combobox(
            config_frame,
            textvariable=self.sap_article_var,
            values=self.sap_columns,
            state="readonly",
            width=30
        )
        sap_article_combo.grid(row=2, column=1, sticky="ew", pady=5, padx=10)
        
        config_frame.columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog, padding=(10, 10))
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text=i18n('apply'), command=self.apply_config).pack(side="right", padx=5)
        ttk.Button(btn_frame, text=i18n('cancel'), command=self.cancel).pack(side="right", padx=5)
    
    def apply_config(self):
        """Apply the configuration and close dialog."""
        cost_article = self.cost_article_var.get()
        cost_value = self.cost_value_var.get()
        sap_article = self.sap_article_var.get()
        
        if not cost_article or not cost_value or not sap_article:
            messagebox.showwarning(
                i18n('validation_error'),
                i18n('paste_valid_data')
            )
            return
        
        self.result = {
            'cost_article': cost_article,
            'cost_value': cost_value,
            'sap_article': sap_article
        }
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel and close dialog."""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and wait for result."""
        self.dialog.wait_window()
        return self.result


class ClipboardPasteDialog:
    """Dialog for pasting SAP data from clipboard."""
    
    def __init__(self, parent):
        self.parent = parent
        self.result_df = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(i18n('paste_dialog_title'))
        self.dialog.geometry("800x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Instructions
        instructions = ttk.Label(
            self.dialog,
            text=i18n('paste_instructions'),
            padding=(10, 10)
        )
        instructions.pack(fill="x")
        
        # Text area for pasting
        text_frame = ttk.LabelFrame(self.dialog, text=i18n('pasted_data'), padding=(10, 10))
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.text_area = tk.Text(text_frame, height=10, width=80)
        self.text_area.pack(side="left", fill="both", expand=True)
        
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=text_scrollbar.set)
        text_scrollbar.pack(side="right", fill="y")
        
        # Bind paste event to auto-preview
        self.text_area.bind("<<Paste>>", lambda e: self.dialog.after(100, self.preview_data))
        self.text_area.bind("<KeyRelease>", lambda e: self.dialog.after(100, self.preview_data))
        
        # Preview button
        btn_frame = ttk.Frame(self.dialog, padding=(10, 5))
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text=i18n('preview'), command=self.preview_data).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=i18n('use_data'), command=self.accept_data).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=i18n('cancel'), command=self.cancel).pack(side="left", padx=5)
        
        # Status label
        self.status_label = ttk.Label(self.dialog, text="", padding=(10, 5))
        self.status_label.pack(fill="x")
        
        # Preview table
        preview_frame = ttk.LabelFrame(self.dialog, text=i18n('preview_label'), padding=(10, 10))
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.preview_tree = ttk.Treeview(preview_frame, show="headings")
        self.preview_tree.pack(side="left", fill="both", expand=True)
        
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=preview_scrollbar.set)
        preview_scrollbar.pack(side="right", fill="y")
    
    def preview_data(self):
        """Parse and preview the pasted data."""
        text = self.text_area.get("1.0", tk.END)
        
        try:
            df = parse_clipboard_data(text)
            
            # Clear current preview
            self.preview_tree.delete(*self.preview_tree.get_children())
            
            # Configure columns
            self.preview_tree["columns"] = list(df.columns)
            for col in df.columns:
                self.preview_tree.heading(col, text=col)
                self.preview_tree.column(col, width=100)
            
            # Add rows (limit to first 20 for preview)
            for idx, row in df.head(20).iterrows():
                self.preview_tree.insert("", "end", values=list(row))
            
            # Just show success - column selection is done in config dialog
            self.status_label.config(
                text=f"✓ {i18n('rows_detected', count=len(df))}",
                foreground="green"
            )
            self._preview_df = df
                
        except ValueError as e:
            self.status_label.config(text=f"✗ {i18n('error')}: {str(e)}", foreground="red")
            self._preview_df = None
        except Exception as e:
            self.status_label.config(text=f"✗ {i18n('error')}: {str(e)}", foreground="red")
            self._preview_df = None
    
    def accept_data(self):
        """Accept the parsed data and close dialog."""
        if hasattr(self, '_preview_df') and self._preview_df is not None:
            self.result_df = self._preview_df
            self.dialog.destroy()
        else:
            messagebox.showwarning(
                i18n('invalid_data'),
                i18n('paste_valid_data')
            )
    
    def cancel(self):
        """Cancel and close dialog."""
        self.result_df = None
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and wait for result."""
        self.dialog.wait_window()
        return self.result_df


class SapPriceUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(i18n('app_title'))
        self.root.geometry("900x650")

        # Variables
        self.cost_file_path = tk.StringVar()
        self.sap_file_path = tk.StringVar()
        self.df_result = None
        self.sap_from_clipboard = None  # Store SAP data from clipboard
        
        # Column configuration (defaults)
        self.column_config = {
            'cost_article': 'Artículo',
            'cost_value': 'Manufactura FC',
            'sap_article': 'Número de artículo'
        }
        
        # Store loaded columns
        self.cost_columns = []
        self.sap_columns = []

        # Layout
        self.create_widgets()

    def create_widgets(self):
        # Top bar with language selector
        top_bar = ttk.Frame(self.root, padding=(10, 5))
        top_bar.pack(fill="x")
        
        ttk.Label(top_bar, text=i18n('language') + ":").pack(side="right", padx=(10, 5))
        self.lang_var = tk.StringVar(value=i18n.language)
        lang_combo = ttk.Combobox(
            top_bar, 
            textvariable=self.lang_var,
            values=['en', 'es'],
            state="readonly",
            width=5
        )
        lang_combo.pack(side="right")
        lang_combo.bind("<<ComboboxSelected>>", self.change_language)
        
        # File Selection Frame
        self.input_frame = ttk.LabelFrame(self.root, text=i18n('file_selection'), padding=(10, 10))
        self.input_frame.pack(fill="x", padx=10, pady=5)

        # Cost File
        self.cost_label = ttk.Label(self.input_frame, text=i18n('cost_file_label'))
        self.cost_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.input_frame, textvariable=self.cost_file_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        self.cost_browse_btn = ttk.Button(self.input_frame, text=i18n('browse'), command=self.browse_cost_file)
        self.cost_browse_btn.grid(row=0, column=2, padx=5, pady=5)

        # SAP File
        self.sap_label = ttk.Label(self.input_frame, text=i18n('sap_file_label'))
        self.sap_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.sap_entry = ttk.Entry(self.input_frame, textvariable=self.sap_file_path, width=50)
        self.sap_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # SAP buttons frame (Browse + Paste)
        sap_btn_frame = ttk.Frame(self.input_frame)
        sap_btn_frame.grid(row=1, column=2, padx=5, pady=5)
        self.sap_browse_btn = ttk.Button(sap_btn_frame, text=i18n('browse'), command=self.browse_sap_file)
        self.sap_browse_btn.pack(side="left", padx=2)
        self.sap_paste_btn = ttk.Button(sap_btn_frame, text=i18n('paste'), command=self.paste_sap_from_clipboard)
        self.sap_paste_btn.pack(side="left", padx=2)
        
        # Status labels
        self.clipboard_status = ttk.Label(self.input_frame, text="", foreground="green")
        self.clipboard_status.grid(row=2, column=0, columnspan=3, sticky="w", padx=5)
        
        self.column_status = ttk.Label(self.input_frame, text="", foreground="blue")
        self.column_status.grid(row=3, column=0, columnspan=3, sticky="w", padx=5)

        # Action Buttons
        self.btn_frame = ttk.Frame(self.root, padding=(10, 5))
        self.btn_frame.pack(fill="x")
        
        # Configure columns button (initially disabled)
        self.config_btn = ttk.Button(
            self.btn_frame, 
            text=i18n('configure_columns'), 
            command=self.configure_columns,
            state="disabled"
        )
        self.config_btn.pack(side="left", padx=5)
        
        self.process_btn = ttk.Button(self.btn_frame, text=i18n('process_files'), command=self.process_files)
        self.process_btn.pack(side="left", padx=5)
        
        self.copy_btn = ttk.Button(self.btn_frame, text=i18n('copy_to_clipboard'), command=self.copy_to_clipboard)
        self.copy_btn.pack(side="left", padx=5)

        # Results Table
        self.table_frame = ttk.LabelFrame(self.root, text=i18n('results'), padding=(10, 10))
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview for dataframe
        self.tree = ttk.Treeview(self.table_frame, columns=("Articulo", "Value"), show="headings")
        self.tree.heading("Articulo", text=i18n('article_sap'))
        self.tree.heading("Value", text=i18n('manufacturing_cost'))
        self.tree.column("Articulo", width=200)
        self.tree.column("Value", width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def change_language(self, event=None):
        """Change the application language and refresh UI."""
        new_lang = self.lang_var.get()
        i18n.set_language(new_lang)
        self.refresh_ui_text()
    
    def refresh_ui_text(self):
        """Refresh all UI text with current language."""
        self.root.title(i18n('app_title'))
        
        # Update frame labels
        self.input_frame.config(text=i18n('file_selection'))
        self.table_frame.config(text=i18n('results'))
        
        # Update labels
        self.cost_label.config(text=i18n('cost_file_label'))
        self.sap_label.config(text=i18n('sap_file_label'))
        
        # Update buttons
        self.cost_browse_btn.config(text=i18n('browse'))
        self.sap_browse_btn.config(text=i18n('browse'))
        self.sap_paste_btn.config(text=i18n('paste'))
        self.config_btn.config(text=i18n('configure_columns'))
        self.process_btn.config(text=i18n('process_files'))
        self.copy_btn.config(text=i18n('copy_to_clipboard'))
        
        # Update table headers
        self.tree.heading("Articulo", text=i18n('article_sap'))
        self.tree.heading("Value", text=i18n('manufacturing_cost'))
        
        # Refresh column status if configured
        if self.cost_columns and self.sap_columns:
            self.update_column_status()

    def update_column_status(self):
        """Update the column configuration status label."""
        self.column_status.config(
            text=i18n('columns_configured',
                      cost_col=self.column_config['cost_article'],
                      value_col=self.column_config['cost_value'],
                      sap_col=self.column_config['sap_article']),
            foreground="blue"
        )

    def check_enable_config_button(self):
        """Enable the configure columns button if both files are loaded."""
        if self.cost_columns and self.sap_columns:
            self.config_btn.config(state="normal")
            self.update_column_status()
        else:
            self.config_btn.config(state="disabled")
            self.column_status.config(text="")

    def configure_columns(self):
        """Open dialog to configure columns."""
        if not self.cost_columns or not self.sap_columns:
            messagebox.showwarning(
                i18n('validation_error'),
                i18n('load_files_first')
            )
            return
        
        dialog = ColumnConfigDialog(
            self.root,
            self.cost_columns,
            self.sap_columns,
            self.column_config
        )
        result = dialog.show()
        
        if result:
            self.column_config = result
            self.update_column_status()

    def paste_sap_from_clipboard(self):
        """Open dialog to paste SAP data from clipboard."""
        dialog = ClipboardPasteDialog(self.root)
        result_df = dialog.show()
        
        if result_df is not None:
            self.sap_from_clipboard = result_df
            self.sap_file_path.set("")  # Clear file path since we're using clipboard
            self.clipboard_status.config(
                text=i18n('data_loaded_clipboard', count=len(result_df)),
                foreground="green"
            )
            # Update SAP columns from clipboard data
            self.sap_columns = list(result_df.columns)
            
            # Try to auto-select a matching column
            for col in self.sap_columns:
                if 'artículo' in col.lower() or 'articulo' in col.lower() or 'article' in col.lower() or 'número' in col.lower():
                    self.column_config['sap_article'] = col
                    break
            
            self.check_enable_config_button()
        else:
            # User cancelled, keep previous state
            pass

    def browse_cost_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if filename:
            self.cost_file_path.set(filename)
            try:
                # Try to load columns from the file
                self.cost_columns = get_excel_columns(filename, 'COSTO PROD')
                
                # Try to auto-select matching columns
                for col in self.cost_columns:
                    if 'artículo' in col.lower() or 'articulo' in col.lower():
                        self.column_config['cost_article'] = col
                    if 'manufactura' in col.lower() or 'costo' in col.lower() or 'fc' in col.lower():
                        self.column_config['cost_value'] = col
                
                self.check_enable_config_button()
            except Exception as e:
                # If we can't read the sheet, try without sheet name
                try:
                    self.cost_columns = get_excel_columns(filename)
                    self.check_enable_config_button()
                except:
                    self.cost_columns = []

    def browse_sap_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if filename:
            self.sap_file_path.set(filename)
            self.sap_from_clipboard = None  # Clear clipboard data when file is selected
            self.clipboard_status.config(text="")
            
            try:
                # Try to load columns from the file
                self.sap_columns = get_excel_columns(filename)
                
                # Try to auto-select a matching column
                for col in self.sap_columns:
                    if 'artículo' in col.lower() or 'articulo' in col.lower() or 'article' in col.lower() or 'número' in col.lower():
                        self.column_config['sap_article'] = col
                        break
                
                self.check_enable_config_button()
            except:
                self.sap_columns = []

    def process_files(self):
        cost_path = self.cost_file_path.get()
        sap_path = self.sap_file_path.get()

        # Check if we have cost file
        if not cost_path:
            messagebox.showwarning(i18n('missing_file'), i18n('missing_cost_file'))
            return
        
        # Check if we have SAP data from file or clipboard
        if not sap_path and self.sap_from_clipboard is None:
            messagebox.showwarning(i18n('missing_sap'), i18n('missing_sap_data'))
            return

        try:
            # Get column configuration
            cost_article_col = self.column_config['cost_article']
            cost_value_col = self.column_config['cost_value']
            sap_article_col = self.column_config['sap_article']
            
            # Load Cost data using handler
            dfCost, _, _ = load_cost_file(cost_path, cost_article_col, cost_value_col)
            
            # Load SAP data from file or use clipboard data
            if self.sap_from_clipboard is not None:
                dfSap, _ = prepare_sap_from_clipboard(self.sap_from_clipboard.copy(), sap_article_col)
            else:
                dfSap, _ = load_sap_file(sap_path, sap_article_col)

            # Merge data using handler
            df_merged, article_col, value_col = merge_data(
                dfSap, dfCost, 
                sap_article_col, cost_article_col, cost_value_col
            )
            
            # Prepare result using handler
            self.df_result = prepare_result(df_merged, article_col, value_col)
            
            # Store column names for display
            self.result_article_col = article_col
            self.result_value_col = value_col

            # Clear current table
            for i in self.tree.get_children():
                self.tree.delete(i)

            # Populate table
            for index, row in self.df_result.iterrows():
                self.tree.insert("", "end", values=(row[article_col], row[value_col]))

            messagebox.showinfo(i18n('success'), i18n('processed_rows', count=len(self.df_result)))

        except ValueError as e:
            messagebox.showerror(i18n('validation_error'), str(e))
        except FileNotFoundError as e:
            messagebox.showerror(i18n('file_not_found'), str(e))
        except Exception as e:
            messagebox.showerror(i18n('error'), i18n('error_occurred', error=str(e)))

    def copy_to_clipboard(self):
        if self.df_result is None:
            messagebox.showwarning(i18n('no_data'), i18n('process_first'))
            return

        try:
            # Extract the value column
            value_col = self.result_value_col if hasattr(self, 'result_value_col') else 'Manufactura FC'
            data_to_copy = self.df_result[value_col].fillna('')
            
            # Convert to string and join with newlines
            clipboard_text = '\n'.join(data_to_copy.astype(str).tolist())
            
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            self.root.update()
            
            messagebox.showinfo(i18n('copied'), i18n('copy_success'))
            
        except Exception as e:
            messagebox.showerror(i18n('error'), i18n('copy_error', error=str(e)))


if __name__ == "__main__":
    root = tk.Tk()
    app = SapPriceUpdaterApp(root)
    root.mainloop()