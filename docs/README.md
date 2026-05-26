# Documentation

This folder contains the documentation for the Pseudo Code Generator Compiler Design project.

## Table of Contents

- [Project Overview](#project-overview)
- [Workflow](#workflow)
- [Compiler Pipeline](#compiler-pipeline)
- [Module Descriptions](#module-descriptions)

## Project Overview

The Pseudo Code Generator is a compiler design project that converts source code into human-readable pseudo code. It processes input through multiple stages, transforming raw text into an abstract syntax tree and finally generating structured pseudo code output.

## Workflow

The entire project follows a systematic workflow from input to output:

1. **Input Reception** - Raw source code is received as input
2. **Lexical Analysis** - The lexer tokenizes the input into meaningful units
3. **Parsing** - The parser builds an abstract syntax tree from tokens
4. **Semantic Analysis** - The analyzer validates the AST structure and types
5. **Code Generation** - The generator converts the AST into pseudo code
6. **Output** - The final pseudo code is delivered to the user

## Compiler Pipeline

### Stage 1: Lexical Analysis (Lexer)

**What it does:**
- Scans the input source code character by character
- Identifies patterns and creates tokens
- Removes whitespace and comments
- Classifies tokens by type (keywords, identifiers, operators, literals, etc.)

**Input:** Raw source code as a string
**Output:** Stream of tokens with metadata (type, value, line number)

**How it works:**
- Maintains a current position in the input
- Reads characters and matches them against token patterns
- Creates token objects with classification
- Continues until end of input is reached

### Stage 2: Parsing (Parser)

**What it does:**
- Reads the token stream from the lexer
- Builds an Abstract Syntax Tree (AST) representing the code structure
- Validates syntax against grammar rules
- Handles operator precedence and associativity

**Input:** Stream of tokens from the lexer
**Output:** Abstract Syntax Tree (AST)

**How it works:**
- Uses recursive descent parsing approach
- Matches token sequences against grammar productions
- Creates AST nodes for statements, expressions, and declarations
- Reports syntax errors if tokens don't match expected patterns

### Stage 3: Semantic Analysis (Analyzer)

**What it does:**
- Validates the AST structure and logic
- Checks variable declarations and usage
- Verifies type compatibility
- Builds symbol tables for scope management

**Input:** Abstract Syntax Tree
**Output:** Validated AST with symbol information

**How it works:**
- Performs depth-first traversal of the AST
- Maintains scope information for variables and functions
- Checks consistency of variable declarations and uses
- Annotates AST nodes with type and scope information

### Stage 4: Code Generation (Code Generator)

**What it does:**
- Traverses the validated AST
- Converts each node into pseudo code statements
- Handles indentation and formatting
- Generates readable, structured output

**Input:** Validated Abstract Syntax Tree
**Output:** Pseudo code text

**How it works:**
- Recursively visits each AST node
- Generates appropriate pseudo code for each node type
- Maintains proper indentation levels
- Combines output from child nodes into parent pseudo code

## Module Descriptions

### Lexer Module

Responsible for breaking down source code into tokens.

**Key Functions:**
- `tokenize()` - Converts input string into token stream
- `identifyTokenType()` - Determines the type of each token
- `createToken()` - Constructs token objects with metadata

**Token Types Handled:**
- Keywords (if, else, for, while, function, etc.)
- Identifiers (variable names, function names)
- Operators (+, -, *, /, =, ==, etc.)
- Literals (numbers, strings, booleans)
- Delimiters ({, }, (, ), [, ], ;, comma)

### Parser Module

Converts token stream into an Abstract Syntax Tree.

**Key Functions:**
- `parse()` - Main entry point for parsing
- `parseStatement()` - Parses individual statements
- `parseExpression()` - Parses expressions with proper precedence
- `parseFunction()` - Parses function declarations

**AST Node Types:**
- Program node (root of the tree)
- Statement nodes (if, for, while, assignment, etc.)
- Expression nodes (binary operations, function calls, literals)
- Declaration nodes (function and variable declarations)

### Analyzer Module

Performs semantic validation on the AST.

**Key Functions:**
- `analyze()` - Main analysis entry point
- `checkDeclarations()` - Validates all variables are declared
- `checkTypes()` - Verifies type consistency
- `buildSymbolTable()` - Creates scope and symbol information

**Validations Performed:**
- Variables are declared before use
- Function calls match declared functions
- Variable types are consistent with usage
- Scope rules are followed

### Code Generator Module

Transforms the validated AST into pseudo code.

**Key Functions:**
- `generate()` - Main code generation entry point
- `generateStatement()` - Creates pseudo code for statements
- `generateExpression()` - Creates pseudo code for expressions
- `generateFunction()` - Creates pseudo code for functions

**Pseudo Code Features:**
- Clear indentation showing code blocks
- Natural language-like keywords
- Explicit control flow representation
- Comments explaining complex logic

---

## End-to-End Example

```
INPUT: JavaScript Code
-----
function add(a, b) {
  return a + b;
}

LEXER OUTPUT: Token Stream
-----
[Function] [Identifier:add] [LParen] [Identifier:a] [Comma] [Identifier:b] [RParen] [LBrace] [Return] [Identifier:a] [Plus] [Identifier:b] [Semicolon] [RBrace]

PARSER OUTPUT: AST
-----
Program
├── FunctionDeclaration
│   ├── name: "add"
│   ├── parameters: [a, b]
│   └── body: BlockStatement
│       └── ReturnStatement
│           └── BinaryExpression (+)
│               ├── left: Identifier (a)
│               └── right: Identifier (b)

ANALYZER OUTPUT: Validated AST
-----
(Same structure with type information added)
- a: number
- b: number
- return type: number

CODE GENERATOR OUTPUT: Pseudo Code
-----
FUNCTION add(a, b)
  RETURN a + b
END FUNCTION
```

This workflow ensures that the source code is correctly understood, validated, and converted into clear, readable pseudo code that represents the program's logic without language-specific syntax.
