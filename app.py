import re

# -----------------------------
# LEXICAL ANALYZER
# -----------------------------
TOKENS = [
    ('IF', r'if'),
    ('ELSE', r'else'),
    ('WHILE', r'while'),
    ('FOR', r'for'),
    ('SWITCH', r'switch'),
    ('CASE', r'case'),
    ('DEFAULT', r'default'),
    ('BREAK', r'break'),
    ('NUMBER', r'\d+'),
    ('RELOP', r'(==|!=|>=|<=|>|<)'),
    ('OP', r'[+\-*/]'),
    ('ASSIGN', r'='),
    ('COLON', r':'),
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
# PARSER + PSEUDOCODE GENERATOR
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
        while self.current():
            self.statement()
        self.output.append("END")
        return "\n".join(self.output)

    # -----------------------------
    # STATEMENTS
    # -----------------------------
    def statement(self):
        token = self.current()
        if token[0] == 'IF':
            self.if_statement()
        elif token[0] == 'WHILE':
            self.while_statement()
        elif token[0] == 'FOR':
            self.for_statement()
        elif token[0] == 'SWITCH':
            self.switch_statement()
        elif token[0] == 'ID':
            self.assignment()
        else:
            raise SyntaxError(f"Invalid statement: {token}")

    def assignment(self):
        var = self.current()[1]
        self.eat('ID')
        self.eat('ASSIGN')
        expr = self.expression()
        self.eat('SEMICOLON')
        self.output.append(f"SET {var} TO {expr}")

    def assignment_inline(self):
        var = self.current()[1]
        self.eat('ID')
        self.eat('ASSIGN')
        expr = self.expression()
        self.eat('SEMICOLON')
        return f"{var} = {expr}"

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
            raise SyntaxError(f"Expected term, got {token}")

    # -----------------------------
    # CONTROL STRUCTURES
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

    # -------- FIXED FOR LOOP --------
    def for_statement(self):
        self.eat('FOR')
        self.eat('LPAREN')

        init = self.assignment_inline()   # has semicolon
        cond_left = self.expression()
        op = self.current()[1]
        self.eat('RELOP')
        cond_right = self.expression()
        self.eat('SEMICOLON')

        update = self.for_update()        # NO semicolon

        self.eat('RPAREN')

        self.output.append(
            f"FOR {init} WHILE {cond_left} {op} {cond_right} DO {update}"
        )

        self.eat('LBRACE')
        while self.current() and self.current()[0] != 'RBRACE':
            self.statement()
        self.eat('RBRACE')
        self.output.append("END FOR")

    def for_update(self):
        var = self.current()[1]
        self.eat('ID')
        self.eat('ASSIGN')
        expr = self.expression()
        return f"{var} = {expr}"

    def switch_statement(self):
        self.eat('SWITCH')
        self.eat('LPAREN')
        expr = self.expression()
        self.eat('RPAREN')

        self.output.append(f"SWITCH {expr}")
        self.eat('LBRACE')

        while self.current() and self.current()[0] in ('CASE', 'DEFAULT'):
            if self.current()[0] == 'CASE':
                self.eat('CASE')
                value = self.expression()
                self.eat('COLON')
                self.output.append(f"CASE {value}")
            else:
                self.eat('DEFAULT')
                self.eat('COLON')
                self.output.append("DEFAULT")

            while self.current() and self.current()[0] not in ('CASE', 'DEFAULT', 'RBRACE'):
                if self.current()[0] == 'BREAK':
                    self.eat('BREAK')
                    self.eat('SEMICOLON')
                    self.output.append("BREAK")
                else:
                    self.statement()

        self.eat('RBRACE')
        self.output.append("END SWITCH")


# -----------------------------
# DRIVER CODE (USER INPUT)
# -----------------------------
if __name__ == "__main__":
    print("Enter C-like code (type END on a new line to finish):")

    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    code = "\n".join(lines)

    tokens = lexer(code)
    print("\nTokens:")
    print(tokens)

    parser = Parser(tokens)
    pseudocode = parser.parse()

    print("\nGenerated Pseudo Code:\n")
    print(pseudocode)
