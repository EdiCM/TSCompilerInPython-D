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
    def __init__(self, node_type, value="", line="N/A"):
        self.type = node_type
        self.value = value
        self.line = line 
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
        elif token_val == 'function':
            return self.parse_function()
        elif token_val == 'return':
            return self.parse_return()
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

    def parse_function(self):
        self.log_sintactico += "SINTACTICO: Analizando estructura 'function'\n"
        line_num = self.current_token.line 
        self.advance() 
        
        id_token = self.expect("Identifier")
        node = ASTNode("DECLARACION_FUNCION", id_token.value, line_num) 
        
        self.expect("Delimiter", "(")
        params_node = ASTNode("PARAMETROS")
        
        while self.current_token.type != "EOF" and self.current_token.value != ")":
            param_id = self.expect("Identifier")
            self.expect("Delimiter", ":")
            param_type = self.expect("DataType")
            
            p_node = ASTNode("PARAMETRO", param_id.value, param_id.line)
            p_node.add_child(ASTNode("TIPO", param_type.value))
            params_node.add_child(p_node)
            
            if self.current_token.value == ",":
                self.advance()
            else:
                break
                
        self.expect("Delimiter", ")")
        node.add_child(params_node)
        
        if self.current_token.value == ":":
            self.expect("Delimiter", ":")
            ret_type = self.expect("DataType")
            node.add_child(ASTNode("TIPO_RETORNO", ret_type.value))
            
        body = self.parse_block()
        node.add_child(body)
        
        return node

    def parse_return(self):
        self.log_sintactico += "SINTACTICO: Analizando 'return'\n"
        self.advance()
        node = ASTNode("RETURN")
        if self.current_token.value != ";":
            expr = self.parse_expression()
            node.add_child(expr)
        self.expect("Delimiter", ";")
        return node

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

    def parse_for(self):
        self.log_sintactico += "SINTACTICO: Analizando estructura 'for'\n"
        self.advance()
        node = ASTNode("ESTRUCTURA_FOR")
        self.expect("Delimiter", "(")

        init_node = ASTNode("INICIALIZACION")
        if self.current_token.value in ['let', 'const', 'var']:
            init_node.add_child(self.parse_declaration()) 
        else:
            init_node.add_child(self.parse_expression_statement())
        node.add_child(init_node)

        cond_node = ASTNode("CONDICION")
        cond_node.add_child(self.parse_expression())
        self.expect("Delimiter", ";")
        node.add_child(cond_node)

        inc_node = ASTNode("INCREMENTO")
        inc_node.add_child(self.parse_expression())
        self.expect("Delimiter", ")")
        node.add_child(inc_node)

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

    def parse_expression_statement(self):
        expr = self.parse_expression()
        self.expect("Delimiter", ";")
        return expr

    def parse_declaration(self):
        line_num = self.current_token.line 
        keyword = self.current_token.value
        self.log_sintactico += f"SINTACTICO: Analizando estructura '{keyword}'\n"
        self.advance()

        id_token = self.expect("Identifier")
        node = ASTNode("DECLARACION", keyword, line_num)
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

    # --- MOTOR DE EXPRESIONES ---
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
            self.log_sintactico += f"SINTACTICO: Detectado objeto '{token.value}'\n"
            self.advance()
            self.expect("Delimiter", ".")
            self.expect("Keyword", "log")
            
            node = ASTNode("LLAMADA_FUNCION", "console.log")
            self.expect("Delimiter", "(")
            
            if self.current_token.value != ")":
                arg = self.parse_expression()
                node.add_child(arg)
                while self.current_token.value == ",":
                    self.advance()
                    arg = self.parse_expression()
                    node.add_child(arg)
                    
            self.expect("Delimiter", ")")
            return node
            
        elif token.type == "Identifier":
            id_val = token.value
            self.log_sintactico += f"SINTACTICO: Push Identificador -> {id_val}\n"
            self.advance()
            
            if self.current_token.value == "(":
                self.log_sintactico += f"SINTACTICO: Detectada llamada a función '{id_val}'\n"
                self.advance() 
                node = ASTNode("LLAMADA_FUNCION", id_val)
                
                if self.current_token.value != ")":
                    arg = self.parse_expression()
                    node.add_child(arg)
                    while self.current_token.value == ",":
                        self.advance()
                        arg = self.parse_expression()
                        node.add_child(arg)
                        
                self.expect("Delimiter", ")")
                return node
                
            return ASTNode("ID", id_val)
            
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
# BLOQUE 4: ANALIZADOR SEMÁNTICO (TIPOS Y FUNCIONES)
# ==========================================
class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.current_scope_level = 0
        self.symbols_flat_list = [] 

    def enter_scope(self):
        self.scopes.append({})
        self.current_scope_level += 1

    def exit_scope(self):
        if self.current_scope_level > 0:
            self.scopes.pop()
            self.current_scope_level -= 1

    # Inyectamos param_signature para recordar qué pide la función
    def define(self, name, type_, value, line, param_signature=None):
        if name in self.scopes[self.current_scope_level]:
            return False 
        scope_name = "Global" if self.current_scope_level == 0 else f"Local ({self.current_scope_level})"
        self.scopes[self.current_scope_level][name] = {'type': type_, 'value': value, 'params': param_signature}
        self.symbols_flat_list.append((name, type_, value, scope_name, line))
        return True

    def lookup(self, name):
        for i in range(self.current_scope_level, -1, -1):
            if name in self.scopes[i]:
                return self.scopes[i][name]
        return None 

class SemanticAnalyzer:
    def __init__(self):
        self.sym_table = SymbolTable()
        self.errors = []
        self.loop_depth = 0 # Contador para saber si estamos dentro de un ciclo
        self.current_func_ret_type = None # Para validar qué tipo debe tener el 'return'

    def analyze(self, ast_root):
        if ast_root: self.visit(ast_root)
        return self.sym_table.symbols_flat_list, self.errors

    def visit(self, node):
        if not node: return "void"
        method_name = f'visit_{node.type}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for child in node.children:
            self.visit(child)
        return "void"

    def visit_PROGRAMA(self, node):
        return self.generic_visit(node)

    def visit_BLOQUE(self, node):
        self.sym_table.enter_scope()
        self.generic_visit(node)
        self.sym_table.exit_scope()
        return "void"

    # --- CONTROL DE FLUJO Y LOOPS ---
    def visit_ESTRUCTURA_WHILE(self, node):
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1
        return "void"

    def visit_ESTRUCTURA_DO_WHILE(self, node):
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1
        return "void"

    def visit_ESTRUCTURA_SWITCH(self, node):
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1
        return "void"

    def visit_ESTRUCTURA_FOR(self, node):
        self.sym_table.enter_scope()
        self.loop_depth += 1
        for child in node.children:
            if child.type == "CUERPO_FOR":
                block = next((c for c in child.children if c.type == "BLOQUE"), None)
                if block:
                    for gc in block.children: self.visit(gc)
                else: self.visit(child)
            else:
                self.visit(child)
        self.loop_depth -= 1
        self.sym_table.exit_scope()
        return "void"

    def visit_CONTROL_FLUJO(self, node):
        # Valida que el break/continue no ande suelto por ahí
        if self.loop_depth == 0:
            self.errors.append(f"Error Semántico: Línea {node.line}. '{node.value}' solo puede usarse dentro de un ciclo o switch.")
        return "void"

    # --- DECLARACIONES ---
    def visit_DECLARACION(self, node):
        id_node = next((c for c in node.children if c.type == "ID"), None)
        type_node = next((c for c in node.children if c.type == "TIPO"), None)
        val_node = next((c for c in node.children if c.type not in ["ID", "TIPO"]), None)

        inferred_type = self.visit(val_node) if val_node else "undefined"
        declared_type = type_node.value if type_node else inferred_type

        if type_node and inferred_type != "undefined" and inferred_type != "any" and declared_type != inferred_type:
            self.errors.append(f"Error Semántico: Línea {node.line}. No se puede asignar '{inferred_type}' a '{declared_type}'.")

        if id_node:
            if not self.sym_table.define(id_node.value, declared_type, "<expr>", node.line):
                self.errors.append(f"Error Semántico: Línea {node.line}. Variable '{id_node.value}' ya declarada.")
        return "void"

    def visit_DECLARACION_FUNCION(self, node):
        func_name = node.value
        ret_node = next((c for c in node.children if c.type == "TIPO_RETORNO"), None)
        ret_type = ret_node.value if ret_node else "void"
        
        # 1. Guardar la firma (tipos de parámetros)
        params_node = next((c for c in node.children if c.type == "PARAMETROS"), None)
        param_signature = []
        if params_node:
            for p in params_node.children:
                p_type_node = next((c for c in p.children if c.type == "TIPO"), None)
                param_signature.append(p_type_node.value if p_type_node else "any")

        if not self.sym_table.define(func_name, f"function->{ret_type}", "func", node.line, param_signature):
            self.errors.append(f"Error Semántico: Línea {node.line}. Función '{func_name}' ya declarada.")
        
        self.sym_table.enter_scope()
        
        # 2. Guardar estado de retorno para validar adentro
        self.current_func_ret_type = ret_type 
        
        if params_node:
            for p in params_node.children:
                p_type = next((c for c in p.children if c.type == "TIPO"), None).value
                self.sym_table.define(p.value, p_type, "param", p.line)
        
        block = next((c for c in node.children if c.type == "BLOQUE"), None)
        if block:
            for child in block.children: self.visit(child)
            
        self.sym_table.exit_scope()
        self.current_func_ret_type = None # Limpiamos al salir
        return "void"

    def visit_RETURN(self, node):
        # Evitar usar 'return' fuera de una función
        if self.current_func_ret_type is None:
            self.errors.append(f"Error Semántico: Línea {node.line}. 'return' no permitido fuera de una función.")
            return "void"
            
        ret_type = "void"
        if node.children:
            ret_type = self.visit(node.children[0])
            
        # Comparar el tipo de retorno de la expresión con el prometido por la función
        if ret_type != self.current_func_ret_type and self.current_func_ret_type != "any" and ret_type != "any":
            self.errors.append(f"Error Semántico: Línea {node.line}. La función espera retornar '{self.current_func_ret_type}' pero retorna '{ret_type}'.")
        return ret_type

    def visit_LLAMADA_FUNCION(self, node):
        if node.value == "console.log":
            self.generic_visit(node)
            return "void"
            
        sym = self.sym_table.lookup(node.value)
        if not sym:
            self.errors.append(f"Error Semántico: Línea {node.line}. Función '{node.value}' no definida.")
            return "any"
            
        expected_params = sym.get('params') or []
        args = node.children
        
        # 1. Validar cantidad de argumentos
        if len(args) != len(expected_params):
            self.errors.append(f"Error Semántico: Línea {node.line}. La función '{node.value}' espera {len(expected_params)} argumentos, pero recibió {len(args)}.")
        else:
            # 2. Validar el tipo de cada argumento
            for i in range(len(args)):
                arg_type = self.visit(args[i])
                if expected_params[i] != "any" and arg_type != "any" and arg_type != expected_params[i]:
                    self.errors.append(f"Error Semántico: Línea {node.line}. El argumento {i+1} de '{node.value}' debe ser '{expected_params[i]}', no '{arg_type}'.")
                    
        return sym['type'].split("->")[-1]

    # --- EXPRESIONES BÁSICAS ---
    def visit_LITERAL(self, node):
        val = node.value
        if val in ["true", "false"]: return "boolean"
        # FIX: Agregamos el backtick a la validación de strings
        if val.startswith('"') or val.startswith("'") or val.startswith('`'): return "string"
        if re.match(r'^\d', val): return "number"
        return "any"

    def visit_ID(self, node):
        sym = self.sym_table.lookup(node.value)
        if not sym:
            self.errors.append(f"Error Semántico: Línea {node.line}. Variable '{node.value}' no definida.")
            return "any"
        return sym['type']

    def visit_OPERACION(self, node):
        left_t = self.visit(node.children[0])
        right_t = self.visit(node.children[1])
        
        # NUEVO: Permitir concatenación de strings si el operador es '+'
        if node.value == "+" and left_t == "string" and right_t == "string":
            return "string"
            
        # Regla original: Todo lo demás requiere números
        if left_t != "number" or right_t != "number":
            self.errors.append(f"Error Semántico: Línea {node.line}. Operación '{node.value}' no válida entre '{left_t}' y '{right_t}'.")
            return "any"
            
        return "number"

    def visit_RELACIONAL(self, node):
        left_t = self.visit(node.children[0])
        right_t = self.visit(node.children[1])
        if left_t != right_t:
            self.errors.append(f"Error Semántico: Línea {node.line}. Comparación entre '{left_t}' y '{right_t}' no válida.")
        return "boolean"

    def visit_IGUALDAD(self, node):
        self.visit(node.children[0])
        self.visit(node.children[1])
        return "boolean"

    def visit_OPERACION_LOGICA(self, node):
        left_t = self.visit(node.children[0])
        right_t = self.visit(node.children[1])
        if left_t != "boolean" or right_t != "boolean":
            self.errors.append(f"Error Semántico: Línea {node.line}. Operador '{node.value}' requiere booleanos.")
        return "boolean"

    def visit_UNARIO(self, node):
        t = self.visit(node.children[0])
        if node.value == "!" and t != "boolean":
            self.errors.append(f"Error Semántico: Línea {node.line}. '!' requiere booleano.")
            return "boolean"
        if node.value in ["-", "+", "++", "--"] and t != "number":
            self.errors.append(f"Error Semántico: Línea {node.line}. '{node.value}' requiere número.")
            return "number"
        return t

    def visit_POSTFIJO(self, node):
        t = self.visit(node.children[0])
        if t != "number":
            self.errors.append(f"Error Semántico: Línea {node.line}. '{node.value}' requiere número.")
        return "number"

    def visit_ASIGNACION(self, node):
        target_t = self.visit(node.children[0])
        value_t = self.visit(node.children[1])
        if target_t != value_t and target_t != "any":
            self.errors.append(f"Error Semántico: Línea {node.line}. No se puede asignar '{value_t}' a '{target_t}'.")
        return target_t

    def visit_TERNARIO(self, node):
        self.visit(node.children[0]) 
        t1 = self.visit(node.children[1])
        t2 = self.visit(node.children[2])
        if t1 != t2: return "any"
        return t1

# ==========================================
# BLOQUE 5: GENERADOR DE CÓDIGO INTERMEDIO (VM STACK)
# ==========================================
class CodeGenerator:
    def __init__(self):
        self.code = []
        self.label_counter = 0
        self.loop_end_labels = [] # Pila para saber a dónde saltar con un 'break'

    def new_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"

    def emit(self, instruction):
        self.code.append(instruction)

    def generate(self, node):
        if not node: return
        method_name = f'gen_{node.type}'
        generator = getattr(self, method_name, self.generic_gen)
        generator(node)
        return "\n".join(self.code)

    def generic_gen(self, node):
        for child in node.children:
            self.generate(child)

    def gen_PROGRAMA(self, node):
        self.generic_gen(node)
        self.emit("HALT")

    def gen_LITERAL(self, node):
        self.emit(f"PUSH {node.value}")

    def gen_ID(self, node):
        self.emit(f"LOAD {node.value}")

    def gen_DECLARACION(self, node):
        id_node = next((c for c in node.children if c.type == "ID"), None)
        val_node = next((c for c in node.children if c.type not in ["ID", "TIPO"]), None)
        if val_node:
            self.generate(val_node)
            self.emit(f"STORE {id_node.value}")

    def gen_ASIGNACION(self, node):
        target = node.children[0]
        val = node.children[1]
        self.generate(val)
        self.emit(f"STORE {target.value}")

    def gen_OPERACION(self, node):
        self.generate(node.children[0])
        self.generate(node.children[1])
        ops = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '%': 'MOD'}
        self.emit(ops.get(node.value, "UNKNOWN_OP"))

    # FIX: Operaciones Lógicas (&&, ||)
    def gen_OPERACION_LOGICA(self, node):
        self.generate(node.children[0])
        self.generate(node.children[1])
        ops = {'&&': 'AND', '||': 'OR'}
        self.emit(ops.get(node.value, "UNKNOWN_LOGIC"))

    # FIX: Unarios (-10, !true)
    def gen_UNARIO(self, node):
        self.generate(node.children[0])
        if node.value == "-": self.emit("NEG")
        elif node.value == "!": self.emit("NOT")

    def gen_RELACIONAL(self, node):
        self.generate(node.children[0])
        self.generate(node.children[1])
        ops = {'<': 'LT', '>': 'GT', '<=': 'LE', '>=': 'GE'}
        self.emit(ops.get(node.value, "UNKNOWN_REL"))

    def gen_IGUALDAD(self, node):
        self.generate(node.children[0])
        self.generate(node.children[1])
        ops = {'===': 'EQ', '==': 'EQ', '!==': 'NEQ', '!=': 'NEQ'}
        self.emit(ops.get(node.value, "UNKNOWN_EQ"))

    def gen_POSTFIJO(self, node):
        target = node.children[0]
        self.emit(f"LOAD {target.value}")
        self.emit("PUSH 1")
        if node.value == "++": self.emit("ADD")
        elif node.value == "--": self.emit("SUB")
        self.emit(f"STORE {target.value}")

    # FIX: Funciones completas
    def gen_DECLARACION_FUNCION(self, node):
        l_end = self.new_label()
        self.emit(f"JMP {l_end}") 
        
        self.emit(f"LABEL func_{node.value}")
        
        # --- NUEVO: La función toma sus parámetros de la pila ---
        params_node = next((c for c in node.children if c.type == "PARAMETROS"), None)
        if params_node:
            # Los sacamos en orden inverso (de último a primero)
            for p in reversed(params_node.children):
                self.emit(f"STORE {p.value}")
        
        block = next((c for c in node.children if c.type == "BLOQUE"), None)
        if block:
            self.generate(block)
        
        self.emit("RET") 
        self.emit(f"LABEL {l_end}")

    def gen_RETURN(self, node):
        if node.children:
            self.generate(node.children[0])
        self.emit("RET")

    def gen_LLAMADA_FUNCION(self, node):
        if node.value == "console.log":
            for arg in node.children:
                self.generate(arg)
                self.emit("PRINT")
        else:
            # Funciones personalizadas
            for arg in node.children:
                self.generate(arg) # Empuja los argumentos a la pila
            self.emit(f"CALL func_{node.value}")

    # ESTRUCTURAS DE CONTROL DE FLUJO
    def gen_CONTROL_FLUJO(self, node):
        if node.value == "break" and self.loop_end_labels:
            self.emit(f"JMP {self.loop_end_labels[-1]}") # Salta al final del ciclo/switch actual

    def gen_ESTRUCTURA_IF(self, node):
        cond = next((c for c in node.children if c.type == "CONDICION"), None)
        true_b = next((c for c in node.children if c.type == "BLOQUE_TRUE"), None)
        false_b = next((c for c in node.children if c.type == "BLOQUE_FALSE"), None)
        
        l_false = self.new_label()
        l_end = self.new_label()
        
        self.generate(cond)
        self.emit(f"JMPF {l_false}")
        self.generate(true_b)
        self.emit(f"JMP {l_end}")
        self.emit(f"LABEL {l_false}")
        if false_b:
            self.generate(false_b)
        self.emit(f"LABEL {l_end}")

    def gen_ESTRUCTURA_WHILE(self, node):
        l_start = self.new_label()
        l_end = self.new_label()
        
        self.loop_end_labels.append(l_end) # Guardamos la etiqueta final por si hay un break
        
        self.emit(f"LABEL {l_start}")
        cond = next((c for c in node.children if c.type == "CONDICION"), None)
        body = next((c for c in node.children if c.type == "CUERPO_WHILE"), None)
        
        self.generate(cond)
        self.emit(f"JMPF {l_end}")
        self.generate(body)
        self.emit(f"JMP {l_start}")
        self.emit(f"LABEL {l_end}")
        
        self.loop_end_labels.pop()
    
    def gen_ESTRUCTURA_SWITCH(self, node):
        l_end = self.new_label()
        self.loop_end_labels.append(l_end)
        
        expr = next((c for c in node.children if c.type == "EXPRESION_SWITCH"), None)
        cases = [c for c in node.children if c.type in ["CASO", "DEFAULT"]]
        
        for i, child in enumerate(cases):
            if child.type == "CASO":
                l_body = self.new_label()
                l_next_comparison = self.new_label()
                
                # 1. Bloque de Comparación
                self.generate(expr)
                self.generate(child.children[0]) # Valor del case
                self.emit("EQ")
                self.emit(f"JMPF {l_next_comparison}") # Si no coincide, salta a comparar el siguiente
                
                # 2. Bloque de ejecución (aquí cae si coincide)
                self.emit(f"LABEL {l_body}") 
                body = next((c for c in child.children if c.type == "CUERPO_CASO"), None)
                if body: self.generate(body)
                
                # Aquí es donde ocurre el fallthrough natural hacia el siguiente LABEL
                self.emit(f"LABEL {l_next_comparison}")
                
            elif child.type == "DEFAULT":
                self.emit(f"LABEL default_case")
                body = next((c for c in child.children if c.type == "CUERPO_DEFAULT"), None)
                if body: self.generate(body)

        self.emit(f"LABEL {l_end}")
        self.loop_end_labels.pop()

    def gen_ESTRUCTURA_DO_WHILE(self, node):
        l_start = self.new_label()
        l_end = self.new_label()
        
        self.loop_end_labels.append(l_end)
        
        self.emit(f"LABEL {l_start}")
        body = next((c for c in node.children if c.type == "CUERPO_DO"), None)
        cond = next((c for c in node.children if c.type == "CONDICION"), None)
        
        self.generate(body)
        self.generate(cond)
        
        self.emit(f"JMPF {l_end}") # Si es falso, salimos
        self.emit(f"JMP {l_start}") # Si es verdadero, volvemos a dar la vuelta
        self.emit(f"LABEL {l_end}")
        
        self.loop_end_labels.pop()

    def gen_ESTRUCTURA_FOR(self, node):
        l_start = self.new_label()
        l_end = self.new_label()
        
        self.loop_end_labels.append(l_end)
        
        init = next((c for c in node.children if c.type == "INICIALIZACION"), None)
        cond = next((c for c in node.children if c.type == "CONDICION"), None)
        inc = next((c for c in node.children if c.type == "INCREMENTO"), None)
        body = next((c for c in node.children if c.type == "CUERPO_FOR"), None)
        
        self.generate(init)
        self.emit(f"LABEL {l_start}")
        self.generate(cond)
        self.emit(f"JMPF {l_end}")
        self.generate(body)
        self.generate(inc)
        self.emit(f"JMP {l_start}")
        self.emit(f"LABEL {l_end}")
        
        self.loop_end_labels.pop()

    # Delegadores
    def gen_BLOQUE(self, node): self.generic_gen(node)
    def gen_CONDICION(self, node): self.generic_gen(node)
    def gen_BLOQUE_TRUE(self, node): self.generic_gen(node)
    def gen_BLOQUE_FALSE(self, node): self.generic_gen(node)
    def gen_CUERPO_WHILE(self, node): self.generic_gen(node)
    def gen_CUERPO_FOR(self, node): self.generic_gen(node)
    def gen_CUERPO_DO(self, node): self.generic_gen(node)
    def gen_INICIALIZACION(self, node): self.generic_gen(node)
    def gen_INCREMENTO(self, node): self.generic_gen(node)

import shlex # Necesario para leer strings con espacios correctamente

# ==========================================
# BLOQUE 6: MÁQUINA VIRTUAL (VIRTUAL MACHINE)
# ==========================================
class VirtualMachine:
    def __init__(self, asm_code):
        self.instructions = asm_code.strip().split('\n')
        self.stack = []
        self.memory = {}
        self.ip = 0 
        self.labels = {}
        self.call_stack = [] # ¡FIX: Pila de llamadas para funciones!
        self.output_log = []
        
        for i, line in enumerate(self.instructions):
            # Usamos shlex para no romper strings con espacios
            parts = shlex.split(line)
            if not parts: continue
            if parts[0] == "LABEL":
                self.labels[parts[1]] = i

    def run(self):
        self.output_log.append(">>> INICIO DE EJECUCIÓN VM\n")
        
        # Dentro del while de run() en VirtualMachine
        while self.ip < len(self.instructions):
            line = self.instructions[self.ip]
            try:
                parts = shlex.split(line)
            except ValueError:
                # Si shlex falla por comillas mal cerradas o complejas, 
                # hacemos un split básico y limpiamos las comillas a mano
                parts = line.split(maxsplit=1)
            if not parts: self.ip += 1; continue
                    
            op = parts[0]
            
            try:
                if op == "PUSH":
                    val = parts[1]
                    if val == "true": self.stack.append(True)
                    elif val == "false": self.stack.append(False)
                    # shlex ya quita las comillas automáticamente
                    elif not any(c.isalpha() for c in val) or '.' in val:
                        try: self.stack.append(float(val) if '.' in val else int(val))
                        except: self.stack.append(val)
                    else:
                        self.stack.append(val)
                
                elif op == "LOAD":
                    var_name = parts[1]
                    self.stack.append(self.memory.get(var_name, 0))
                
                elif op == "STORE":
                    var_name = parts[1]
                    self.memory[var_name] = self.stack.pop()
                
                elif op == "ADD":
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a + b)
                elif op == "SUB":
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a - b)
                elif op == "MUL":
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a * b)
                elif op == "DIV":
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a / b)
                elif op == "NEG":
                    self.stack.append(-self.stack.pop())
                
                elif op == "EQ":
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a == b)
                elif op == "NEQ":
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a != b)
                elif op == "LT":
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a < b)
                elif op == "GT":
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a > b)
                elif op == "NOT":
                    self.stack.append(not self.stack.pop())
                elif op == "AND":
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a and b)
                elif op == "OR":
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a or b)
                
                elif op == "JMP":
                    self.ip = self.labels[parts[1]]
                    continue
                elif op == "JMPF":
                    condition = self.stack.pop()
                    if not condition:
                        self.ip = self.labels[parts[1]]
                        continue
                
                # --- FIX: IMPLEMENTACIÓN DE FUNCIONES ---
                elif op == "CALL":
                    self.call_stack.append(self.ip + 1) # Guardamos a dónde volver
                    self.ip = self.labels[parts[1]] # Saltamos a la función
                    continue
                
                elif op == "RET":
                    if self.call_stack:
                        self.ip = self.call_stack.pop() # Volvemos a donde nos llamaron
                        continue
                    else:
                        break # Fin del programa si no hay a dónde volver

                elif op == "PRINT":
                    val = self.stack.pop()
                    self.output_log.append(f"[CONSOLE]: {val}")
                
                elif op == "HALT":
                    break
                    
            except Exception as e:
                self.output_log.append(f"❌ ERROR EN VM (IP {self.ip}): {e}")
                break
                
            self.ip += 1
            
        self.output_log.append("\n>>> EJECUCIÓN FINALIZADA")
        return "\n".join(self.output_log)
       
# ==========================================
# BLOQUE 7: GUI (INTERFAZ)
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
                    semantic = SemanticAnalyzer()
                    symbols_list, sem_errors = semantic.analyze(ast_root)
                    
                    for sym in symbols_list:
                        self.tab_semantico.insert("", tk.END, values=(sym[0], sym[1], sym[2], sym[3], sym[4]))
                        
                    if sem_errors:
                        for err in sem_errors: self.output.insert(tk.END, f"✗ {err}\n")
                        self._update_tab(self.txt_intermedio, "Corrija los errores semánticos para generar código.")
                    else:
                        # --- GENERADOR DE CÓDIGO INTERMEDIO ---
                        generator = CodeGenerator()
                        asm_code = generator.generate(ast_root)
                        self._update_tab(self.txt_intermedio, asm_code)
                        
                        # --- NUEVO: MÁQUINA VIRTUAL (EJECUCIÓN) ---
                        vm = VirtualMachine(asm_code)
                        resultado_ejecucion = vm.run()
                        self._update_tab(self.txt_ejecucion, resultado_ejecucion)
                        
                        self.output.insert(tk.END, "✓ Compilación y Ejecución completadas con éxito.\n")
            else:
                for err in lex_errors: self.output.insert(tk.END, f"✗ {err}\n")
                self._update_tab(self.txt_sintactico, "El Parser no se ejecutó debido a errores léxicos.")
                self._update_tab(self.txt_ast, "")
                self._update_tab(self.txt_intermedio, "")

        except Exception as e:
            self.output.insert(tk.END, f"❌ Error interno crítico: {e}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = GreenCompilerGUI(root)
    root.mainloop()