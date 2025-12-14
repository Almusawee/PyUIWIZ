"""
Frame Widget Example with all hooks:
- useState: Counter state
- useEffect: Logging on mount/update
- useRef: DOM access for animations
- useContext: Theme context
- use_state (framework): Alternative state
"""

import tkinter as tk
from pyuiwizard import PyUIWizard, create_element, use_state, use_effect, use_ref, create_context, use_context
import time

# Create a theme context
ThemeContext = create_context('light')

def ThemeFrame(props):
    """Frame with all hook types"""
    component_key = props.get('key', 'theme_frame')
    
    # useState - Counter
    [count, setCount] = useState(0, key=f"{component_key}_counter")
    
    # useState - Text
    [text, setText] = useState("Hello Frame", key=f"{component_key}_text")
    
    # useRef - For DOM-like access
    frameRef = useRef(None)
    
    # useContext - Theme
    theme = useContext(ThemeContext)
    
    # useEffect - On mount and count change
    useEffect(lambda: print(f"🔵 Frame mounted/updated. Count: {count}, Theme: {theme}"), 
               [count, theme])
    
    # useEffect - Cleanup on unmount
    useEffect(lambda: lambda: print(f"🗑️ Frame {component_key} unmounting"), [])
    
    # Event handler with ref
    def handle_click():
        setCount(count + 1)
        if frameRef.current:
            print(f"Frame ref exists: {frameRef.current}")
    
    # Toggle theme
    def toggle_theme():
        ThemeContext.set('dark' if theme == 'light' else 'light')
    
    return create_element('frame', {
        'key': component_key,
        'class': f'bg-{"gray-800" if theme == "dark" else "white"} p-6 m-4 border rounded-lg shadow',
        'ref': lambda w: setattr(frameRef, 'current', w) if w else None
    },
        create_element('label', {
            'key': f'{component_key}_title',
            'text': f'{text} (Theme: {theme})',
            'class': f'text-{"white" if theme == "dark" else "black"} text-xl font-bold mb-4'
        }),
        create_element('label', {
            'key': f'{component_key}_count',
            'text': f'Count: {count}',
            'class': f'text-{"gray-300" if theme == "dark" else "gray-700"} text-lg mb-2'
        }),
        create_element('frame', {
            'key': f'{component_key}_button_row',
            'class': 'flex gap-2'
        },
            create_element('button', {
                'key': f'{component_key}_inc_btn',
                'text': 'Increment',
                'onClick': handle_click,
                'class': 'bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded'
            }),
            create_element('button', {
                'key': f'{component_key}_theme_btn',
                'text': 'Toggle Theme',
                'onClick': toggle_theme,
                'class': 'bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded'
            })
        )
    )

# Test the Frame component
def test_frame():
    wizard = PyUIWizard(title="Frame Example", width=400, height=300)
    
    def render(state):
        return create_element('frame', {'key': 'root', 'class': 'p-8'},
            create_element(ThemeFrame, {'key': 'frame1'}),
            create_element(ThemeFrame, {'key': 'frame2'})
        )
    
    wizard.render_app(render)
    wizard.run()

if __name__ == "__main__":
    test_frame()