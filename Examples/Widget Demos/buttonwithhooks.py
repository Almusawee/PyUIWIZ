"""
buttonwithhooks.py - Button widget with all event handlers and hooks
Demonstrates: onClick, onMouse, useState with callbacks
"""
from pyuiwizard import PyUIWizard, create_element, useState, useEffect, useRef

def ButtonDemo(props):
    """Button widget with all interactive features"""
    
    [clicks, setClicks] = useState(0)
    [hover, setHover] = useState(False)
    [disabled, setDisabled] = useState(False)
    buttonRef = useRef(None)
    
    # Track all interactions
    useEffect(lambda: print(f"🔄 Clicks: {clicks}, Hover: {hover}, Disabled: {disabled}"), 
              [clicks, hover, disabled])
    
    def handleClick():
        if not disabled:
            setClicks(clicks + 1)
            if clicks >= 10:
                setDisabled(True)  # Disable after 10 clicks
    
    def handleMouseEnter(e):
        setHover(True)
        print(f"🐭 Mouse entered at ({e['x']}, {e['y']})")
    
    def handleMouseLeave(e):
        setHover(False)
        print("🐭 Mouse left")
    
    def handleRightClick(e):
        setClicks(0)
        setDisabled(False)
        print("🔄 Reset by right click")
        return False  # Prevent context menu
    
    # Button variants based on state
    variant = "danger" if disabled else ("success" if clicks >= 5 else "primary")
    variants = {
        "primary": "bg-blue-500 hover:bg-blue-600",
        "success": "bg-green-500 hover:bg-green-600",
        "danger": "bg-red-500 hover:bg-red-600 cursor-not-allowed"
    }
    
    return create_element('frame', {
        'class': 'p-6 bg-gray-50 rounded-lg'
    },
        create_element('label', {
            'text': f'Button Interactions: {clicks} clicks',
            'class': 'text-gray-800 text-lg font-bold mb-4'
        }),
        
        # Main button with all events
        create_element('button', {
            'text': f'{"🔴 Disabled" if disabled else "🟢 Click me!"}',
            'onClick': handleClick,
            'onMouseEnter': handleMouseEnter,
            'onMouseLeave': handleMouseLeave,
            'onRightClick': handleRightClick,
            'onDoubleClick': lambda: print("🎯 Double click!"),
            'onKeyPress': lambda e: print(f"⌨️ Key: {e['key']}"),
            'disabled': disabled,
            'class': f'{variants[variant]} text-white font-bold py-3 px-6 rounded-lg shadow-md '
                     f'{"opacity-75" if disabled else "hover:shadow-lg"} '
                     f'transition-all duration-200',
            'ref': buttonRef,
            'key': 'main_button'
        }),
        
        # Feedback labels
        create_element('label', {
            'text': f'Hover: {"✅ Yes" if hover else "❌ No"}',
            'class': 'text-gray-600 mt-4'
        }),
        
        create_element('label', {
            'text': f'Status: {"🔴 Disabled" if disabled else "🟢 Active"}',
            'class': 'text-gray-600'
        }),
        
        # Action buttons
        create_element('frame', {'class': 'flex gap-2 mt-4'},
            create_element('button', {
                'text': 'Reset',
                'onClick': lambda: [setClicks(0), setDisabled(False)],
                'class': 'bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded'
            }),
            
            create_element('button', {
                'text': 'Toggle Disabled',
                'onClick': lambda: setDisabled(not disabled),
                'class': 'bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded'
            })
        )
    )

# Run the demo
if __name__ == "__main__":
    wizard = PyUIWizard(title="Button Demo", width=500, height=400)
    wizard.render_app(lambda s: create_element(ButtonDemo, {}))
    wizard.run()