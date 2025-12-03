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
)


class ClipboardPasteDialog:
    """Dialog for pasting SAP data from clipboard."""
    
    def __init__(self, parent):
        self.parent = parent
        self.result_df = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Pegar Datos SAP desde Portapapeles")
        self.dialog.geometry("800x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Instructions
        instructions = ttk.Label(
            self.dialog,
            text="Pegue los datos de la tabla SAP (Ctrl+V) en el área de texto.\n"
                 "Los datos deben estar separados por tabulaciones (copiados desde Excel).",
            padding=(10, 10)
        )
        instructions.pack(fill="x")
        
        # Text area for pasting
        text_frame = ttk.LabelFrame(self.dialog, text="Datos Pegados", padding=(10, 10))
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
        
        ttk.Button(btn_frame, text="Vista Previa", command=self.preview_data).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Usar estos Datos", command=self.accept_data).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.cancel).pack(side="left", padx=5)
        
        # Status label
        self.status_label = ttk.Label(self.dialog, text="", padding=(10, 5))
        self.status_label.pack(fill="x")
        
        # Preview table
        preview_frame = ttk.LabelFrame(self.dialog, text="Vista Previa", padding=(10, 10))
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
            
            # Check for required column
            if "Número de artículo" in df.columns:
                self.status_label.config(
                    text=f"✓ {len(df)} filas detectadas. Columna 'Número de artículo' encontrada.",
                    foreground="green"
                )
                self._preview_df = df
            else:
                self.status_label.config(
                    text="⚠ Columna 'Número de artículo' no encontrada. Verifique los datos.",
                    foreground="orange"
                )
                self._preview_df = None
                
        except ValueError as e:
            self.status_label.config(text=f"✗ Error: {str(e)}", foreground="red")
            self._preview_df = None
        except Exception as e:
            self.status_label.config(text=f"✗ Error inesperado: {str(e)}", foreground="red")
            self._preview_df = None
    
    def accept_data(self):
        """Accept the parsed data and close dialog."""
        if hasattr(self, '_preview_df') and self._preview_df is not None:
            self.result_df = self._preview_df
            self.dialog.destroy()
        else:
            messagebox.showwarning(
                "Datos Inválidos",
                "Por favor pegue datos válidos con la columna 'Número de artículo'."
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
        self.root.title("SAP Price Updater")
        self.root.geometry("800x600")

        # Variables
        self.cost_file_path = tk.StringVar()
        self.sap_file_path = tk.StringVar()
        self.df_result = None
        self.sap_from_clipboard = None  # Store SAP data from clipboard

        # Layout
        self.create_widgets()

    def create_widgets(self):
        # File Selection Frame
        input_frame = ttk.LabelFrame(self.root, text="Selección de Archivos", padding=(10, 10))
        input_frame.pack(fill="x", padx=10, pady=5)

        # Cost File
        ttk.Label(input_frame, text="Archivo de Costos (COSTO STD PRODUCTOS):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.cost_file_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text="Examinar", command=self.browse_cost_file).grid(row=0, column=2, padx=5, pady=5)

        # SAP File
        ttk.Label(input_frame, text="Archivo SAP (o pegar desde portapapeles):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.sap_entry = ttk.Entry(input_frame, textvariable=self.sap_file_path, width=50)
        self.sap_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # SAP buttons frame (Examinar + Pegar)
        sap_btn_frame = ttk.Frame(input_frame)
        sap_btn_frame.grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(sap_btn_frame, text="Examinar", command=self.browse_sap_file).pack(side="left", padx=2)
        ttk.Button(sap_btn_frame, text="Pegar", command=self.paste_sap_from_clipboard).pack(side="left", padx=2)
        
        # Status label for clipboard data
        self.clipboard_status = ttk.Label(input_frame, text="", foreground="green")
        self.clipboard_status.grid(row=2, column=0, columnspan=3, sticky="w", padx=5)

        # Action Buttons
        btn_frame = ttk.Frame(self.root, padding=(10, 5))
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="Procesar Archivos", command=self.process_files).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Copiar 'Manufactura FC' al Portapapeles", command=self.copy_to_clipboard).pack(side="left", padx=5)

        # Results Table
        table_frame = ttk.LabelFrame(self.root, text="Resultados", padding=(10, 10))
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview for dataframe
        self.tree = ttk.Treeview(table_frame, columns=("Articulo", "Manufactura FC"), show="headings")
        self.tree.heading("Articulo", text="Artículo (SAP)")
        self.tree.heading("Manufactura FC", text="Manufactura FC")
        self.tree.column("Articulo", width=200)
        self.tree.column("Manufactura FC", width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def paste_sap_from_clipboard(self):
        """Open dialog to paste SAP data from clipboard."""
        dialog = ClipboardPasteDialog(self.root)
        result_df = dialog.show()
        
        if result_df is not None:
            self.sap_from_clipboard = result_df
            self.sap_file_path.set("")  # Clear file path since we're using clipboard
            self.clipboard_status.config(
                text=f"✓ Datos SAP cargados desde portapapeles ({len(result_df)} filas)",
                foreground="green"
            )
        else:
            # User cancelled, keep previous state
            pass

    def browse_cost_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx *.xls")])
        if filename:
            self.cost_file_path.set(filename)

    def browse_sap_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx *.xls")])
        if filename:
            self.sap_file_path.set(filename)
            self.sap_from_clipboard = None  # Clear clipboard data when file is selected
            self.clipboard_status.config(text="")

    def process_files(self):
        cost_path = self.cost_file_path.get()
        sap_path = self.sap_file_path.get()

        # Check if we have cost file
        if not cost_path:
            messagebox.showwarning("Archivo Faltante", "Por favor seleccione el archivo de costos.")
            return
        
        # Check if we have SAP data from file or clipboard
        if not sap_path and self.sap_from_clipboard is None:
            messagebox.showwarning("Datos SAP Faltantes", "Por favor seleccione un archivo SAP o pegue datos desde el portapapeles.")
            return

        try:
            # Load Cost data using handler
            dfCost = load_cost_file(cost_path)
            
            # Load SAP data from file or use clipboard data
            if self.sap_from_clipboard is not None:
                dfSap = prepare_sap_from_clipboard(self.sap_from_clipboard)
            else:
                dfSap = load_sap_file(sap_path)

            # Merge data using handler
            df_merged = merge_data(dfSap, dfCost)
            
            # Prepare result using handler
            self.df_result = prepare_result(df_merged)

            # Clear current table
            for i in self.tree.get_children():
                self.tree.delete(i)

            # Populate table
            for index, row in self.df_result.iterrows():
                self.tree.insert("", "end", values=(row['Número de artículo'], row['Manufactura FC']))

            messagebox.showinfo("Éxito", f"Se procesaron {len(self.df_result)} filas.")

        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
        except FileNotFoundError as e:
            messagebox.showerror("Archivo No Encontrado", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")

    def copy_to_clipboard(self):
        if self.df_result is None:
            messagebox.showwarning("Sin Datos", "Por favor procese los archivos primero.")
            return

        try:
            # Extract the column
            # We want to copy exactly what is in the column, preserving order.
            # We fill NaN with empty string so the clipboard has a blank line for missing matches
            # This ensures alignment when pasting back to Excel.
            data_to_copy = self.df_result['Manufactura FC'].fillna('')
            
            # Convert to string and join with newlines
            clipboard_text = '\n'.join(data_to_copy.astype(str).tolist())
            
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            self.root.update() # Keep clipboard after app closes if needed, though standard behavior varies
            
            messagebox.showinfo("Copiado", "Valores de Manufactura FC copiados al portapapeles en el orden del archivo SAP.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al copiar:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SapPriceUpdaterApp(root)
    root.mainloop()
