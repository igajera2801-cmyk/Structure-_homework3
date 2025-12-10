"""
tokenizer.py - Lexical Analyzer with Location Tracking

Converts source code into a stream of tokens, each with line/column information.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Token:
    """A token with its value, type, and source location."""
    tag: str           # Token type (e.g., 'number', 'identifier', '+')
    value: str         # The actual text
    line: int          # Line number (1-indexed)
    column: int        # Column number (1-indexed)
    
    def __repr__(self):
        return f"Token({self.tag!r}, {self.value!r}, line={self.line}, col={self.column})"


# Token patterns - order matters! More specific patterns first.
PATTERNS = [
    # Comments (must come before division operator)
    (r'//[^\n]*', 'comment'),
    (r'#[^\n]*', 'comment'),
    
    # Keywords (must come before identifier)
    (r'\bTRUE\b', 'boolean'),
    (r'\bFALSE\b', 'boolean'),
    (r'\bprint\b', 'print'),
    (r'\bif\b', 'if'),
    (r'\belse\b', 'else'),
    (r'\bwhile\b', 'while'),
    (r'\bfor\b', 'for'),
    (r'\bbreak\b', 'break'),
    (r'\bcontinue\b', 'continue'),
    (r'\breturn\b', 'return'),
    (r'\bfunction\b', 'function'),
    (r'\band\b', '&&'),
    (r'\bor\b', '||'),
    (r'\bnot\b', '!'),
    
    # Literals
    (r'\d+\.\d*|\.\d+|\d+', 'number'),      # Numbers (int and float)
    (r'"([^"\\]|\\.)*"', 'string'),          # Double-quoted strings
    (r"'([^'\\]|\\.)*'", 'string'),          # Single-quoted strings
    
    # Identifiers
    (r'[a-zA-Z_][a-zA-Z0-9_]*', 'identifier'),
    
    # Multi-character operators (must come before single-char)
    (r'==', '=='),
    (r'!=', '!='),
    (r'<=', '<='),
    (r'>=', '>='),
    (r'&&', '&&'),
    (r'\|\|', '||'),
    
    # Single-character operators and punctuation
    (r'\+', '+'),
    (r'-', '-'),
    (r'\*', '*'),
    (r'/', '/'),
    (r'%', '%'),
    (r'<', '<'),
    (r'>', '>'),
    (r'=', '='),
    (r'!', '!'),
    (r'\(', '('),
    (r'\)', ')'),
    (r'\{', '{'),
    (r'\}', '}'),
    (r'\[', '['),
    (r'\]', ']'),
    (r';', ';'),
    (r',', ','),
    (r'\.', '.'),
    
    # Whitespace (will be skipped)
    (r'[ \t]+', 'whitespace'),
    (r'\n', 'newline'),
]

# Compile all patterns
COMPILED_PATTERNS = [(re.compile(pattern), tag) for pattern, tag in PATTERNS]


class TokenizerError(Exception):
    """Exception raised for tokenization errors."""
    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"Tokenizer error at line {line}, column {column}: {message}")


def tokenize(source: str) -> List[Token]:
    """
    Tokenize the source code into a list of tokens.
    
    Args:
        source: The source code string
        
    Returns:
        List of Token objects
        
    Raises:
        TokenizerError: If an unexpected character is encountered
    """
    tokens = []
    pos = 0
    line = 1
    column = 1
    
    while pos < len(source):
        match = None
        
        for pattern, tag in COMPILED_PATTERNS:
            match = pattern.match(source, pos)
            if match:
                value = match.group(0)
                
                # Skip whitespace, newlines, and comments but track position
                if tag == 'newline':
                    line += 1
                    column = 1
                elif tag in ('whitespace', 'comment'):
                    column += len(value)
                else:
                    # Create token with current position
                    tokens.append(Token(tag, value, line, column))
                    column += len(value)
                
                pos = match.end()
                break
        
        if not match:
            raise TokenizerError(f"Unexpected character: {source[pos]!r}", line, column)
    
    # Add end-of-file token
    tokens.append(Token('EOF', '', line, column))
    
    return tokens


def tokenize_string(source: str) -> List[Token]:
    """Alias for tokenize() for backwards compatibility."""
    return tokenize(source)


# Test functions
def test_tokenize_numbers():
    tokens = tokenize("42 3.14 .5")
    assert tokens[0].tag == 'number' and tokens[0].value == '42'
    assert tokens[1].tag == 'number' and tokens[1].value == '3.14'
    assert tokens[2].tag == 'number' and tokens[2].value == '.5'
    print("✓ test_tokenize_numbers passed")


def test_tokenize_identifiers():
    tokens = tokenize("x foo _bar baz123")
    assert all(t.tag == 'identifier' for t in tokens[:-1])
    print("✓ test_tokenize_identifiers passed")


def test_tokenize_operators():
    tokens = tokenize("+ - * / == != <= >=")
    expected = ['+', '-', '*', '/', '==', '!=', '<=', '>=']
    for i, exp in enumerate(expected):
        assert tokens[i].tag == exp, f"Expected {exp}, got {tokens[i].tag}"
    print("✓ test_tokenize_operators passed")


def test_tokenize_keywords():
    tokens = tokenize("if else while TRUE FALSE print")
    expected = ['if', 'else', 'while', 'boolean', 'boolean', 'print']
    for i, exp in enumerate(expected):
        assert tokens[i].tag == exp
    print("✓ test_tokenize_keywords passed")


def test_tokenize_strings():
    tokens = tokenize('"hello" \'world\'')
    assert tokens[0].tag == 'string' and tokens[0].value == '"hello"'
    assert tokens[1].tag == 'string' and tokens[1].value == "'world'"
    print("✓ test_tokenize_strings passed")


def test_location_tracking():
    source = "x = 5\ny = 10"
    tokens = tokenize(source)
    # x is at line 1, col 1
    assert tokens[0].line == 1 and tokens[0].column == 1
    # y is at line 2, col 1
    y_token = [t for t in tokens if t.value == 'y'][0]
    assert y_token.line == 2 and y_token.column == 1
    print("✓ test_location_tracking passed")


if __name__ == "__main__":
    test_tokenize_numbers()
    test_tokenize_identifiers()
    test_tokenize_operators()
    test_tokenize_keywords()
    test_tokenize_strings()
    test_location_tracking()
    print("\nAll tokenizer tests passed!")
