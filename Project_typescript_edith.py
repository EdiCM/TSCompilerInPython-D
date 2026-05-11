import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class GreenCompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TypeScript Green-Compiler IDE")
        self.root.geometry("1100x700")
        
        # Colores (Modern Green)
        self.CLR_BG = "#1e2310"
        self.CLR_PANEL = "#2d3618"
        self.CLR_EDITOR = "#fdfdfb"
        self.CLR_TEXT = "#1a1a1a"
        self.CLR_GREEN_BRIGHT = "#A8B65F"
        self.CLR_ERROR = "#ff4d4d"

        self.root.configure(bg=self.CLR_BG)
        
        # 1. Crear el Menú Superior
        self._create_menu()
        
        self._setup_styles()
        self._create_widgets()

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menú File
        menu_file = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=menu_file)
        menu_file.add_command(label="New", command=self._new_file)
        menu_file.add_command(label="Open", command=self._open_file)
        menu_file.add_command(label="Save", command=self._save_file)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.root.quit)

        # Menú Edit
        menu_edit = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=menu_edit)
        menu_edit.add_command(label="Search")
        menu_edit.add_command(label="Replace")

        # Menú Terminal
        menu_terminal = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Terminal", menu=menu_terminal)
        menu_terminal.add_command(label="Run", command=self._run_analysis)
        menu_terminal.add_command(label="Debug")

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=self.CLR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.CLR_PANEL, foreground="white", padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", self.CLR_GREEN_BRIGHT)], foreground=[("selected", "black")])
        style.configure("Treeview", background="#0f1108", foreground="white", fieldbackground="#0f1108", borderwidth=0)
        style.configure("Treeview.Heading", background=self.CLR_PANEL, foreground="white", relief="flat")

    def _create_widgets(self):
        # --- Barra de Herramientas (Botones Rápidos) ---
        toolbar = tk.Frame(self.root, bg=self.CLR_BG, pady=5)
        toolbar.pack(fill=tk.X)

        # Botón Run
        self.btn_run = tk.Button(toolbar, text="▶ RUN", bg=self.CLR_GREEN_BRIGHT, 
                                fg="black", font=("Segoe UI", 9, "bold"), padx=15,
                                command=self._run_analysis)
        self.btn_run.pack(side=tk.LEFT, padx=5)

        # Botón Debug
        self.btn_debug = tk.Button(toolbar, text="🪲 DEBUG", bg=self.CLR_PANEL, 
                                  fg="white", font=("Segoe UI", 9, "bold"), padx=15)
        self.btn_debug.pack(side=tk.LEFT, padx=5)

        # Botón New
        self.btn_new = tk.Button(toolbar, text="📄 NEW", bg=self.CLR_PANEL, 
                                fg="white", font=("Segoe UI", 9, "bold"), padx=15,
                                command=self._new_file)
        self.btn_new.pack(side=tk.LEFT, padx=5)

        # --- Paneles ---
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.CLR_BG, sashwidth=4)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Editor
        editor_frame = tk.Frame(main_pane, bg=self.CLR_PANEL)
        main_pane.add(editor_frame, width=500)

        self.line_nums = tk.Text(editor_frame, width=3, bg=self.CLR_PANEL, fg=self.CLR_GREEN_BRIGHT, 
                                state="disabled", font=("Consolas", 11), bd=0)
        self.line_nums.pack(side=tk.LEFT, fill=tk.Y)

        self.editor = tk.Text(editor_frame, font=("Consolas", 11), bg=self.CLR_EDITOR, 
                             fg=self.CLR_TEXT, bd=0, padx=5, pady=5, undo=True)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.editor.bind("<KeyRelease>", self._update_line_numbers)

        # Pestañas
        tabs_frame = tk.Frame(main_pane, bg=self.CLR_BG)
        main_pane.add(tabs_frame, width=550)

        self.notebook = ttk.Notebook(tabs_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_tokens = self._create_token_table("Tokens")
        self.tab_sintactico = self._create_tab_text("Sintáctico")
        self.tab_ast = self._create_tab_text("AST (Árbol)")
        self.tab_semantico = self._create_tab_table("Semántico")
        self.tab_intermedio = self._create_tab_text("Cód. Intermedio")
        self.tab_ejecucion = self._create_tab_text("Ejecución")

        # Output Errores
        output_frame = tk.Frame(self.root, bg=self.CLR_BG, height=100)
        output_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        self.output = tk.Text(output_frame, height=5, bg="#0f1108", fg=self.CLR_ERROR, 
                             font=("Consolas", 10), state="disabled")
        self.output.pack(fill=tk.X)

    def _create_tab_text(self, name):
        frame = tk.Frame(self.notebook, bg="#0f1108")
        self.notebook.add(frame, text=name)
        txt = tk.Text(frame, bg="#0f1108", fg="#d0d0d0", font=("Consolas", 10), padx=10, pady=10, bd=0, state="disabled")
        txt.pack(fill=tk.BOTH, expand=True)
        return txt

    def _create_token_table(self, name):
        frame = tk.Frame(self.notebook, bg="#0f1108")
        self.notebook.add(frame, text=name)
        cols = ("Línea", "Tipo", "Valor")
        table = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            table.heading(col, text=col)
            table.column(col, width=100, anchor="center")
        table.pack(fill=tk.BOTH, expand=True)
        return table

    def _create_tab_table(self, name):
        frame = tk.Frame(self.notebook, bg="#0f1108")
        self.notebook.add(frame, text=name)
        cols = ("Variable", "Tipo", "Valor", "Scope", "Línea")
        table = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            table.heading(col, text=col)
            table.column(col, width=80, anchor="center")
        table.pack(fill=tk.BOTH, expand=True)
        return table

    # --- Acciones de Archivo ---
    def _new_file(self):
        self.editor.delete("1.0", tk.END)
        self._update_line_numbers()

    def _open_file(self):
        path = filedialog.askopenfilename(filetypes=[("TypeScript files", "*.ts"), ("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", content)
            self._update_line_numbers()

    def _save_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".ts", filetypes=[("TypeScript files", "*.ts"), ("Text files", "*.txt")])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.editor.get("1.0", tk.END))

    def _update_line_numbers(self, event=None):
        lines = self.editor.get("1.0", "end-1c").split("\n")
        nums = "\n".join(str(i) for i in range(1, len(lines) + 1))
        self.line_nums.config(state="normal")
        self.line_nums.delete("1.0", tk.END)
        self.line_nums.insert("1.0", nums)
        self.line_nums.config(state="disabled")

    def _run_analysis(self):
        # Aquí irá la lógica cuando la definamos
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = GreenCompilerGUI(root)
    root.mainloop()