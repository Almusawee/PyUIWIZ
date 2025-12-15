import tkinter as tk
from pyuiwizard import PyUIWizard, create_element, useState, useEffect, useRef, create_context, useContext
import time

# Create theme context
ThemeContext = create_context('light')

def ThemeFrame(props):
    """Frame with OPTIMIZED hook usage"""
    component_key = props.get('key', 'theme_frame')
    
    
    count_state = useState(0, key=f"{component_key}_counter")
    count = count_state[0]
    setCount = count_state[1]
    
    text_state = useState("Hello Frame", key=f"{component_key}_text")
    text = text_state[0]
    setText = text_state[1]
    
    # Store ref in component instance, not in render
    # This prevents ref from changing every render
    if not hasattr(ThemeFrame, '_refs'):
        ThemeFrame._refs = {}
    
    if component_key not in ThemeFrame._refs:
        ThemeFrame._refs[component_key] = useRef(None)
    
    frameRef = ThemeFrame._refs[component_key]
    
    # useContext with proper theme
    theme = useContext(ThemeContext)
    
    #  useEffect with proper dependencies
    # Only runs when count OR theme changes, not on every render
    useEffect(lambda: print(f"🔵 Frame updated. Count: {count}, Theme: {theme}"), 
               [count, theme])
    
    # useEffect for mount/unmount
    useEffect(lambda: 
        (print(f"🎯 Frame {component_key} mounted"), 
         lambda: print(f"🗑️ Frame {component_key} unmounted"))[0], 
        [])
    
    def handle_click():
        # Functional update for better performance
        setCount(lambda prev: prev + 1)
        
        # Access ref safely
        if hasattr(frameRef, 'current') and frameRef.current:
            print(f"✅ Frame ref accessible")
    
    def toggle_theme():
        ThemeContext.set('dark' if theme == 'light' else 'light')
    
    # Stable ref function that doesn't change every render
    # Using a class method to ensure same function reference
    def set_ref(widget):
        if widget and hasattr(frameRef, 'current'):
            frameRef.current = widget
    
    # Determine theme-based styling
    if theme == 'dark':
        bg_color = 'bg-gray-500'
        text_color = 'text-white'
        border_color = 'border-gray-700'
    else:
        bg_color = 'bg-white'
        text_color = 'text-black'
        border_color = 'border-gray-300'
    
    return create_element('frame', {
        'key': component_key,
        'class': f'{bg_color} {border_color} p-6 m-4 border rounded shadow bg-teal-100',
        #Stable ref that doesn't trigger re-renders
        'ref': set_ref
    },
        create_element('label', {
            'key': f'{component_key}_title',
            'text': f'{text} (Theme: {theme})',
            'class': f'{text_color} text-sm font-bold mb-2'
        }),
        create_element('label', {
            'key': f'{component_key}_count',
            'text': f'Count: {count}',
            'class': f'{text_color} text-lg mb-2 bg-yellow-100'
        }),
        create_element('frame', {
            'key': f'{component_key}_button_row',
            'class': 'flex gap-2 bg-white-600'
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
                'class': 'bg-green-300 hover:bg-green-500 text-white px-4 py-2 rounded'
            })
        )
    )

# Clean up refs on app exit
def cleanup_refs():
    if hasattr(ThemeFrame, '_refs'):
        ThemeFrame._refs.clear()

# Test with optimized rendering
def test_optimized_frame():
    wizard = PyUIWizard(
        title="Optimized Frame Example", 
        width=650, 
        height=1200, 
        use_diffing=True
    )
    
    # Create global state
    wizard.create_state('app_state', {})
    
    def render(state):
        return create_element('frame', {
            'key': 'root', 
            'class': 'p-8 bg-yellow-600 ',
            'fg': 'white'
        },
            create_element('label', {
                'key': 'main_title',
                'text': 'Optimized Frame Demo',
                'class': 'text-xl font-bold mb-6 text-gray-300'
            }),
            create_element(ThemeFrame, {'key': 'frame1'}),
            create_element(ThemeFrame, {'key': 'frame2'})
        )
    
    wizard.render_app(render)
    
    # Register cleanup
    wizard.root.protocol("WM_DELETE_WINDOW", lambda: (cleanup_refs(), wizard.root.quit()))
    
    wizard.run()

if __name__ == "__main__":
    test_optimized_frame()