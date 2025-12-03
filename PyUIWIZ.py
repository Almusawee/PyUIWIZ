"""
PyUIWizard 4.0.0 - Complete Reactive GUI Framework with useState Hook
A production-ready framework with React-like hooks, functional diffing, and elegant styling

Author: PyUIWizard Team
License: MIT
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable, Any, List, Dict, Optional, Tuple, Union, TypeVar
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import json
import weakref
from functools import wraps
import inspect

__version__ = "4.0.0"
__all__ = [
    'PyUIWizard', 'Stream', 'Component', 'create_element', 'use_state',
    'DESIGN_TOKENS', 'PERFORMANCE', 'ERROR_BOUNDARY', 'TIME_TRAVEL'
]

T = TypeVar('T')

# ===============================
# Thread Safety Utilities
# ===============================
class ThreadSafeMixin:
    """Mixin for thread-safe operations"""
    def __init__(self):
        self._lock = threading.RLock()
    
    def synchronized(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self._lock:
                return func(*args, **kwargs)
        return wrapper

# ===============================
# Performance Monitor
# ===============================
class PerformanceMonitor:
    def __init__(self):
        self.operation_times = defaultdict(list)
        self.operation_counts = defaultdict(int)
        self._lock = threading.Lock()
    
    def measure_time(self, operation_name: str):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                
                duration = (end_time - start_time) * 1000
                with self._lock:
                    self.operation_times[operation_name].append(duration)
                    self.operation_counts[operation_name] += 1
                return result
            return wrapper
        return decorator
    
    def get_stats(self):
        with self._lock:
            stats = {}
            for op_name, times in self.operation_times.items():
                count = self.operation_counts[op_name]
                avg_time = sum(times) / len(times) if times else 0
                min_time = min(times) if times else 0
                max_time = max(times) if times else 0
                
                stats[op_name] = {
                    'count': count,
                    'avg_ms': round(avg_time, 2),
                    'min_ms': round(min_time, 2),
                    'max_ms': round(max_time, 2),
                    'total_ms': round(sum(times), 2)
                }
            return stats
    
    def print_stats(self):
        print("\n" + "="*60)
        print("PERFORMANCE STATISTICS")
        print("="*60)
        stats = self.get_stats()
        for op_name, stat in sorted(stats.items()):
            print(f"\n{op_name}:")
            print(f"  Calls:  {stat['count']}")
            print(f"  Avg:    {stat['avg_ms']:.2f}ms")
            print(f"  Min:    {stat['min_ms']:.2f}ms")
            print(f"  Max:    {stat['max_ms']:.2f}ms")
        print("="*60 + "\n")
    
    def reset(self):
        with self._lock:
            self.operation_times.clear()
            self.operation_counts.clear()

PERFORMANCE = PerformanceMonitor()

# ===============================
# Diff Operation Types
# ===============================
class DiffType(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    REPLACE = "REPLACE"
    REMOVE = "REMOVE"
    REORDER = "REORDER"
    NONE = "NONE"

# ===============================
# Complete Functional Diffing Engine
# ===============================
class FunctionalDiffer:
    """Pure functional diffing using map, filter, zip, get, update"""
    
    def __init__(self):
        self.stats = {
            'diffs': 0,
            'patches': 0,
            'cache_hits': 0,
            'create_ops': 0,
            'update_ops': 0,
            'remove_ops': 0,
            'replace_ops': 0,
            'reorder_ops': 0
        }
        self.patch_cache = {}
    
    @PERFORMANCE.measure_time('functional_diff')
    def diff(self, old_vdom: Optional[Dict], new_vdom: Optional[Dict]) -> List[Dict]:
        """Main diff function - returns list of operations"""
        self.stats['diffs'] += 1
        
        if not new_vdom:
            return [{'type': DiffType.REMOVE, 'path': [], 'old': old_vdom}]
        
        if not old_vdom:
            return [{'type': DiffType.CREATE, 'path': [], 'node': new_vdom}]
        
        patches = self._diff_node(old_vdom, new_vdom, [])
        self.stats['patches'] += len(patches)
        return patches
    
    def _diff_node(self, old: Dict, new: Dict, path: List) -> List[Dict]:
        """Diff a single node using functional composition"""
        patches = []
        
        if old.get('type') != new.get('type'):
            self.stats['replace_ops'] += 1
            return [{'type': DiffType.REPLACE, 'path': path, 'old': old, 'new': new}]
        
        if old.get('key') != new.get('key'):
            self.stats['replace_ops'] += 1
            return [{'type': DiffType.REPLACE, 'path': path, 'old': old, 'new': new}]
        
        props_patch = self._diff_props(
            old.get('props', {}),
            new.get('props', {}),
            path
        )
        
        if props_patch:
            patches.append(props_patch)
            self.stats['update_ops'] += 1
        
        children_patches = self._diff_children(
            old.get('children', []),
            new.get('children', []),
            path
        )
        
        patches.extend(filter(lambda p: p is not None, children_patches))
        
        return patches
    
    def _diff_props(self, old_props: Dict, new_props: Dict, path: List) -> Optional[Dict]:
        """Diff properties using dict methods"""
        changed = {
            key: new_props[key]
            for key in new_props
            if old_props.get(key) != new_props.get(key)
        }
        
        removed = list(filter(
            lambda key: key not in new_props,
            old_props.keys()
        ))
        
        if changed or removed:
            return {
                'type': DiffType.UPDATE,
                'path': path,
                'props': {
                    'changed': changed,
                    'removed': removed
                }
            }
        
        return None
    
    def _diff_children(self, old_children: List, new_children: List, path: List) -> List[Dict]:
        """Diff children using zip, map, filter"""
        has_keys = any(c.get('key') is not None for c in new_children)
        
        if has_keys:
            return self._diff_keyed_children(old_children, new_children, path)
        else:
            return self._diff_indexed_children(old_children, new_children, path)
    
    def _diff_indexed_children(self, old_children: List, new_children: List, path: List) -> List[Dict]:
        """Diff children by index using zip and map"""
        max_len = max(len(old_children), len(new_children))
        
        old_padded = old_children + [None] * (max_len - len(old_children))
        new_padded = new_children + [None] * (max_len - len(new_children))
        
        patches = map(
            lambda indexed: self._diff_child_pair(
                indexed[1][0],
                indexed[1][1],
                path + [indexed[0]]
            ),
            enumerate(zip(old_padded, new_padded))
        )
        
        return list(filter(lambda p: p, self._flatten(patches)))
    
    def _diff_keyed_children(self, old_children: List, new_children: List, path: List) -> List[Dict]:
        """Diff keyed children for optimal list updates"""
        old_by_key = {
            child.get('key'): child
            for child in old_children
            if child.get('key') is not None
        }
        
        new_by_key = {
            child.get('key'): child
            for child in new_children
            if child.get('key') is not None
        }
        
        patches = []
        
        for key, new_child in new_by_key.items():
            old_child = old_by_key.get(key)
            
            if old_child:
                child_patches = self._diff_node(old_child, new_child, path + [key])
                patches.extend(child_patches)
            else:
                patches.append({
                    'type': DiffType.CREATE,
                    'path': path + [key],
                    'node': new_child
                })
                self.stats['create_ops'] += 1
        
        removed_keys = filter(
            lambda key: key not in new_by_key,
            old_by_key.keys()
        )
        
        remove_patches = map(
            lambda key: {
                'type': DiffType.REMOVE,
                'path': path + [key],
                'old': old_by_key[key]
            },
            removed_keys
        )
        
        patches.extend(remove_patches)
        self.stats['remove_ops'] += len(list(removed_keys))
        
        if self._children_reordered(old_children, new_children):
            patches.append({
                'type': DiffType.REORDER,
                'path': path,
                'old_order': [c.get('key') for c in old_children],
                'new_order': [c.get('key') for c in new_children]
            })
            self.stats['reorder_ops'] += 1
        
        return patches
    
    def _diff_child_pair(self, old_child: Optional[Dict], new_child: Optional[Dict], path: List) -> List[Dict]:
        """Helper to diff a single child pair"""
        if old_child is None and new_child is None:
            return []
        elif old_child is None:
            self.stats['create_ops'] += 1
            return [{'type': DiffType.CREATE, 'path': path, 'node': new_child}]
        elif new_child is None:
            self.stats['remove_ops'] += 1
            return [{'type': DiffType.REMOVE, 'path': path, 'old': old_child}]
        else:
            return self._diff_node(old_child, new_child, path)
    
    def _children_reordered(self, old_children: List, new_children: List) -> bool:
        """Check if keyed children were reordered"""
        old_keys = [c.get('key') for c in old_children if c.get('key')]
        new_keys = [c.get('key') for c in new_children if c.get('key')]
        
        if len(old_keys) != len(new_keys):
            return False
        
        return not all(map(lambda pair: pair[0] == pair[1], zip(old_keys, new_keys)))
    
    def _flatten(self, nested_list):
        """Flatten nested list"""
        result = []
        for item in nested_list:
            if isinstance(item, list):
                result.extend(self._flatten(item))
            else:
                result.append(item)
        return result
    
    def get_stats(self):
        return self.stats.copy()
    
    def reset_stats(self):
        for key in self.stats:
            self.stats[key] = 0

# ===============================
# useState Hook Implementation (Pythonic Fiber Context)
# ===============================

# Global state management (Pythonic fiber context)
_component_state_manager = {}  # Maps (path_tuple, state_id) -> Stream
_current_component_path = []   # Current VDOM path during rendering
_current_component_key = None  # Current component key
_hook_index = 0                # Tracks hook call order within component
_component_render_stack = []   # Stack for nested component rendering


def use_state(initial_value, key=None):
    """
    React-like useState hook for component-level state management.
    
    Args:
        initial_value: Initial value for the state
        key: Optional unique key for the state (defaults to auto-generated)
    
    Returns:
        tuple: [current_value, setter_function]
    
    Raises:
        RuntimeError: If called outside of a component rendering context.
    """
    global _hook_index, _component_state_manager, _current_component_path
    
    # === Context Validation ===
    if not _current_component_path:
        raise RuntimeError(
            "useState must be called within a component's render function. "
            "No component context found (is this called outside of render?)."
        )
    
    # === Streamlined Identity System ===
    # 1. Positional Identity (primary): Where in the VDOM tree?
    path_tuple = tuple(_current_component_path)
    
    # 2. Call Order Identity (secondary): Which hook call within component?
    if key:
        state_id = key  # User-provided explicit key
    else:
        state_id = f"hook_{_hook_index}"  # Auto-generated based on call order
    
    # Combined unique identifier
    full_state_id = (path_tuple, state_id)
    
    # === State Initialization (if needed) ===
    if full_state_id not in _component_state_manager:
        # Create new Stream for this state slot
        stream = Stream(
            initial_value, 
            name=f"useState({state_id}) at {path_tuple}"
        )
        _component_state_manager[full_state_id] = stream
    
    # === Get Existing State ===
    stream = _component_state_manager[full_state_id]
    
    # === Direct Stream Value Access ===
    # Get current value directly from stream (ensures synchronization)
    current_value = stream.value
    
    # === Setter Function ===
    def set_state(new_value):
        """Update state and trigger reactive re-render"""
        stream.set(new_value)
    
    # === Prepare for Next Hook Call ===
    _hook_index += 1
    
    return [current_value, set_state]


def _with_hook_rendering(component_class_or_func, props, path):
    """
    Wrapper to manage hook context during component rendering.
    
    This function establishes the component context for hooks to work.
    """
    global _hook_index, _current_component_path, _current_component_key, _component_render_stack
    
    # === Save Previous Context ===
    prev_path = _current_component_path.copy()
    prev_key = _current_component_key
    prev_hook_index = _hook_index
    
    # Push current component to stack for debugging/tracing
    _component_render_stack.append({
        'path': path,
        'key': props.get('key'),
        'type': component_class_or_func.__name__ if hasattr(component_class_or_func, '__name__') else str(component_class_or_func)
    })
    
    try:
        # === Establish New Context ===
        _current_component_path = path
        _current_component_key = props.get('key')
        _hook_index = 0  # Reset hook counter for this component
        
        # === Render Component ===
        if isinstance(component_class_or_func, type):
            # Class component: instantiate and call render()
            component = component_class_or_func(props)
            result = component.render()
        else:
            # Function component: call directly
            result = component_class_or_func(props)
        
        return result
        
    finally:
        # === Restore Previous Context ===
        _current_component_path = prev_path
        _current_component_key = prev_key
        _hook_index = prev_hook_index
        _component_render_stack.pop()


def clear_component_state(component_path=None, state_key=None):
    """
    Clear component state (useful for testing and hot reloading).
    
    Args:
        component_path: Clear all state for this component path
        state_key: Clear specific state key (if provided)
    """
    global _component_state_manager
    
    if component_path is None and state_key is None:
        # Clear everything
        for stream in _component_state_manager.values():
            if hasattr(stream, 'dispose'):
                stream.dispose()
        _component_state_manager.clear()
    elif component_path is not None:
        # Clear specific component's state
        path_tuple = tuple(component_path)
        keys_to_remove = [
            key for key in _component_state_manager.keys() 
            if key[0] == path_tuple and (state_key is None or key[1] == state_key)
        ]
        for key in keys_to_remove:
            stream = _component_state_manager[key]
            if hasattr(stream, 'dispose'):
                stream.dispose()
            del _component_state_manager[key]


def get_hook_debug_info():
    """Get debugging information about current hook state"""
    return {
        'current_path': _current_component_path,
        'current_key': _current_component_key,
        'hook_index': _hook_index,
        'render_stack': _component_render_stack.copy(),
        'state_count': len(_component_state_manager)
    }

# ===============================
# Complete Widget Factory
# ===============================
class WidgetFactory:
    """Factory for creating all Tkinter widgets with full prop support"""
    
    @staticmethod
    def create_widget(node_type: str, parent, props: Dict) -> Optional[tk.Widget]:
        """Create widget based on type with complete prop handling"""
        creators = {
            'frame': WidgetFactory._create_frame,
            'label': WidgetFactory._create_label,
            'button': WidgetFactory._create_button,
            'entry': WidgetFactory._create_entry,
            'text': WidgetFactory._create_text,
            'canvas': WidgetFactory._create_canvas,
            'listbox': WidgetFactory._create_listbox,
            'checkbox': WidgetFactory._create_checkbox,
            'radio': WidgetFactory._create_radio,
            'scale': WidgetFactory._create_scale,
            'scrollbar': WidgetFactory._create_scrollbar,
            'combobox': WidgetFactory._create_combobox,
            'progressbar': WidgetFactory._create_progressbar,
            'separator': WidgetFactory._create_separator,
        }
        
        creator = creators.get(node_type, WidgetFactory._create_frame)
        return creator(parent, props)
    
    @staticmethod
    def _create_frame(parent, props):
        bg = props.get('bg', 'white')
        frame = tk.Frame(
            parent,
            bg=bg,
            relief=props.get('relief', 'flat'),
            bd=props.get('border_width', 0)
        )
        
        if props.get('width'):
            frame.config(width=props['width'])
        if props.get('height'):
            frame.config(height=props['height'])
        
        return frame
    
    @staticmethod
    def _create_label(parent, props):
        font_size = props.get('font_size', 12)
        font_weight = props.get('font_weight', 'normal')
        font_family = props.get('font_family', 'Arial')
        font = (font_family, font_size, font_weight)
        
        bg = props.get('bg', parent['bg'] if isinstance(parent, tk.Frame) else 'white')
        
        label = tk.Label(
            parent,
            text=props.get('text', ''),
            fg=props.get('fg', 'black'),
            bg=bg,
            font=font,
            justify=props.get('justify', 'left'),
            anchor=props.get('anchor', 'w')
        )
        
        if props.get('width'):
            label.config(width=props['width'])
        if props.get('height'):
            label.config(height=props['height'])
        
        return label
    
    @staticmethod
    def _create_button(parent, props):
        font_size = props.get('font_size', 10)
        font_family = props.get('font_family', 'Arial')
        font = (font_family, font_size)
        
        button = tk.Button(
            parent,
            text=props.get('text', ''),
            fg=props.get('fg', 'white'),
            bg=props.get('bg', 'gray'),
            activebackground=props.get('active_bg', props.get('bg', 'gray')),
            activeforeground=props.get('active_fg', props.get('fg', 'white')),
            command=props.get('onClick'),
            font=font,
            relief=props.get('relief', 'flat'),
            cursor=props.get('cursor', 'hand2'),
            state=props.get('state', 'normal')
        )
        
        if props.get('width'):
            button.config(width=props['width'])
        if props.get('height'):
            button.config(height=props['height'])
        
        return button
    
    @staticmethod
    def _create_entry(parent, props):
        entry = tk.Entry(
            parent,
            bg=props.get('bg', 'white'),
            fg=props.get('fg', 'black'),
            font=(props.get('font_family', 'Arial'), props.get('font_size', 12)),
            relief=props.get('relief', 'sunken'),
            state=props.get('state', 'normal'),
            show=props.get('show', '')  # For password fields
        )
        
        if 'text' in props:
            entry.insert(0, props['text'])
        
        if 'onChange' in props:
            entry.bind('<KeyRelease>', lambda e: props['onChange'](entry.get()))
        
        if 'onSubmit' in props:
            entry.bind('<Return>', lambda e: props['onSubmit'](entry.get()))
        
        if props.get('width'):
            entry.config(width=props['width'])
        
        return entry
    
    @staticmethod
    def _create_text(parent, props):
        text_widget = scrolledtext.ScrolledText(
            parent,
            bg=props.get('bg', 'white'),
            fg=props.get('fg', 'black'),
            font=(props.get('font_family', 'Arial'), props.get('font_size', 10)),
            wrap=props.get('wrap', 'word'),
            state=props.get('state', 'normal')
        )
        
        if 'text' in props:
            text_widget.insert('1.0', props['text'])
        
        if 'onChange' in props:
            def on_change(event):
                props['onChange'](text_widget.get('1.0', 'end-1c'))
            text_widget.bind('<KeyRelease>', on_change)
        
        if props.get('width'):
            text_widget.config(width=props['width'])
        if props.get('height'):
            text_widget.config(height=props['height'])
        
        return text_widget
    
    @staticmethod
    def _create_canvas(parent, props):
        canvas = tk.Canvas(
            parent,
            bg=props.get('bg', 'white'),
            width=props.get('width', 300),
            height=props.get('height', 200),
            relief=props.get('relief', 'flat'),
            bd=props.get('border_width', 0)
        )
        
        if 'onDraw' in props:
            props['onDraw'](canvas)
        
        return canvas
    
    @staticmethod
    def _create_listbox(parent, props):
        listbox = tk.Listbox(
            parent,
            bg=props.get('bg', 'white'),
            fg=props.get('fg', 'black'),
            font=(props.get('font_family', 'Arial'), props.get('font_size', 10)),
            selectmode=props.get('selectmode', 'single'),
            relief=props.get('relief', 'sunken')
        )
        
        if 'items' in props:
            for item in props['items']:
                listbox.insert('end', item)
        
        if 'onSelect' in props:
            def on_select(event):
                if listbox.curselection():
                    props['onSelect'](listbox.get(listbox.curselection()[0]))
            listbox.bind('<<ListboxSelect>>', on_select)
        
        if props.get('width'):
            listbox.config(width=props['width'])
        if props.get('height'):
            listbox.config(height=props['height'])
        
        return listbox
    
    @staticmethod
    def _create_checkbox(parent, props):
        var = tk.BooleanVar(value=props.get('checked', False))
        
        checkbox = tk.Checkbutton(
            parent,
            text=props.get('text', ''),
            variable=var,
            bg=props.get('bg', parent['bg'] if isinstance(parent, tk.Frame) else 'white'),
            fg=props.get('fg', 'black'),
            font=(props.get('font_family', 'Arial'), props.get('font_size', 10)),
            command=lambda: props.get('onChange', lambda x: None)(var.get())
        )
        
        # Store variable reference to prevent garbage collection
        checkbox._py_var = var
        
        return checkbox
    
    @staticmethod
    def _create_radio(parent, props):
        var = tk.StringVar(value=props.get('value', ''))
        
        radio = tk.Radiobutton(
            parent,
            text=props.get('text', ''),
            variable=var,
            value=props.get('option_value', ''),
            bg=props.get('bg', parent['bg'] if isinstance(parent, tk.Frame) else 'white'),
            fg=props.get('fg', 'black'),
            font=(props.get('font_family', 'Arial'), props.get('font_size', 10)),
            command=lambda: props.get('onChange', lambda x: None)(var.get())
        )
        
        radio._py_var = var
        
        return radio
    
    @staticmethod
    def _create_scale(parent, props):
        scale = tk.Scale(
            parent,
            from_=props.get('min', 0),
            to=props.get('max', 100),
            orient=props.get('orient', 'horizontal'),
            bg=props.get('bg', parent['bg'] if isinstance(parent, tk.Frame) else 'white'),
            fg=props.get('fg', 'black'),
            command=lambda val: props.get('onChange', lambda x: None)(float(val))
        )
        
        if 'value' in props:
            scale.set(props['value'])
        
        if props.get('width'):
            scale.config(length=props['width'])
        
        return scale
    
    @staticmethod
    def _create_scrollbar(parent, props):
        scrollbar = tk.Scrollbar(
            parent,
            orient=props.get('orient', 'vertical'),
            command=props.get('command')
        )
        
        return scrollbar
    
    @staticmethod
    def _create_combobox(parent, props):
        combobox = ttk.Combobox(
            parent,
            values=props.get('values', []),
            state=props.get('state', 'readonly')
        )
        
        if 'value' in props:
            combobox.set(props['value'])
        
        if 'onChange' in props:
            combobox.bind('<<ComboboxSelected>>', 
                         lambda e: props['onChange'](combobox.get()))
        
        if props.get('width'):
            combobox.config(width=props['width'])
        
        return combobox
    
    @staticmethod
    def _create_progressbar(parent, props):
        progressbar = ttk.Progressbar(
            parent,
            orient=props.get('orient', 'horizontal'),
            mode=props.get('mode', 'determinate'),
            maximum=props.get('max', 100),
            value=props.get('value', 0)
        )
        
        if props.get('width'):
            progressbar.config(length=props['width'])
        
        return progressbar
    
    @staticmethod
    def _create_separator(parent, props):
        separator = ttk.Separator(
            parent,
            orient=props.get('orient', 'horizontal')
        )
        
        return separator
    
    @staticmethod
    def update_widget_prop(widget, prop: str, value):
        """Update a widget property with comprehensive support"""
        widget_type = widget.__class__.__name__
        
        # Common properties for all widgets
        common_props = {
            'bg': lambda w, v: w.config(bg=v) if hasattr(w, 'config') else None,
            'fg': lambda w, v: w.config(fg=v) if hasattr(w, 'config') else None,
            'width': lambda w, v: w.config(width=v) if hasattr(w, 'config') else None,
            'height': lambda w, v: w.config(height=v) if hasattr(w, 'config') else None,
            'relief': lambda w, v: w.config(relief=v) if hasattr(w, 'config') else None,
            'state': lambda w, v: w.config(state=v) if hasattr(w, 'config') else None,
        }
        
        # Text-based widget properties
        text_props = {
            'text': lambda w, v: w.config(text=v),
            'font_size': lambda w, v: WidgetFactory._update_font_size(w, v),
            'font_weight': lambda w, v: WidgetFactory._update_font_weight(w, v),
            'font_family': lambda w, v: WidgetFactory._update_font_family(w, v),
        }
        
        # Button-specific
        button_props = {
            'onClick': lambda w, v: w.config(command=v),
            'active_bg': lambda w, v: w.config(activebackground=v),
            'active_fg': lambda w, v: w.config(activeforeground=v),
        }
        
        # Entry-specific
        entry_props = {
            'show': lambda w, v: w.config(show=v),
        }
        
        # Try common props first
        if prop in common_props:
            try:
                common_props[prop](widget, value)
                return
            except:
                pass
        
        # Try text props
        if widget_type in ['Label', 'Button', 'Entry', 'Text'] and prop in text_props:
            try:
                text_props[prop](widget, value)
                return
            except:
                pass
        
        # Try button props
        if widget_type == 'Button' and prop in button_props:
            try:
                button_props[prop](widget, value)
                return
            except:
                pass
        
        # Try entry props
        if widget_type == 'Entry' and prop in entry_props:
            try:
                entry_props[prop](widget, value)
                return
            except:
                pass
        
        # Handle border_width specially
        if prop == 'border_width':
            try:
                if value > 0:
                    widget.config(relief='solid', bd=value)
                else:
                    widget.config(relief='flat', bd=0)
            except:
                pass
    
    @staticmethod
    def _update_font_size(widget, size):
        current_font = widget.cget('font')
        if isinstance(current_font, tuple):
            widget.config(font=(current_font[0], size, current_font[2] if len(current_font) > 2 else 'normal'))
        else:
            widget.config(font=('Arial', size, 'normal'))
    
    @staticmethod
    def _update_font_weight(widget, weight):
        current_font = widget.cget('font')
        if isinstance(current_font, tuple):
            widget.config(font=(current_font[0], current_font[1] if len(current_font) > 1 else 12, weight))
        else:
            widget.config(font=('Arial', 12, weight))
    
    @staticmethod
    def _update_font_family(widget, family):
        current_font = widget.cget('font')
        if isinstance(current_font, tuple):
            widget.config(font=(family, current_font[1] if len(current_font) > 1 else 12, 
                              current_font[2] if len(current_font) > 2 else 'normal'))
        else:
            widget.config(font=(family, 12, 'normal'))

# ===============================
# Complete Layout Manager
# ===============================
class LayoutManager:
    """Handle all layout managers: pack, grid, place"""
    
    @staticmethod
    def apply_layout(widget, node: Dict, parent, position):
        """Apply layout with support for pack, grid, and place"""
        props = node.get('props', {})
        layout_type = props.get('layout_manager', 'pack')
        
        if layout_type == 'grid':
            LayoutManager._apply_grid(widget, props, position)
        elif layout_type == 'place':
            LayoutManager._apply_place(widget, props)
        else:
            LayoutManager._apply_pack(widget, props, position)
    
    @staticmethod
    def _apply_pack(widget, props, position):
        """Apply pack layout"""
        pack_opts = {
            'side': props.get('side', 'top'),
            'padx': props.get('padx', 0),
            'pady': props.get('pady', 0),
            'fill': props.get('fill', 'none'),
            'expand': props.get('expand', False),
            'anchor': props.get('anchor', 'center')
        }
        
        if props.get('width_full'):
            pack_opts['fill'] = 'x'
        if props.get('height_full'):
            pack_opts['fill'] = 'y'
        if props.get('fill_both'):
            pack_opts['fill'] = 'both'
            pack_opts['expand'] = True
        
        widget.pack(**pack_opts)
    
    @staticmethod
    def _apply_grid(widget, props, position):
        """Apply grid layout"""
        grid_opts = {
            'row': props.get('row', position),
            'column': props.get('column', 0),
            'rowspan': props.get('rowspan', 1),
            'columnspan': props.get('columnspan', 1),
            'padx': props.get('padx', 0),
            'pady': props.get('pady', 0),
            'sticky': props.get('sticky', '')
        }
        
        widget.grid(**grid_opts)
    
    @staticmethod
    def _apply_place(widget, props):
        """Apply place layout (absolute positioning)"""
        place_opts = {}
        
        if 'x' in props:
            place_opts['x'] = props['x']
        if 'y' in props:
            place_opts['y'] = props['y']
        if 'relx' in props:
            place_opts['relx'] = props['relx']
        if 'rely' in props:
            place_opts['rely'] = props['rely']
        if 'anchor' in props:
            place_opts['anchor'] = props['anchor']
        
        widget.place(**place_opts)

# ===============================
# Complete Event System
# ===============================
class EventSystem:
    """Comprehensive event handling system"""
    
    # Event type mapping
    EVENT_MAP = {
        'onClick': '<Button-1>',
        'onDoubleClick': '<Double-Button-1>',
        'onRightClick': '<Button-3>',
        'onMouseEnter': '<Enter>',
        'onMouseLeave': '<Leave>',
        'onMouseMove': '<Motion>',
        'onFocus': '<FocusIn>',
        'onBlur': '<FocusOut>',
        'onKeyPress': '<KeyPress>',
        'onKeyRelease': '<KeyRelease>',
        'onChange': '<KeyRelease>',
        'onSubmit': '<Return>',
    }
    
    @staticmethod
    def bind_events(widget, props: Dict):
        """Bind all events from props to widget"""
        for prop_name, tk_event in EventSystem.EVENT_MAP.items():
            if prop_name in props:
                handler = props[prop_name]
                
                # Special handling for different event types
                if prop_name == 'onClick' and hasattr(widget, 'config'):
                    # Buttons use command instead of binding
                    if isinstance(widget, tk.Button):
                        widget.config(command=handler)
                    else:
                        widget.bind(tk_event, lambda e, h=handler: h(e))
                
                elif prop_name == 'onChange':
                    if isinstance(widget, (tk.Entry, scrolledtext.ScrolledText)):
                        widget.bind(tk_event, lambda e, h=handler: h(widget.get() if isinstance(widget, tk.Entry) else widget.get('1.0', 'end-1c')))
                
                elif prop_name == 'onSubmit':
                    if isinstance(widget, tk.Entry):
                        widget.bind(tk_event, lambda e, h=handler: h(widget.get()))
                
                else:
                    # Standard event binding
                    widget.bind(tk_event, lambda e, h=handler: h(e))
    
    @staticmethod
    def unbind_events(widget, props: Dict):
        """Unbind events from widget"""
        for prop_name, tk_event in EventSystem.EVENT_MAP.items():
            if prop_name in props:
                try:
                    widget.unbind(tk_event)
                except:
                    pass

# ===============================
# Complete VDOM Tree Tracker
# ===============================
class VDOMTreeTracker:
    """Track the complete VDOM tree structure for accurate patching"""
    
    def __init__(self):
        self.tree = None
        self.node_map = {}  # path -> node
        self.key_map = {}   # key -> node
        self._lock = threading.RLock()
    
    def update(self, vdom: Dict):
        """Update the tracked VDOM tree"""
        with self._lock:
            self.tree = vdom
            self.node_map.clear()
            self.key_map.clear()
            self._index_tree(vdom, [])
    
    def _index_tree(self, node: Dict, path: List):
        """Recursively index the tree"""
        path_key = tuple(path)
        self.node_map[path_key] = node
        
        if 'key' in node:
            self.key_map[node['key']] = node
        
        for i, child in enumerate(node.get('children', [])):
            child_path = path + [child.get('key', i)]
            self._index_tree(child, child_path)
    
    def get_node(self, path: List) -> Optional[Dict]:
        """Get node by path"""
        with self._lock:
            return self.node_map.get(tuple(path))
    
    def get_node_by_key(self, key: str) -> Optional[Dict]:
        """Get node by key"""
        with self._lock:
            return self.key_map.get(key)
    
    def get_parent(self, path: List) -> Optional[Dict]:
        """Get parent node"""
        if len(path) <= 1:
            return None
        parent_path = path[:-1]
        return self.get_node(parent_path)

# ===============================
# Complete Functional Patcher
# ===============================
class FunctionalPatcher:
    """Apply patches using functional composition with complete VDOM tracking"""
    
    def __init__(self):
        self.widget_map = {}
        self.key_map = {}
        self.widget_to_path = {}
        self.widget_to_key = {}
        self.parent_map = {}
        self.vdom_tracker = VDOMTreeTracker()
        self._lock = threading.RLock()
    
    @PERFORMANCE.measure_time('apply_patches')
    def apply_patches(self, patches: List[Dict], vdom: Dict, root_widget):
        """Apply patches using map and filter with complete tracking"""
        with self._lock:
            # Update VDOM tree tracking
            self.vdom_tracker.update(vdom)
            
            # Group patches by type
            grouped = defaultdict(list)
            for patch in patches:
                grouped[patch['type']].append(patch)
            
            # Apply in optimal order
            self._apply_operations(grouped.get(DiffType.REMOVE, []), root_widget, 'remove')
            self._apply_operations(grouped.get(DiffType.REORDER, []), root_widget, 'reorder')
            self._apply_operations(grouped.get(DiffType.CREATE, []), root_widget, 'create')
            self._apply_operations(grouped.get(DiffType.UPDATE, []), root_widget, 'update')
            self._apply_operations(grouped.get(DiffType.REPLACE, []), root_widget, 'replace')
    
    def _apply_operations(self, patches: List[Dict], root_widget, op_type: str):
        """Apply a batch of operations of the same type"""
        for patch in patches:
            if op_type == 'remove':
                self._apply_remove(patch, root_widget)
            elif op_type == 'create':
                self._apply_create(patch, root_widget)
            elif op_type == 'update':
                self._apply_update(patch, root_widget)
            elif op_type == 'replace':
                self._apply_replace(patch, root_widget)
            elif op_type == 'reorder':
                self._apply_reorder(patch, root_widget)
    
    def _apply_remove(self, patch: Dict, root_widget):
        """Apply REMOVE patch with recursive cleanup"""
        path = patch['path']
        widget = self._get_widget_by_path(path, root_widget)
        
        if widget:
            # Recursively clean up all children
            self._recursive_cleanup(widget)
            # Destroy widget
            widget.destroy()
            # Clean up this widget's mappings
            self._cleanup_widget_mappings(widget, path)
    
    def _recursive_cleanup(self, widget):
        """Recursively clean up all child widgets"""
        if hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                self._recursive_cleanup(child)
                # Clean up child's mappings
                if child in self.widget_to_path:
                    path = self.widget_to_path[child]
                    self._cleanup_widget_mappings(child, list(path))
    
    def _apply_create(self, patch: Dict, root_widget):
        """Apply CREATE patch"""
        path = patch['path']
        node = patch['node']
        
        # Find parent widget
        parent_path = path[:-1] if len(path) > 1 else []
        parent = self._get_widget_by_path(parent_path, root_widget)
        
        if parent is None:
            parent = root_widget
        
        # Create widget tree
        widget = self._create_widget_tree(node, parent, path)
        
        # Apply layout
        position = path[-1] if path else 0
        LayoutManager.apply_layout(widget, node, parent, position)
    
    def _create_widget_tree(self, node: Dict, parent, path: List):
        """Create widget and all its children"""
        # Create the widget
        widget = WidgetFactory.create_widget(
            node.get('type', 'frame'),
            parent,
            node.get('props', {})
        )
        
        if not widget:
            return None
        
        # Store mappings
        path_key = tuple(path)
        self.widget_map[path_key] = widget
        self.widget_to_path[widget] = path_key
        self.parent_map[widget] = parent
        
        if 'key' in node:
            self.key_map[node['key']] = widget
            self.widget_to_key[widget] = node['key']
        
        # Bind events
        EventSystem.bind_events(widget, node.get('props', {}))
        
        # Create children
        for i, child in enumerate(node.get('children', [])):
            child_path = path + [child.get('key', i)]
            self._create_widget_tree(child, widget, child_path)
        
        return widget
    
    def _apply_update(self, patch: Dict, root_widget):
        """Apply UPDATE patch"""
        path = patch['path']
        props = patch['props']
        
        widget = self._get_widget_by_path(path, root_widget)
        if not widget:
            return
        
        # Get the current node to check for event changes
        node = self.vdom_tracker.get_node(path)
        old_props = node.get('props', {}) if node else {}
        
        # Unbind old events that changed
        events_to_unbind = {}
        for prop in props.get('removed', []):
            if prop in EventSystem.EVENT_MAP:
                events_to_unbind[prop] = old_props.get(prop)
        
        EventSystem.unbind_events(widget, events_to_unbind)
        
        # Apply property changes
        for key, value in props.get('changed', {}).items():
            if key in EventSystem.EVENT_MAP:
                # Rebind event
                EventSystem.bind_events(widget, {key: value})
            else:
                # Update regular property
                WidgetFactory.update_widget_prop(widget, key, value)
        
        # Handle removed props
        for key in props.get('removed', []):
            if key not in EventSystem.EVENT_MAP:
                self._reset_widget_prop(widget, key)
    
    def _apply_replace(self, patch: Dict, root_widget):
        """Apply REPLACE patch"""
        path = patch['path']
        new_node = patch['new']
        
        widget = self._get_widget_by_path(path, root_widget)
        if not widget:
            return
        
        # Store parent and position info
        parent = self.parent_map.get(widget)
        if not parent:
            parent_path = path[:-1] if len(path) > 1 else []
            parent = self._get_widget_by_path(parent_path, root_widget) or root_widget
        
        # Destroy old widget and children
        self._recursive_cleanup(widget)
        widget.destroy()
        self._cleanup_widget_mappings(widget, path)
        
        # Create new widget tree
        new_widget = self._create_widget_tree(new_node, parent, path)
        
        # Apply layout
        position = path[-1] if path else 0
        LayoutManager.apply_layout(new_widget, new_node, parent, position)
    
    def _apply_reorder(self, patch: Dict, root_widget):
        """Apply REORDER patch"""
        path = patch['path']
        new_order = patch['new_order']
        
        parent_widget = self._get_widget_by_path(path, root_widget)
        if not parent_widget or not hasattr(parent_widget, 'winfo_children'):
            return
        
        children = parent_widget.winfo_children()
        
        if children and new_order:
            # Remove all children from parent
            for child in children:
                child.pack_forget()
            
            # Re-add in new order
            for key in new_order:
                widget = self.key_map.get(key)
                if widget and widget.master == parent_widget:
                    widget.pack(side='top', fill='x', padx=5, pady=2)
    
    def _get_widget_by_path(self, path: List, root_widget):
        """Get widget by path"""
        if not path:
            return root_widget
        return self.widget_map.get(tuple(path))
    
    def _cleanup_widget_mappings(self, widget, path):
        """Clean up mappings for a widget"""
        path_key = tuple(path)
        
        if path_key in self.widget_map:
            del self.widget_map[path_key]
        
        if widget in self.widget_to_key:
            key = self.widget_to_key[widget]
            if key in self.key_map:
                del self.key_map[key]
            del self.widget_to_key[widget]
        
        if widget in self.widget_to_path:
            del self.widget_to_path[widget]
        
        if widget in self.parent_map:
            del self.parent_map[widget]
    
    def _reset_widget_prop(self, widget, prop: str):
        """Reset a widget property to default"""
        defaults = {
            'fg': 'black',
            'bg': 'white',
            'text': '',
            'relief': 'flat',
            'bd': 0,
            'state': 'normal'
        }
        
        if prop in defaults:
            try:
                WidgetFactory.update_widget_prop(widget, prop, defaults[prop])
            except:
                pass

# ===============================
# Design Tokens & Theme System
# ===============================
class DesignTokens:
    """Complete Tailwind-inspired design token system"""
    
    def __init__(self):
        self.tokens = {
            'colors': {
                'slate': {50: '#f8fafc', 100: '#f1f5f9', 200: '#e2e8f0', 300: '#cbd5e1', 400: '#94a3b8', 500: '#64748b', 600: '#475569', 700: '#334155', 800: '#1e293b', 900: '#0f172a'},
                'gray': {50: '#f9fafb', 100: '#f3f4f6', 200: '#e5e7eb', 300: '#d1d5db', 400: '#9ca3af', 500: '#6b7280', 600: '#4b5563', 700: '#374151', 800: '#1f2937', 900: '#111827'},
                'blue': {50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 300: '#93c5fd', 400: '#60a5fa', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8', 800: '#1e40af', 900: '#1e3a8a'},
                'red': {50: '#fef2f2', 100: '#fee2e2', 200: '#fecaca', 300: '#fca5a5', 400: '#f87171', 500: '#ef4444', 600: '#dc2626', 700: '#b91c1c', 800: '#991b1b', 900: '#7f1d1d'},
                'green': {50: '#f0fdf4', 100: '#dcfce7', 200: '#bbf7d0', 300: '#86efac', 400: '#4ade80', 500: '#22c55e', 600: '#16a34a', 700: '#15803d', 800: '#166534', 900: '#14532d'},
                'yellow': {50: '#fefce8', 100: '#fef9c3', 200: '#fef08a', 300: '#fde047', 400: '#facc15', 500: '#eab308', 600: '#ca8a04', 700: '#a16207', 800: '#854d0e', 900: '#713f12'},
                'purple': {50: '#faf5ff', 100: '#f3e8ff', 200: '#e9d5ff', 300: '#d8b4fe', 400: '#c084fc', 500: '#a855f7', 600: '#9333ea', 700: '#7e22ce', 800: '#6b21a8', 900: '#581c87'},
                'pink': {50: '#fdf2f8', 100: '#fce7f3', 200: '#fbcfe8', 300: '#f9a8d4', 400: '#f472b6', 500: '#ec4899', 600: '#db2777', 700: '#be185d', 800: '#9d174d', 900: '#831843'},
                'orange': {50: '#fff7ed', 100: '#ffedd5', 200: '#fed7aa', 300: '#fdba74', 400: '#fb923c', 500: '#f97316', 600: '#ea580c', 700: '#c2410c', 800: '#9a3412', 900: '#7c2d12'},
            },
            'spacing': {
                '0': 0, '1': 4, '2': 8, '3': 12, '4': 16, '5': 20, '6': 24, '8': 32,
                '10': 40, '12': 48, '16': 64, '20': 80, '24': 96, '32': 128, '40': 160, '48': 192
            },
            'font_size': {
                'xs': 10, 'sm': 12, 'base': 14, 'lg': 16, 'xl': 18, '2xl': 20, '3xl': 24, '4xl': 28, '5xl': 32
            },
            'font_weight': {
                'normal': 'normal', 'medium': 'normal', 'semibold': 'bold', 'bold': 'bold'
            },
            'border_radius': {
                'none': 0, 'sm': 2, 'default': 4, 'md': 6, 'lg': 8, 'xl': 12, '2xl': 16, 'full': 9999
            },
            'opacity': {
                '0': 0, '25': 0.25, '50': 0.5, '75': 0.75, '100': 1.0
            },
            'breakpoints': {
                'sm': 640, 'md': 768, 'lg': 1024, 'xl': 1280, '2xl': 1536
            }
        }
        self.current_theme = 'light'
        self.dark_mode = False
        
    def get_color(self, color_name, shade=500):
        if '-' in color_name:
            color, shade_str = color_name.split('-')
            shade = int(shade_str)
        else:
            color = color_name
        return self.tokens['colors'].get(color, {}).get(shade, '#000000')
    
    def set_theme(self, theme):
        self.current_theme = theme
        self.dark_mode = (theme == 'dark')

DESIGN_TOKENS = DesignTokens()

# ===============================
# Error Handling
# ===============================
@dataclass
class ErrorValue:
    error: Exception
    timestamp: float
    original_value: Any = None
    
    def __repr__(self):
        return f"ErrorValue({self.error.__class__.__name__}: {str(self.error)})"

class ErrorBoundary:
    def __init__(self):
        self.errors = []
        self.error_handlers = []
        self._lock = threading.Lock()
    
    def handle_error(self, error: ErrorValue, stream_name: str = "unknown"):
        with self._lock:
            self.errors.append({'stream': stream_name, 'error': error, 'timestamp': time.time()})
        for handler in self.error_handlers:
            try:
                handler(error, stream_name)
            except Exception as e:
                print(f"Error handler failed: {e}")
    
    def on_error(self, handler: Callable):
        self.error_handlers.append(handler)
        return lambda: self.error_handlers.remove(handler)
    
    def get_errors(self, stream_name: Optional[str] = None):
        with self._lock:
            if stream_name:
                return [e for e in self.errors if e['stream'] == stream_name]
            return self.errors.copy()
    
    def clear_errors(self):
        with self._lock:
            self.errors.clear()

ERROR_BOUNDARY = ErrorBoundary()

# ===============================
# Time-Travel Debugging
# ===============================
class StateSnapshot:
    def __init__(self, stream_name: str, value: Any, timestamp: float, metadata: Dict = None):
        self.stream_name = stream_name
        self.value = value
        self.timestamp = timestamp
        self.metadata = metadata or {}
    
    def to_dict(self):
        return {
            'stream': self.stream_name,
            'value': str(self.value),
            'timestamp': self.timestamp,
            'time': time.ctime(self.timestamp)
        }

class TimeTravelDebugger:
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)
        self.current_index = -1
        self.enabled = True
        self.paused = False
        self._lock = threading.Lock()
    
    def record(self, snapshot: StateSnapshot):
        if self.enabled and not self.paused:
            with self._lock:
                self.history.append(snapshot)
                self.current_index = len(self.history) - 1
    
    def undo(self):
        with self._lock:
            if self.current_index > 0:
                self.current_index -= 1
                return self.history[self.current_index]
            return None
    
    def redo(self):
        with self._lock:
            if self.current_index < len(self.history) - 1:
                self.current_index += 1
                return self.history[self.current_index]
            return None
    
    def export_history(self, filepath: str):
        with self._lock:
            data = [snapshot.to_dict() for snapshot in self.history]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ History exported to {filepath}")
    
    def clear(self):
        with self._lock:
            self.history.clear()
            self.current_index = -1

TIME_TRAVEL = TimeTravelDebugger()

# ===============================
# VDOM Cache
# ===============================
class VDOMCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
        self.access_count = defaultdict(int)
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()
    
    def get(self, key: str):
        with self._lock:
            if key in self.cache:
                self.access_count[key] += 1
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any):
        with self._lock:
            if len(self.cache) >= self.max_size:
                min_key = min(self.access_count, key=self.access_count.get)
                del self.cache[min_key]
                del self.access_count[min_key]
            self.cache[key] = value
            self.access_count[key] = 0
    
    def clear(self):
        with self._lock:
            self.cache.clear()
            self.access_count.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self):
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                'size': len(self.cache),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': f"{hit_rate:.1f}%"
            }

# ===============================
# Thread-Safe Reactive Stream
# ===============================
class Stream(ThreadSafeMixin):
    _id_counter = 0
    _counter_lock = threading.Lock()
    
    def __init__(self, initial_value=None, name: Optional[str] = None):
        ThreadSafeMixin.__init__(self)
        
        with Stream._counter_lock:
            Stream._id_counter += 1
            self.id = Stream._id_counter
        
        self.name = name or f"Stream_{self.id}"
        
        self._value = initial_value
        self._subscribers = []
        self._error_handlers = []
        self._disposed = False
        
        # Debounce & Throttle
        self._debounce_timer = None
        self._debounce_delay = 0
        self._throttle_last = 0
        self._throttle_delay = 0
        
        # History tracking
        self._track_history = False
        self._local_history = deque(maxlen=50)
    
    @property
    def value(self):
        with self._lock:
            return self._value
    
    def set(self, new_value):
        with self._lock:
            if self._disposed:
                print(f"⚠️  Attempting to set disposed stream: {self.name}")
                return
            
            old_value = self._value
            self._value = new_value
            
            # Record in time-travel
            if TIME_TRAVEL.enabled:
                TIME_TRAVEL.record(StateSnapshot(self.name, new_value, time.time()))
            
            # Track local history
            if self._track_history:
                self._local_history.append({
                    'timestamp': time.time(),
                    'old': old_value,
                    'new': new_value
                })
            
            # Apply throttling
            if self._throttle_delay > 0:
                current_time = time.time()
                if current_time - self._throttle_last < self._throttle_delay:
                    return
                self._throttle_last = current_time
            
            # Apply debouncing
            if self._debounce_delay > 0:
                if self._debounce_timer:
                    self._debounce_timer.cancel()
                self._debounce_timer = threading.Timer(
                    self._debounce_delay,
                    lambda: self._notify(old_value, new_value)
                )
                self._debounce_timer.start()
            else:
                self._notify(old_value, new_value)
    
    def _notify(self, old_value, new_value):
        with self._lock:
            subscribers_copy = self._subscribers.copy()
        
        for subscriber in subscribers_copy:
            try:
                subscriber(new_value, old_value)
            except Exception as e:
                self._handle_error(ErrorValue(e, time.time(), new_value))
    
    def _handle_error(self, error_value: ErrorValue):
        for handler in self._error_handlers:
            try:
                recovery = handler(error_value)
                if recovery is not None:
                    self.set(recovery)
                    return
            except:
                pass
        ERROR_BOUNDARY.handle_error(error_value, self.name)
    
    def map(self, transform_fn: Callable) -> 'Stream':
        derived = Stream(name=f"{self.name}.map")
        def update(new_val, old_val):
            try:
                derived.set(transform_fn(new_val))
            except Exception as e:
                derived._handle_error(ErrorValue(e, time.time(), new_val))
        self.subscribe(update)
        if self._value is not None:
            try:
                derived.set(transform_fn(self._value))
            except:
                pass
        return derived
    
    def filter(self, predicate_fn: Callable) -> 'Stream':
        derived = Stream(name=f"{self.name}.filter")
        def update(new_val, old_val):
            try:
                if predicate_fn(new_val):
                    derived.set(new_val)
            except Exception as e:
                derived._handle_error(ErrorValue(e, time.time(), new_val))
        self.subscribe(update)
        return derived
    
    def catch_error(self, handler: Callable) -> 'Stream':
        self._error_handlers.append(handler)
        return self
    
    def debounce(self, delay: float) -> 'Stream':
        """Debounce updates (wait after last change)"""
        self._debounce_delay = delay
        return self
    
    def throttle(self, delay: float) -> 'Stream':
        """Throttle updates (minimum time between updates)"""
        self._throttle_delay = delay
        return self
    
    def distinct(self) -> 'Stream':
        """Only emit when value changes"""
        derived = Stream(name=f"{self.name}.distinct")
        last = [None]
        def update(new_val, old_val):
            if new_val != last[0]:
                last[0] = new_val
                derived.set(new_val)
        self.subscribe(update)
        return derived
    
    def tap(self, side_effect: Callable) -> 'Stream':
        """Perform side effect without affecting stream"""
        def update(new_val, old_val):
            try:
                side_effect(new_val)
            except Exception as e:
                print(f"Tap error: {e}")
        self.subscribe(update)
        return self
    
    def scan(self, accumulator_fn: Callable, initial: Any) -> 'Stream':
        """Accumulate values over time"""
        derived = Stream(initial, name=f"{self.name}.scan")
        def update(new_val, old_val):
            try:
                accumulated = accumulator_fn(derived.value, new_val)
                derived.set(accumulated)
            except Exception as e:
                derived._handle_error(ErrorValue(e, time.time(), new_val))
        self.subscribe(update)
        return derived
    
    def track_history(self, enabled: bool = True):
        self._track_history = enabled
        return self
    
    def get_history(self):
        with self._lock:
            return list(self._local_history)
    
    def subscribe(self, subscriber_fn: Callable):
        with self._lock:
            if not self._disposed:
                self._subscribers.append(subscriber_fn)
        return lambda: self._unsubscribe(subscriber_fn)
    
    def _unsubscribe(self, subscriber_fn):
        with self._lock:
            if subscriber_fn in self._subscribers:
                self._subscribers.remove(subscriber_fn)
    
    def dispose(self):
        with self._lock:
            if not self._disposed:
                self._disposed = True
                if self._debounce_timer:
                    self._debounce_timer.cancel()
                self._subscribers.clear()
                self._error_handlers.clear()
                print(f"🗑️  Disposed stream: {self.name}")
    
    def __repr__(self):
        with self._lock:
            status = "disposed" if self._disposed else f"value={self._value}"
            return f"Stream({self.name}, {status}, subs={len(self._subscribers)})"

# ===============================
# StreamProcessor
# ===============================
class StreamProcessor:
    def __init__(self):
        self.streams: Dict[str, Stream] = {}
        self.pipelines: Dict[str, Stream] = {}
        self._lock = threading.Lock()
    
    def create_stream(self, name: str, initial_value=None) -> Stream:
        with self._lock:
            stream = Stream(initial_value, name=name)
            self.streams[name] = stream
            return stream
    
    def combine_latest(self, stream_names: List[str], combine_fn: Callable = None) -> Stream:
        result = Stream(name=f"combineLatest({','.join(stream_names)})")
        latest = {}
        latest_lock = threading.Lock()
        
        def update_combined(stream_name):
            def updater(new_val, old_val):
                with latest_lock:
                    latest[stream_name] = new_val
                    if len(latest) == len(stream_names):
                        values = [latest[name] for name in stream_names]
                try:
                    result.set(combine_fn(*values) if combine_fn else tuple(values))
                except Exception as e:
                    result._handle_error(ErrorValue(e, time.time(), values))
            return updater
        
        for name in stream_names:
            if name in self.streams:
                self.streams[name].subscribe(update_combined(name))
        return result
    
    def create_pipeline(self, name: str, input_stream: Stream, *operations) -> Stream:
        current = input_stream
        for op in operations:
            if isinstance(op, tuple):
                op_type, *args = op
                if op_type == 'map':
                    current = current.map(args[0])
                elif op_type == 'filter':
                    current = current.filter(args[0])
                elif op_type == 'distinct':
                    current = current.distinct()
                elif op_type == 'catch':
                    current = current.catch_error(args[0])
                elif op_type == 'tap':
                    current = current.tap(args[0])
                elif op_type == 'debounce':
                    current = current.debounce(args[0])
                elif op_type == 'throttle':
                    current = current.throttle(args[0])
                elif op_type == 'scan':
                    current = current.scan(args[0], args[1])
            else:
                current = current.map(op)
        current.name = name
        with self._lock:
            self.pipelines[name] = current
        return current
    
    def dispose_all(self):
        with self._lock:
            for s in list(self.streams.values()) + list(self.pipelines.values()):
                s.dispose()
            self.streams.clear()
            self.pipelines.clear()

# ===============================
# Complete Style Resolver
# ===============================
class AdvancedStyleResolver:
    def __init__(self):
        self.tokens = DESIGN_TOKENS
        self.breakpoint = 'md'
        self.style_cache = {}
        self._lock = threading.Lock()
    
    def set_breakpoint(self, bp):
        with self._lock:
            self.breakpoint = bp
            self.style_cache.clear()
    
    def resolve_classes(self, class_string, current_breakpoint=None):
        if current_breakpoint:
            self.breakpoint = current_breakpoint
        
        cache_key = f"{class_string}_{self.breakpoint}_{self.tokens.current_theme}"
        
        with self._lock:
            if cache_key in self.style_cache:
                return self.style_cache[cache_key]
        
        resolved = {}
        for cls in class_string.split():
            self._resolve_class(cls, resolved)
        
        with self._lock:
            self.style_cache[cache_key] = resolved
        return resolved
    
    def _resolve_class(self, cls, resolved):
        # Handle breakpoint prefixes
        if ':' in cls:
            bp_prefix, actual_cls = cls.split(':', 1)
            if bp_prefix in ['sm', 'md', 'lg', 'xl', '2xl']:
                bp_order = ['sm', 'md', 'lg', 'xl', '2xl']
                current_idx = bp_order.index(self.breakpoint) if self.breakpoint in bp_order else 1
                prefix_idx = bp_order.index(bp_prefix)
                if current_idx < prefix_idx:
                    return
                cls = actual_cls
        
        # Handle dark mode
        if cls.startswith('dark:'):
            if not self.tokens.dark_mode:
                return
            cls = cls[5:]
        
        # Handle hover
        if cls.startswith('hover:'):
            hover_props = self._get_props(cls[6:])
            if 'bg' in hover_props:
                resolved['active_bg'] = hover_props['bg']
            return
        
        resolved.update(self._get_props(cls))
    
    def _get_props(self, cls):
        # Background colors
        if cls.startswith('bg-'):
            return {'bg': self.tokens.get_color(cls[3:])}
        
        # Text colors
        if cls.startswith('text-'):
            color_part = cls[5:]
            sizes = ['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl']
            if color_part in sizes:
                return {'font_size': self.tokens.tokens['font_size'][color_part]}
            return {'fg': self.tokens.get_color(color_part)}
        
        # Padding
        if cls.startswith('p-'):
            val = self.tokens.tokens['spacing'].get(cls[2:], 0)
            return {'padx': val, 'pady': val}
        if cls.startswith('px-'):
            return {'padx': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        if cls.startswith('py-'):
            return {'pady': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        
        # Margin
        if cls.startswith('m-'):
            val = self.tokens.tokens['spacing'].get(cls[2:], 0)
            return {'margin': val}
        
        # Width/Height
        if cls.startswith('w-'):
            size = cls[2:]
            if size == 'full':
                return {'width_full': True}
            return {'width': self.tokens.tokens['spacing'].get(size, 0)}
        if cls.startswith('h-'):
            size = cls[2:]
            if size == 'full':
                return {'height_full': True}
            return {'height': self.tokens.tokens['spacing'].get(size, 0)}
        
        # Layout
        if cls == 'flex':
            return {'layout': 'horizontal'}
        if cls == 'flex-col':
            return {'layout': 'vertical'}
        if cls.startswith('gap-'):
            return {'spacing': self.tokens.tokens['spacing'].get(cls[4:], 0)}
        
        # Typography
        if cls.startswith('font-'):
            weight = cls[5:]
            if weight in self.tokens.tokens['font_weight']:
                return {'font_weight': self.tokens.tokens['font_weight'][weight]}
        
        # Border
        if cls == 'border':
            return {'border_width': 1}
        if cls.startswith('border-'):
            size = cls[7:]
            if size.isdigit():
                return {'border_width': int(size)}
        
        # Rounded
        if cls.startswith('rounded'):
            if cls == 'rounded':
                return {'border_radius': self.tokens.tokens['border_radius']['default']}
            size = cls[8:] if cls.startswith('rounded-') else 'default'
            return {'border_radius': self.tokens.tokens['border_radius'].get(size, 4)}
        
        # Opacity
        if cls.startswith('opacity-'):
            opacity = self.tokens.tokens['opacity'].get(cls[8:], 1.0)
            return {'opacity': opacity}
        
        return {}

# ===============================
# Responsive Layout Engine
# ===============================
class ResponsiveLayoutEngine:
    def __init__(self, root_window):
        self.root = root_window
        self.current_breakpoint = 'md'
        self.breakpoint_stream = Stream('md', name='window_breakpoint')
        self._last_resize_time = 0
        self.root.bind('<Configure>', self._handle_resize)
    
    def _handle_resize(self, event):
        if event.widget == self.root:
            current_time = time.time() * 1000
            if current_time - self._last_resize_time > 100:
                self._last_resize_time = current_time
                self._update_breakpoint(event.width)
    
    def _update_breakpoint(self, width):
        breakpoints = DESIGN_TOKENS.tokens['breakpoints']
        new_bp = 'sm'
        
        if width >= breakpoints.get('2xl', 1536):
            new_bp = '2xl'
        elif width >= breakpoints.get('xl', 1280):
            new_bp = 'xl'
        elif width >= breakpoints.get('lg', 1024):
            new_bp = 'lg'
        elif width >= breakpoints.get('md', 768):
            new_bp = 'md'
        
        if new_bp != self.current_breakpoint:
            self.current_breakpoint = new_bp
            self.breakpoint_stream.set(new_bp)

# ===============================
# Component System with Hook Support
# ===============================
class Component:
    """Base class for reusable components with hook support"""
    
    def __init__(self, props: Dict = None):
        self.props = props or {}
        self.state = {}
        self.streams = {}
        self._mounted = False
        self._path = None
    
    def create_state(self, name: str, initial_value=None) -> Stream:
        """Create a state stream for this component (legacy method)"""
        stream = Stream(initial_value, name=f"{self.__class__.__name__}.{name}")
        self.streams[name] = stream
        return stream
    
    def render(self):
        """Override this method to define component UI"""
        raise NotImplementedError("Component must implement render()")
    
    def on_mount(self):
        """Called when component is first mounted"""
        pass
    
    def on_unmount(self):
        """Called when component is unmounted"""
        pass
    
    def _mount(self):
        if not self._mounted:
            self._mounted = True
            self.on_mount()
    
    def _unmount(self):
        if self._mounted:
            self._mounted = False
            for stream in self.streams.values():
                stream.dispose()
            self.on_unmount()

def create_element(element_type: Union[str, type], props: Dict = None, *children) -> Dict:
    """Helper function to create VDOM elements (like React.createElement)"""
    props = props or {}
    
    # If element_type is a Component class, instantiate and render it
    if inspect.isclass(element_type) and issubclass(element_type, Component):
        # We'll render it later in _with_hook_rendering
        return {
            'type': element_type,
            'props': props,
            'children': list(children),
            'key': props.get('key')
        }
    
    # If it's already a component instance
    elif isinstance(element_type, Component):
        return element_type.render()
    
    # If it's a function component
    elif callable(element_type) and not isinstance(element_type, str):
        return {
            'type': element_type,
            'props': props,
            'children': list(children),
            'key': props.get('key')
        }
    
    # Regular VDOM node
    return {
        'type': element_type,
        'props': props,
        'children': list(children),
        'key': props.get('key')
    }

# ===============================
# Hook-Aware VDOM Renderer
# ===============================
class HookAwareVDOMRenderer:
    """Renderer that handles useState hooks during VDOM rendering"""
    
    def __init__(self, root):
        self.root = root
        self.patcher = FunctionalPatcher()
        self.current_vdom = None
        self.widgets = []
    
    @PERFORMANCE.measure_time('hook_aware_render')
    def render(self, diff_result):
        """Render using functional diffing with hook support"""
        render_type = diff_result.get('type', 'full')
        
        # Reset hook context at the start of each render cycle
        global _current_component_path, _hook_index, _component_render_stack
        _current_component_path = []
        _hook_index = 0
        _component_render_stack = []
        
        if render_type == 'full':
            self._render_full(diff_result['vdom'])
            self.current_vdom = diff_result['vdom']
            
        elif render_type == 'patches':
            patches = diff_result['patches']
            vdom = diff_result['vdom']
            self.patcher.apply_patches(patches, vdom, self.root)
            self.current_vdom = vdom
            
        elif render_type == 'none':
            pass
    
    def _render_full(self, vdom):
        """Render full VDOM tree with hook support"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.patcher = FunctionalPatcher()
        self.widgets = []
        
        # Render with empty path (root)
        self._render_vdom_with_hooks(vdom, self.root, [])
    
    def _render_vdom_with_hooks(self, vdom, parent, path):
        """Recursively render VDOM with hook context"""
        if not vdom or not isinstance(vdom, dict):
            return
        
        # Handle component rendering with hooks
        node_type = vdom.get('type', 'frame')
        props = vdom.get('props', {})
        children = vdom.get('children', [])
        
        # Check if this is a component (class or function)
        is_component = (
            (isinstance(node_type, type) and issubclass(node_type, Component)) or
            (callable(node_type) and not isinstance(node_type, str))
        )
        
        if is_component:
            # Render component with hook context
            rendered = _with_hook_rendering(node_type, props, path)
            return self._render_vdom_with_hooks(rendered, parent, path)
        
        # Regular widget rendering
        widget = WidgetFactory.create_widget(node_type, parent, props)
        
        if widget:
            # Bind events
            EventSystem.bind_events(widget, props)
            
            # Apply layout
            position = path[-1] if path else 0
            LayoutManager.apply_layout(widget, vdom, parent, position)
            
            # Track widget
            self.widgets.append(widget)
            
            # Render children
            for i, child in enumerate(children):
                child_path = path + [i]
                self._render_vdom_with_hooks(child, widget, child_path)
    
    def get_widget_by_key(self, key):
        """Get widget by its VDOM key"""
        return self.patcher.key_map.get(key)
    
    def get_stats(self):
        """Get renderer statistics"""
        return {
            'widget_count': len(self.patcher.widget_map),
            'key_mappings': len(self.patcher.key_map),
            'total_widgets': len(self.widgets)
        }

# ===============================
# Main PyUIWizard Class with Hook Support
# ===============================
class PyUIWizard:
    """
    Main class for PyUIWizard framework with full useState hook support
    
    Usage:
        wizard = PyUIWizard(use_diffing=True)
        wizard.create_state('count', 0)  # Global state
        wizard.render_app(my_render_function)  # Can use use_state() inside components
        wizard.run()
    """
    
    def __init__(self, title="PyUIWizard App", width=800, height=600, use_diffing=True):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        
        self.processor = StreamProcessor()
        self.style_resolver = AdvancedStyleResolver()
        self.layout_engine = ResponsiveLayoutEngine(self.root)
        self.cache = VDOMCache()
        
        self.use_diffing = use_diffing
        self.differ = FunctionalDiffer() if use_diffing else None
        self.renderer = HookAwareVDOMRenderer(self.root) if use_diffing else None
        
        self.last_vdom = None
        self.render_function = None
        self.render_count = 0
        self.skip_count = 0
        
        # Setup error handling
        ERROR_BOUNDARY.on_error(self._handle_error)
        
        print(f"🚀 PyUIWizard {__version__} initialized with useState hook support")
    
    def create_state(self, name: str, initial_value=None) -> Stream:
        """Create a global state stream"""
        return self.processor.create_stream(name, initial_value)
    
    def create_computed(self, name: str, dependencies: List[str], compute_fn: Callable) -> Stream:
        """Create a computed stream from dependencies"""
        return self.processor.combine_latest(dependencies, compute_fn)
    
    def render_app(self, render_fn: Callable):
        """Set the main render function"""
        self.render_function = render_fn
        
        # Get all state streams
        state_names = list(self.processor.streams.keys())
        
        if not state_names:
            print("⚠️  No global state streams created. Create state first with create_state()")
            # Still allow render with just useState hooks
            state_names = []
        
        # Create combined stream for global state
        if state_names:
            combined = self.processor.combine_latest(
                state_names,
                lambda *values: dict(zip(state_names, values))
            )
            
            # Setup render pipeline
            if self.use_diffing:
                ui_stream = self.processor.create_pipeline(
                    'ui_pipeline',
                    combined,
                    ('distinct',),
                    ('map', self._create_vdom),
                    ('map', self._resolve_styles),
                    ('debounce', 0.016),  # 60fps
                    ('map', self._diff_with_previous),
                    ('catch', lambda err: self._error_vdom(err))
                )
            else:
                ui_stream = self.processor.create_pipeline(
                    'ui_pipeline',
                    combined,
                    ('distinct',),
                    ('map', self._create_vdom),
                    ('map', self._resolve_styles),
                    ('catch', lambda err: self._error_vdom(err))
                )
            
            # Subscribe to updates
            ui_stream.subscribe(self._render_to_screen)
        else:
            # No global state, just render once
            self._render_to_screen({})
        
        # React to breakpoint changes
        self.layout_engine.breakpoint_stream.subscribe(
            lambda bp, old: (self.style_resolver.set_breakpoint(bp), self.cache.clear())
        )
    
    @PERFORMANCE.measure_time('create_vdom')
    def _create_vdom(self, state):
        """Create VDOM from render function with hook context reset"""
        # Reset hook context before each render
        global _current_component_path, _hook_index
        _current_component_path = []
        _hook_index = 0
        
        cache_key = json.dumps(state, sort_keys=True)
        cached = self.cache.get(cache_key)
        if cached:
            self.skip_count += 1
            return cached
        
        self.render_count += 1
        
        # Add breakpoint to state
        state['breakpoint'] = self.layout_engine.current_breakpoint
        
        # Call user's render function
        vdom = self.render_function(state)
        
        self.cache.set(cache_key, vdom)
        return vdom
    
    @PERFORMANCE.measure_time('resolve_styles')
    def _resolve_styles(self, vdom):
        """Resolve Tailwind-style classes"""
        def resolve(node):
            if 'props' in node and 'class' in node['props']:
                resolved = self.style_resolver.resolve_classes(
                    node['props']['class'],
                    self.layout_engine.current_breakpoint
                )
                node_props = node['props'].copy()
                del node_props['class']
                node_props.update(resolved)
                node['props'] = node_props
            if 'children' in node:
                node['children'] = [resolve(c) for c in node['children']]
            return node
        return resolve(vdom.copy())
    
    def _diff_with_previous(self, new_vdom):
        """Generate patches using functional diffing"""
        if self.last_vdom is None:
            self.last_vdom = new_vdom
            return {'type': 'full', 'vdom': new_vdom}
        
        patches = self.differ.diff(self.last_vdom, new_vdom)
        self.last_vdom = new_vdom
        
        if not patches:
            return {'type': 'none'}
        
        return {'type': 'patches', 'patches': patches, 'vdom': new_vdom}
    
    def _render_to_screen(self, diff_result, old_val=None):
        """Render to screen using the hook-aware renderer"""
        if self.use_diffing:
            self.renderer.render(diff_result)
        else:
            # Fallback to full re-render
            self._render_full(diff_result)
    
    def _render_full(self, vdom):
        """Full re-render without diffing (for non-diffing mode)"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Reset hook context
        global _current_component_path, _hook_index
        _current_component_path = []
        _hook_index = 0
        
        self._render_node_with_hooks(vdom, self.root, [])
    
    def _render_node_with_hooks(self, node, parent, path):
        """Render a single VDOM node with hook support"""
        if not node or not isinstance(node, dict):
            return
        
        node_type = node.get('type', 'frame')
        props = node.get('props', {})
        children = node.get('children', [])
        
        # Handle component rendering with hooks
        is_component = (
            (isinstance(node_type, type) and issubclass(node_type, Component)) or
            (callable(node_type) and not isinstance(node_type, str))
        )
        
        if is_component:
            # Render component with hook context
            rendered = _with_hook_rendering(node_type, props, path)
            return self._render_node_with_hooks(rendered, parent, path)
        
        # Regular widget rendering
        widget = WidgetFactory.create_widget(node_type, parent, props)
        
        if widget:
            EventSystem.bind_events(widget, props)
            LayoutManager.apply_layout(widget, node, parent, path[-1] if path else 0)
            
            for i, child in enumerate(children):
                child_path = path + [i]
                self._render_node_with_hooks(child, widget, child_path)
    
    def _error_vdom(self, error: ErrorValue):
        """Create error VDOM"""
        return {
            'type': 'frame',
            'props': {'bg': '#fee2e2', 'padx': 20, 'pady': 20},
            'children': [
                {'type': 'label', 'props': {
                    'text': '⚠️ Error Occurred',
                    'fg': '#991b1b',
                    'font_size': 16,
                    'font_weight': 'bold'
                }},
                {'type': 'label', 'props': {
                    'text': str(error.error),
                    'fg': '#7f1d1d',
                    'font_size': 12
                }}
            ]
        }
    
    def _handle_error(self, error: ErrorValue, stream_name: str):
        """Handle errors"""
        print(f"❌ Error in {stream_name}: {error.error}")
    
    def run(self):
        """Start the application"""
        print(f"\n🚀 PyUIWizard {__version__} started")
        print(f"   Mode: {'Functional Diffing with Hooks' if self.use_diffing else 'Full Re-render'}")
        print(f"   Window: {self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")
        self.root.mainloop()
    
    def get_stats(self):
        """Get performance statistics"""
        stats = {
            'renders': self.render_count,
            'skipped': self.skip_count,
            'cache': self.cache.get_stats(),
            'performance': PERFORMANCE.get_stats(),
            'hooks': get_hook_debug_info()
        }
        
        if self.use_diffing:
            stats['diffing'] = self.differ.get_stats()
            stats['renderer'] = self.renderer.get_stats()
        
        return stats
    
    def print_stats(self):
        """Print all statistics"""
        print("\n" + "="*60)
        print("PYUIWIZARD STATISTICS")
        print("="*60)
        stats = self.get_stats()
        print(f"\nRenders: {stats['renders']}")
        print(f"Skipped: {stats['skipped']}")
        print(f"Cache: {stats['cache']}")
        print(f"Hook State: {stats['hooks']['state_count']} states managed")
        if 'diffing' in stats:
            print(f"\nDiffing: {stats['diffing']}")
        PERFORMANCE.print_stats()
    
    def dispose(self):
        """Clean up resources"""
        self.processor.dispose_all()
        self.cache.clear()
        clear_component_state()  # Clear all hook state
        if self.root:
            self.root.quit()

# ===============================
# Example Usage with useState
# ===============================
if __name__ == "__main__":
    # Create wizard instance
    wizard = PyUIWizard(title="PyUIWizard 4.0 Demo", width=600, height=400, use_diffing=True)
    
    # Create global state
    global_counter = wizard.create_state('global_counter', 0)
    
    # Define function components using useState
    def CounterButton(props):
        """Function component using useState hook"""
        [count, setCount] = use_state(0, key="counter_button")
        
        def handle_click():
            setCount(count + 1)
            # Also update global state
            global_counter.set(global_counter.value + 1)
        
        return create_element('frame', {
            'class': 'bg-white p-4 m-2 border rounded',
            'key': 'counter_button'
        },
            create_element('label', {
                'text': f'Local: {count}, Global: {props.get("global", 0)}',
                'class': 'text-gray-800 text-lg'
            }),
            create_element('button', {
                'text': 'Increment Both',
                'class': 'bg-blue-500 hover:bg-blue-600 text-white p-2 mt-2',
                'onClick': handle_click
            })
        )
    
    def UserProfile(props):
        """Another function component with multiple useState hooks"""
        [username, setUsername] = use_state("Guest", key="username")
        [theme, setTheme] = use_state("light", key="theme")
        
        def toggle_theme():
            setTheme("dark" if theme == "light" else "light")
        
        return create_element('frame', {
            'class': f'p-4 m-2 rounded-lg bg-{"gray-100" if theme == "light" else "gray-800"}',
            'key': 'user_profile'
        },
            create_element('label', {
                'text': f'User: {username}',
                'class': f'text-{"gray-800" if theme == "light" else "white"} text-xl'
            }),
            create_element('button', {
                'text': f'Switch to {"" if theme == "light" else ""}Theme',
                'class': f'{"bg-gray-800 text-white" if theme == "light" else "bg-gray-100 text-black"} p-2 mt-2',
                'onClick': toggle_theme
            })
        )
    
    # Main render function
    def main_render(state):
        return create_element('frame', 
            {'class': 'bg-gray-100 p-6 h-full'},
            create_element('label', {
                'text': '🧙 PyUIWizard 4.0 with useState Hook',
                'class': 'text-gray-900 text-2xl font-bold mb-4'
            }),
            create_element(CounterButton, {
                'global': state.get('global_counter', 0),
                'key': 'counter1'
            }),
            create_element(UserProfile, {'key': 'profile1'}),
            create_element(UserProfile, {'key': 'profile2'}),  # Second instance with independent state
            create_element('frame', {
                'class': 'mt-4 p-4 bg-gray-800 text-gray-300 rounded',
                'key': 'footer'
            },
                create_element('label', {
                    'text': f'Global Counter: {state.get("global_counter", 0)} | Theme: {DESIGN_TOKENS.current_theme.title()}',
                    'class': 'text-sm'
                })
            )
        )
    
    # Setup render
    wizard.render_app(main_render)
    
    # Run app
    wizard.run()
    
    # Print stats on exit
    wizard.print_stats()