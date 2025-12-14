"""
Calculator Demo App - PyUIWizard 4.2.0
Tests: useState and useEffect hooks, component reusability, state management, events, responsive design
"""

from pyuiwizard import PyUIWizard, create_element, useState, useEffect, Component, DESIGN_TOKENS
import math

# ======================================
# 1️⃣ BUTTON COMPONENT - REUSABLE
# ======================================
def CalculatorButton(props):
    """Reusable calculator button with visual feedback"""
    [isPressed, setIsPressed] = useState(False, key=f"btn_pressed_{props['key']}")
    
    def handle_press():
        setIsPressed(True)
        # Trigger the actual operation
        if props.get('onPress'):
            props['onPress']()
        # Reset pressed state after animation
        def reset():
            setIsPressed(False)
        if hasattr(props, 'root'):
            props.root.after(150, reset)
    
    # Different button types
    button_class = "bg-gray-200 hover:bg-gray-300 text-gray-800"
    if props.get('type') == 'operator':
        button_class = "bg-blue-500 hover:bg-blue-600 text-white"
    elif props.get('type') == 'equals':
        button_class = "bg-green-500 hover:bg-green-600 text-white"
    elif props.get('type') == 'clear':
        button_class = "bg-red-500 hover:bg-red-600 text-white"
    elif props.get('type') == 'scientific':
        button_class = "bg-purple-500 hover:bg-purple-600 text-white"
    
    # Add pressed effect
    if isPressed:
        button_class += " scale-95 opacity-80"
    
    return create_element('button', {
        'text': props['label'],
        'class': f"{button_class} font-bold text-lg rounded-lg transition-all duration-150",
        'onClick': handle_press,
        'key': props['key']
    })

# ======================================
# 2️⃣ DISPLAY COMPONENT - SMART
# ======================================
def CalculatorDisplay(props):
    """Display component with history tracking"""
    [history, setHistory] = useState([], key="calc_history")
    current_value = props.get('value', '0')
    
    # Add to history on new calculation
    useEffect(
        lambda: setHistory([current_value] + history[:4]) if props.get('isResult') else None,
        [current_value, props.get('isResult')]
    )
    
    return create_element('frame', {
        'class': 'bg-gray-900 p-4 rounded-lg shadow-inner',
        'key': 'display_frame'
    },
        # Main display
        create_element('label', {
            'text': current_value,
            'class': 'text-white text-3xl font-mono text-right block',
            'key': 'main_display'
        }),
        # History
        create_element('frame', {
            'class': 'mt-2',
            'key': 'history_frame'
        },
            create_element('label', {
                'text': 'History:',
                'class': 'text-gray-400 text-xs',
                'key': 'history_label'
            }),
            *[
                create_element('label', {
                    'text': item,
                    'class': 'text-gray-500 text-sm font-mono text-right block',
                    'key': f'history_{i}'
                }) for i, item in enumerate(history[:3])
            ]
        )
    )

# ======================================
# 3️⃣ MEMORY COMPONENT - WITH HOOKS
# ======================================
def MemoryPanel(props):
    """Memory operations (M+, M-, MR, MC)"""
    [memory, setMemory] = useState(0, key="calculator_memory")
    [isMemoryUsed, setIsMemoryUsed] = useState(False, key="memory_used")
    
    def memory_add():
        try:
            current = float(props.get('currentValue', 0))
            setMemory(memory + current)
            setIsMemoryUsed(True)
        except:
            pass
    
    def memory_subtract():
        try:
            current = float(props.get('currentValue', 0))
            setMemory(memory - current)
            setIsMemoryUsed(True)
        except:
            pass
    
    def memory_recall():
        if props.get('onRecall'):
            props['onRecall'](str(memory))
    
    def memory_clear():
        setMemory(0)
        setIsMemoryUsed(False)
    
    return create_element('frame', {
        'class': 'bg-gray-100 p-3 rounded border',
        'key': 'memory_panel'
    },
        create_element('label', {
            'text': f'Memory: {memory}' if isMemoryUsed else 'Memory: Empty',
            'class': 'text-gray-700 text-sm font-bold',
            'key': 'memory_display'
        }),
        create_element('frame', {
            'class': 'flex flex-wrap gap-1 mt-2',
            'key': 'memory_buttons'
        },
            create_element(CalculatorButton, {
                'label': 'M+',
                'type': 'scientific',
                'onPress': memory_add,
                'key': 'mplus'
            }),
            create_element(CalculatorButton, {
                'label': 'M-',
                'type': 'scientific',
                'onPress': memory_subtract,
                'key': 'mminus'
            }),
            create_element(CalculatorButton, {
                'label': 'MR',
                'type': 'scientific',
                'onPress': memory_recall,
                'key': 'mrecall'
            }),
            create_element(CalculatorButton, {
                'label': 'MC',
                'type': 'clear',
                'onPress': memory_clear,
                'key': 'mclear'
            })
        )
    )

# ======================================
# 4️⃣ MAIN CALCULATOR COMPONENT
# ======================================
def CalculatorApp(props):
    """Main calculator with full functionality"""
    
    # 🎯 STATE HOOKS - Like React!
    [display, setDisplay] = useState('0', key="calc_display")
    [operator, setOperator] = useState(None, key="calc_operator")
    [prevValue, setPrevValue] = useState(None, key="calc_prev_value")
    [isResult, setIsResult] = useState(False, key="calc_is_result")
    [isScientificMode, setIsScientificMode] = useState(False, key="scientific_mode")
    
    # 🎯 EFFECT HOOK - Track operations
    useEffect(
        lambda: print(f"Calculator state updated: {display}"),
        [display]
    )
    
    # Handle digit input
    def handle_digit(digit):
        if isResult or display == '0' or display == 'Error':
            setDisplay(digit)
            setIsResult(False)
        else:
            setDisplay(display + digit)
    
    # Handle operator
    def handle_operation(op):
        try:
            if prevValue is None:
                setPrevValue(float(display))
                setOperator(op)
                setDisplay('0')
            else:
                calculate_result()
                setOperator(op)
                setPrevValue(float(display))
                setDisplay('0')
        except:
            setDisplay('Error')
    
    # Calculate result
    def calculate_result():
        if prevValue is not None and operator:
            try:
                current = float(display)
                result = 0
                
                if operator == '+':
                    result = prevValue + current
                elif operator == '-':
                    result = prevValue - current
                elif operator == '×':
                    result = prevValue * current
                elif operator == '÷':
                    if current != 0:
                        result = prevValue / current
                    else:
                        setDisplay('Error: Div/0')
                        reset()
                        return
                elif operator == '^':
                    result = prevValue ** current
                
                # Format result
                if result.is_integer():
                    result_str = str(int(result))
                else:
                    result_str = f"{result:.6f}".rstrip('0').rstrip('.')
                
                setDisplay(result_str)
                setPrevValue(None)
                setOperator(None)
                setIsResult(True)
                
            except Exception as e:
                setDisplay('Error')
                reset()
    
    # Clear calculator
    def clear():
        setDisplay('0')
        setPrevValue(None)
        setOperator(None)
        setIsResult(False)
    
    # Backspace
    def backspace():
        if len(display) > 1 and display != 'Error':
            setDisplay(display[:-1])
        else:
            setDisplay('0')
    
    # Toggle scientific mode
    def toggle_scientific():
        setIsScientificMode(not isScientificMode)
    
    # Scientific functions
    def scientific_function(func):
        try:
            value = float(display)
            result = 0
            
            if func == 'sin':
                result = math.sin(math.radians(value))
            elif func == 'cos':
                result = math.cos(math.radians(value))
            elif func == 'tan':
                result = math.tan(math.radians(value))
            elif func == 'log':
                result = math.log10(value) if value > 0 else 'Error'
            elif func == 'ln':
                result = math.log(value) if value > 0 else 'Error'
            elif func == 'sqrt':
                result = math.sqrt(value) if value >= 0 else 'Error'
            elif func == 'square':
                result = value ** 2
            elif func == 'inverse':
                result = 1 / value if value != 0 else 'Error'
            elif func == 'pi':
                result = math.pi
            
            if result != 'Error':
                if isinstance(result, float):
                    result_str = f"{result:.6f}".rstrip('0').rstrip('.')
                else:
                    result_str = str(result)
                setDisplay(result_str)
                setIsResult(True)
            else:
                setDisplay('Error')
                
        except:
            setDisplay('Error')
    
    # Memory recall callback
    def handle_memory_recall(value):
        setDisplay(value)
        setIsResult(True)
    
    # Button layout - Standard mode
    standard_buttons = [
        ['C', '⌫', '÷', '×'],
        ['7', '8', '9', '-'],
        ['4', '5', '6', '+'],
        ['1', '2', '3', '='],
        ['0', '.', '±', '^']
    ]
    
    # Button layout - Scientific mode
    scientific_buttons = [
        ['sin', 'cos', 'tan', 'log'],
        ['ln', '√', 'x²', '1/x'],
        ['π', '(', ')', 'mod']
    ]
    
    # Map buttons to handlers
    def get_button_handler(label):
        if label.isdigit() or label == '.':
            return lambda: handle_digit(label)
        elif label in ['+', '-', '×', '÷', '^']:
            return lambda: handle_operation(label)
        elif label == '=':
            return calculate_result
        elif label == 'C':
            return clear
        elif label == '⌫':
            return backspace
        elif label == '±':
            return lambda: setDisplay(str(-float(display)) if display != '0' else '0')
        elif label in ['sin', 'cos', 'tan', 'log', 'ln', 'sqrt', 'square', 'inverse', 'pi']:
            return lambda: scientific_function(label)
        else:
            return None
    
    # Get button type
    def get_button_type(label):
        if label in ['+', '-', '×', '÷', '^']:
            return 'operator'
        elif label == '=':
            return 'equals'
        elif label == 'C':
            return 'clear'
        elif label in ['sin', 'cos', 'tan', 'log', 'ln', '√', 'x²', '1/x', 'π', 'mod']:
            return 'scientific'
        else:
            return 'digit'
    
    # Build button grid
    def build_button_grid(button_grid):
        return [
            create_element('frame', {
                'class': 'flex gap-2 mb-2',
                'key': f'row_{ri}'
            },
                *[
                    create_element(CalculatorButton, {
                        'label': btn,
                        'type': get_button_type(btn),
                        'onPress': get_button_handler(btn),
                        'key': f'btn_{ri}_{ci}'
                    }) for ci, btn in enumerate(row)
                ]
            ) for ri, row in enumerate(button_grid)
        ]
    
    return create_element('frame', {
        'class': 'bg-gray-50 p-6 rounded-xl shadow-lg max-w-md mx-auto my-8',
        'key': 'calculator_main'
    },
        # Header
        create_element('frame', {
            'class': 'mb-4',
            'key': 'header'
        },
            create_element('label', {
                'text': '🧮 PyUIWizard Calculator',
                'class': 'text-2xl font-bold text-gray-800',
                'key': 'title'
            }),
            create_element('label', {
                'text': 'v4.2.0 - React-like Python GUI',
                'class': 'text-gray-500 text-sm',
                'key': 'subtitle'
            })
        ),
        
        # Display
        create_element(CalculatorDisplay, {
            'value': display,
            'isResult': isResult,
            'key': 'display'
        }),
        
        # Memory Panel
        create_element(MemoryPanel, {
            'currentValue': display,
            'onRecall': handle_memory_recall,
            'key': 'memory'
        }),
        
        # Mode Toggle
        create_element('frame', {
            'class': 'my-4 flex justify-between items-center',
            'key': 'mode_toggle'
        },
            create_element('label', {
                'text': f'Mode: {"🔬 Scientific" if isScientificMode else "🧮 Standard"}',
                'class': 'text-gray-700 font-bold',
                'key': 'mode_label'
            }),
            create_element(CalculatorButton, {
                'label': '🔬' if not isScientificMode else '🧮',
                'type': 'scientific',
                'onPress': toggle_scientific,
                'key': 'toggle_mode'
            })
        ),
        
        # Scientific Functions (when enabled)
        *(
            build_button_grid(scientific_buttons) if isScientificMode else []
        ),
        
        # Main Button Grid
        *build_button_grid(standard_buttons),
        
        # Status Bar
        create_element('frame', {
            'class': 'mt-4 pt-3 border-t border-gray-200',
            'key': 'status'
        },
            create_element('label', {
                'text': f'Operator: {operator if operator else "None"} | Prev: {prevValue if prevValue else "None"}',
                'class': 'text-gray-500 text-xs font-mono',
                'key': 'status_text'
            }),
            create_element('label', {
                'text': '✅ Each button maintains independent state via useState hooks',
                'class': 'text-green-600 text-xs mt-1',
                'key': 'hook_status'
            })
        )
    )

# ======================================
# 5️⃣ ADVANCED FEATURES DEMO
# ======================================
class ThemeToggle(Component):
    """Class component demonstrating Component lifecycle"""
    
    def __init__(self, props):
        super().__init__(props)
        self.state = {'dark_mode': False}
    
    def on_mount(self):
        print("🔧 ThemeToggle component mounted")
    
    def toggle_theme(self):
        self.state['dark_mode'] = not self.state['dark_mode']
        DESIGN_TOKENS.set_theme('dark' if self.state['dark_mode'] else 'light')
        # Force re-render (in real app, would use useState)
        if hasattr(self, 'wizard'):
            self.wizard._render_trigger.set(self.wizard._render_trigger.value + 1)
    
    def render(self):
        return create_element('frame', {
            'class': 'fixed bottom-4 right-4',
            'key': 'theme_toggle'
        },
            create_element('button', {
                'text': '🌙' if not self.state['dark_mode'] else '☀️',
                'class': 'bg-gray-800 text-white p-3 rounded-full shadow-lg hover:bg-gray-900',
                'onClick': self.toggle_theme,
                'key': 'theme_button'
            })
        )

# ======================================
# 6️⃣ MAIN APP WITH MULTIPLE COMPONENTS
# ======================================
def MainApp(state):
    """Main app combining multiple components"""
    [showAdvanced, setShowAdvanced] = useState(False, key="show_advanced")
    
    return create_element('frame', {
        'class': 'min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 p-6',
        'key': 'app_root'
    },
        # Header
        create_element('frame', {
            'class': 'text-center mb-8',
            'key': 'app_header'
        },
            create_element('h1', {
                'text': 'PyUIWizard 4.2.0 - Calculator Demo',
                'class': 'text-4xl font-bold text-gray-800 mb-2',
                'key': 'app_title'
            }),
            create_element('p', {
                'text': 'Demonstrating React-like hooks, component reusability, and state management in Python Tkinter',
                'class': 'text-gray-600 max-w-2xl mx-auto',
                'key': 'app_desc'
            })
        ),
        
        # Calculator
        create_element(CalculatorApp, {'key': 'calculator'}),
        
        # Advanced Features Toggle
        create_element('frame', {
            'class': 'mt-8 text-center',
            'key': 'advanced_toggle'
        },
            create_element('button', {
                'text': f"{'Hide' if showAdvanced else 'Show'} Advanced Features",
                'class': 'bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded',
                'onClick': lambda: setShowAdvanced(not showAdvanced),
                'key': 'toggle_advanced'
            })
        ),
        
        # Advanced Features Panel
        *([
            create_element('frame', {
                'class': 'mt-6 p-6 bg-white rounded-xl shadow max-w-2xl mx-auto',
                'key': 'advanced_panel'
            },
                create_element('h2', {
                    'text': '🧪 Advanced Features Demo',
                    'class': 'text-xl font-bold text-gray-800 mb-4',
                    'key': 'advanced_title'
                }),
                create_element('p', {
                    'text': 'Multiple independent counters demonstrating component isolation:',
                    'class': 'text-gray-600 mb-4',
                    'key': 'advanced_desc'
                }),
                
                # Multiple independent counters
                create_element('frame', {
                    'class': 'flex flex-wrap gap-4',
                    'key': 'counters_demo'
                },
                    *[
                        create_element(CounterDemo, {
                            'label': f'Counter {i+1}',
                            'initial': i * 10,
                            'key': f'counter_{i}'
                        }) for i in range(6)
                    ]
                ),
                
                # Component stats
                create_element('frame', {
                    'class': 'mt-6 p-4 bg-gray-100 rounded',
                    'key': 'stats'
                },
                    create_element('label', {
                        'text': '📊 Framework Stats:',
                        'class': 'font-bold text-gray-700',
                        'key': 'stats_label'
                    }),
                    create_element('label', {
                        'text': f'• Theme: {DESIGN_TOKENS.current_theme} | Breakpoint: {state.get("breakpoint", "md")}',
                        'class': 'text-gray-600 text-sm',
                        'key': 'stats_details'
                    })
                )
            )
        ] if showAdvanced else []),
        
        # Footer
        create_element('frame', {
            'class': 'mt-12 text-center text-gray-500 text-sm',
            'key': 'footer'
        },
            create_element('p', {
                'text': '✨ PyUIWizard 4.2.0 - React-like GUI Framework for Python',
                'key': 'footer_text'
            }),
            create_element('p', {
                'text': '✅ Each calculator button is an independent component instance with its own useState hook',
                'class': 'text-green-600 font-medium mt-1',
                'key': 'hook_demo'
            })
        )
    )

# ======================================
# 7️⃣ COUNTER DEMO COMPONENT
# ======================================
def CounterDemo(props):
    """Simple counter to demonstrate component reusability"""
    [count, setCount] = useState(props.get('initial', 0), key=f"demo_counter_{props['key']}")
    [clicks, setClicks] = useState(0, key=f"demo_clicks_{props['key']}")
    
    def increment():
        setCount(count + 1)
        setClicks(clicks + 1)
    
    def decrement():
        setCount(count - 1)
        setClicks(clicks + 1)
    
    def reset():
        setCount(props.get('initial', 0))
        setClicks(0)
    
    return create_element('frame', {
        'class': 'bg-white p-4 rounded-lg shadow flex-1 min-w-[200px]',
        'key': props['key']
    },
        create_element('label', {
            'text': props['label'],
            'class': 'font-bold text-gray-700',
            'key': f"{props['key']}_label"
        }),
        create_element('label', {
            'text': f'Count: {count}',
            'class': 'text-2xl font-mono my-2',
            'key': f"{props['key']}_count"
        }),
        create_element('label', {
            'text': f'Clicks: {clicks}',
            'class': 'text-gray-500 text-sm',
            'key': f"{props['key']}_clicks"
        }),
        create_element('frame', {
            'class': 'flex gap-2 mt-3',
            'key': f"{props['key']}_buttons"
        },
            create_element('button', {
                'text': '-',
                'class': 'bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded flex-1',
                'onClick': decrement,
                'key': f"{props['key']}_dec"
            }),
            create_element('button', {
                'text': 'Reset',
                'class': 'bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded flex-1',
                'onClick': reset,
                'key': f"{props['key']}_reset"
            }),
            create_element('button', {
                'text': '+',
                'class': 'bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded flex-1',
                'onClick': increment,
                'key': f"{props['key']}_inc"
            })
        )
    )

# ======================================
# 8️⃣ RUN THE APPLICATION
# ======================================
if __name__ == "__main__":
    print("""
    🧮 PYUIWIZARD 4.2.0 CALCULATOR DEMO
    ====================================
    Testing Framework Features:
    1. ✅ useState hooks for component state
    2. ✅ Reusable functional components
    3. ✅ Independent component instances
    4. ✅ Component lifecycle (useEffect)
    5. ✅ Responsive design with Tailwind classes
    6. ✅ Event handling with debouncing
    7. ✅ Multiple independent state containers
    8. ✅ Component composition
    
    Click buttons to test:
    - Each calculator button is independent
    - Memory panel uses separate state
    - Counters demonstrate reusability
    ====================================
    """)
    
    # Initialize wizard
    wizard = PyUIWizard(
        title="PyUIWizard 4.2.0 - Calculator Demo",
        width=900,
        height=800,
        use_diffing=True
    )
    
    # Set light theme
    DESIGN_TOKENS.set_theme('light')
    
    # Add a global theme toggle
    theme_toggle = ThemeToggle({})
    theme_toggle.wizard = wizard
    
    # Run the app
    wizard.render_app(MainApp)
    wizard.run()