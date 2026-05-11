import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re

# ==========================================
# BLOQUE 1: ESTRUCTURAS BÁSICAS
# ==========================================
class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

class ASTNode:
    """Clase para construir el Árbol Sintáctico Abstracto (AST)"""
    def __init__(self, node_type, value=""):
        self.type = node_type
        self.value = value
        self.children = []

    def add_child(self, child):
        if child:
            self.children.append(child)

    def print_tree(self, level=0):
        ret = "  " * level + f"<{self.type}> {self.value}\n"
        for child in self.children:
            ret += child.print_tree(level + 1)
        return ret

class ParseException(Exception):
    pass

# ==========================================
# BLOQUE 2: LEXER TYPESCRIPT 
# ==========================================
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
            ('OP_ARROW',   r'=>'),                     
            ('OP_STRICT',  r'===|!=='),                
            ('OP_NULLISH', r'\?\?'),                   
            ('OP_OPTIONAL',r'\?\.'),                   
            ('OP_TERNARY', r'\?'),                     
            ('OP_REL',     r'<=|>=|==|!=|>|<'),         
            ('OP_LOGIC',   r'&&|\|\||!'),                
            ('OP_INC',     r'\+\+|--'),                
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
                if '\n' in value: line_num += value.count('\n')
                continue
            elif kind == 'NEWLINE':
                line_start = mo.end()
                line_num += 1
            elif kind == 'NUMBER_ERR':
                self.errors.append(f"Error Léxico: Número mal formado '{value}' en línea {line_num}")
                self.tokens.append(Token("Invalid", value, line_num, column))
            elif kind == 'ID':
                if value in self.keywords: 
                    t_type = "BooleanLiteral" if value in ("true", "false") else "Keyword"
                elif value in self.datatypes: 
                    t_type = "DataType"
                else: 
                    t_type = "Identifier"
                self.tokens.append(Token(t_type, value, line_num, column))
            elif kind == 'MISMATCH':
                self.errors.append(f"Error Léxico: Carácter ilegal '{value}' en línea {line_num}")
                self.tokens.append(Token("Invalid", value, line_num, column))
            else:
                type_map = {
                    'OP_ARROW': 'Operator', 'OP_STRICT': 'Operator', 'OP_NULLISH': 'Operator',
                    'OP_OPTIONAL': 'Operator', 'OP_TERNARY': 'Operator', 'OP_REL': 'Operator', 
                    'OP_LOGIC': 'Operator', 'OP_INC': 'Operator', 'OP_ARIT': 'Operator', 
                    'ASSIGN': 'Assignment', 'NUMBER': 'Number', 'STRING': 'String', 'DELIM': 'Delimiter'
                }
                self.tokens.append(Token(type_map.get(kind, kind), value, line_num, column))
        
        self.tokens.append(Token("EOF", "EOF", line_num, 0))
        return self.tokens, self.errors

# ==========================================
# BLOQUE 3: PARSER ROBUSTO Y COMPLETO
# ==========================================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos]
        self.errors = []
        self.log_sintactico = ">>> INICIO DE ANALISIS SINTACTICO\n"
        self.log_sintactico += ">>> ANALISIS SINTACTICO: <PROGRAMA>\n\n"

    def advance(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.current_token = self.tokens[self.pos]

    def expect(self, expected_type, expected_value=None):
        if self.current_token.type == expected_type and (expected_value is None or self.current_token.value == expected_value):
            val = self.current_token.value
            if expected_type == "Identifier": 
                self.log_sintactico += f"SINTACTICO: Push Identificador -> {val}\n"
            elif expected_type == "DataType": 
                self.log_sintactico += f"SINTACTICO: Tipo de dato -> {val}\n"
            elif expected_type == "Delimiter": 
                self.log_sintactico += f"SINTACTICO: Delimitador '{val}'\n"
            elif expected_type == "Assignment": 
                self.log_sintactico += f"SINTACTICO: Operador de Asignación '{val}'\n"
            
            token_to_return = self.current_token
            self.advance()
            return token_to_return
        else:
            esperado = expected_value if expected_value else expected_type
            self.errors.append(f"Error Sintáctico: Línea {self.current_token.line}. Se esperaba '{esperado}' pero se encontró '{self.current_token.value}'.")
            raise ParseException()

    def synchronize(self):
        self.log_sintactico += f"SINTACTICO: [!] Entrando en modo recuperación. Descartando nodo actual.\n"
        while self.current_token.type != "EOF":
            if self.current_token.value in [";", "}"]:
                self.advance() 
                self.log_sintactico += f"SINTACTICO: [!] Sincronización exitosa en '{self.current_token.value}'.\n\n"
                return
            self.advance()

    def parse(self):
        root = ASTNode("PROGRAMA")
        while self.current_token.type != "EOF":
            try:
                stmt = self.parse_statement()
                if stmt: root.add_child(stmt)
            except ParseException:
                self.synchronize()
        return root, self.log_sintactico, self.errors

    def parse_statement(self):
        token_val = self.current_token.value
        
        if token_val in ['let', 'const', 'var']:
            return self.parse_declaration()
        elif token_val == 'if':
            return self.parse_if()
        elif token_val == 'while':
            return self.parse_while()
        elif token_val == 'for':
            return self.parse_for()
        elif token_val == 'do':
            return self.parse_do_while()
        elif token_val == 'switch':
            return self.parse_switch()
        elif token_val in ['break', 'continue']:
            self.log_sintactico += f"SINTACTICO: Analizando control de flujo '{token_val}'\n"
            self.advance()
            self.expect("Delimiter", ";")
            return ASTNode("CONTROL_FLUJO", token_val)
        elif token_val == '{':
            return self.parse_block()
        else:
            return self.parse_expression_statement()

    def parse_block(self):
        self.log_sintactico += "SINTACTICO: <INICIO_BLOQUE>\n"
        self.expect("Delimiter", "{")
        
        block_node = ASTNode("BLOQUE")
        while self.current_token.type != "EOF" and self.current_token.value != "}":
            try:
                stmt = self.parse_statement()
                if stmt: block_node.add_child(stmt)
            except ParseException:
                self.synchronize()

        self.expect("Delimiter", "}")
        self.log_sintactico += "SINTACTICO: <FIN_BLOQUE>\n"
        return block_node

    # --- REGLAS DE FLUJO EXISTENTES ---
    def parse_if(self):
        self.log_sintactico += "SINTACTICO: Analizando estructura 'if'\n"
        self.advance() 
        node = ASTNode("ESTRUCTURA_IF")
        
        self.expect("Delimiter", "(")
        cond_node = ASTNode("CONDICION")
        cond_node.add_child(self.parse_expression())
        node.add_child(cond_node)
        self.expect("Delimiter", ")")

        true_node = ASTNode("BLOQUE_TRUE")
        true_node.add_child(self.parse_statement())
        node.add_child(true_node)

        if self.current_token.value == 'else':
            self.log_sintactico += "SINTACTICO: Analizando estructura 'else'\n"
            self.advance()
            false_node = ASTNode("BLOQUE_FALSE")
            false_node.add_child(self.parse_statement())
            node.add_child(false_node)

        return node

    def parse_while(self):
        self.log_sintactico += "SINTACTICO: Analizando estructura 'while'\n"
        self.advance()
        node = ASTNode("ESTRUCTURA_WHILE")
        
        self.expect("Delimiter", "(")
        cond_node = ASTNode("CONDICION")
        cond_node.add_child(self.parse_expression())
        node.add_child(cond_node)
        self.expect("Delimiter", ")")

        body_node = ASTNode("CUERPO_WHILE")
        body_node.add_child(self.parse_statement())
        node.add_child(body_node)

        return node

    # --- NUEVAS REGLAS DE FLUJO: FOR, DO-WHILE, SWITCH ---
    def parse_for(self):
        self.log_sintactico += "SINTACTICO: Analizando estructura 'for'\n"
        self.advance()
        node = ASTNode("ESTRUCTURA_FOR")
        self.expect("Delimiter", "(")

        # 1. Inicialización
        init_node = ASTNode("INICIALIZACION")
        if self.current_token.value in ['let', 'const', 'var']:
            init_node.add_child(self.parse_declaration()) # Esto ya consume el ';'
        else:
            init_node.add_child(self.parse_expression_statement()) # Esto también consume el ';'
        node.add_child(init_node)

        # 2. Condición
        cond_node = ASTNode("CONDICION")
        cond_node.add_child(self.parse_expression())
        self.expect("Delimiter", ";")
        node.add_child(cond_node)

        # 3. Incremento
        inc_node = ASTNode("INCREMENTO")
        inc_node.add_child(self.parse_expression())
        self.expect("Delimiter", ")")
        node.add_child(inc_node)

        # 4. Cuerpo
        body_node = ASTNode("CUERPO_FOR")
        body_node.add_child(self.parse_statement())
        node.add_child(body_node)

        return node

    def parse_do_while(self):
        self.log_sintactico += "SINTACTICO: Analizando estructura 'do-while'\n"
        self.advance()
        node = ASTNode("ESTRUCTURA_DO_WHILE")

        body_node = ASTNode("CUERPO_DO")
        body_node.add_child(self.parse_statement())
        node.add_child(body_node)

        self.expect("Keyword", "while")
        self.expect("Delimiter", "(")
        
        cond_node = ASTNode("CONDICION")
        cond_node.add_child(self.parse_expression())
        node.add_child(cond_node)
        
        self.expect("Delimiter", ")")
        self.expect("Delimiter", ";")
        return node

    def parse_switch(self):
        self.log_sintactico += "SINTACTICO: Analizando estructura 'switch'\n"
        self.advance()
        node = ASTNode("ESTRUCTURA_SWITCH")

        self.expect("Delimiter", "(")
        expr_node = ASTNode("EXPRESION_SWITCH")
        expr_node.add_child(self.parse_expression())
        node.add_child(expr_node)
        self.expect("Delimiter", ")")

        self.expect("Delimiter", "{")
        while self.current_token.type != "EOF" and self.current_token.value != "}":
            if self.current_token.value == "case":
                self.log_sintactico += "SINTACTICO: Analizando 'case'\n"
                self.advance()
                case_node = ASTNode("CASO")
                case_node.add_child(self.parse_expression())
                self.expect("Delimiter", ":")
                
                body_node = ASTNode("CUERPO_CASO")
                # Leer sentencias hasta encontrar el siguiente case, default, o cerrar el switch
                while self.current_token.type != "EOF" and self.current_token.value not in ["case", "default", "}"]:
                    stmt = self.parse_statement()
                    if stmt: body_node.add_child(stmt)
                case_node.add_child(body_node)
                node.add_child(case_node)

            elif self.current_token.value == "default":
                self.log_sintactico += "SINTACTICO: Analizando 'default'\n"
                self.advance()
                self.expect("Delimiter", ":")
                def_node = ASTNode("DEFAULT")
                
                body_node = ASTNode("CUERPO_DEFAULT")
                while self.current_token.type != "EOF" and self.current_token.value not in ["case", "default", "}"]:
                    stmt = self.parse_statement()
                    if stmt: body_node.add_child(stmt)
                def_node.add_child(body_node)
                node.add_child(def_node)
            else:
                self.errors.append(f"Error Sintáctico: Línea {self.current_token.line}. Se esperaba 'case' o 'default'.")
                raise ParseException()

        self.expect("Delimiter", "}")
        return node

    # --- REGLA DE VARIABLES Y EXPRESIONES GENERALES ---
    def parse_expression_statement(self):
        expr = self.parse_expression()
        self.expect("Delimiter", ";")
        return expr

    def parse_declaration(self):
        keyword = self.current_token.value
        self.log_sintactico += f"SINTACTICO: Analizando estructura '{keyword}'\n"
        self.advance()

        id_token = self.expect("Identifier")
        node = ASTNode("DECLARACION", keyword)
        node.add_child(ASTNode("ID", id_token.value))

        if self.current_token.value == ":":
            self.expect("Delimiter", ":")
            type_token = self.expect("DataType")
            node.add_child(ASTNode("TIPO", type_token.value))

        if self.current_token.value == "=":
            self.expect("Assignment", "=")
            expr_node = self.parse_expression()
            node.add_child(expr_node)
        elif keyword == 'const':
            self.errors.append(f"Error Sintáctico: Línea {self.current_token.line}. La constante '{id_token.value}' debe inicializarse.")
            raise ParseException()

        self.expect("Delimiter", ";")
        self.log_sintactico += f"SINTACTICO: Fin de estructura '{keyword}'\n\n"
        return node

    # --- MOTOR DE EXPRESIONES MATEMÁTICAS / LÓGICAS ---
    def parse_expression(self):
        node = self.parse_ternary()
        if self.current_token.value == "=":
            op_val = self.current_token.value
            self.log_sintactico += f"SINTACTICO: Operador de Asignación '='\n"
            self.advance()
            right = self.parse_expression()
            parent = ASTNode("ASIGNACION", op_val)
            parent.add_child(node)
            parent.add_child(right)
            return parent
        return node

    def parse_ternary(self):
        node = self.parse_nullish()
        if self.current_token.value == "?":
            self.log_sintactico += f"SINTACTICO: Operador Ternario '?'\n"
            self.advance()
            true_expr = self.parse_expression()
            self.expect("Delimiter", ":")
            false_expr = self.parse_expression()
            parent = ASTNode("TERNARIO", "?:")
            parent.add_child(node)
            parent.add_child(true_expr)
            parent.add_child(false_expr)
            return parent
        return node

    def parse_nullish(self):
        node = self.parse_logical_or()
        while self.current_token.value == "??":
            op_val = self.current_token.value
            self.log_sintactico += f"SINTACTICO: Operador Nullish '{op_val}'\n"
            self.advance()
            right = self.parse_logical_or()
            parent = ASTNode("NULLISH", op_val)
            parent.add_child(node)
            parent.add_child(right)
            node = parent
        return node

    def parse_logical_or(self):
        node = self.parse_logical_and()
        while self.current_token.value == "||":
            op_val = self.current_token.value
            self.advance()
            right = self.parse_logical_and()
            parent = ASTNode("OPERACION_LOGICA", op_val)
            parent.add_child(node)
            parent.add_child(right)
            node = parent
        return node

    def parse_logical_and(self):
        node = self.parse_equality()
        while self.current_token.value == "&&":
            op_val = self.current_token.value
            self.advance()
            right = self.parse_equality()
            parent = ASTNode("OPERACION_LOGICA", op_val)
            parent.add_child(node)
            parent.add_child(right)
            node = parent
        return node

    def parse_equality(self):
        node = self.parse_relational()
        while self.current_token.value in ['===', '!==', '==', '!=']:
            op_val = self.current_token.value
            self.advance()
            right = self.parse_relational()
            parent = ASTNode("IGUALDAD", op_val)
            parent.add_child(node)
            parent.add_child(right)
            node = parent
        return node

    def parse_relational(self):
        node = self.parse_additive()
        while self.current_token.value in ['<', '>', '<=', '>=']:
            op_val = self.current_token.value
            self.advance()
            right = self.parse_additive()
            parent = ASTNode("RELACIONAL", op_val)
            parent.add_child(node)
            parent.add_child(right)
            node = parent
        return node

    def parse_additive(self):
        node = self.parse_multiplicative()
        while self.current_token.value in ['+', '-']:
            op_val = self.current_token.value
            self.advance()
            right = self.parse_multiplicative()
            parent = ASTNode("OPERACION", op_val)
            parent.add_child(node)
            parent.add_child(right)
            node = parent
        return node

    def parse_multiplicative(self):
        node = self.parse_unary()
        while self.current_token.value in ['*', '/', '%']:
            op_val = self.current_token.value
            self.advance()
            right = self.parse_unary()
            parent = ASTNode("OPERACION", op_val)
            parent.add_child(node)
            parent.add_child(right)
            node = parent
        return node

    def parse_unary(self):
        if self.current_token.value in ['-', '+', '!', '++', '--']:
            op_val = self.current_token.value
            self.advance()
            operand = self.parse_unary()
            node = ASTNode("UNARIO", op_val)
            node.add_child(operand)
            return node
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()
        if self.current_token.value in ['++', '--']:
            op_val = self.current_token.value
            self.advance()
            parent = ASTNode("POSTFIJO", op_val)
            parent.add_child(node)
            return parent
        return node

    def parse_primary(self):
        token = self.current_token
        if token.type in ["Number", "String", "BooleanLiteral"]:
            self.log_sintactico += f"SINTACTICO: Push Literal -> {token.value}\n"
            self.advance()
            return ASTNode("LITERAL", token.value)
        elif token.type == "Keyword" and token.value in ["console"]:
            # Arreglo magistral para console.log
            self.log_sintactico += f"SINTACTICO: Detectado objeto '{token.value}'\n"
            self.advance()
            self.expect("Delimiter", ".")
            self.expect("Keyword", "log")
            
            node = ASTNode("LLAMADA_FUNCION", "console.log")
            self.expect("Delimiter", "(")
            arg = self.parse_expression()
            node.add_child(arg)
            self.expect("Delimiter", ")")
            return node
        elif token.type == "Identifier":
            self.log_sintactico += f"SINTACTICO: Push Identificador -> {token.value}\n"
            self.advance()
            return ASTNode("ID", token.value)
        elif token.value == "(":
            self.log_sintactico += f"SINTACTICO: Delimitador '('\n"
            self.advance()
            node = self.parse_expression()
            self.expect("Delimiter", ")")
            return node
        else:
            self.errors.append(f"Error Sintáctico: Línea {token.line}. Expresión inválida o inesperada cerca de '{token.value}'.")
            raise ParseException()

# ==========================================
# BLOQUE 4: GUI (INTERFAZ)
# ==========================================
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

        menu_file = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=menu_file)
        menu_file.add_command(label="New", command=self._new_file)
        menu_file.add_command(label="Open", command=self._open_file)
        menu_file.add_command(label="Save", command=self._save_file)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.root.quit)

        menu_edit = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=menu_edit)
        menu_edit.add_command(label="Search")
        menu_edit.add_command(label="Replace")

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
        toolbar = tk.Frame(self.root, bg=self.CLR_BG, pady=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_run = tk.Button(toolbar, text="▶ RUN", bg=self.CLR_GREEN_BRIGHT, fg="black", font=("Segoe UI", 9, "bold"), padx=15, command=self._run_analysis)
        self.btn_run.pack(side=tk.LEFT, padx=5)

        self.btn_debug = tk.Button(toolbar, text="🪲 DEBUG", bg=self.CLR_PANEL, fg="white", font=("Segoe UI", 9, "bold"), padx=15)
        self.btn_debug.pack(side=tk.LEFT, padx=5)

        self.btn_new = tk.Button(toolbar, text="📄 NEW", bg=self.CLR_PANEL, fg="white", font=("Segoe UI", 9, "bold"), padx=15, command=self._new_file)
        self.btn_new.pack(side=tk.LEFT, padx=5)

        output_frame = tk.Frame(self.root, bg=self.CLR_BG, height=120)
        output_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        tk.Label(output_frame, text="Terminal Output", bg=self.CLR_BG, fg=self.CLR_GREEN_BRIGHT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.output = tk.Text(output_frame, height=6, bg="#0f1108", fg=self.CLR_ERROR, font=("Consolas", 10), state="disabled")
        self.output.pack(fill=tk.X)

        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.CLR_BG, sashwidth=4)
        main_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        editor_frame = tk.Frame(main_pane, bg=self.CLR_PANEL)
        main_pane.add(editor_frame, width=500)

        self.line_nums = tk.Text(editor_frame, width=3, bg=self.CLR_PANEL, fg=self.CLR_GREEN_BRIGHT, state="disabled", font=("Consolas", 11), bd=0)
        self.line_nums.pack(side=tk.LEFT, fill=tk.Y)

        self.editor = tk.Text(editor_frame, font=("Consolas", 11), bg=self.CLR_EDITOR, fg=self.CLR_TEXT, bd=0, padx=5, pady=5, undo=True)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.editor.bind("<KeyRelease>", self._update_line_numbers)

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
        for i in self.tab_tokens.get_children(): self.tab_tokens.delete(i)
        for i in self.tab_semantico.get_children(): self.tab_semantico.delete(i)
        
        self.output.config(state="normal")
        self.output.delete("1.0", tk.END)
        
        source = self.editor.get("1.0", tk.END).strip()
        if not source: 
            self.output.insert(tk.END, "⚠ No hay código para analizar.\n")
            self.output.config(state="disabled")
            return

        try:
            lexer = Lexer(source)
            tokens, lex_errors = lexer.tokenize()
            
            for t in tokens:
                if t.type != "EOF":
                    self.tab_tokens.insert("", tk.END, values=(t.line, t.column, t.type, t.value))

            if not lex_errors:
                parser = Parser(tokens)
                ast_root, log_sintactico, sint_errors = parser.parse()
                
                self._update_tab(self.txt_sintactico, log_sintactico)
                self._update_tab(self.txt_ast, ast_root.print_tree())
                
                if sint_errors:
                    for err in sint_errors: self.output.insert(tk.END, f"✗ {err}\n")
                else:
                    self.output.insert(tk.END, "✓ Análisis Léxico y Sintáctico completado sin errores.\n")
            else:
                for err in lex_errors: self.output.insert(tk.END, f"✗ {err}\n")
                self._update_tab(self.txt_sintactico, "El Parser no se ejecutó debido a errores léxicos previos.")
                self._update_tab(self.txt_ast, "")

        except Exception as e:
            self.output.insert(tk.END, f"❌ Error interno crítico: {e}\n")
            
        self.output.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = GreenCompilerGUI(root)
    root.mainloop()