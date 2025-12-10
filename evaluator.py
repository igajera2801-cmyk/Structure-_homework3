"""
evaluator.py - AST Evaluator with Variable Watch Support

Evaluates the AST and executes the program. Supports watching variables
for changes and reporting when they are created or modified.
"""

from typing import Dict, Any, Optional, Callable, List


class RuntimeError(Exception):
    """Exception raised for runtime errors."""
    def __init__(self, message: str, node: Dict[str, Any]):
        self.node = node
        line = node.get('line', '?')
        column = node.get('column', '?')
        super().__init__(f"Runtime error at line {line}, column {column}: {message}")


class BreakException(Exception):
    """Exception used to implement break statement."""
    pass


class ContinueException(Exception):
    """Exception used to implement continue statement."""
    pass


class Environment:
    """
    Environment for storing variables with watch support.
    """
    
    def __init__(self, parent: Optional['Environment'] = None):
        self.variables: Dict[str, Any] = {}
        self.parent = parent
        self.watch_callback: Optional[Callable[[str, Any, int, int], None]] = None
        self.watched_variable: Optional[str] = None
    
    def set_watch(self, variable_name: str, callback: Callable[[str, Any, int, int], None]):
        """
        Set a watch on a variable.
        
        Args:
            variable_name: The name of the variable to watch
            callback: Function called when variable changes: callback(name, value, line, col)
        """
        self.watched_variable = variable_name
        self.watch_callback = callback
        
        # Propagate to parent environments
        if self.parent:
            self.parent.set_watch(variable_name, callback)
    
    def _notify_watch(self, name: str, value: Any, line: int, column: int):
        """Notify the watch callback if this variable is being watched."""
        if self.watched_variable == name and self.watch_callback:
            self.watch_callback(name, value, line, column)
        if self.parent:
            self.parent._notify_watch(name, value, line, column)
    
    def define(self, name: str, value: Any, line: int = 0, column: int = 0):
        """
        Define a new variable in the current scope.
        """
        is_new = name not in self.variables
        self.variables[name] = value
        self._notify_watch(name, value, line, column)
    
    def assign(self, name: str, value: Any, line: int = 0, column: int = 0) -> bool:
        """
        Assign a value to an existing variable (searches parent scopes).
        Returns True if found and assigned, False otherwise.
        """
        if name in self.variables:
            self.variables[name] = value
            self._notify_watch(name, value, line, column)
            return True
        elif self.parent:
            return self.parent.assign(name, value, line, column)
        else:
            # Variable doesn't exist, create it in current scope
            self.variables[name] = value
            self._notify_watch(name, value, line, column)
            return True
    
    def get(self, name: str) -> Any:
        """Get a variable's value (searches parent scopes)."""
        if name in self.variables:
            return self.variables[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise KeyError(f"Undefined variable: {name}")
    
    def exists(self, name: str) -> bool:
        """Check if a variable exists."""
        if name in self.variables:
            return True
        elif self.parent:
            return self.parent.exists(name)
        return False


class Evaluator:
    """
    Evaluates AST nodes and executes the program.
    """
    
    def __init__(self, env: Optional[Environment] = None):
        self.env = env or Environment()
        self.output: List[str] = []  # Captured print output
    
    def evaluate(self, node: Dict[str, Any]) -> Any:
        """
        Evaluate an AST node.
        
        Args:
            node: The AST node to evaluate
            
        Returns:
            The result of evaluating the node
        """
        tag = node.get('tag')
        
        # Dispatch to appropriate handler
        handler = getattr(self, f'eval_{tag}', None)
        if handler:
            return handler(node)
        else:
            raise RuntimeError(f"Unknown node type: {tag}", node)
    
    def eval_program(self, node: Dict[str, Any]) -> Any:
        """Evaluate a program (sequence of statements)."""
        result = None
        for stmt in node.get('statements', []):
            result = self.evaluate(stmt)
        return result
    
    def eval_block(self, node: Dict[str, Any]) -> Any:
        """Evaluate a block of statements in a new scope."""
        # Create a new environment for the block
        old_env = self.env
        self.env = Environment(parent=old_env)
        
        # Copy watch settings to new environment
        if old_env.watched_variable:
            self.env.set_watch(old_env.watched_variable, old_env.watch_callback)
        
        try:
            result = None
            for stmt in node.get('statements', []):
                result = self.evaluate(stmt)
            return result
        finally:
            self.env = old_env
    
    def eval_assign(self, node: Dict[str, Any]) -> Any:
        """Evaluate an assignment statement."""
        name = node['name']
        value = self.evaluate(node['value'])
        line = node.get('line', 0)
        column = node.get('column', 0)
        
        self.env.assign(name, value, line, column)
        return value
    
    def eval_print(self, node: Dict[str, Any]) -> None:
        """Evaluate a print statement."""
        value = self.evaluate(node['value'])
        output = str(value)
        self.output.append(output)
        print(output)
        return None
    
    def eval_if(self, node: Dict[str, Any]) -> Any:
        """Evaluate an if statement."""
        condition = self.evaluate(node['condition'])
        
        if self._is_truthy(condition):
            return self.evaluate(node['then'])
        elif node.get('else_'):
            return self.evaluate(node['else_'])
        return None
    
    def eval_while(self, node: Dict[str, Any]) -> Any:
        """Evaluate a while loop."""
        result = None
        while self._is_truthy(self.evaluate(node['condition'])):
            try:
                result = self.evaluate(node['body'])
            except BreakException:
                break
            except ContinueException:
                continue
        return result
    
    def eval_binary(self, node: Dict[str, Any]) -> Any:
        """Evaluate a binary operation."""
        op = node['op']
        left = self.evaluate(node['left'])
        
        # Short-circuit evaluation for logical operators
        if op == '&&':
            if not self._is_truthy(left):
                return left
            return self.evaluate(node['right'])
        elif op == '||':
            if self._is_truthy(left):
                return left
            return self.evaluate(node['right'])
        
        right = self.evaluate(node['right'])
        
        # Arithmetic operators
        if op == '+':
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            if right == 0:
                raise RuntimeError("Division by zero", node)
            return left / right
        elif op == '%':
            return left % right
        
        # Comparison operators
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            return left < right
        elif op == '>':
            return left > right
        elif op == '<=':
            return left <= right
        elif op == '>=':
            return left >= right
        
        else:
            raise RuntimeError(f"Unknown operator: {op}", node)
    
    def eval_unary(self, node: Dict[str, Any]) -> Any:
        """Evaluate a unary operation."""
        op = node['op']
        operand = self.evaluate(node['operand'])
        
        if op == '-':
            return -operand
        elif op == '!':
            return not self._is_truthy(operand)
        else:
            raise RuntimeError(f"Unknown unary operator: {op}", node)
    
    def eval_number(self, node: Dict[str, Any]) -> Any:
        """Evaluate a number literal."""
        return node['value']
    
    def eval_string(self, node: Dict[str, Any]) -> Any:
        """Evaluate a string literal."""
        return node['value']
    
    def eval_boolean(self, node: Dict[str, Any]) -> Any:
        """Evaluate a boolean literal."""
        return node['value']
    
    def eval_identifier(self, node: Dict[str, Any]) -> Any:
        """Evaluate an identifier (variable reference)."""
        name = node['name']
        try:
            return self.env.get(name)
        except KeyError:
            raise RuntimeError(f"Undefined variable: {name}", node)
    
    def _is_truthy(self, value: Any) -> bool:
        """Determine if a value is truthy."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        return True


def evaluate(ast_or_source, env: Optional[Dict[str, Any]] = None, 
             watch: Optional[str] = None,
             watch_callback: Optional[Callable] = None) -> Any:
    """
    Evaluate an AST or source code.
    
    Args:
        ast_or_source: Either an AST dict or source code string
        env: Optional initial environment (dict of variables)
        watch: Optional variable name to watch for changes
        watch_callback: Optional callback for watch notifications
        
    Returns:
        The result of evaluation
    """
    from parser import parse
    
    # Parse if needed
    if isinstance(ast_or_source, str):
        ast = parse(ast_or_source)
    else:
        ast = ast_or_source
    
    # Create environment
    environment = Environment()
    if env:
        for name, value in env.items():
            environment.define(name, value)
    
    # Set up watch
    if watch and watch_callback:
        environment.set_watch(watch, watch_callback)
    
    # Evaluate
    evaluator = Evaluator(environment)
    return evaluator.evaluate(ast)


# Test functions
def test_evaluate_number():
    result = evaluate("42")
    assert result == 42
    print("✓ test_evaluate_number passed")


def test_evaluate_arithmetic():
    assert evaluate("2 + 3") == 5
    assert evaluate("10 - 4") == 6
    assert evaluate("3 * 4") == 12
    assert evaluate("15 / 3") == 5
    assert evaluate("2 + 3 * 4") == 14  # Precedence
    print("✓ test_evaluate_arithmetic passed")


def test_evaluate_comparison():
    assert evaluate("5 == 5") == True
    assert evaluate("5 != 3") == True
    assert evaluate("3 < 5") == True
    assert evaluate("5 > 3") == True
    print("✓ test_evaluate_comparison passed")


def test_evaluate_assignment():
    result = evaluate("x = 10; x + 5")
    assert result == 15
    print("✓ test_evaluate_assignment passed")


def test_evaluate_if():
    assert evaluate("x = 5; if (x == 5) { x = 10 }; x") == 10
    assert evaluate("x = 5; if (x == 3) { x = 10 } else { x = 20 }; x") == 20
    print("✓ test_evaluate_if passed")


def test_evaluate_while():
    result = evaluate("x = 0; while (x < 5) { x = x + 1 }; x")
    assert result == 5
    print("✓ test_evaluate_while passed")


def test_watch_variable():
    """Test the watch functionality."""
    watched_changes = []
    
    def on_change(name, value, line, col):
        watched_changes.append({
            'name': name,
            'value': value,
            'line': line,
            'column': col
        })
    
    evaluate("x = 5; x = 10; y = 20; x = 15", 
             watch='x', watch_callback=on_change)
    
    # Should have recorded 3 changes to x
    assert len(watched_changes) == 3
    assert watched_changes[0]['value'] == 5
    assert watched_changes[1]['value'] == 10
    assert watched_changes[2]['value'] == 15
    print("✓ test_watch_variable passed")


def test_watch_with_location():
    """Test that watch reports correct locations."""
    watched_changes = []
    
    def on_change(name, value, line, col):
        watched_changes.append({
            'name': name,
            'value': value,
            'line': line,
            'column': col
        })
    
    source = """x = 1
x = 2
x = 3"""
    
    evaluate(source, watch='x', watch_callback=on_change)
    
    assert watched_changes[0]['line'] == 1
    assert watched_changes[1]['line'] == 2
    assert watched_changes[2]['line'] == 3
    print("✓ test_watch_with_location passed")


if __name__ == "__main__":
    test_evaluate_number()
    test_evaluate_arithmetic()
    test_evaluate_comparison()
    test_evaluate_assignment()
    test_evaluate_if()
    test_evaluate_while()
    test_watch_variable()
    test_watch_with_location()
    print("\nAll evaluator tests passed!")
