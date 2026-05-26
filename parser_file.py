import re

# -----------------------------
# LEXICAL ANALYZER (C SUBSET)
# -----------------------------
TOKENS = [
    ('INT', r'int'),
    ('IF', r'if'),
    ('ELSE', r'else'),
    ('WHILE', r'while'),
    ('FOR', r'for'),

    ('NUMBER', r'\d+'),
    ('RELOP', r'(==|!=|>=|<=|>|<)'),
    ('OP', r'[+\-*/]'),
    ('ASSIGN', r'='),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),
    ('SEMICOLON', r';'),

    ('ID', r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('SKIP', r'[ \t\n]+'),
]

def lexer(code):
    tokens = []
    pos = 0
    while pos < len(code):
        match = None
        for token_type, pattern in TOKENS:
            regex = re.compile(pattern)
            match = regex.match(code[pos:])
            if match:
                if token_type != 'SKIP':
                    tokens.append((token_type, match.group()))
                pos += match.end()
                break
        if not match:
            raise SyntaxError(f"Invalid character: {code[pos]}")
    return tokens


# -----------------------------
# PARSER (C SYNTAX SUBSET)
# -----------------------------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.output = []

    def current(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def eat(self, token_type):
        if self.current() and self.current()[0] == token_type:
            self.index += 1
        else:
            raise SyntaxError(f"Expected {token_type}, got {self.current()}")

    def parse(self):
        self.output.append("BEGIN")
        while self.current() is not None:
            self.statement()
        self.output.append("END")
        return "\n".join(self.output)

    # -----------------------------
    # STATEMENTS
    # -----------------------------
    def statement(self):
        token = self.current()

        if token[0] == 'INT':
            self.declaration()
        elif token[0] == 'ID':
            self.assignment()
        elif token[0] == 'IF':
            self.if_statement()
        elif token[0] == 'WHILE':
            self.while_statement()
        elif token[0] == 'FOR':
            self.for_statement()
        else:
            raise SyntaxError(f"Invalid statement: {token}")

    # -----------------------------
    # DECLARATION
    # -----------------------------
    def declaration(self):
        self.eat('INT')
        var = self.current()[1]
        self.eat('ID')

        if self.current() and self.current()[0] == 'ASSIGN':
            self.eat('ASSIGN')
            expr = self.expression()
            self.output.append(f"DECLARE {var} = {expr}")
        else:
            self.output.append(f"DECLARE {var}")

        self.eat('SEMICOLON')

    # -----------------------------
    # ASSIGNMENT
    # -----------------------------
    def assignment(self):
        var = self.current()[1]
        self.eat('ID')
        self.eat('ASSIGN')
        expr = self.expression()
        self.eat('SEMICOLON')
        self.output.append(f"SET {var} TO {expr}")

    # -----------------------------
    # EXPRESSIONS
    # -----------------------------
    def expression(self):
        left = self.term()
        while self.current() and self.current()[0] == 'OP':
            op = self.current()[1]
            self.eat('OP')
            right = self.term()
            left = f"{left} {op} {right}"
        return left

    def term(self):
        token = self.current()
        if token[0] == 'ID':
            self.eat('ID')
            return token[1]
        elif token[0] == 'NUMBER':
            self.eat('NUMBER')
            return token[1]
        else:
            raise SyntaxError("Invalid expression")

    # -----------------------------
    # IF-ELSE (FIXED)
    # -----------------------------
    def if_statement(self):
        self.eat('IF')
        self.eat('LPAREN')

        left = self.expression()
        op = self.current()[1]
        self.eat('RELOP')
        right = self.expression()

        self.eat('RPAREN')

        self.output.append(f"IF {left} {op} {right} THEN")
        self.eat('LBRACE')

        while self.current() and self.current()[0] != 'RBRACE':
            self.statement()

        self.eat('RBRACE')

        if self.current() and self.current()[0] == 'ELSE':
            self.eat('ELSE')
            self.output.append("ELSE")

            self.eat('LBRACE')
            while self.current() and self.current()[0] != 'RBRACE':
                self.statement()
            self.eat('RBRACE')

        self.output.append("END IF")

    # -----------------------------
    # WHILE
    # -----------------------------
    def while_statement(self):
        self.eat('WHILE')
        self.eat('LPAREN')

        left = self.expression()
        op = self.current()[1]
        self.eat('RELOP')
        right = self.expression()

        self.eat('RPAREN')

        self.output.append(f"WHILE {left} {op} {right} DO")
        self.eat('LBRACE')

        while self.current() and self.current()[0] != 'RBRACE':
            self.statement()

        self.eat('RBRACE')
        self.output.append("END WHILE")

    # -----------------------------
    # FOR
    # -----------------------------
    def for_statement(self):
        self.eat('FOR')
        self.eat('LPAREN')

        init = self.assignment_inline()
        left = self.expression()
        op = self.current()[1]
        self.eat('RELOP')
        right = self.expression()
        self.eat('SEMICOLON')
        update = self.assignment_inline()

        self.eat('RPAREN')

        self.output.append(f"FOR LOOP WHILE {left} {op} {right}")
        self.output.append(f"INITIALIZE {init}")
        self.output.append(f"UPDATE {update}")

        self.eat('LBRACE')
        while self.current() and self.current()[0] != 'RBRACE':
            self.statement()
        self.eat('RBRACE')

        self.output.append("END FOR")

    def assignment_inline(self):
        var = self.current()[1]
        self.eat('ID')
        self.eat('ASSIGN')
        expr = self.expression()
        return f"{var} = {expr}"