# Language Tools with Variable Watch Support

A simple interpreted language with tokenizer, parser, and evaluator. Includes a **watch** feature that tracks when a variable is created or modified and reports the value and source location.

## Files

- **tokenizer.py** - Lexical analyzer with location tracking
- **parser.py** - Recursive descent parser producing AST with location info
- **evaluator.py** - AST evaluator with watch callback support
- **runner.py** - Main runner with `watch=<identifier>` command line argument

## Usage

### Basic Execution
```bash
python runner.py program.t
```

### With Variable Watching
```bash
python runner.py program.t watch=counter
python runner.py program.t watch=x
python runner.py program.t --watch myvar
```

### Output Format
When a watched variable changes, you'll see:
```
[WATCH] counter = 5 at line 12, column 5
```

## Language Features

- **Variables**: `x = 5`
- **Arithmetic**: `+ - * / %`
- **Comparison**: `== != < > <= >=`
- **Logical**: `and or not` (or `&& || !`)
- **Booleans**: `TRUE FALSE`
- **Strings**: `"hello"` or `'world'`
- **Print**: `print x` or `print "hello"`
- **If/Else**: `if (condition) { ... } else { ... }`
- **While**: `while (condition) { ... }`
- **Blocks**: `{ statement; statement; }`
- **Comments**: `// single line` or `# single line`

## Example Program

```
// example.t - Run with: python runner.py example.t watch=counter

counter = 0
while (counter < 5) {
    counter = counter + 1
    print counter
}

print "Done!"
```

## Watch Feature Implementation

The watch feature works by:
1. **Tokenizer** records line/column for each token
2. **Parser** propagates location info to AST nodes
3. **Evaluator** calls a watch callback when the watched variable is assigned
4. **Runner** sets up the callback to print notifications

This allows you to debug your programs by seeing exactly when and where variables change!

## Running Tests

```bash
python tokenizer.py   # Run tokenizer tests
python parser.py      # Run parser tests
python evaluator.py   # Run evaluator tests
```
