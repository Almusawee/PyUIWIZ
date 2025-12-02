
The framework's working mechanism is a high-speed, five-step pipeline that runs every time the application's state changes.
🧙 The PyUIWizard Framework Description
PyUIWizard is a novel, declarative, functional framework designed for Python GUI development. It adopts the architectural principles of modern web frameworks (like React) and functional reactive programming (FRP) to build dynamic, high-performance UIs using traditional imperative toolkits (like Tkinter) as a backend.
It is comprised of three major, highly-decoupled components:
 * Functional Reactive Core: Manages the state and data flow.
 * Declarative VDOM Layer: Defines the UI structure.
 * Imperative Patcher: Executes the minimal updates to the graphical interface.
⚙️ The Framework's Working Mechanism: The 5-Step Pipeline
The application runs in a unidirectional data flow loop. A user action triggers Step 1, which flows sequentially through to Step 5.

Step 1: User Action / Stream Mutation (The Cause)
The process begins when an external event occurs:
 * Trigger: A user clicks a button, a network packet arrives, or a timer expires.
 * Action: The corresponding event handler mutates the state by calling the set() method on a specific reactive stream (e.g., count_stream.set(new_value)).
 * Core Role: The StreamProcessor registers this change.

Step 2: State Combination and Transformation (The Brain)
The Reactive Core takes the mutated state and prepares the complete, consolidated state object for the UI.
 * Mechanism: The combine_latest operator monitors all relevant streams (count_stream, theme_stream, etc.). As soon as any one stream emits a new value, the operator collects the latest value from all streams.
 * Output: A single, comprehensive Python dictionary containing the entire current state of the application ({'count': 10, 'theme': 'dark', 'window_bp': 'lg'}). This dictionary is the input for the next step.

Step 3: VDOM Generation (The Blueprint)
This is the pure, functional part where the UI blueprint is created.
 * Mechanism: The central rendering function (_create_keyed_ui) and its child Functional Components (like CounterDisplay and Controls) are called with the State Dictionary from Step 2.
 * Result: These functions execute and return a new Virtual DOM (VDOM) tree—a nested structure of Python dictionaries that describes the desired look of the entire UI for the current state.
 * Crucial Point: This step involves zero interaction with Tkinter and no manual manipulation of the UI.

Step 4: Functional Diffing (The Optimization)
This is where performance efficiency is achieved. The engine avoids unnecessary work.
 * Mechanism: The Functional Diffing Engine takes two VDOM trees:
   * The Old VDOM (the blueprint from the previous state).
   * The New VDOM (the blueprint from the current state, generated in Step 3).
 * Comparison: It compares the two, widget by widget, key by key, and property by property.
 * Output: It generates a minimal Patch List—a list containing only the imperative commands needed to transform the old UI into the new one (e.g., [{'op': 'UPDATE_PROP', 'path': ['Root', 'CounterLabel'], 'prop': 'text', 'value': 'Count: 11'}]).

Step 5: Real DOM Patching (The Execution)
This is the only part of the pipeline that touches the graphical toolkit.
 * Mechanism: The Tkinter Patcher (FunctionalPatcher) receives the minimal Patch List from Step 4.
 * Action: It iterates through the list, translating each declarative patch instruction into the required imperative Tkinter calls:
   * UPDATE_PROP: Calls widget.config(prop=value)
   * CREATE_WIDGET: Calls tk.Label(parent, **props)
   * REMOVE_WIDGET: Calls widget.destroy()
 * Result: The GUI is updated in the most efficient manner possible, closing the loop and waiting for the next user action.
