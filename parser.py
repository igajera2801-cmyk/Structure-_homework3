"""
parser.py - Recursive Descent Parser with Location Tracking

Parses tokens into an Abstract Syntax Tree (AST) where each node
contains source location information.
"""

from typing import List, Dict, Any, Optional
from tokenizer import Token, tokenize


class ParseError(Exception):
    """Exception raised for parsing errors."""
    def __init__(self, message: str, token: Token):
        self.token = token
        super().__init__(f"Parse error at line {token.line}, column {token.column}: {message}")


class Parser:
    """
    Recursive descent parser for the language.
    
    Grammar (simplified):
        program     -> statement*
        statement   -> assignment | print_stmt | if_stmt | while_stmt | block | expr_stmt
        assignment  -> IDENTIFIER '=' expression ';'?
        print_stmt  -> 'print' expression ';'?
        if_stmt     -> 'if' '(' expression ')' statement ('else' statement)?
        while_stmt  -> 'while' '(' expression ')' statement
        block       -> '{' statement* '}'
        expr_stmt   -> expression ';'?
        expression  -> logical_or
        logical_or  -> logical_and ('||' logical_and)*
        logical_and -> equality ('&&' equality)*
        equality    -> comparison (('==' | '!=') comparison)*
        comparison  -> term (('<' | '>' | '<=' | '>=') term)*
        term        -> factor (('+' | '-') factor)*
        factor      -> unary (('*' | '/' | '%') unary)*
        unary       -> ('!' | '-') unary | primary
        primary     -> NUMBER | STRING | BOOLEAN | IDENTIFIER | '(' expression ')'
    """
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def current(self) -> Token:
        """Get the current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF
    
    def peek(self, offset: int = 0) -> Token:
        """Look ahead at a token."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]
    
    def advance(self) -> Token:
        """Move to the next token and return the previous one."""
        token = self.current()
        if self.pos < len(self.tokens):
            self.pos += 1
        return token
    
    def match(self, *tags: str) -> bool:
        """Check if current token matches any of the given tags."""
        return self.current().tag in tags
    
    def consume(self, tag: str, message: str) -> Token:
        """Consume a token of the expected type or raise an error."""
        if self.current().tag == tag:
            return self.advance()
        raise ParseError(message, self.current())
    
    def make_node(self, tag: str, token: Token, **kwargs) -> Dict[str, Any]:
        """Create an AST node with location information."""
        return {
            'tag': tag,
            'line': token.line,
            'column': token.column,
            **kwargs
        }
    
    # ===== Parsing Methods =====
    
    def parse(self) -> Dict[str, Any]:
        """Parse the entire program."""
        statements = []
        start_token = self.current()
        
        while not self.match('EOF'):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        return self.make_node('program', start_token, statements=statements)
    
    def parse_statement(self) -> Optional[Dict[str, Any]]:
        """Parse a single statement."""
        # Skip semicolons
        while self.match(';'):
            self.advance()
        
        if self.match('EOF'):
            return None
        
        if self.match('print'):
            return self.parse_print()
        elif self.match('if'):
            return self.parse_if()
        elif self.match('while'):
            return self.parse_while()
        elif self.match('{'):
            return self.parse_block()
        elif self.match('identifier') and self.peek(1).tag == '=':
            return self.parse_assignment()
        else:
            return self.parse_expression_statement()
    
    def parse_assignment(self) -> Dict[str, Any]:
        """Parse an assignment statement: identifier = expression"""
        name_token = self.consume('identifier', "Expected variable name")
        self.consume('=', "Expected '=' in assignment")
        value = self.parse_expression()
        
        # Optional semicolon
        if self.match(';'):
            self.advance()
        
        return self.make_node('assign', name_token,
                              name=name_token.value,
                              value=value)
    
    def parse_print(self) -> Dict[str, Any]:
        """Parse a print statement."""
        print_token = self.consume('print', "Expected 'print'")
        value = self.parse_expression()
        
        if self.match(';'):
            self.advance()
        
        return self.make_node('print', print_token, value=value)
    
    def parse_if(self) -> Dict[str, Any]:
        """Parse an if statement."""
        if_token = self.consume('if', "Expected 'if'")
        self.consume('(', "Expected '(' after 'if'")
        condition = self.parse_expression()
        self.consume(')', "Expected ')' after condition")
        
        then_branch = self.parse_statement()
        else_branch = None
        
        if self.match('else'):
            self.advance()
            else_branch = self.parse_statement()
        
        # Optional semicolon after if statement
        if self.match(';'):
            self.advance()
        
        return self.make_node('if', if_token,
                              condition=condition,
                              then=then_branch,
                              else_=else_branch)
    
    def parse_while(self) -> Dict[str, Any]:
        """Parse a while statement."""
        while_token = self.consume('while', "Expected 'while'")
        self.consume('(', "Expected '(' after 'while'")
        condition = self.parse_expression()
        self.consume(')', "Expected ')' after condition")
        
        body = self.parse_statement()
        
        if self.match(';'):
            self.advance()
        
        return self.make_node('while', while_token,
                              condition=condition,
                              body=body)
    
    def parse_block(self) -> Dict[str, Any]:
        """Parse a block of statements."""
        open_brace = self.consume('{', "Expected '{'")
        statements = []
        
        while not self.match('}') and not self.match('EOF'):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        self.consume('}', "Expected '}'")
        
        return self.make_node('block', open_brace, statements=statements)
    
    def parse_expression_statement(self) -> Dict[str, Any]:
        """Parse an expression as a statement."""
        expr = self.parse_expression()
        
        if self.match(';'):
            self.advance()
        
        return expr
    
    def parse_expression(self) -> Dict[str, Any]:
        """Parse an expression (entry point for expression parsing)."""
        return self.parse_logical_or()
    
    def parse_logical_or(self) -> Dict[str, Any]:
        """Parse logical OR expressions."""
        left = self.parse_logical_and()
        
        while self.match('||'):
            op_token = self.advance()
            right = self.parse_logical_and()
            left = self.make_node('binary', op_token,
                                  op='||',
                                  left=left,
                                  right=right)
        
        return left
    
    def parse_logical_and(self) -> Dict[str, Any]:
        """Parse logical AND expressions."""
        left = self.parse_equality()
        
        while self.match('&&'):
            op_token = self.advance()
            right = self.parse_equality()
            left = self.make_node('binary', op_token,
                                  op='&&',
                                  left=left,
                                  right=right)
        
        return left
    
    def parse_equality(self) -> Dict[str, Any]:
        """Parse equality expressions."""
        left = self.parse_comparison()
        
        while self.match('==', '!='):
            op_token = self.advance()
            right = self.parse_comparison()
            left = self.make_node('binary', op_token,
                                  op=op_token.tag,
                                  left=left,
                                  right=right)
        
        return left
    
    def parse_comparison(self) -> Dict[str, Any]:
        """Parse comparison expressions."""
        left = self.parse_term()
        
        while self.match('<', '>', '<=', '>='):
            op_token = self.advance()
            right = self.parse_term()
            left = self.make_node('binary', op_token,
                                  op=op_token.tag,
                                  left=left,
                                  right=right)
        
        return left
    
    def parse_term(self) -> Dict[str, Any]:
        """Parse addition/subtraction expressions."""
        left = self.parse_factor()
        
        while self.match('+', '-'):
            op_token = self.advance()
            right = self.parse_factor()
            left = self.make_node('binary', op_token,
                                  op=op_token.tag,
                                  left=left,
                                  right=right)
        
        return left
    
    def parse_factor(self) -> Dict[str, Any]:
        """Parse multiplication/division expressions."""
        left = self.parse_unary()
        
        while self.match('*', '/', '%'):
            op_token = self.advance()
            right = self.parse_unary()
            left = self.make_node('binary', op_token,
                                  op=op_token.tag,
                                  left=left,
                                  right=right)
        
        return left
    
    def parse_unary(self) -> Dict[str, Any]:
        """Parse unary expressions."""
        if self.match('!', '-'):
            op_token = self.advance()
            operand = self.parse_unary()
            return self.make_node('unary', op_token,
                                  op=op_token.tag,
                                  operand=operand)
        
        return self.parse_primary()
    
    def parse_primary(self) -> Dict[str, Any]:
        """Parse primary expressions (literals, identifiers, parenthesized expressions)."""
        token = self.current()
        
        if self.match('number'):
            self.advance()
            # Handle both int and float
            value = float(token.value) if '.' in token.value else int(token.value)
            return self.make_node('number', token, value=value)
        
        elif self.match('string'):
            self.advance()
            # Remove quotes and handle escape sequences
            value = token.value[1:-1]  # Remove surrounding quotes
            value = value.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'")
            return self.make_node('string', token, value=value)
        
        elif self.match('boolean'):
            self.advance()
            value = token.value == 'TRUE'
            return self.make_node('boolean', token, value=value)
        
        elif self.match('identifier'):
            self.advance()
            return self.make_node('identifier', token, name=token.value)
        
        elif self.match('('):
            self.advance()
            expr = self.parse_expression()
            self.consume(')', "Expected ')' after expression")
            return expr
        
        else:
            raise ParseError(f"Unexpected token: {token.tag}", token)


def parse(source_or_tokens) -> Dict[str, Any]:
    """
    Parse source code or tokens into an AST.
    
    Args:
        source_or_tokens: Either a source string or a list of tokens
        
    Returns:
        AST dictionary
    """
    if isinstance(source_or_tokens, str):
        tokens = tokenize(source_or_tokens)
    else:
        tokens = source_or_tokens
    
    parser = Parser(tokens)
    return parser.parse()


# Test functions
def test_parse_number():
    ast = parse("42")
    stmt = ast['statements'][0]
    assert stmt['tag'] == 'number'
    assert stmt['value'] == 42
    print("✓ test_parse_number passed")


def test_parse_assignment():
    ast = parse("x = 5")
    stmt = ast['statements'][0]
    assert stmt['tag'] == 'assign'
    assert stmt['name'] == 'x'
    assert stmt['value']['value'] == 5
    print("✓ test_parse_assignment passed")


def test_parse_binary():
    ast = parse("2 + 3 * 4")
    stmt = ast['statements'][0]
    assert stmt['tag'] == 'binary'
    assert stmt['op'] == '+'
    assert stmt['left']['value'] == 2
    assert stmt['right']['op'] == '*'
    print("✓ test_parse_binary passed")


def test_parse_if():
    ast = parse("if (x == 5) { y = 10 }")
    stmt = ast['statements'][0]
    assert stmt['tag'] == 'if'
    assert stmt['condition']['op'] == '=='
    print("✓ test_parse_if passed")


def test_parse_while():
    ast = parse("while (x < 10) { x = x + 1 }")
    stmt = ast['statements'][0]
    assert stmt['tag'] == 'while'
    print("✓ test_parse_while passed")


def test_location_info():
    source = "x = 5\ny = 10"
    ast = parse(source)
    # First assignment should be at line 1
    assert ast['statements'][0]['line'] == 1
    # Second assignment should be at line 2
    assert ast['statements'][1]['line'] == 2
    print("✓ test_location_info passed")


if __name__ == "__main__":
    test_parse_number()
    test_parse_assignment()
    test_parse_binary()
    test_parse_if()
    test_parse_while()
    test_location_info()
    print("\nAll parser tests passed!")
