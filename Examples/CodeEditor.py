"""
Code Editor with Live Preview
Features: Syntax highlighting, live preview, multiple languages, code execution
"""
from pyuiwizard import PyUIWizard, create_element, useState, useEffect, useRef, Component
import re
import ast
import io
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime

# ======================================
# 1. CODE SYNTAX HIGHLIGHTER
# ======================================
class CodeHighlighter:
    """Syntax highlighter for multiple languages"""
    
    KEYWORDS = {
        'python': {
            'keywords': [
                'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
                'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from',
                'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not',
                'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
            ],
            'builtins': [
                'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray',
                'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex',
                'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec',
                'filter', 'float', 'format', 'frozenset', 'getattr', 'globals',
                'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
                'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview',
                'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property',
                'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice',
                'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type',
                'vars', 'zip', '__import__'
            ],
            'constants': ['True', 'False', 'None']
        },
        'javascript': {
            'keywords': [
                'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
                'default', 'delete', 'do', 'else', 'export', 'extends', 'finally',
                'for', 'function', 'if', 'import', 'in', 'instanceof', 'new', 'return',
                'super', 'switch', 'this', 'throw', 'try', 'typeof', 'var', 'void',
                'while', 'with', 'yield'
            ],
            'builtins': [
                'Array', 'Date', 'eval', 'function', 'hasOwnProperty', 'Infinity',
                'isFinite', 'isNaN', 'isPrototypeOf', 'length', 'Math', 'NaN',
                'Number', 'Object', 'prototype', 'String', 'toString', 'undefined',
                'valueOf'
            ]
        },
        'html': {
            'tags': [
                'html', 'head', 'body', 'title', 'meta', 'link', 'style', 'script',
                'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'img',
                'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'form', 'input',
                'button', 'textarea', 'select', 'option'
            ]
        }
    }
    
    @staticmethod
    def highlight(code, language='python'):
        """Highlight code with syntax coloring"""
        if language == 'python':
            return CodeHighlighter._highlight_python(code)
        elif language == 'javascript':
            return CodeHighlighter._highlight_javascript(code)
        elif language == 'html':
            return CodeHighlighter._highlight_html(code)
        else:
            return code
    
    @staticmethod
    def _highlight_python(code):
        """Highlight Python code"""
        lines = code.split('\n')
        highlighted_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                highlighted_lines.append(line)
                continue
            
            highlighted = line
            
            # Highlight keywords
            for keyword in CodeHighlighter.KEYWORDS['python']['keywords']:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                highlighted = re.sub(pattern, f'<keyword>{keyword}</keyword>', highlighted)
            
            # Highlight builtins
            for builtin in CodeHighlighter.KEYWORDS['python']['builtins']:
                pattern = r'\b' + re.escape(builtin) + r'\b'
                highlighted = re.sub(pattern, f'<builtin>{builtin}</builtin>', highlighted)
            
            # Highlight constants
            for constant in CodeHighlighter.KEYWORDS['python']['constants']:
                pattern = r'\b' + re.escape(constant) + r'\b'
                highlighted = re.sub(pattern, f'<constant>{constant}</constant>', highlighted)
            
            # Highlight strings
            highlighted = re.sub(r'(\'[^\']*\'|"[^"]*")', r'<string>\1</string>', highlighted)
            
            # Highlight comments
            highlighted = re.sub(r'#.*$', r'<comment>\g<0></comment>', highlighted)
            
            # Highlight numbers
            highlighted = re.sub(r'\b\d+\b', r'<number>\g<0></number>', highlighted)
            
            highlighted_lines.append(highlighted)
        
        return '\n'.join(highlighted_lines)
    
    @staticmethod
    def _highlight_javascript(code):
        """Highlight JavaScript code"""
        lines = code.split('\n')
        highlighted_lines = []
        
        for line in lines:
            highlighted = line
            
            # Highlight keywords
            for keyword in CodeHighlighter.KEYWORDS['javascript']['keywords']:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                highlighted = re.sub(pattern, f'<keyword>{keyword}</keyword>', highlighted)
            
            # Highlight builtins
            for builtin in CodeHighlighter.KEYWORDS['javascript']['builtins']:
                pattern = r'\b' + re.escape(builtin) + r'\b'
                highlighted = re.sub(pattern, f'<builtin>{builtin}</builtin>', highlighted)
            
            # Highlight strings
            highlighted = re.sub(r'(\'[^\']*\'|"[^"]*")', r'<string>\1</string>', highlighted)
            
            # Highlight comments
            highlighted = re.sub(r'//.*$', r'<comment>\g<0></comment>', highlighted)
            highlighted = re.sub(r'/\*.*?\*/', r'<comment>\g<0></comment>', highlighted, flags=re.DOTALL)
            
            highlighted_lines.append(highlighted)
        
        return '\n'.join(highlighted_lines)
    
    @staticmethod
    def _highlight_html(code):
        """Highlight HTML code"""
        highlighted = code
        
        # Highlight tags
        for tag in CodeHighlighter.KEYWORDS['html']['tags']:
            pattern = r'&lt;/?\b' + re.escape(tag) + r'\b[^&]*&gt;'
            highlighted = re.sub(pattern, r'<tag>\g<0></tag>', highlighted, flags=re.IGNORECASE)
        
        # Highlight attributes
        highlighted = re.sub(r'(\b\w+)=', r'<attr>\1</attr>=', highlighted)
        
        # Highlight strings
        highlighted = re.sub(r'&quot;[^&]*&quot;', r'<string>\g<0></string>', highlighted)
        
        # Highlight comments
        highlighted = re.sub(r'&lt;!--.*?--&gt;', r'<comment>\g<0></comment>', highlighted, flags=re.DOTALL)
        
        return highlighted

# ======================================
# 2. CODE EXECUTION ENGINE
# ======================================
class CodeExecutor:
    """Safe code execution engine"""
    
    @staticmethod
    def execute_python(code):
        """Execute Python code safely"""
        # Create a safe execution environment
        safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'ascii': ascii,
            'bin': bin, 'bool': bool, 'chr': chr, 'dict': dict,
            'dir': dir, 'divmod': divmod, 'enumerate': enumerate,
            'filter': filter, 'float': float, 'format': format,
            'hash': hash, 'hex': hex, 'int': int, 'isinstance': isinstance,
            'issubclass': issubclass, 'iter': iter, 'len': len,
            'list': list, 'map': map, 'max': max, 'min': min,
            'next': next, 'oct': oct, 'ord': ord, 'pow': pow,
            'print': print, 'range': range, 'repr': repr,
            'reversed': reversed, 'round': round, 'set': set,
            'slice': slice, 'sorted': sorted, 'str': str,
            'sum': sum, 'tuple': tuple, 'type': type, 'zip': zip,
            'True': True, 'False': False, 'None': None
        }
        
        # Remove dangerous functions
        dangerous = ['open', 'exec', 'eval', '__import__', 'compile']
        for func in dangerous:
            if func in safe_builtins:
                del safe_builtins[func]
        
        # Create restricted globals
        restricted_globals = {
            '__builtins__': safe_builtins,
            'print': print
        }
        
        # Capture output
        output = io.StringIO()
        error = None
        
        try:
            with redirect_stdout(output), redirect_stderr(output):
                # Parse and execute code
                parsed = ast.parse(code, mode='exec')
                
                # Check for dangerous operations
                CodeExecutor._check_ast(parsed)
                
                # Execute in restricted environment
                exec(compile(parsed, '<string>', 'exec'), restricted_globals)
                
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
        
        return {
            'output': output.getvalue(),
            'error': error,
            'success': error is None
        }
    
    @staticmethod
    def _check_ast(node):
        """Check AST for dangerous operations"""
        dangerous_nodes = {
            ast.Import: 'import statements',
            ast.ImportFrom: 'import statements',
            ast.Call: lambda n: CodeExecutor._check_call(n)
        }
        
        for child in ast.walk(node):
            for dangerous_type, check in dangerous_nodes.items():
                if isinstance(child, dangerous_type):
                    if callable(check):
                        check(child)
                    else:
                        raise SecurityError(f"Disallowed: {check}")
    
    @staticmethod
    def _check_call(node):
        """Check function calls for dangerous functions"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in ['open', 'exec', 'eval', '__import__']:
                raise SecurityError(f"Disallowed function: {func_name}")

class SecurityError(Exception):
    """Security error for unsafe code"""
    pass

# ======================================
# 3. EDITOR COMPONENTS
# ======================================
def CodeEditor(props):
    """Code editor with syntax highlighting"""
    [code, setCode] = useState(props.get('code', ''), key=f"editor_{props['key']}")
    [language, setLanguage] = useState(props.get('language', 'python'), key=f"language_{props['key']}")
    [showLineNumbers, setShowLineNumbers] = useState(True, key=f"line_numbers_{props['key']}")
    [fontSize, setFontSize] = useState(14, key=f"font_size_{props['key']}")
    
    editor_ref = useRef(None)
    
    # Apply syntax highlighting
    highlighted_code = CodeHighlighter.highlight(code, language)
    
    # Handle code changes
    def handle_code_change(new_code):
        setCode(new_code)
        if props.onChange:
            props.onChange(new_code)
    
    # Auto-indent on Enter
    def handle_keypress(event):
        if event['key'] == 'Enter' and editor_ref.current:
            # Get current line
            widget = editor_ref.current
            current_pos = widget.index('insert')
            line_num = int(current_pos.split('.')[0])
            
            # Get previous line indentation
            prev_line = widget.get(f'{line_num - 1}.0', f'{line_num - 1}.end')
            indent_match = re.match(r'^(\s*)', prev_line)
            if indent_match:
                indent = indent_match.group(1)
                
                # Check if previous line ends with colon
                if prev_line.rstrip().endswith(':'):
                    indent += '    '  # Add extra indent
                
                # Insert indentation
                widget.insert('insert', indent)
    
    return create_element('frame', {
        'class': 'flex flex-col h-full border rounded-lg overflow-hidden'
    },
        # Editor header
        create_element('frame', {
            'class': 'bg-gray-100 dark:bg-gray-800 border-b p-2 flex items-center justify-between'
        },
            create_element('frame', {'class': 'flex items-center space-x-4'},
                create_element('combobox', {
                    'values': ['python', 'javascript', 'html', 'css', 'json'],
                    'value': language,
                    'onChange': lambda lang: (setLanguage(lang), props.onLanguageChange and props.onLanguageChange(lang)),
                    'class': 'border rounded px-2 py-1 text-sm'
                }),
                create_element('frame', {'class': 'flex items-center space-x-2'},
                    create_element('checkbox', {
                        'text': 'Line Numbers',
                        'checked': showLineNumbers,
                        'onChange': setShowLineNumbers,
                        'class': 'text-sm'
                    }),
                    create_element('frame', {'class': 'flex items-center'},
                        create_element('button', {
                            'text': 'A-',
                            'onClick': lambda: setFontSize(max(8, fontSize - 1)),
                            'class': 'px-2 py-1 text-sm'
                        }),
                        create_element('label', {
                            'text': f'{fontSize}px',
                            'class': 'mx-2 text-sm'
                        }),
                        create_element('button', {
                            'text': 'A+',
                            'onClick': lambda: setFontSize(min(24, fontSize + 1)),
                            'class': 'px-2 py-1 text-sm'
                        })
                    )
                )
            ),
            create_element('frame', {'class': 'flex items-center'},
                create_element('label', {
                    'text': f'{len(code)} chars, {len(code.splitlines())} lines',
                    'class': 'text-sm text-gray-500'
                })
            )
        ),
        
        # Editor content
        create_element('frame', {'class': 'flex flex-1 overflow-hidden'},
            # Line numbers
            showLineNumbers and create_element('frame', {
                'class': 'bg-gray-50 dark:bg-gray-900 text-right py-2 overflow-y-auto'
            },
                *[create_element('label', {
                    'text': str(i + 1),
                    'class': 'text-gray-400 dark:text-gray-600 text-sm px-2',
                    'key': f'line_{i}'
                }) for i in range(max(1, len(code.splitlines())))]
            ),
            
            # Code editor
            create_element('text', {
                'value': code,
                'onChange': handle_code_change,
                'onKeyPress': handle_keypress,
                'onRef': lambda widget: editor_ref.current := widget,
                'class': 'flex-1 font-mono',
                'wrap': 'none',
                'undo': True
            })
        ),
        
        # Status bar
        create_element('frame', {
            'class': 'bg-gray-100 dark:bg-gray-800 border-t p-2 text-sm text-gray-500'
        },
            create_element('label', {
                'text': f'Language: {language} | UTF-8 | LF'
            })
        )
    )

def LivePreview(props):
    """Live preview pane for HTML/CSS/JS"""
    [html, setHtml] = useState(props.get('html', ''), key="preview_html")
    [css, setCss] = useState(props.get('css', ''), key="preview_css")
    [js, setJs] = useState(props.get('js', ''), key="preview_js")
    [refreshKey, setRefreshKey] = useState(0, key="preview_refresh")
    
    # Combine code into a complete HTML page
    combined_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            {css}
        </style>
    </head>
    <body>
        {html}
        <script>
            {js}
        </script>
    </body>
    </html>
    '''
    
    # Update when props change
    useEffect(
        lambda: (
            setHtml(props.get('html', '')),
            setCss(props.get('css', '')),
            setJs(props.get('js', ''))
        ),
        [props.html, props.css, props.js]
    )
    
    def refresh_preview():
        setRefreshKey(refreshKey + 1)
    
    return create_element('frame', {
        'class': 'flex flex-col h-full border rounded-lg overflow-hidden'
    },
        # Preview header
        create_element('frame', {
            'class': 'bg-gray-100 dark:bg-gray-800 border-b p-2 flex items-center justify-between'
        },
            create_element('label', {
                'text': 'Live Preview',
                'class': 'font-bold'
            }),
            create_element('button', {
                'text': '⟳ Refresh',
                'onClick': refresh_preview,
                'class': 'px-3 py-1 bg-blue-500 text-white rounded text-sm'
            })
        ),
        
        # Preview content
        create_element('frame', {
            'class': 'flex-1 bg-white overflow-auto p-4',
            'key': f'preview_{refreshKey}'
        },
            # Render HTML content
            html and create_element('htmlviewer', {
                'content': combined_html,
                'class': 'w-full h-full'
            }),
            
            # Empty state
            not html and create_element('frame', {
                'class': 'flex items-center justify-center h-full text-gray-400'
            },
                create_element('label', {
                    'text': 'HTML preview will appear here'
                })
            )
        )
    )

def OutputConsole(props):
    """Output console for code execution results"""
    [output, setOutput] = useState([], key="console_output")
    [autoScroll, setAutoScroll] = useState(True, key="console_autoscroll")
    
    console_ref = useRef(None)
    
    # Add new output
    def add_output(text, type='info'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        new_entry = {
            'id': len(output),
            'timestamp': timestamp,
            'text': text,
            'type': type  # info, error, success
        }
        
        setOutput(prev => [...prev, new_entry])
    
    # Clear console
    def clear_console():
        setOutput([])
    
    # Scroll to bottom when new output added
    useEffect(
        lambda: (
            autoScroll and console_ref.current and console_ref.current.scroll_to_end()
        ),
        [output]
    )
    
    return create_element('frame', {
        'class': 'flex flex-col h-full border rounded-lg overflow-hidden'
    },
        # Console header
        create_element('frame', {
            'class': 'bg-gray-100 dark:bg-gray-800 border-b p-2 flex items-center justify-between'
        },
            create_element('label', {
                'text': 'Console Output',
                'class': 'font-bold'
            }),
            create_element('frame', {'class': 'flex items-center space-x-2'},
                create_element('checkbox', {
                    'text': 'Auto-scroll',
                    'checked': autoScroll,
                    'onChange': setAutoScroll,
                    'class': 'text-sm'
                }),
                create_element('button', {
                    'text': 'Clear',
                    'onClick': clear_console,
                    'class': 'px-3 py-1 bg-gray-300 dark:bg-gray-700 rounded text-sm'
                })
            )
        ),
        
        # Console content
        create_element('frame', {
            'class': 'flex-1 bg-black text-white font-mono text-sm overflow-auto p-3',
            'onRef': lambda widget: console_ref.current := widget
        },
            *[create_element('frame', {'class': 'mb-1', 'key': entry['id']},
                create_element('label', {
                    'text': f'[{entry["timestamp"]}] ',
                    'class': 'text-gray-500'
                }),
                create_element('label', {
                    'text': entry['text'],
                    'class': {
                        'info': 'text-gray-300',
                        'error': 'text-red-400',
                        'success': 'text-green-400'
                    }[entry['type']]
                })
            ) for entry in output]
        ),
        
        # Input (for interactive console)
        props.interactive and create_element('frame', {'class': 'border-t p-2'},
            create_element('entry', {
                'placeholder': 'Enter Python code...',
                'onSubmit': lambda cmd: (
                    add_output(f'>>> {cmd}', 'info'),
                    # Execute command
                    execute_command(cmd)
                ),
                'class': 'w-full bg-gray-800 text-white border-none px-3 py-2'
            })
        )
    )

# ======================================
# 4. MAIN EDITOR COMPONENT
# ======================================
def CodeEditorApp(props):
    """Main code editor application"""
    [activeTab, setActiveTab] = useState('html', key="editor_tab")
    [htmlCode, setHtmlCode] = useState('''<!DOCTYPE html>
<html>
<head>
    <title>My Page</title>
</head>
<body>
    <h1>Hello, World!</h1>
    <p>Edit this code and see live preview.</p>
</body>
</html>''', key="html_code")
    
    [cssCode, setCssCode] = useState('''body {
    font-family: Arial, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background: #f5f5f5;
}

h1 {
    color: #333;
    border-bottom: 2px solid #4CAF50;
    padding-bottom: 10px;
}

p {
    color: #666;
    line-height: 1.6;
}''', key="css_code")
    
    [jsCode, setJsCode] = useState('''// JavaScript code
console.log("Hello from JavaScript!");

document.addEventListener('DOMContentLoaded', function() {
    // Add interactive elements here
    const h1 = document.querySelector('h1');
    if (h1) {
        h1.addEventListener('click', function() {
            this.style.color = this.style.color === 'red' ? '#333' : 'red';
        });
    }
});''', key="js_code")
    
    [pythonCode, setPythonCode] = useState('''# Python code example
print("Hello, World!")

# Fibonacci sequence
def fibonacci(n):
    """Generate Fibonacci sequence up to n"""
    a, b = 0, 1
    result = []
    while a < n:
        result.append(a)
        a, b = b, a + b
    return result

# Calculate first 10 Fibonacci numbers
fib_numbers = fibonacci(100)
print(f"Fibonacci numbers under 100: {fib_numbers}")

# List comprehension example
squares = [x**2 for x in range(10)]
print(f"Squares: {squares}")''', key="python_code")
    
    [consoleOutput, setConsoleOutput] = useState([], key="editor_output")
    
    # Execute Python code
    def execute_python():
        result = CodeExecutor.execute_python(pythonCode)
        
        if result['success']:
            if result['output']:
                add_console_output(result['output'], 'success')
            else:
                add_console_output("Code executed successfully (no output)", 'info')
        else:
            add_console_output(result['error'], 'error')
    
    # Add output to console
    def add_console_output(text, type='info'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        new_output = {
            'timestamp': timestamp,
            'text': text,
            'type': type
        }
        setConsoleOutput(prev => [new_output, ...prev])
    
    # Save code
    def save_code():
        # In real app, save to file
        add_console_output("Code saved successfully", 'success')
    
    # Load example
    def load_example():
        setHtmlCode('''<!DOCTYPE html>
<html>
<head>
    <title>Example</title>
    <style>
        body { font-family: Arial; }
        .container { max-width: 600px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Example Page</h1>
        <button onclick="alert('Hello!')">Click me</button>
    </div>
</body>
</html>''')
        setCssCode('')
        setJsCode('')
        add_console_output("Loaded example code", 'info')
    
    return create_element('frame', {
        'class': 'min-h-screen bg-gray-100 dark:bg-gray-900'
    },
        create_element('frame', {'class': 'max-w-7xl mx-auto p-4'},
            # Header
            create_element('frame', {'class': 'mb-6'},
                create_element('frame', {'class': 'flex items-center justify-between'},
                    create_element('frame', {},
                        create_element('label', {
                            'text': '💻 PyUIWizard Code Editor',
                            'class': 'text-2xl font-bold text-gray-800 dark:text-gray-200'
                        }),
                        create_element('label', {
                            'text': 'Write code with live preview and execution',
                            'class': 'text-gray-500 dark:text-gray-400'
                        })
                    ),
                    create_element('frame', {'class': 'flex space-x-2'},
                        create_element('button', {
                            'text': 'Load Example',
                            'onClick': load_example,
                            'class': 'bg-gray-300 dark:bg-gray-700 hover:bg-gray-400 dark:hover:bg-gray-600 px-4 py-2 rounded'
                        }),
                        create_element('button', {
                            'text': 'Save',
                            'onClick': save_code,
                            'class': 'bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded'
                        }),
                        activeTab == 'python' and create_element('button', {
                            'text': 'Run Python',
                            'onClick': execute_python,
                            'class': 'bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded'
                        })
                    )
                )
            ),
            
            # Tab navigation
            create_element('frame', {'class': 'mb-4 border-b'},
                create_element('frame', {'class': 'flex'},
                    *[create_element('button', {
                        'text': label,
                        'onClick': lambda tab=tab: setActiveTab(tab),
                        'class': f'''
                            px-4 py-2 border-b-2 font-medium
                            {activeTab == tab
                                and 'border-blue-500 text-blue-600 dark:text-blue-400'
                                or 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}
                        ''',
                        'relief': 'flat'
                    }) for label, tab in [
                        ('HTML', 'html'),
                        ('CSS', 'css'),
                        ('JavaScript', 'js'),
                        ('Python', 'python'),
                        ('Preview', 'preview'),
                        ('Console', 'console')
                    ]]
                )
            ),
            
            # Main content based on active tab
            create_element('frame', {'class': 'h-[calc(100vh-200px)]'},
                activeTab == 'html' and create_element(CodeEditor, {
                    'key': 'html_editor',
                    'code': htmlCode,
                    'language': 'html',
                    'onChange': setHtmlCode
                }),
                
                activeTab == 'css' and create_element(CodeEditor, {
                    'key': 'css_editor',
                    'code': cssCode,
                    'language': 'css',
                    'onChange': setCssCode
                }),
                
                activeTab == 'js' and create_element(CodeEditor, {
                    'key': 'js_editor',
                    'code': jsCode,
                    'language': 'javascript',
                    'onChange': setJsCode
                }),
                
                activeTab == 'python' and create_element(CodeEditor, {
                    'key': 'python_editor',
                    'code': pythonCode,
                    'language': 'python',
                    'onChange': setPythonCode
                }),
                
                activeTab == 'preview' and create_element(LivePreview, {
                    'html': htmlCode,
                    'css': cssCode,
                    'js': jsCode
                }),
                
                activeTab == 'console' and create_element(OutputConsole, {
                    'output': consoleOutput,
                    'interactive': activeTab == 'console'
                })
            ),
            
            # Footer
            create_element('frame', {'class': 'mt-4 text-center text-gray-500 dark:text-gray-400 text-sm'},
                create_element('frame', {'class': 'flex items-center justify-center space-x-6'},
                    create_element('label', {
                        'text': f'HTML: {len(htmlCode)} chars'
                    }),
                    create_element('label', {
                        'text': f'CSS: {len(cssCode)} chars'
                    }),
                    create_element('label', {
                        'text': f'JS: {len(jsCode)} chars'
                    }),
                    create_element('label', {
                        'text': f'Python: {len(pythonCode)} chars'
                    }),
                    create_element('label', {
                        'text': f'Last run: {datetime.now().strftime("%H:%M:%S")}'
                    })
                )
            )
        )
    )

# ======================================
# 5. RUN THE CODE EDITOR
# ======================================
if __name__ == "__main__":
    print("""
    💻 PYUIWIZARD CODE EDITOR
    ========================
    Features:
    1. Multi-language code editor (HTML, CSS, JS, Python)
    2. Live preview for web technologies
    3. Python code execution with output console
    4. Syntax highlighting
    5. Auto-indentation and line numbers
    
    Instructions:
    - Switch between tabs to edit different file types
    - Python code can be executed with the "Run Python" button
    - Web code (HTML/CSS/JS) shows live preview
    - Check console for execution output
    ========================
    """)
    
    # Initialize application
    wizard = PyUIWizard(
        title="PyUIWizard Code Editor",
        width=1400,
        height=900,
        use_diffing=True
    )
    
    # Run editor
    wizard.render_app(lambda state: CodeEditorApp({}))
    wizard.run()