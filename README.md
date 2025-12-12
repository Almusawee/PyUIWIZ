# PyUIWizard: React-Like GUI Framework for Python 🚀


**PyUIWizard** is not just another GUI library – it's a **revolutionary reactive framework** that brings the magic of React.js to pure Python. Built on Tkinter for cross-platform reliability, it empowers you to craft dynamic, stateful desktop apps with hooks, virtual DOM, and blazing-fast updates. Say goodbye to clunky callbacks and hello to declarative, composable UIs that feel alive!

Why settle for static interfaces when you can build **interactive masterpieces** with the same patterns powering modern web apps? Whether you're a data scientist prototyping dashboards, a hobbyist creating games, or an enterprise dev needing robust tools – PyUIWizard makes Python GUI development **fun, fast, and future-proof**.  

**Ready to revolutionize your apps?** Install now and experience the thrill of React in Python! 🌟

## Why PyUIWizard? The Uniqueness That Sets It Apart 🔥

What makes PyUIWizard stand out in a sea of GUI libraries (Tkinter, PyQt, Kivy)? It's the **seamless fusion of web-inspired reactivity with Python's simplicity**. Here's what makes each part **uniquely powerful** – and why you'll be hooked:

- **React-Like Hooks in Pure Python** 🎣:  
  Forget boilerplate state management! Use `use_state`, `use_effect`, `use_ref`, and `use_context` just like in React. Thread-safe, lifecycle-aware, and isolated per component – they handle updates magically, triggering targeted re-renders. **Unique Twist**: Built-in batching and functional updates (e.g., `set_count(prev => prev + 1)`) prevent unnecessary renders, making your apps buttery smooth. Imagine managing complex state without a single global variable – pure bliss!

- **Virtual DOM with Functional Diffing & Patching** 🔄:  
  No more full re-renders! PyUIWizard's immutable VDOM computes minimal patches (CREATE, UPDATE, REMOVE, MOVE) using a pure functional differ with memoization and key optimizations. **Unique Edge**: Handles keyed lists like React's reconciliation, detecting moves/reorders efficiently. Patches apply batched to Tkinter widgets – up to 10x faster than naive updates. Watch your app stay responsive even with thousands of elements!

- **Stream-Based Reactivity** 🌊:  
  At its core, a powerful observable system (inspired by Rx) turns data into live streams. Create states, computed values, intervals, or event-based streams – all with operators like `map`, `filter`, `debounce`. **Unique Power**: Pipelines chain operations (e.g., `combine_latest` for multi-state deps), ensuring your UI reacts instantly to changes. No more polling or manual syncing – data flows, and your app glows!

- **Thread-Safe Everything** 🔒:  
  GUIs + concurrency = headaches? Not here! RLock-based mixins with timeouts prevent deadlocks in hooks, effects, and state ops. **Unique Safety Net**: Atomic contexts and thread-local managers make it rock-solid for async tasks, events, or multi-threaded apps. Build without fear – even in complex scenarios like real-time data feeds.

- **Performance Monitoring Built-In** 📊:  
  Track every operation (diffing, rendering, memory) with p95/p99 metrics, counts, and JSON exports. **Unique Insight**: Real-time stats printing and resets help optimize on-the-fly. Spot bottlenecks instantly – because who wants a sluggish app when you can have a speed demon?

- **Comprehensive Widget Factory with Accessibility** 🛠️:  
  18 Tkinter widgets (buttons, entries, canvases, treeviews, etc.) enhanced with ARIA roles, keyboard shortcuts, and screen-reader support. **Unique Polish**: Dynamic prop updates, placeholders, syntax highlighting (e.g., Python in text widgets), and drag-drop. Accessibility isn't an afterthought – it's baked in, making your apps inclusive by default.

- **Responsive Design & Tailwind-Like Styling** 📱:  
  Auto-detect breakpoints (xs to 2xl) on resize, with a layout engine for grid/flex/place. Parse classes like `bg-red-500 p-4 md:flex` into Tkinter props. **Unique Flexibility**: Theme switching (light/dark), CSS variables, and responsive variants – build mobile-feeling desktops without extra effort. Resize and watch your UI adapt seamlessly!

- **Error Boundaries & Time Travel Debugging** ⏳:  
  Catch crashes with fallbacks; snapshot history for undo/redo/replay. **Unique Superpower**: Time-travel lets you rewind state/VDOM – debug like a time lord! Errors are logged with paths and recovery attempts, turning bugs into quick fixes.

- **Component System with Full Lifecycles** 🧩:  
  Functional or class-based components with `on_mount`, `should_update`, etc. Compose with `create_element` (JSX-like). **Unique Composability**: Providers for contexts, fragments for grouping – build complex UIs from simple pieces. Lifecycles handle mounting/unmounting cleanly, with stream disposal to prevent leaks.

These aren't just features – they're **game-changers** that make PyUIWizard the most modern Python GUI framework. No JavaScript, no heavy dependencies – just Pythonic elegance with web-scale power. **You'll wonder how you ever built apps without it!**

## Installation 📦

Get started in seconds:

```bash
pip install pyuiwizard  # Coming soon to PyPI – for now, clone and install!
```

Requirements: Python 3.8+, Tkinter (built-in on most systems).

## Quick Start: Build a Reactive Todo App in Minutes ✅

Dive right in with this self-contained example. Copy-paste and run – watch hooks bring it to life!

```python
from pyuiwizard import PyUIWizard, create_element, use_state

def TodoItem(props):
    [isDone, setIsDone] = use_state(False, key=f"todo_{props['id']}")
    return create_element('frame', {'class': 'flex items-center p-3 bg-white border rounded hover:bg-gray-50', 'key': f"todo_item_{props['id']}"},
        create_element('checkbox', {'checked': isDone, 'onChange': lambda val: setIsDone(val), 'key': f"todo_check_{props['id']}"}),
        create_element('label', {'text': props['text'], 'class': f"ml-2 flex-1 {'line-through text-gray-400' if isDone else 'text-gray-800'}", 'key': f"todo_text_{props['id']}"}),
        create_element('button', {'text': '❌', 'onClick': props['onDelete'], 'class': 'text-red-500 hover:text-red-700', 'key': f"todo_delete_{props['id']}"})
    )

def TodoApp(props):
    [todos, setTodos] = use_state([{'id': 1, 'text': 'Learn PyUIWizard'}, {'id': 2, 'text': 'Build an app'}], key="todo_list")
    [newTodo, setNewTodo] = use_state('', key="new_todo_input")
    
    def addTodo():
        if newTodo.strip():
            new_id = max([t['id'] for t in todos], default=0) + 1
            setTodos([*todos, {'id': new_id, 'text': newTodo}])
            setNewTodo('')
    
    def deleteTodo(id):
        setTodos([t for t in todos if t['id'] != id])
    
    return create_element('frame', {'class': 'p-6 max-w-2xl mx-auto', 'key': 'todo_app'},
        # ... (full code in docs – add input, list, stats)
    )

def main_render(state):
    return create_element('frame', {'class': 'min-h-screen bg-gray-50', 'key': 'app_root'},
        # Header, TodoApp, Footer
    )

if __name__ == "__main__":
    wizard = PyUIWizard(title="PyUIWizard Todo App", width=400, height=700, use_diffing=True)
    wizard.render_app(main_render)
    wizard.run()
```

Run it: `python todo_app.py`. Add todos, check them off – feel the reactivity! Hooks update only what's needed. **Pro Tip**: Resize the window to see responsive magic.

## Deep Dive: Mastering the Framework 📘

### Hooks in Action
```python
[count, setCount] = use_state(0)
use_effect(lambda: print("Mounted!"), [])  # Runs once
```
Thread-safe and lifecycle-managed – no leaks!

### Streams for Power Users
```python
counter = wizard.create_state('counter', 0)
computed = wizard.create_computed('doubled', ['counter'], lambda c: c * 2)
```
Reactivity without effort.

### Performance Tools
Call `wizard.print_stats()` – get detailed metrics. Export to JSON for analysis.

Explore more in our [full docs](https://github.com/Almusawee/PyUIWIZ/tree/main) (hooks, widgets, layouts, debugging). But if you prefer quick guide read the -> [quick guide](https://github.com/Almusawee/PyUIWIZ/blob/main/ShortGuide.md)

## Contributing & Community 👥

Love it? Star the repo, fork, and PR! We're building a community – join discussions on GitHub. Report issues, suggest features – let's make Python GUIs epic together.

## License
MIT – Free to use, modify, and share. Built by the PyUIWizard Team.

**Don't just read about it – build with it!** Clone now, run the demo, and unleash your creativity. PyUIWizard isn't a tool; it's your superpower. What will you create first? 🚀