import tkinter as tk
from pyuiwizard import PyUIWizard, create_element, useState, useEffect, useRef
import time
# Custom hook for button analytics
def useButtonPress(button_name):
    """Track button presses with analytics"""
    [pressCount, setPressCount] = useState(0, key=f"{button_name}_press_count")
    [lastPressTime, setLastPressTime] = useState(None, key=f"{button_name}_last_press")
    
    def record_press():
        now = time.time()
        setPressCount(pressCount + 1)
        setLastPressTime(now)
        return now
    
    # Analytics effect
    useEffect(lambda: print(f"📊 Button '{button_name}' pressed {pressCount} times"), 
               [pressCount])
    
    return pressCount, lastPressTime, record_press

def SmartButton(props):
    """Smart button with all hooks and analytics"""
    key = props.get('key', 'smart_button')
    label = props.get('label', 'Click me')
    
    # Custom hook
    [pressCount, lastPressTime, record_press] = useButtonPress(key)
    
    # useState - Multiple states
    [isActive, setIsActive] = useState(False, key=f"{key}_active")
    [isLoading, setIsLoading] = useState(False, key=f"{key}_loading")
    [buttonText, setButtonText] = useState(label, key=f"{key}_text")
    
    # useRef - For focus/blur
    buttonRef = useRef(None)
    
    # useEffect - Complex side effects
    useEffect(lambda: print(f"🔘 Button '{key}' mounted"), [])
    
    useEffect(lambda: 
        print(f"🔄 Button active state changed: {isActive}") if isActive else None,
        [isActive]
    )
    
    # Async click handler
    def handle_click():
        # Record press
        record_press()
        
        # Set loading state
        setIsLoading(True)
        setButtonText("Loading...")
        
        # Simulate async operation
        def async_operation():
            time.sleep(1)  # Simulate work
            setIsLoading(False)
            setIsActive(not isActive)
            setButtonText(f"Clicked {pressCount + 1} times")
        
        import threading
        threading.Thread(target=async_operation, daemon=True).start()
    
    # Double click handler
    def handle_double_click():
        print(f"🖱️ Double clicked {key}")
    
    # Right click handler
    def handle_right_click():
        print(f"🖱️ Right clicked {key}")
    
    # Calculate dynamic styles
    button_class = f"px-6 py-3 rounded font-bold transition-all "
    
    if isLoading:
        button_class += "bg-gray-400 cursor-wait "
    elif isActive:
        button_class += "bg-green-500 hover:bg-green-600 "
    else:
        button_class += "bg-blue-500 hover:bg-blue-600 "
    
    button_class += "text-white shadow hover:shadow-lg"
    
    return create_element('frame', {
        'key': f"{key}_container",
        'class': 'p-4 border rounded'
    },
        create_element('button', {
            'key': key,
            'text': buttonText,
            'onClick': handle_click,
            'onDoubleClick': handle_double_click,
            'onRightClick': handle_right_click,
            'class': button_class,
            'state': 'disabled' if isLoading else 'normal',
            'ref': lambda w: setattr(buttonRef, 'current', w)
        }),
        create_element('label', {
            'key': f'{key}_stats',
            'text': f'Presses: {pressCount} | Active: {isActive}',
            'class': 'text-sm text-gray-600 mt-2'
        })
    )

def test_buttons():
    wizard = PyUIWizard(title="Button Examples", width=650, height=1200)
    
    def render(state):
        return create_element('frame', {'key': 'root', 'class': 'p-8 bg-gray-50'},
            create_element('label', {
                'key': 'title',
                'text': 'Smart Buttons with Hooks',
                'class': 'text-2xl font-bold mb-6 text-gray-800'
            }),
            create_element('frame', {'key': 'btn_grd', 'class': 'flex gap-4'},
                create_element(SmartButton, {'key': 'btn1', 'label': 'Primary Action'}),
                create_element(SmartButton, {'key': 'btn2', 'label': 'Secondary Action'}),
                create_element(SmartButton, {'key': 'btn3', 'label': 'Tertiary Action'})
            )
        )
    
    wizard.render_app(render)
    wizard.run()

if __name__ == "__main__":
    test_buttons()