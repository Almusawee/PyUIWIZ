🧠 PYUIWIZARD 4.2.0 - ULTIMATE ARCHITECTURE GUIDE

🎯 7 CRITICAL STEPS TO BUILD ANY UI

🔑 1. FRAMEWORK INITIALIZATION (ONE-TIME)

```python
from pyuiwizardv420 import PyUIWizard, create_element, use_state, use_effect, Component

# Step A: Create app instance
wizard = PyUIWizard(
    title="Your App",        # Window title
    width=800,              # Window width
    height=600,             # Window height
    use_diffing=True        # ✅ ALWAYS KEEP TRUE (critical for performance)
)

# Step B: Set main render function (step 4)
wizard.render_app(main_render)

# Step C: Run app
wizard.run()
```

---

⚛️ 2. CREATE REUSABLE COMPONENTS (LIKE REACT)

```python
# Functional Component Pattern
def YourComponent(props):
    """
    Props = Component properties (immutable)
    Return = VDOM element tree
    """
    
    # 🎯 STEP 2A: DECLARE STATE (like React)
    [count, setCount] = use_state(0, key="unique_key_for_component")
    
    # 🎯 STEP 2B: DECLARE EFFECTS (optional)
    use_effect(
        lambda: print(f"Count changed to {count}"),
        [count]  # Run when 'count' changes
    )
    
    # 🎯 STEP 2C: RETURN VDOM
    return create_element('button', {
        'text': f'Count: {count}',
        'onClick': lambda: setCount(count + 1),
        'class': 'your-tailwind-classes',
        'key': props.get('key')  # 🔥 CRITICAL FOR PERFORMANCE
    })

# Class Component Pattern (for lifecycle methods)
class YourClassComponent(Component):
    def __init__(self, props):
        super().__init__(props)
        self.state = {'value': 0}
    
    def on_mount(self):
        print("Component mounted")
    
    def render(self):
        return create_element('div', {'key': self.props.get('key')},
            f"Value: {self.state['value']}"
        )
```

---

📦 3. VDOM ELEMENT CREATION (BUILDING BLOCKS)

```python
# 🔥 CRITICAL SYNTAX:
element = create_element(
    element_type,     # String ('button'), Component class, or function
    props,            # Dict of properties
    *children         # Unlimited child elements
)

# EXAMPLE HIERARCHY:
return create_element('frame', {
        'class': 'p-4 bg-white',
        'key': 'container'  # 🔥 ALWAYS USE KEYS!
    },
    create_element('label', {
        'text': 'Hello',
        'class': 'text-xl',
        'key': 'title'
    }),
    create_element('button', {
        'text': 'Click me',
        'onClick': handle_click,
        'key': 'main_button'
    }),
    create_element(ReusableComponent, {
        'data': some_data,
        'key': 'child_component'  # 🔥 PASS KEY TO COMPONENTS TOO!
    })
)
```

---

🔄 4. MAIN RENDER FUNCTION (ROOT OF YOUR APP)

```python
def main_render(state):
    """
    Called on every state change.
    state = Global state + hooks state + framework data
    """
    
    # 🎯 STEP 4A: USE STATE HOOKS (if needed globally)
    [theme, setTheme] = use_state('light', key="app_theme")
    
    # 🎯 STEP 4B: COMPOSE UI
    return create_element('frame', {'class': 'min-h-screen', 'key': 'root'},
        create_element(Navbar, {'key': 'navbar'}),
        create_element(Sidebar, {'key': 'sidebar'}),
        create_element(MainContent, {'key': 'main'}),
        create_element(Footer, {'key': 'footer'})
    )
```

---

⚡ 5. STATE MANAGEMENT STRATEGY

Option A: Local Component State (Most Common)

```python
def Counter(props):
    [count, setCount] = use_state(0, key=f"counter_{props['id']}")
    # ✅ Independent per instance
    # ✅ Automatic cleanup
    # ✅ No prop drilling
```

Option B: Lifting State Up (Parent-Managed)

```python
def ParentComponent(props):
    [count, setCount] = use_state(0, key="parent_counter")
    
    def increment():
        setCount(count + 1)
    
    return create_element('div', {'key': 'parent'},
        create_element(ChildComponent, {
            'value': count,
            'onIncrement': increment,
            'key': 'child'
        })
    )
```

Option C: Global Streams (Advanced)

```python
# Create once
counter_stream = wizard.create_state('global_counter', 0)

# Use anywhere via state param in main_render
def main_render(state):
    global_count = state.get('global_counter', 0)
    return create_element('div', {'key': 'root'}, 
        f"Global: {global_count}"
    )
```

---

🎨 6. STYLING SYSTEM (TAILWIND-LIKE)

```python
create_element('button', {
    'class': ' '.join([
        'bg-blue-500',          # Background color
        'hover:bg-blue-600',    # Hover state
        'text-white',           # Text color
        'font-bold',            # Font weight
        'py-2 px-4',            # Padding
        'rounded',              # Border radius
        'shadow',               # Box shadow
        'transition-all',       # CSS transitions
        'duration-300'          # Transition duration
    ]),
    'key': 'styled_button'
})
```

Responsive Design:

```python
create_element('div', {
    'class': ' '.join([
        'w-full',          # Full width on mobile
        'md:w-1/2',        # Half width on medium+
        'lg:w-1/3',        # Third width on large+
        'flex',            # Flexbox
        'flex-col',        # Column direction
        'md:flex-row',     # Row on medium+
        'gap-4'            # Gap between children
    ]),
    'key': 'responsive_container'
})
```

---

🚀 7. EVENT HANDLING & SIDE EFFECTS

```python
def InteractiveComponent(props):
    [data, setData] = use_state([], key="data_list")
    [loading, setLoading] = use_state(False, key="loading_state")
    
    # 🎯 Event Handler
    def fetch_data():
        setLoading(True)
        
        # Simulate async operation
        import threading
        def load():
            import time
            time.sleep(1)  # API call
            setData(['Item 1', 'Item 2', 'Item 3'])
            setLoading(False)
        
        threading.Thread(target=load).start()
    
    # 🎯 Side Effect (like React's useEffect)
    use_effect(
        lambda: fetch_data(),  # Run once on mount
        []                     # Empty dependency array = run once
    )
    
    # 🎯 Conditional Rendering
    return create_element('div', {'key': 'interactive'},
        create_element('button', {
            'text': 'Refresh' if not loading else 'Loading...',
            'onClick': fetch_data if not loading else None,
            'class': 'bg-blue-500 text-white p-2 rounded disabled:opacity-50',
            'key': 'refresh_btn'
        }),
        create_element('ul', {'key': 'list'},
            *[
                create_element('li', {
                    'text': item,
                    'key': f'item_{i}'  # 🔥 CRITICAL FOR LISTS
                }) for i, item in enumerate(data)
            ]
        ) if data else create_element('p', {
            'text': 'No data',
            'key': 'empty_state'
        })
    )
```

---

🧩 ARCHITECTURE PATTERNS

Pattern 1: Container/Presenter

```python
# Container (Smart - has state/logic)
def UserContainer(props):
    [users, setUsers] = use_state([], key="users")
    
    def load_users():
        # API call logic here
        setUsers([{'name': 'Alice'}, {'name': 'Bob'}])
    
    return create_element(UserList, {
        'users': users,
        'onLoad': load_users,
        'key': 'user_list'
    })

# Presenter (Dumb - just displays)
def UserList(props):
    return create_element('div', {'key': 'list'},
        create_element('button', {
            'text': 'Load Users',
            'onClick': props['onLoad'],
            'key': 'load_btn'
        }),
        *[create_element('p', {
            'text': user['name'],
            'key': f'user_{i}'
        }) for i, user in enumerate(props['users'])]
    )
```

Pattern 2: Higher-Order Component

```python
def withLoading(Component):
    def Wrapped(props):
        [loading, setLoading] = use_state(False, key="hoc_loading")
        
        return create_element('div', {'key': f"hoc_{props.get('key')}"},
            create_element(Component, {
                **props,
                'loading': loading,
                'setLoading': setLoading
            })
        )
    return Wrapped

# Usage
EnhancedComponent = withLoading(MyComponent)
```

Pattern 3: Render Props

```python
def DataFetcher(props):
    [data, setData] = use_state(None, key="fetcher_data")
    
    use_effect(
        lambda: fetch_data(props['url'], setData),
        [props['url']]
    )
    
    # Render children with data
    return props['children'](data)

# Usage
create_element(DataFetcher, {'url': '/api/data', 'key': 'fetcher'},
    lambda data: create_element('div', {'key': 'content'},
        f"Data: {data}" if data else "Loading..."
    )
)
```

---

⚡ PERFORMANCE CRITICALS

🔥 ALWAYS DO THESE:

```python
# ✅ CORRECT - Stable keys
create_element(Component, {'key': 'stable_unique_id'})

# ✅ CORRECT - Keyed lists
[create_element('li', {'key': item.id, 'text': item.name}) for item in items]

# ✅ CORRECT - Memoized callbacks
def MyComponent(props):
    [count, setCount] = use_state(0, key="counter")
    
    # Memoize with useCallback pattern
    def increment():
        setCount(count + 1)
    
    return create_element('button', {
        'onClick': increment,  # Same function reference
        'key': 'button'
    })
```

❌ NEVER DO THESE:

```python
# ❌ WRONG - Dynamic keys
create_element(Component, {'key': f"item_{Math.random()}"})

# ❌ WRONG - Inline functions in render
create_element('button', {
    'onClick': lambda: setCount(count + 1),  # New function each render
})

# ❌ WRONG - No keys in lists
[create_element('li', {'text': item.name}) for item in items]  # ❌ NO KEY!
```

---

📦 COMPLETE TEMPLATE

```python
from pyuiwizardv420 import PyUIWizard, create_element, use_state, use_effect

# 1. Define components
def Header(props):
    return create_element('header', {
        'class': 'bg-gray-800 text-white p-4',
        'key': 'app_header'
    },
        create_element('h1', {
            'text': 'My PyUIWizard App',
            'class': 'text-2xl font-bold',
            'key': 'title'
        })
    )

def CounterApp(props):
    [count, setCount] = use_state(0, key=f"counter_{props['id']}")
    
    return create_element('div', {
        'class': 'p-4 border rounded',
        'key': props['key']
    },
        create_element('h2', {
            'text': f'Counter {props["id"]}',
            'class': 'text-lg font-bold mb-2',
            'key': f'counter_title_{props["id"]}'
        }),
        create_element('p', {
            'text': f'Count: {count}',
            'class': 'text-3xl mb-4',
            'key': f'counter_display_{props["id"]}'
        }),
        create_element('button', {
            'text': 'Increment',
            'onClick': lambda: setCount(count + 1),
            'class': 'bg-blue-500 text-white px-4 py-2 rounded',
            'key': f'counter_button_{props["id"]}'
        })
    )

# 2. Main render function
def main_render(state):
    return create_element('div', {
        'class': 'min-h-screen bg-gray-100',
        'key': 'app_root'
    },
        create_element(Header, {'key': 'header'}),
        create_element('main', {
            'class': 'p-6 max-w-4xl mx-auto',
            'key': 'main_content'
        },
            create_element('h2', {
                'text': 'Multiple Independent Counters',
                'class': 'text-xl font-bold mb-4',
                'key': 'section_title'
            }),
            create_element('div', {
                'class': 'grid grid-cols-3 gap-4',
                'key': 'counters_grid'
            },
                create_element(CounterApp, {'key': 'counter1', 'id': 1}),
                create_element(CounterApp, {'key': 'counter2', 'id': 2}),
                create_element(CounterApp, {'key': 'counter3', 'id': 3})
            )
        )
    )

# 3. Initialize and run
if __name__ == "__main__":
    wizard = PyUIWizard(
        title="PyUIWizard Demo",
        width=800,
        height=600,
        use_diffing=True
    )
    
    wizard.render_app(main_render)
    wizard.run()
```

---

🚨 CRITICAL CHECKLIST

BEFORE RUNNING:

1. ✅ Import framework components
2. ✅ Create PyUIWizard instance with use_diffing=True
3. ✅ Define at least one component function
4. ✅ Create main render function
5. ✅ Register main render with wizard.render_app()
6. ✅ Call wizard.run()

FOR EACH COMPONENT:

1. ✅ Use use_state for local state
2. ✅ Return create_element() tree
3. ✅ Add key prop to EVERY element
4. ✅ Use stable, unique keys (not random!)
5. ✅ Keep render functions pure (no side effects)

FOR LISTS:

1. ✅ Map items to elements with unique key
2. ✅ Never use array index as key (unless static list)
3. ✅ Extract list items to separate component if complex

---

🎯 SUMMARY: 7 STEPS TO ANY UI

Step Code Purpose
1. Import from pyuiwizardv420 import * Get framework tools
2. Initialize wizard = PyUIWizard() Create app window
3. Components def MyComponent(props): Build reusable UI pieces
4. State [value, setValue] = use_state() Manage component data
5. Render return create_element(...) Describe UI structure
6. Compose main_render() Assemble components
7. Run wizard.render_app(); wizard.run() Launch application

---

⚡ ULTIMATE RULE:

"Think React, Write Python" - Every React pattern works here:

· ✅ Functional components with hooks
· ✅ Props down, events up
· ✅ Virtual DOM with diffing
· ✅ Component composition
· ✅ Unidirectional data flow

You now have a complete mental model. Build anything. 🚀