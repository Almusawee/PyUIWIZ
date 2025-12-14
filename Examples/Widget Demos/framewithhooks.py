"""
framewithhooks.py - Frame widget with all hooks
Demonstrates: useState, useEffect, useRef and useContext
"""
from pyuiwizard import PyUIWizard, create_element, useState, useEffect, useRef, useContext, create_context, Component

# Create a context for theme
ThemeContext = create_context('light')

def FrameDemo(props):
    """Frame widget showcasing all hook types"""
    
    # useState - Component state
    [count, setCount] = useState(0)
    [title, setTitle] = useState("Frame Demo")
    
    # useRef - DOM reference
    frameRef = useRef(None)
    
    # useContext - Theme context
    theme = useContext(ThemeContext)
    
    # useEffect - Side effects
    useEffect(lambda: print(f"🎯 Frame mounted! Count: {count}"), [])  # Mount
    useEffect(lambda: print(f"🔢 Count updated to: {count}"), [count])  # Update
    useEffect(lambda: lambda: print("🗑️ Frame unmounting"), [])  # Cleanup
    
    # useRef with effect
    useEffect(lambda: 
        print(f"📏 Frame dimensions: {frameRef.current.winfo_width() if frameRef.current else 'N/A'}"),
        [frameRef.current]
    )
    
    def increment():
        setCount(count + 1)
        if count >= 5:
            setTitle("Frame Demo 🚀")
    
    return create_element('frame', {
        'key': 'main_frame',
        'class': f"p-6 m-4 bg-{theme}-100 border border-{theme}-300 {'rounded-lg' if count > 2 else ''}",
        'ref': frameRef
    },
        # Title with dynamic styling
        create_element('label', {
            'text': f"{title} (Count: {count})",
            'class': f"text-{theme}-800 text-xl font-bold mb-4"
        }),
        
        # Counter buttons
        create_element('button', {
            'text': 'Increment',
            'onClick': increment,
            'class': 'bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 mr-2 rounded'
        }),
        
        create_element('button', {
            'text': 'Reset',
            'onClick': lambda: setCount(0),
            'class': 'bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded'
        }),
        
        # Theme toggle
        create_element('button', {
            'text': f'Switch to {"dark" if theme == "light" else "light"} theme',
            'onClick': lambda: ThemeContext.set('dark' if theme == 'light' else 'light'),
            'class': 'bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 mt-4 rounded'
        }),
        
        # Dynamic content based on count
        create_element('label', {
            'text': f"{'🌟' * min(count, 10)}" if count > 0 else "Click increment!",
            'class': 'text-green-600 text-lg mt-4'
        })
    )

def main_render(state):
    return create_element('frame', {'class': 'p-8'},
        create_element(FrameDemo, {'key': 'demo'})
    )

if __name__ == "__main__":
    wizard = PyUIWizard(title="Frame Demo", width=500, height=400)
    wizard.render_app(main_render)
    wizard.run()