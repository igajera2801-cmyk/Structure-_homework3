#!/usr/bin/env python3
"""
runner.py - Language Interpreter Runner with Variable Watch Support

Usage:
    python runner.py <source_file>                  # Run a source file
    python runner.py <source_file> watch=<var>      # Run with variable watching
    python runner.py --help                         # Show help

Examples:
    python runner.py program.t
    python runner.py program.t watch=x
    python runner.py program.t watch=counter

When a watched variable is created or modified, the runner prints:
    [WATCH] <variable> = <value> at line <line>, column <col>
"""

import sys
import os
import argparse
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tokenizer import tokenize, TokenizerError
from parser import parse, ParseError
from evaluator import evaluate, Environment, Evaluator, RuntimeError as EvalRuntimeError


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


def colorize(text: str, color: str) -> str:
    """Apply color to text if stdout is a terminal."""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.RESET}"
    return text


def create_watch_callback(variable_name: str):
    """
    Create a callback function for watching variable changes.
    
    Returns a function that prints watch notifications when called.
    """
    def watch_callback(name: str, value: any, line: int, column: int):
        # Format the value nicely
        if isinstance(value, str):
            value_str = f'"{value}"'
        elif isinstance(value, bool):
            value_str = "TRUE" if value else "FALSE"
        else:
            value_str = str(value)
        
        # Print the watch notification
        watch_msg = f"[WATCH] {name} = {value_str} at line {line}, column {column}"
        print(colorize(watch_msg, Colors.YELLOW))
    
    return watch_callback


def run_file(filepath: str, watch_variable: Optional[str] = None) -> bool:
    """
    Run a source file through the interpreter.
    
    Args:
        filepath: Path to the source file
        watch_variable: Optional variable name to watch for changes
        
    Returns:
        True if execution succeeded, False otherwise
    """
    # Read the source file
    try:
        with open(filepath, 'r') as f:
            source = f.read()
    except FileNotFoundError:
        print(colorize(f"Error: File not found: {filepath}", Colors.RED))
        return False
    except IOError as e:
        print(colorize(f"Error reading file: {e}", Colors.RED))
        return False
    
    return run_source(source, filepath, watch_variable)


def run_source(source: str, filename: str = "<stdin>", 
               watch_variable: Optional[str] = None) -> bool:
    """
    Run source code through the interpreter.
    
    Args:
        source: The source code string
        filename: Name of the source file (for error messages)
        watch_variable: Optional variable name to watch for changes
        
    Returns:
        True if execution succeeded, False otherwise
    """
    if watch_variable:
        print(colorize(f"=== Watching variable: {watch_variable} ===", Colors.CYAN))
        print()
    
    try:
        # Tokenize
        tokens = tokenize(source)
        
        # Parse
        ast = parse(tokens)
        
        # Set up environment with watch callback
        env = Environment()
        watch_callback = None
        
        if watch_variable:
            watch_callback = create_watch_callback(watch_variable)
            env.set_watch(watch_variable, watch_callback)
        
        # Evaluate
        evaluator = Evaluator(env)
        result = evaluator.evaluate(ast)
        
        return True
        
    except TokenizerError as e:
        print(colorize(f"Tokenizer Error in {filename}:", Colors.RED))
        print(colorize(f"  {e}", Colors.RED))
        return False
        
    except ParseError as e:
        print(colorize(f"Parse Error in {filename}:", Colors.RED))
        print(colorize(f"  {e}", Colors.RED))
        return False
        
    except EvalRuntimeError as e:
        print(colorize(f"Runtime Error in {filename}:", Colors.RED))
        print(colorize(f"  {e}", Colors.RED))
        return False
        
    except Exception as e:
        print(colorize(f"Unexpected Error in {filename}:", Colors.RED))
        print(colorize(f"  {type(e).__name__}: {e}", Colors.RED))
        return False


def parse_watch_arg(arg: str) -> Optional[str]:
    """
    Parse a watch=<identifier> argument.
    
    Args:
        arg: The command line argument
        
    Returns:
        The variable name to watch, or None if not a watch argument
    """
    if arg.startswith('watch='):
        return arg[6:]  # Extract everything after 'watch='
    return None


def main():
    """Main entry point for the runner."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Run programs in the custom language interpreter.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s program.t                 Run program.t
  %(prog)s program.t watch=x         Run and watch variable 'x'
  %(prog)s program.t watch=counter   Run and watch variable 'counter'

When watching a variable, the interpreter prints a notification each time
the variable is created or modified, showing the new value and the source
location where the change occurred.
        """
    )
    
    parser.add_argument('file', nargs='?', help='Source file to run')
    parser.add_argument('extras', nargs='*', help='Additional arguments (e.g., watch=<var>)')
    parser.add_argument('--watch', '-w', dest='watch', 
                        help='Variable name to watch for changes')
    parser.add_argument('--version', '-v', action='version', 
                        version='Language Tools Runner v1.0')
    
    args = parser.parse_args()
    
    # Check if we have a file to run
    if not args.file:
        parser.print_help()
        sys.exit(1)
    
    # Extract watch variable from command line
    watch_variable = args.watch
    
    # Check extra arguments for watch=<var> format
    for extra in args.extras:
        watch_var = parse_watch_arg(extra)
        if watch_var:
            watch_variable = watch_var
            break
    
    # Run the file
    success = run_file(args.file, watch_variable)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


def run_interactive():
    """Run an interactive REPL session."""
    print(colorize("Language Tools Interactive Mode", Colors.HEADER))
    print("Type 'exit' or 'quit' to exit, 'help' for help.")
    print()
    
    env = Environment()
    evaluator = Evaluator(env)
    watch_variable = None
    
    while True:
        try:
            # Read input
            prompt = colorize(">>> ", Colors.GREEN)
            line = input(prompt)
            
            # Handle special commands
            if line.strip().lower() in ('exit', 'quit'):
                print("Goodbye!")
                break
            
            if line.strip().lower() == 'help':
                print("Commands:")
                print("  exit, quit     - Exit the interpreter")
                print("  help           - Show this help")
                print("  watch <var>    - Watch a variable for changes")
                print("  unwatch        - Stop watching variables")
                print("  env            - Show current environment")
                continue
            
            if line.strip().lower().startswith('watch '):
                var_name = line.strip()[6:].strip()
                watch_variable = var_name
                env.set_watch(var_name, create_watch_callback(var_name))
                print(colorize(f"Now watching: {var_name}", Colors.CYAN))
                continue
            
            if line.strip().lower() == 'unwatch':
                watch_variable = None
                env.watched_variable = None
                env.watch_callback = None
                print(colorize("Stopped watching variables", Colors.CYAN))
                continue
            
            if line.strip().lower() == 'env':
                print("Current variables:")
                for name, value in env.variables.items():
                    print(f"  {name} = {value}")
                continue
            
            if not line.strip():
                continue
            
            # Parse and evaluate
            tokens = tokenize(line)
            ast = parse(tokens)
            result = evaluator.evaluate(ast)
            
            if result is not None:
                print(result)
                
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit.")
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(colorize(f"Error: {e}", Colors.RED))


if __name__ == "__main__":
    # Check if running interactively (no arguments)
    if len(sys.argv) == 1:
        # Could start REPL here, but let's just show help
        main()
    else:
        main()
