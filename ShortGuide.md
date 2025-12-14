# 🎯 PyUIWizard: The 5 Critical Steps

## **Mental Model: React for Tkinter**

Think of PyUIWizard as **React + Tkinter**. You write declarative component functions, the framework handles the DOM updates.

---

## **Step 1: Initialize** 
```python
wizard = PyUIWizard(title="App", width=800, height=600, use_diffing=True)
```
Creates the runtime. `use_diffing=True` enables efficient updates (always use it).

---

## **Step 2: Write Component Functions**

```python
def MyComponent(props):
    # 1. Get parent's key (CRITICAL for diffing!)
    key = props.get('key')
    
    # 2. useState hooks (TOP LEVEL ONLY, same order every render)
    [state, setState] = useState(initial, key='unique_id')
    
    # 3. Event handlers
    def handle_event():
        setState(new_value)  # Or: setState(lambda prev: prev + 1)
    
    # 4. Return VDOM tree
    return create_element('frame', {'key': key},  # Use parent's key!
        create_element('label', {'text': state, 'key': f'{key}_label'}),
        create_element('button', {'onClick': handle_event, 'key': f'{key}_btn'})
    )
```

**Golden Rules:**
- ✅ Get `key` from props, use it for root element
- ✅ `useState` at top level only (not in loops/conditions/callbacks)
- ✅ Namespace child keys: `f'{parent_key}_child_name'`
- ✅ Event handlers update state via `setState`

---

## **Step 3: Understand `create_element()`**

```python
create_element(type, props, *children)
```

**The Signature:**
- `type`: `'frame'`, `'label'`, `'button'`, `MyComponent`, etc.
- `props`: `{'key': 'id', 'class': 'bg-blue-500', 'onClick': fn, ...}`
- `*children`: More `create_element()` calls

**Critical Props:**
```python
{
    'key': 'unique_id',              # ✅ REQUIRED for diffing
    'class': 'bg-blue-500 p-4',      # Tailwind-style classes
    'text': 'Hello',                 # Widget content
    'onClick': handler,              # Event handler
    'onChange': handler,             # Input handler
}
```

**Think:** `<div key="id" className="bg-blue-500">{children}</div>` but Python.

---

## **Step 4: The Key System (The Secret Sauce)**

Keys tell the differ **"this is the same element across renders"**.

```python
# ❌ WRONG: No keys
create_element(Counter, {'id': 1})  # Differ can't track this!

# ✅ CORRECT: With keys
create_element(Counter, {'key': 'counter1', 'id': 1})
```

**Key Patterns:**

```python
# Parent gives keys to children
def Parent(props):
    return create_element('frame', {'key': 'parent'},
        create_element(Child, {'key': 'child1'}),  # ✅ Unique key
        create_element(Child, {'key': 'child2'})   # ✅ Unique key
    )

# Child uses parent's key for root, namespaces its children
def Child(props):
    key = props.get('key')  # Get from parent
    return create_element('frame', {'key': key},  # Use it
        create_element('label', {'key': f'{key}_label'}),  # Namespace
        create_element('button', {'key': f'{key}_btn'})
    )
```

**Why?** Without keys, the differ thinks `counter1` was deleted and `counter2` was created, destroying all state. With keys, it knows they're the same components moved.

---

## **Step 5: Wire & Run**

```python
# Main render (root of UI tree)
def main_render(state):
    return create_element('frame', {'key': 'root'},
        create_element(MyComponent, {'key': 'comp1'}),
        create_element(MyComponent, {'key': 'comp2'})
    )

# Optional: Global state
global_counter = wizard.create_state('global_counter', 0)

# Register & run
wizard.render_app(main_render)
wizard.run()
```

---

## **🧠 The Data Flow**

```
useState call → Triggers re-render → 
  main_render(state) → 
    Components expand → 
      VDOM tree built → 
        Differ compares old vs new → 
          Patches generated → 
            Only changed widgets update
```

**Result:** Counter button updates? Only that label changes. Optimal.

---

## **⚡ Quick Reference Card**

| Concept | Rule | Example |
|---------|------|---------|
| **Component** | Function returning `create_element()` | `def Btn(props): return create_element('button', ...)` |
| **useState** | Top level, unique keys, same order | `[val, setVal] = useState(0, key='myval')` |
| **Keys** | Every component needs unique key from parent | `create_element(Comp, {'key': 'comp1'})` |
| **Props** | Pass down via props dict | `{'key': 'id', 'text': 'Hi', 'onClick': fn}` |
| **Styling** | Tailwind-style classes | `'class': 'bg-blue-500 p-4 rounded'` |
| **Events** | camelCase handlers | `'onClick'`, `'onChange'`, `'onSubmit'` |

---

## **🚨 Common Mistakes**

```python
# ❌ useState in wrong place
def Component(props):
    if condition:
        [state, setState] = useState(0)  # BREAKS! Must be top level
    
# ✅ CORRECT
def Component(props):
    [state, setState] = useState(0)
    if condition:
        setState(new_value)  # Use it here instead

# ❌ Missing keys
create_element(MyComponent, {'id': 1})  # Differ can't track!

# ✅ CORRECT
create_element(MyComponent, {'key': 'comp1', 'id': 1})

# ❌ Not using parent's key
def Child(props):
    return create_element('frame', {'key': 'hardcoded'})  # BREAKS!

# ✅ CORRECT
def Child(props):
    key = props.get('key')
    return create_element('frame', {'key': key})
```

---

## **💡 Power Pattern: List Rendering**

```python
def TodoList(props):
    [todos, setTodos] = useState([
        {'id': 1, 'text': 'Learn PyUIWizard'},
        {'id': 2, 'text': 'Build app'}
    ], key='todos')
    
    return create_element('frame', {'key': props.get('key')},
        # Unpack list into children
        *[
            create_element(TodoItem, {
                'todo': todo,
                'key': f'todo_{todo["id"]}'  # ✅ Unique key per item
            })
            for todo in todos
        ]
    )
```

**Why `*[...]`?** `create_element()` takes variadic children. The `*` unpacks the list.

---

## **🎯 That's It!**

**The entire framework in one sentence:**

> Write functions that call `create_element()` with unique keys, use `useState` for state at the top level, and the framework efficiently updates only what changed.

**Think React, but Python + Tkinter.** 🚀

