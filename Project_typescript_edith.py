import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re

# --- CLASE TOKEN ---
class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

# --- BLOQUE 2: LEXER TYPESCRIPT (CORREGIDO) ---
# --- BLOQUE 2: LEXER TYPESCRIPT (CORREGIDO) ---
class Lexer:
    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.errors = []
        
        self.datatypes = {'number', 'string', 'boolean', 'any', 'void', 'unknown', 'never', 'null', 'undefined', 'object', 'bigint'}
        self.keywords = {'let', 'const', 'var', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'break', 'continue', 'function', 'return', 'console', 'log', 'interface', 'type', 'true', 'false'}

    def tokenize(self):
        token_specification = [
            ('COMMENT',    r'//.*|/\*[\s\S]*?\*/'),    
            ('NUMBER_ERR', r'\d+\.\d+\.\d+'),         
            ('NUMBER',     r'\d+(\.\d+)?'),             
            ('STRING',     r'("[^"]*"|\'[^\']*\'|`[^`]*`)'), 
            ('OP_ARROW',   r'=>'),                     # Flecha de función
            ('OP_STRICT',  r'===|!=='),                # Igualdad estricta TS
            ('OP_NULLISH', r'\?\?'),                   # Nullish coalescing (??)
            ('OP_OPTIONAL',r'\?\.'),                   # Optional chaining (?.)
            ('OP_TERNARY', r'\?'),                     # Ternario (?) -> Va DESPUÉS de los otros dos
            ('OP_REL',     r'<=|>=|==|!=|>|<'),         
            ('OP_LOGIC',   r'&&|\|\||!'),                # Lógicos (AND, OR)
            ('OP_INC',     r'\+\+|--'),                # Incrementos
            ('ASSIGN',     r'='),                       
            ('OP_ARIT',    r'[\+\-\*/%]'),              
            ('DELIM',      r'[()\[\]\{\};,:\.]'),       
            ('ID',         r'[a-zA-Z_][a-zA-Z0-9_]*'),  
            ('NEWLINE',    r'\n'),                      
            ('SKIP',       r'[ \t]+'),                  
            ('MISMATCH',   r'.'),                       
        ]
        
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
        line_num = 1
        line_start = 0
        
        for mo in re.finditer(tok_regex, self.source):
            kind = mo.lastgroup
            value = mo.group()
            column = mo.start() - line_start
            
            if kind == 'SKIP' or kind == 'COMMENT':
                if '\n' in value: 
                    line_num += value.count('\n')
                continue
            elif kind == 'NEWLINE':
                line_start = mo.end()
                line_num += 1
            elif kind == 'NUMBER_ERR':
                self.errors.append(f"Error Léxico: Número mal formado '{value}' en línea {line_num}")
                self.tokens.append(Token("Invalid", value, line_num, column))
            elif kind == 'ID':
                if value in self.keywords: 
                    t_type = "Keyword"
                elif value in self.datatypes: 
                    t_type = "DataType"
                else: 
                    t_type = "Identifier"
                self.tokens.append(Token(t_type, value, line_num, column))
            elif kind == 'MISMATCH':
                self.errors.append(f"Error Léxico: Carácter ilegal '{value}' en línea {line_num}")
                self.tokens.append(Token("Invalid", value, line_num, column))
            else:
                # Mapeamos los nuevos operadores a la categoría "Operator" para que en la tabla se vea limpio
                type_map = {
                    'OP_ARROW': 'Operator', 'OP_STRICT': 'Operator', 'OP_NULLISH': 'Operator',
                    'OP_OPTIONAL': 'Operator', 'OP_TERNARY': 'Operator', 'OP_REL': 'Operator', 
                    'OP_LOGIC': 'Operator', 'OP_INC': 'Operator', 'OP_ARIT': 'Operator', 
                    'ASSIGN': 'Assignment', 'NUMBER': 'Number', 'STRING': 'String', 'DELIM': 'Delimiter'
                }
                self.tokens.append(Token(type_map.get(kind, kind), value, line_num, column))
        
        self.tokens.append(Token("EOF", "EOF", line_num, 0))
        return self.tokens, self.errors

# --- BLOQUE 1: GUI (CORREGIDA CON TODAS TUS OPCIONES) ---
class GreenCompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TypeScript Green-Compiler IDE")
        self.root.geometry("1100x700")
        
        self.CLR_BG = "#1e2310"
        self.CLR_PANEL = "#2d3618"
        self.CLR_EDITOR = "#fdfdfb"
        self.CLR_TEXT = "#1a1a1a"
        self.CLR_GREEN_BRIGHT = "#A8B65F"
        self.CLR_ERROR = "#ff4d4d"

        self.root.configure(bg=self.CLR_BG)
        
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
        # --- Barra de Herramientas ---
        toolbar = tk.Frame(self.root, bg=self.CLR_BG, pady=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_run = tk.Button(toolbar, text="▶ RUN", bg=self.CLR_GREEN_BRIGHT, 
                                fg="black", font=("Segoe UI", 9, "bold"), padx=15,
                                command=self._run_analysis)
        self.btn_run.pack(side=tk.LEFT, padx=5)

        self.btn_debug = tk.Button(toolbar, text="🪲 DEBUG", bg=self.CLR_PANEL, 
                                  fg="white", font=("Segoe UI", 9, "bold"), padx=15)
        self.btn_debug.pack(side=tk.LEFT, padx=5)

        self.btn_new = tk.Button(toolbar, text="📄 NEW", bg=self.CLR_PANEL, 
                                fg="white", font=("Segoe UI", 9, "bold"), padx=15,
                                command=self._new_file)
        self.btn_new.pack(side=tk.LEFT, padx=5)

        # --- Output Errores (Anclado abajo para que no se pierda) ---
        output_frame = tk.Frame(self.root, bg=self.CLR_BG, height=120)
        output_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        tk.Label(output_frame, text="Terminal Output", bg=self.CLR_BG, fg=self.CLR_GREEN_BRIGHT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.output = tk.Text(output_frame, height=6, bg="#0f1108", fg=self.CLR_ERROR, font=("Consolas", 10), state="disabled")
        self.output.pack(fill=tk.X)

        # --- Paneles Centrales ---
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.CLR_BG, sashwidth=4)
        main_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

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
        self.txt_sintactico = self._create_tab_text("Sintáctico")
        self.txt_ast = self._create_tab_text("AST (Árbol)")
        self.tab_semantico = self._create_sym_table("Semántico")
        self.txt_intermedio = self._create_tab_text("Cód. Intermedio")
        self.txt_ejecucion = self._create_tab_text("Ejecución")

    def _create_tab_text(self, name):
        frame = tk.Frame(self.notebook, bg="#0f1108")
        self.notebook.add(frame, text=name)
        txt = tk.Text(frame, bg="#0f1108", fg="#d0d0d0", font=("Consolas", 10), padx=10, pady=10, bd=0, state="disabled")
        txt.pack(fill=tk.BOTH, expand=True)
        return txt

    def _create_token_table(self, name):
        frame = tk.Frame(self.notebook, bg="#0f1108")
        self.notebook.add(frame, text=name)
        cols = ("Línea", "Pos", "Tipo", "Valor")
        table = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            table.heading(col, text=col)
            table.column(col, width=80, anchor="center")
        table.pack(fill=tk.BOTH, expand=True)
        return table

    def _create_sym_table(self, name):
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

    def _update_tab(self, widget, content):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.config(state="disabled")

    def _run_analysis(self):
        # 1. Limpiar pantalla
        for i in self.tab_tokens.get_children(): self.tab_tokens.delete(i)
        for i in self.tab_semantico.get_children(): self.tab_semantico.delete(i)
        
        self.output.config(state="normal")
        self.output.delete("1.0", tk.END)
        
        source = self.editor.get("1.0", tk.END).strip()
        if not source: 
            self.output.insert(tk.END, "⚠ No hay código para analizar.\n")
            self.output.config(state="disabled")
            return

        # Protección para evitar que falle silenciosamente
        try:
            lexer = Lexer(source)
            tokens, errors = lexer.tokenize()
        except Exception as e:
            self.output.insert(tk.END, f"❌ Error interno crítico en el Lexer: {e}\n")
            self.output.config(state="disabled")
            return

        # 2. Llenar tabla de Tokens
        for t in tokens:
            if t.type != "EOF":
                self.tab_tokens.insert("", tk.END, values=(t.line, t.column, t.type, t.value))

       # 3. Mostrar rastro sintáctico preliminar
        log_sint = ">>> INICIO DE ANALISIS SINTACTICO\n"
        log_sint += ">>> ANALISIS SINTACTICO: <PROGRAMA>\n\n"
        for t in tokens:
            if t.type == "Keyword": 
                log_sint += f"SINTACTICO: Analizando estructura '{t.value}'\n"
            elif t.type == "Identifier": 
                log_sint += f"SINTACTICO: Push Identificador -> {t.value}\n"
            elif t.type == "DataType": 
                log_sint += f"SINTACTICO: Tipo de dato -> {t.value}\n"
            elif t.type == "Number" or t.type == "String" or t.type == "BooleanLiteral": 
                log_sint += f"SINTACTICO: Push Literal -> {t.value}\n"
            elif t.type == "Operator" or t.type == "Assignment":
                log_sint += f"SINTACTICO: Operador '{t.value}'\n"
            elif t.type == "Delimiter":
                log_sint += f"SINTACTICO: Delimitador '{t.value}'\n"
                if t.value == "{":
                    log_sint += "SINTACTICO: <INICIO_BLOQUE>\n"
                elif t.value == "}":
                    log_sint += "SINTACTICO: <FIN_BLOQUE>\n"
                    
        self._update_tab(self.txt_sintactico, log_sint)

        # 4. Mostrar errores léxicos abajo
        if errors:
            for err in errors: self.output.insert(tk.END, f"✗ {err}\n")
        else:
            self.output.insert(tk.END, "✓ Análisis léxico completado sin errores.\n")
            
        self.output.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = GreenCompilerGUI(root)
    root.mainloop()