import re

# ================================================================
# C LEXER
# ================================================================
C_TOKENS = [
    ('COMMENT',  r'//[^\n]*|/\*[\s\S]*?\*/'),
    ('PREPROC',  r'#[^\n]*'),
    ('VOID',     r'void\b'),
    ('INT',      r'int\b'),
    ('FLOAT',    r'float\b'),
    ('DOUBLE',   r'double\b'),
    ('CHAR',     r'char\b'),
    ('IF',       r'if\b'),
    ('ELSE',     r'else\b'),
    ('WHILE',    r'while\b'),
    ('FOR',      r'for\b'),
    ('RETURN',   r'return\b'),
    ('NUMBER',   r'\d+(\.\d+)?'),
    ('STRING',   r'"[^"]*"'),
    ('INC',      r'\+\+'),
    ('DEC',      r'--'),
    ('LOGOP',    r'&&|\|\|'),
    ('RELOP',    r'==|!=|>=|<=|>|<'),
    ('NOT',      r'!'),
    ('MODOP',    r'%'),
    ('OP',       r'[+\-*/]'),
    ('ASSIGN',   r'='),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('LBRACE',   r'\{'),
    ('RBRACE',   r'\}'),
    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('SEMICOLON',r';'),
    ('COMMA',    r','),
    ('ID',       r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('SKIP',     r'[ \t\n\r]+'),
]

def c_lexer(code):
    tokens = []
    pos = 0
    while pos < len(code):
        match = None
        for tt, pat in C_TOKENS:
            m = re.compile(pat).match(code[pos:])
            if m:
                match = m
                if tt not in ('SKIP', 'COMMENT', 'PREPROC'):
                    tokens.append((tt, m.group()))
                pos += m.end()
                break
        if not match:
            raise SyntaxError(f"Invalid character: '{code[pos]}'")
    return tokens


# ================================================================
# PYTHON LEXER  (proper INDENT / DEDENT, dot access, class, 1e7)
# ================================================================
PY_LINE_TOKENS = [
    ('COMMENT',   r'#[^\n]*'),
    ('CLASS',     r'class\b'),
    ('DEF',       r'def\b'),
    ('IF',        r'if\b'),
    ('ELIF',      r'elif\b'),
    ('ELSE',      r'else\b'),
    ('WHILE',     r'while\b'),
    ('FOR',       r'for\b'),
    ('IN',        r'in\b'),
    ('RETURN',    r'return\b'),
    ('PRINT',     r'print\b'),
    ('AND',       r'and\b'),
    ('OR',        r'or\b'),
    ('NOT',       r'not\b'),
    ('TRUE',      r'True\b'),
    ('FALSE',     r'False\b'),
    ('NONE',      r'None\b'),
    ('NUMBER',    r'\d+(\.\d+)?(e[+\-]?\d+)?'),   # 0, 3.14, 1e7
    ('STRING',    r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"]*"|\'[^\']*\''),
    ('RELOP',     r'==|!=|>=|<=|>|<'),
    ('AUGASSIGN', r'\+=|-=|\*=|/=|//=|%='),
    ('OP',        r'[+\-*/]'),
    ('ASSIGN',    r'='),
    ('DOT',       r'\.'),
    ('COLON',     r':'),
    ('LPAREN',    r'\('),
    ('RPAREN',    r'\)'),
    ('LBRACKET',  r'\['),
    ('RBRACKET',  r'\]'),
    ('COMMA',     r','),
    ('SKIP',      r'[ \t]+'),
    ('ID',        r'[a-zA-Z_][a-zA-Z0-9_]*'),
]

def _lex_line(text):
    tokens = []
    pos = 0
    while pos < len(text):
        match = None
        for tt, pat in PY_LINE_TOKENS:
            m = re.compile(pat).match(text[pos:])
            if m:
                match = m
                if tt not in ('SKIP', 'COMMENT'):
                    tokens.append((tt, m.group()))
                pos += m.end()
                break
        if not match:
            raise SyntaxError(f"Invalid character: '{text[pos]}'")
    return tokens

def python_lexer(code):
    """
    Line-by-line lexer that:
      1. Merges continuation lines (inside unmatched brackets)
      2. Emits INDENT / DEDENT tokens based on indentation changes
    """
    tokens = []
    indent_stack = [0]

    raw_lines = code.split('\n')

    # ── Step 1: merge continuation lines ─────────────────────────
    merged = []          # [(indent_level, stripped_content), ...]
    buf_indent   = None
    buf_content  = ''
    depth = 0            # unmatched ( [ {

    for line in raw_lines:
        stripped = line.rstrip()
        content  = stripped.lstrip()
        if not content or content.startswith('#'):
            continue

        current_indent = len(stripped) - len(content)

        if buf_indent is None:
            buf_indent  = current_indent
            buf_content = content
        else:
            buf_content += ' ' + content

        # recalculate bracket depth for the whole buffer
        depth = (buf_content.count('(') + buf_content.count('[') + buf_content.count('{')
               - buf_content.count(')') - buf_content.count(']') - buf_content.count('}'))

        if depth <= 0:
            merged.append((buf_indent, buf_content))
            buf_indent  = None
            buf_content = ''
            depth       = 0

    if buf_content:
        merged.append((buf_indent or 0, buf_content))

    # ── Step 2: emit INDENT / DEDENT + line tokens ────────────────
    for indent, content in merged:
        if indent > indent_stack[-1]:
            indent_stack.append(indent)
            tokens.append(('INDENT', str(indent)))
        elif indent < indent_stack[-1]:
            while len(indent_stack) > 1 and indent_stack[-1] > indent:
                indent_stack.pop()
                tokens.append(('DEDENT', str(indent_stack[-1])))
        # (equal indent → no token)

        tokens.extend(_lex_line(content))
        tokens.append(('NEWLINE', '\n'))

    # flush remaining indents
    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(('DEDENT', '0'))

    return tokens


# ================================================================
# C PARSER
# ================================================================
C_TYPES = ('INT', 'FLOAT', 'DOUBLE', 'CHAR', 'VOID')

class CParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index  = 0
        self.output = []
        self.indent = 0

    def _line(self, text):
        self.output.append("  " * self.indent + text)

    def current(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def eat(self, tt):
        tok = self.current()
        if tok and tok[0] == tt:
            self.index += 1
            return tok
        raise SyntaxError(f"Expected {tt}, got {tok}")

    # ── Top level ─────────────────────────────────────────────────
    def parse(self):
        self._line("BEGIN")
        self.indent += 1
        while self.current():
            self.top_level()
        self.indent -= 1
        self._line("END")
        return "\n".join(self.output)

    def top_level(self):
        tok = self.current()
        if tok[0] in C_TYPES:
            self.function_or_global()
        elif tok[0] in ('IF', 'WHILE', 'FOR', 'RETURN', 'ID', 'SEMICOLON'):
            self.statement()
        else:
            self.index += 1

    def function_or_global(self):
        ret_type = self.current()[1].upper(); self.index += 1
        name = self.current()[1]; self.eat('ID')
        if self.current() and self.current()[0] == 'LPAREN':
            self.eat('LPAREN')
            params = self.param_list()
            self.eat('RPAREN')
            self._line(f"FUNCTION {name}({', '.join(params) or 'no parameters'})")
            self.indent += 1
            self.eat('LBRACE')
            while self.current() and self.current()[0] != 'RBRACE':
                self.statement()
            self.eat('RBRACE')
            self.indent -= 1
            self._line(f"END FUNCTION {name}")
        else:
            self.finish_decl(ret_type, name)
            if self.current() and self.current()[0] == 'SEMICOLON':
                self.eat('SEMICOLON')

    def param_list(self):
        params = []
        while self.current() and self.current()[0] != 'RPAREN':
            if self.current()[0] == 'COMMA': self.eat('COMMA'); continue
            if self.current()[0] in C_TYPES: self.index += 1
            if self.current() and self.current()[0] == 'ID':
                pname = self.current()[1]; self.index += 1
                while self.current() and self.current()[0] == 'LBRACKET':
                    self.eat('LBRACKET')
                    dim = ''
                    if self.current() and self.current()[0] != 'RBRACKET':
                        dim = self.current()[1]; self.index += 1
                    self.eat('RBRACKET')
                    pname += f'[{dim}]'
                params.append(pname)
        return params

    # ── Statements ────────────────────────────────────────────────
    def statement(self):
        tok = self.current()
        if tok is None: return
        if tok[0] in C_TYPES:    self.local_declaration()
        elif tok[0] == 'IF':     self.if_statement()
        elif tok[0] == 'WHILE':  self.while_statement()
        elif tok[0] == 'FOR':    self.for_statement()
        elif tok[0] == 'RETURN': self.return_statement()
        elif tok[0] == 'ID':     self.expr_statement()
        elif tok[0] == 'SEMICOLON': self.eat('SEMICOLON')
        else: self.index += 1

    def local_declaration(self):
        type_name = self.current()[1].upper(); self.index += 1
        first = True
        while True:
            if not first: self.eat('COMMA')
            first = False
            name = self.current()[1]; self.eat('ID')
            self.finish_decl(type_name, name)
            if self.current() and self.current()[0] == 'COMMA': continue
            break
        self.eat('SEMICOLON')

    def finish_decl(self, type_name, name):
        dims = []
        while self.current() and self.current()[0] == 'LBRACKET':
            self.eat('LBRACKET')
            dim = '' if self.current()[0] == 'RBRACKET' else self.expr()
            self.eat('RBRACKET')
            dims.append(dim)
        full  = name + ''.join(f'[{d}]' for d in dims)
        arr   = "ARRAY " if dims else ""
        if self.current() and self.current()[0] == 'ASSIGN':
            self.eat('ASSIGN')
            val = self.skip_brace_init() if self.current()[0] == 'LBRACE' else self.expr()
            self._line(f"DECLARE {type_name} {arr}{full} ← {val}")
        else:
            self._line(f"DECLARE {type_name} {arr}{full}")

    def skip_brace_init(self):
        self.eat('LBRACE'); depth = 1
        while self.current() and depth > 0:
            if self.current()[0] == 'LBRACE': depth += 1
            elif self.current()[0] == 'RBRACE': depth -= 1
            self.index += 1
        return "[initializer]"

    def expr_statement(self):
        name = self.current()[1]; self.eat('ID')
        lhs = name
        while self.current() and self.current()[0] == 'LBRACKET':
            self.eat('LBRACKET'); idx = self.expr(); self.eat('RBRACKET')
            lhs = f"{lhs}[{idx}]"
        tok = self.current()
        if tok and tok[0] == 'ASSIGN':
            self.eat('ASSIGN'); self._line(f"SET {lhs} ← {self.expr()}"); self.eat('SEMICOLON')
        elif tok and tok[0] == 'LPAREN':
            self.eat('LPAREN'); args = self.arg_list(); self.eat('RPAREN'); self.eat('SEMICOLON')
            label = "OUTPUT" if name in ('printf','puts','print') else f"CALL {name}"
            self._line(f"{label}({', '.join(args)})" if label.startswith('CALL') else f"{label} {', '.join(args)}")
        elif tok and tok[0] == 'INC':
            self.eat('INC'); self.eat('SEMICOLON'); self._line(f"SET {lhs} ← {lhs} + 1")
        elif tok and tok[0] == 'DEC':
            self.eat('DEC'); self.eat('SEMICOLON'); self._line(f"SET {lhs} ← {lhs} - 1")
        else:
            while self.current() and self.current()[0] != 'SEMICOLON': self.index += 1
            if self.current(): self.eat('SEMICOLON')

    def return_statement(self):
        self.eat('RETURN')
        if self.current() and self.current()[0] != 'SEMICOLON':
            self._line(f"RETURN {self.expr()}")
        else:
            self._line("RETURN")
        self.eat('SEMICOLON')

    # ── Control flow ──────────────────────────────────────────────
    def if_statement(self):
        self.eat('IF'); self.eat('LPAREN'); cond = self.condition(); self.eat('RPAREN')
        self._line(f"IF {cond} THEN"); self.indent += 1
        self.eat('LBRACE')
        while self.current() and self.current()[0] != 'RBRACE': self.statement()
        self.eat('RBRACE'); self.indent -= 1
        if self.current() and self.current()[0] == 'ELSE':
            self.eat('ELSE')
            if self.current() and self.current()[0] == 'IF':
                self._line("ELSE"); self.indent += 1; self.if_statement(); self.indent -= 1; return
            self._line("ELSE"); self.indent += 1
            self.eat('LBRACE')
            while self.current() and self.current()[0] != 'RBRACE': self.statement()
            self.eat('RBRACE'); self.indent -= 1
        self._line("END IF")

    def while_statement(self):
        self.eat('WHILE'); self.eat('LPAREN'); cond = self.condition(); self.eat('RPAREN')
        self._line(f"WHILE {cond} DO"); self.indent += 1
        self.eat('LBRACE')
        while self.current() and self.current()[0] != 'RBRACE': self.statement()
        self.eat('RBRACE'); self.indent -= 1; self._line("END WHILE")

    def for_statement(self):
        self.eat('FOR'); self.eat('LPAREN')
        init = self.for_init(); self.eat('SEMICOLON')
        cond = self.condition(); self.eat('SEMICOLON')
        upd  = self.for_update(); self.eat('RPAREN')
        self._line(f"FOR {init}, WHILE {cond}, UPDATE {upd} DO"); self.indent += 1
        self.eat('LBRACE')
        while self.current() and self.current()[0] != 'RBRACE': self.statement()
        self.eat('RBRACE'); self.indent -= 1; self._line("END FOR")

    def for_init(self):
        if self.current() and self.current()[0] in C_TYPES: self.index += 1
        name = self.current()[1]; self.eat('ID')
        if self.current() and self.current()[0] == 'ASSIGN':
            self.eat('ASSIGN'); return f"{name} ← {self.expr()}"
        return name

    def for_update(self):
        name = self.current()[1]; self.eat('ID')
        while self.current() and self.current()[0] == 'LBRACKET':
            self.eat('LBRACKET'); idx = self.expr(); self.eat('RBRACKET'); name = f"{name}[{idx}]"
        tok = self.current()
        if tok and tok[0] == 'INC':  self.eat('INC');  return f"{name} ← {name} + 1"
        if tok and tok[0] == 'DEC':  self.eat('DEC');  return f"{name} ← {name} - 1"
        if tok and tok[0] == 'ASSIGN': self.eat('ASSIGN'); return f"{name} ← {self.expr()}"
        return name

    # ── Expression parser ─────────────────────────────────────────
    def condition(self): return self.logical_or()
    def logical_or(self):
        l = self.logical_and()
        while self.current() and self.current()[0] == 'LOGOP' and self.current()[1] == '||':
            self.index += 1; l = f"{l} OR {self.logical_and()}"
        return l
    def logical_and(self):
        l = self.comparison()
        while self.current() and self.current()[0] == 'LOGOP' and self.current()[1] == '&&':
            self.index += 1; l = f"{l} AND {self.comparison()}"
        return l
    def comparison(self):
        l = self.additive()
        if self.current() and self.current()[0] == 'RELOP':
            op = self.current()[1]; self.index += 1; return f"{l} {op} {self.additive()}"
        return l
    def additive(self):
        l = self.multiplicative()
        while self.current() and self.current()[0] == 'OP' and self.current()[1] in ('+','-'):
            op = self.current()[1]; self.index += 1; l = f"{l} {op} {self.multiplicative()}"
        return l
    def multiplicative(self):
        l = self.unary()
        while self.current() and ((self.current()[0]=='OP' and self.current()[1] in ('*','/')) or self.current()[0]=='MODOP'):
            op = self.current()[1]; self.index += 1; l = f"{l} {op} {self.unary()}"
        return l
    def unary(self):
        tok = self.current()
        if tok and tok[0] == 'NOT': self.index += 1; return f"NOT {self.postfix()}"
        if tok and tok[0] == 'OP' and tok[1] == '-': self.index += 1; return f"-{self.postfix()}"
        return self.postfix()
    def postfix(self):
        tok = self.current()
        if tok is None: raise SyntaxError("Unexpected end of expression")
        if tok[0] == 'LPAREN':
            self.eat('LPAREN'); inner = self.condition(); self.eat('RPAREN'); base = f"({inner})"
        elif tok[0] == 'ID':
            self.index += 1; base = tok[1]
            if self.current() and self.current()[0] == 'LPAREN':
                self.eat('LPAREN'); args = self.arg_list(); self.eat('RPAREN')
                base = f"CALL {tok[1]}({', '.join(args)})"
            else:
                while self.current() and self.current()[0] == 'LBRACKET':
                    self.eat('LBRACKET'); idx = self.expr(); self.eat('RBRACKET'); base = f"{base}[{idx}]"
        elif tok[0] == 'NUMBER': self.index += 1; base = tok[1]
        elif tok[0] == 'STRING': self.index += 1; base = tok[1]
        else: raise SyntaxError(f"Unexpected token: {tok}")
        return base

    def expr(self): return self.condition()
    def arg_list(self):
        args = []
        while self.current() and self.current()[0] != 'RPAREN':
            if self.current()[0] == 'COMMA': self.eat('COMMA')
            else: args.append(self.expr())
        return args


# ================================================================
# PYTHON PARSER  (INDENT / DEDENT block aware)
# ================================================================
class PythonParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index  = 0
        self.output = []
        self.indent = 0

    def _line(self, text):
        self.output.append("  " * self.indent + text)

    def current(self):
        """Return next non-NEWLINE token, advancing past NEWLINEs."""
        while self.index < len(self.tokens) and self.tokens[self.index][0] == 'NEWLINE':
            self.index += 1
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def eat(self, tt):
        tok = self.current()
        if tok and tok[0] == tt:
            self.index += 1
            return tok
        raise SyntaxError(f"Expected {tt}, got {tok}")

    # ── Block (INDENT … DEDENT) ───────────────────────────────────
    def block(self):
        if self.current() and self.current()[0] == 'INDENT':
            self.eat('INDENT')
        while self.current() and self.current()[0] != 'DEDENT':
            self.statement()
        if self.current() and self.current()[0] == 'DEDENT':
            self.eat('DEDENT')

    # ── Top level ─────────────────────────────────────────────────
    def parse(self):
        self._line("BEGIN")
        self.indent += 1
        while self.current():
            self.statement()
        self.indent -= 1
        self._line("END")
        return "\n".join(self.output)

    def statement(self):
        tok = self.current()
        if not tok or tok[0] in ('DEDENT', 'INDENT'): return
        if   tok[0] == 'CLASS':  self.class_def()
        elif tok[0] == 'DEF':    self.func_def()
        elif tok[0] == 'IF':     self.if_stmt()
        elif tok[0] == 'WHILE':  self.while_stmt()
        elif tok[0] == 'FOR':    self.for_stmt()
        elif tok[0] == 'RETURN': self.return_stmt()
        elif tok[0] == 'PRINT':  self.print_stmt()
        elif tok[0] == 'ID':     self.assign_or_call()
        else: self.index += 1

    # ── Class definition ──────────────────────────────────────────
    def class_def(self):
        self.eat('CLASS')
        name = self.current()[1]; self.eat('ID')
        if self.current() and self.current()[0] == 'LPAREN':
            self.eat('LPAREN')
            while self.current() and self.current()[0] != 'RPAREN': self.index += 1
            self.eat('RPAREN')
        self.eat('COLON')
        self._line(f"CLASS {name}")
        self.indent += 1
        self.block()
        self.indent -= 1
        self._line(f"END CLASS {name}")

    # ── Function / method ─────────────────────────────────────────
    def func_def(self):
        self.eat('DEF')
        name   = self.current()[1]; self.eat('ID')
        self.eat('LPAREN')
        params = []
        while self.current() and self.current()[0] != 'RPAREN':
            if self.current()[0] == 'COMMA': self.eat('COMMA')
            else: params.append(self.current()[1]); self.index += 1
        self.eat('RPAREN'); self.eat('COLON')
        visible = [p for p in params if p != 'self']
        self._line(f"FUNCTION {name}({', '.join(visible) or 'no parameters'})")
        self.indent += 1
        self.block()
        self.indent -= 1
        self._line(f"END FUNCTION {name}")

    # ── Assignment / standalone call ──────────────────────────────
    def assign_or_call(self):
        """
        Handles:  name[...] = rhs
                  name.attr... = rhs
                  name.method(...)
                  name(...)
                  name AUGASSIGN rhs
        """
        name = self.current()[1]; self.eat('ID')

        # build dotted name  self.graph
        while self.current() and self.current()[0] == 'DOT':
            self.eat('DOT'); attr = self.current()[1]; self.eat('ID')
            name = f"{name}.{attr}"

        # standalone function / method call
        if self.current() and self.current()[0] == 'LPAREN':
            self.eat('LPAREN'); args = self._arg_list(); self.eat('RPAREN')
            self._line(f"CALL {name}({', '.join(args)})")
            return

        # array subscripts on LHS  a[i][j]
        while self.current() and self.current()[0] == 'LBRACKET':
            self.eat('LBRACKET'); idx = self.expression(); self.eat('RBRACKET')
            name = f"{name}[{idx}]"

        tok = self.current()
        if tok and tok[0] == 'ASSIGN':
            self.eat('ASSIGN'); self._line(f"SET {name} ← {self.expression()}")
        elif tok and tok[0] == 'AUGASSIGN':
            op = tok[1][0]; self.index += 1  # e.g. '+=' → '+'
            self._line(f"SET {name} ← {name} {op} {self.expression()}")
        # else: bare expression — ignore

    # ── Control flow ──────────────────────────────────────────────
    def if_stmt(self):
        self.eat('IF'); cond = self.condition(); self.eat('COLON')
        self._line(f"IF {cond} THEN")
        self.indent += 1; self.block(); self.indent -= 1
        while self.current() and self.current()[0] == 'ELIF':
            self.eat('ELIF'); cond = self.condition(); self.eat('COLON')
            self._line(f"ELSE IF {cond} THEN")
            self.indent += 1; self.block(); self.indent -= 1
        if self.current() and self.current()[0] == 'ELSE':
            self.eat('ELSE'); self.eat('COLON')
            self._line("ELSE")
            self.indent += 1; self.block(); self.indent -= 1
        self._line("END IF")

    def while_stmt(self):
        self.eat('WHILE'); cond = self.condition(); self.eat('COLON')
        self._line(f"WHILE {cond} DO")
        self.indent += 1; self.block(); self.indent -= 1
        self._line("END WHILE")

    def for_stmt(self):
        self.eat('FOR'); var = self.current()[1]; self.eat('ID')
        self.eat('IN'); iterable = self.expression(); self.eat('COLON')
        self._line(f"FOR EACH {var} IN {iterable} DO")
        self.indent += 1; self.block(); self.indent -= 1
        self._line("END FOR")

    def return_stmt(self):
        self.eat('RETURN')
        if self.current() and self.current()[0] not in ('NEWLINE','DEDENT'):
            self._line(f"RETURN {self.expression()}")
        else:
            self._line("RETURN")

    def print_stmt(self):
        self.eat('PRINT'); self.eat('LPAREN')
        args = self._arg_list(); self.eat('RPAREN')
        self._line(f"OUTPUT {', '.join(args)}")

    # ── Expressions ───────────────────────────────────────────────
    def _arg_list(self):
        args = []
        while self.current() and self.current()[0] != 'RPAREN':
            if self.current()[0] == 'COMMA': self.eat('COMMA')
            else: args.append(self.expression())
        return args

    def condition(self):
        l = self.comparison()
        while self.current() and self.current()[0] in ('AND','OR'):
            op = self.current()[1].upper(); self.index += 1
            l = f"{l} {op} {self.comparison()}"
        return l

    def comparison(self):
        l = self.expression()
        if self.current() and self.current()[0] == 'RELOP':
            op = self.current()[1]; self.index += 1
            return f"{l} {op} {self.expression()}"
        return l

    def expression(self):
        if self.current() and self.current()[0] == 'NOT':
            self.index += 1; return f"NOT {self.term()}"
        l = self.term()
        while self.current() and self.current()[0] == 'OP':
            op = self.current()[1]; self.index += 1; l = f"{l} {op} {self.term()}"
        return l

    # ── List-comprehension lookahead ──────────────────────────────
    def _is_comprehension(self):
        """Peek ahead: is the current [...] a list comprehension?"""
        save = self.index; depth = 0
        while self.index < len(self.tokens):
            tt = self.tokens[self.index][0]
            if tt in ('LBRACKET','LPAREN','LBRACE'): depth += 1
            elif tt in ('RBRACKET','RPAREN','RBRACE'):
                depth -= 1
                if depth == 0: self.index = save; return False
            elif tt == 'FOR' and depth == 1:
                self.index = save; return True
            self.index += 1
        self.index = save; return False

    def _skip_brackets(self):
        """Consume from opening [ to its matching ]."""
        open_tt  = self.tokens[self.index][0]
        close_tt = {'LBRACKET':'RBRACKET','LPAREN':'RPAREN','LBRACE':'RBRACE'}[open_tt]
        self.index += 1; depth = 1
        while self.current() and depth > 0:
            tt = self.tokens[self.index][0]
            if tt == open_tt: depth += 1
            elif tt == close_tt: depth -= 1
            self.index += 1

    def term(self):
        tok = self.current()
        if tok is None: raise SyntaxError("Unexpected end of expression")

        # ── identifier (possibly attribute chain / call / subscript) ──
        if tok[0] == 'ID':
            self.index += 1; name = tok[1]
            # dot-chain: self.graph, self.V
            while self.current() and self.current()[0] == 'DOT':
                self.eat('DOT'); attr = self.current()[1]; self.eat('ID')
                name = f"{name}.{attr}"
            # function / method call
            if self.current() and self.current()[0] == 'LPAREN':
                self.eat('LPAREN'); args = self._arg_list(); self.eat('RPAREN')
                return f"CALL {name}({', '.join(args)})"
            # subscripts: a[i], a[i][j]
            while self.current() and self.current()[0] == 'LBRACKET':
                self.eat('LBRACKET'); idx = self.expression(); self.eat('RBRACKET')
                name = f"{name}[{idx}]"
            return name

        if tok[0] == 'NUMBER':  self.index += 1; return tok[1]
        if tok[0] == 'STRING':  self.index += 1; return tok[1]
        if tok[0] in ('TRUE','FALSE','NONE'): self.index += 1; return tok[1]

        # ── parenthesised expression ──────────────────────────────
        if tok[0] == 'LPAREN':
            self.eat('LPAREN'); e = self.condition(); self.eat('RPAREN')
            return f"({e})"

        # ── list literal or comprehension ─────────────────────────
        if tok[0] == 'LBRACKET':
            if self._is_comprehension():
                self._skip_brackets(); return '[list comprehension]'
            self.eat('LBRACKET')
            items = []
            while self.current() and self.current()[0] != 'RBRACKET':
                if self.current()[0] == 'COMMA': self.eat('COMMA')
                else: items.append(self.expression())
            self.eat('RBRACKET')
            # Don't expand huge literals — summarise if > 6 elements
            if len(items) > 6: return f"[{items[0]}, {items[1]}, ... ({len(items)} items)]"
            return f"[{', '.join(items)}]"

        raise SyntaxError(f"Unexpected token in expression: {tok}")


# ================================================================
# UNIFIED INTERFACE
# ================================================================
def lexer(code, language='c'):
    return python_lexer(code) if language == 'python' else c_lexer(code)

def Parser(tokens, language='c'):
    return PythonParser(tokens) if language == 'python' else CParser(tokens)
