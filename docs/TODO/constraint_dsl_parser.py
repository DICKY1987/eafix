#!/usr/bin/env python3
"""
Constraint DSL Parser - Safe evaluation of trading constraints
Supports: comparisons, arithmetic, dotted paths, functions, and safety checks
"""

import ast
import operator
import re
import math
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class DSLError(Exception):
    """Raised when DSL expression cannot be safely evaluated"""
    pass


class TokenType(Enum):
    NUMBER = "NUMBER"
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    OPERATOR = "OPERATOR"
    FUNCTION = "FUNCTION"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    DOT = "DOT"
    COMMA = "COMMA"
    EOF = "EOF"


@dataclass
class Token:
    type: TokenType
    value: str
    position: int


class DSLLexer:
    """Tokenize DSL expressions safely"""
    
    # Safe operators and functions whitelist
    OPERATORS = {
        '<': operator.lt, '<=': operator.le, '==': operator.eq,
        '!=': operator.ne, '>=': operator.ge, '>': operator.gt,
        '+': operator.add, '-': operator.sub, '*': operator.mul, 
        '/': operator.truediv, '%': operator.mod,
        'and': lambda x, y: x and y, 'or': lambda x, y: x or y,
        'not': operator.not_, 'in': lambda x, y: x in y
    }
    
    FUNCTIONS = {
        'abs': abs, 'min': min, 'max': max, 'round': round,
        'len': len, 'sum': sum, 'avg': lambda x: sum(x)/len(x) if x else 0,
        'sqrt': math.sqrt, 'log': math.log, 'exp': math.exp,
        'floor': math.floor, 'ceil': math.ceil,
        'any': any, 'all': all
    }
    
    def __init__(self, expression: str):
        self.expression = expression
        self.position = 0
        self.tokens = []
        
    def tokenize(self) -> List[Token]:
        """Convert expression string into tokens"""
        while self.position < len(self.expression):
            if self.expression[self.position].isspace():
                self.position += 1
                continue
                
            # Numbers (including floats)
            if self.expression[self.position].isdigit() or self.expression[self.position] == '.':
                self.tokens.append(self._read_number())
            
            # Identifiers and keywords
            elif self.expression[self.position].isalpha() or self.expression[self.position] == '_':
                self.tokens.append(self._read_identifier())
            
            # Strings
            elif self.expression[self.position] in ['"', "'"]:
                self.tokens.append(self._read_string())
            
            # Two-character operators
            elif self.position + 1 < len(self.expression):
                two_char = self.expression[self.position:self.position + 2]
                if two_char in ['<=', '>=', '==', '!=']:
                    self.tokens.append(Token(TokenType.OPERATOR, two_char, self.position))
                    self.position += 2
                else:
                    self._read_single_char()
            
            else:
                self._read_single_char()
        
        self.tokens.append(Token(TokenType.EOF, "", self.position))
        return self.tokens
    
    def _read_number(self) -> Token:
        start = self.position
        while (self.position < len(self.expression) and 
               (self.expression[self.position].isdigit() or self.expression[self.position] == '.')):
            self.position += 1
        
        value = self.expression[start:self.position]
        return Token(TokenType.NUMBER, value, start)
    
    def _read_identifier(self) -> Token:
        start = self.position
        while (self.position < len(self.expression) and 
               (self.expression[self.position].isalnum() or self.expression[self.position] == '_')):
            self.position += 1
        
        value = self.expression[start:self.position]
        
        # Check if it's a function
        if value in self.FUNCTIONS:
            return Token(TokenType.FUNCTION, value, start)
        elif value in ['and', 'or', 'not', 'in']:
            return Token(TokenType.OPERATOR, value, start)
        else:
            return Token(TokenType.IDENTIFIER, value, start)
    
    def _read_string(self) -> Token:
        quote_char = self.expression[self.position]
        start = self.position
        self.position += 1  # Skip opening quote
        
        value = ""
        while self.position < len(self.expression) and self.expression[self.position] != quote_char:
            if self.expression[self.position] == '\\':
                self.position += 1  # Skip escape character
                if self.position < len(self.expression):
                    value += self.expression[self.position]
            else:
                value += self.expression[self.position]
            self.position += 1
        
        if self.position >= len(self.expression):
            raise DSLError(f"Unterminated string starting at position {start}")
        
        self.position += 1  # Skip closing quote
        return Token(TokenType.STRING, value, start)
    
    def _read_single_char(self):
        char = self.expression[self.position]
        
        if char in '<>!+-%*/().,':
            if char == '(':
                token_type = TokenType.LPAREN
            elif char == ')':
                token_type = TokenType.RPAREN
            elif char == '.':
                token_type = TokenType.DOT
            elif char == ',':
                token_type = TokenType.COMMA
            else:
                token_type = TokenType.OPERATOR
                
            self.tokens.append(Token(token_type, char, self.position))
        else:
            raise DSLError(f"Unexpected character '{char}' at position {self.position}")
        
        self.position += 1


class DSLParser:
    """Parse and evaluate DSL expressions safely"""
    
    def __init__(self, lexer: DSLLexer):
        self.lexer = lexer
        self.tokens = lexer.tokenize()
        self.position = 0
        self.current_token = self.tokens[0] if self.tokens else None
    
    def parse_and_evaluate(self, context: Dict[str, Any]) -> bool:
        """Parse and evaluate the expression with given context"""
        try:
            result = self._parse_or_expression(context)
            if self.current_token.type != TokenType.EOF:
                raise DSLError(f"Unexpected token after expression: {self.current_token.value}")
            return bool(result)
        except Exception as e:
            raise DSLError(f"Failed to evaluate expression: {str(e)}")
    
    def _advance(self):
        """Move to next token"""
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
    
    def _parse_or_expression(self, context: Dict[str, Any]) -> Any:
        """Parse OR expressions (lowest precedence)"""
        result = self._parse_and_expression(context)
        
        while self.current_token.type == TokenType.OPERATOR and self.current_token.value == 'or':
            self._advance()
            right = self._parse_and_expression(context)
            result = result or right
        
        return result
    
    def _parse_and_expression(self, context: Dict[str, Any]) -> Any:
        """Parse AND expressions"""
        result = self._parse_equality_expression(context)
        
        while self.current_token.type == TokenType.OPERATOR and self.current_token.value == 'and':
            self._advance()
            right = self._parse_equality_expression(context)
            result = result and right
        
        return result
    
    def _parse_equality_expression(self, context: Dict[str, Any]) -> Any:
        """Parse equality and comparison expressions"""
        result = self._parse_relational_expression(context)
        
        while (self.current_token.type == TokenType.OPERATOR and 
               self.current_token.value in ['==', '!=', 'in']):
            op = self.current_token.value
            self._advance()
            right = self._parse_relational_expression(context)
            
            if op == 'in':
                result = DSLLexer.OPERATORS[op](result, right)
            else:
                result = DSLLexer.OPERATORS[op](result, right)
        
        return result
    
    def _parse_relational_expression(self, context: Dict[str, Any]) -> Any:
        """Parse relational expressions (<, >, <=, >=)"""
        result = self._parse_additive_expression(context)
        
        while (self.current_token.type == TokenType.OPERATOR and 
               self.current_token.value in ['<', '>', '<=', '>=']):
            op = self.current_token.value
            self._advance()
            right = self._parse_additive_expression(context)
            result = DSLLexer.OPERATORS[op](result, right)
        
        return result
    
    def _parse_additive_expression(self, context: Dict[str, Any]) -> Any:
        """Parse addition and subtraction"""
        result = self._parse_multiplicative_expression(context)
        
        while (self.current_token.type == TokenType.OPERATOR and 
               self.current_token.value in ['+', '-']):
            op = self.current_token.value
            self._advance()
            right = self._parse_multiplicative_expression(context)
            result = DSLLexer.OPERATORS[op](result, right)
        
        return result
    
    def _parse_multiplicative_expression(self, context: Dict[str, Any]) -> Any:
        """Parse multiplication, division, and modulo"""
        result = self._parse_unary_expression(context)
        
        while (self.current_token.type == TokenType.OPERATOR and 
               self.current_token.value in ['*', '/', '%']):
            op = self.current_token.value
            self._advance()
            right = self._parse_unary_expression(context)
            
            if op == '/' and right == 0:
                raise DSLError("Division by zero")
            
            result = DSLLexer.OPERATORS[op](result, right)
        
        return result
    
    def _parse_unary_expression(self, context: Dict[str, Any]) -> Any:
        """Parse unary expressions (not, -)"""
        if self.current_token.type == TokenType.OPERATOR and self.current_token.value in ['not', '-']:
            op = self.current_token.value
            self._advance()
            operand = self._parse_unary_expression(context)
            
            if op == 'not':
                return DSLLexer.OPERATORS[op](operand)
            elif op == '-':
                return -operand
        
        return self._parse_primary_expression(context)
    
    def _parse_primary_expression(self, context: Dict[str, Any]) -> Any:
        """Parse primary expressions (numbers, identifiers, functions, parentheses)"""
        
        # Numbers
        if self.current_token.type == TokenType.NUMBER:
            value = self.current_token.value
            self._advance()
            return float(value) if '.' in value else int(value)
        
        # Strings
        elif self.current_token.type == TokenType.STRING:
            value = self.current_token.value
            self._advance()
            return value
        
        # Functions
        elif self.current_token.type == TokenType.FUNCTION:
            return self._parse_function_call(context)
        
        # Identifiers (variable access with dot notation)
        elif self.current_token.type == TokenType.IDENTIFIER:
            return self._parse_identifier_access(context)
        
        # Parentheses
        elif self.current_token.type == TokenType.LPAREN:
            self._advance()  # Skip '('
            result = self._parse_or_expression(context)
            
            if self.current_token.type != TokenType.RPAREN:
                raise DSLError("Expected ')' after expression")
            
            self._advance()  # Skip ')'
            return result
        
        else:
            raise DSLError(f"Unexpected token: {self.current_token.value}")
    
    def _parse_function_call(self, context: Dict[str, Any]) -> Any:
        """Parse function calls"""
        func_name = self.current_token.value
        self._advance()
        
        if self.current_token.type != TokenType.LPAREN:
            raise DSLError(f"Expected '(' after function name {func_name}")
        
        self._advance()  # Skip '('
        
        args = []
        if self.current_token.type != TokenType.RPAREN:
            args.append(self._parse_or_expression(context))
            
            while self.current_token.type == TokenType.COMMA:
                self._advance()  # Skip ','
                args.append(self._parse_or_expression(context))
        
        if self.current_token.type != TokenType.RPAREN:
            raise DSLError("Expected ')' after function arguments")
        
        self._advance()  # Skip ')'
        
        # Apply function with safety checks
        func = DSLLexer.FUNCTIONS.get(func_name)
        if not func:
            raise DSLError(f"Unknown function: {func_name}")
        
        try:
            return func(*args)
        except Exception as e:
            raise DSLError(f"Error calling function {func_name}: {str(e)}")
    
    def _parse_identifier_access(self, context: Dict[str, Any]) -> Any:
        """Parse identifier access with dot notation"""
        path = [self.current_token.value]
        self._advance()
        
        # Handle dot notation for nested access
        while self.current_token.type == TokenType.DOT:
            self._advance()  # Skip '.'
            
            if self.current_token.type != TokenType.IDENTIFIER:
                raise DSLError("Expected identifier after '.'")
            
            path.append(self.current_token.value)
            self._advance()
        
        # Resolve the path in context
        return self._resolve_path(path, context)
    
    def _resolve_path(self, path: List[str], context: Dict[str, Any]) -> Any:
        """Resolve dotted path in context"""
        result = context
        
        for part in path:
            if isinstance(result, dict):
                if part not in result:
                    raise DSLError(f"Key '{part}' not found in context")
                result = result[part]
            elif hasattr(result, part):
                result = getattr(result, part)
            else:
                raise DSLError(f"Cannot access '{part}' on {type(result)}")
        
        return result


class ConstraintDSL:
    """Main interface for constraint DSL evaluation"""
    
    @staticmethod
    def evaluate(expression: str, context: Dict[str, Any]) -> bool:
        """Evaluate DSL expression with trading context"""
        if not expression or not expression.strip():
            return True  # Empty constraint always passes
        
        # Add safety limits
        if len(expression) > 1000:
            raise DSLError("Expression too long (max 1000 characters)")
        
        # Validate no dangerous patterns
        dangerous_patterns = [
            r'__\w+__',  # dunder methods
            r'import\s+',  # import statements
            r'exec\s*\(',  # exec calls
            r'eval\s*\(',  # eval calls
            r'open\s*\(',  # file operations
            r'file\s*\(',  # file operations
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                raise DSLError(f"Expression contains dangerous pattern: {pattern}")
        
        try:
            lexer = DSLLexer(expression)
            parser = DSLParser(lexer)
            return parser.parse_and_evaluate(context)
        except DSLError:
            raise
        except Exception as e:
            raise DSLError(f"Unexpected error evaluating expression: {str(e)}")


# Example usage and test cases
if __name__ == "__main__":
    # Test cases for trading constraints
    test_cases = [
        {
            "expression": "spread_pips < normal_spread * 2.0",
            "context": {"spread_pips": 1.5, "normal_spread": 1.0},
            "expected": False
        },
        {
            "expression": "portfolio_correlation < 0.7 and risk_pct < 5.0",
            "context": {"portfolio_correlation": 0.6, "risk_pct": 3.0},
            "expected": True
        },
        {
            "expression": "bridge_latency_ms < baseline.p95 * 1.5",
            "context": {"bridge_latency_ms": 150, "baseline": {"p95": 120}},
            "expected": False
        },
        {
            "expression": "len(failed_symbols) == 0",
            "context": {"failed_symbols": []},
            "expected": True
        },
        {
            "expression": "max(spreads) < 3.0 and avg(spreads) < 2.0",
            "context": {"spreads": [1.2, 1.8, 2.1]},
            "expected": True
        }
    ]
    
    print("Running DSL test cases:")
    for i, test in enumerate(test_cases):
        try:
            result = ConstraintDSL.evaluate(test["expression"], test["context"])
            status = "PASS" if result == test["expected"] else "FAIL"
            print(f"Test {i+1}: {status} - {test['expression']} -> {result}")
        except DSLError as e:
            print(f"Test {i+1}: ERROR - {e}")
    
    print("\nDSL Parser ready for Guardian constraint evaluation")