"""
PyUIWizard 4.2.0 - Complete Reactive GUI Framework with Hooks (useState, useEffect, useRef, useContext)
FULL PRODUCTION VERSION 

Author: PyUIWizard Team
License: MIT
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable, Any, List, Dict, Optional, Tuple, Union, TypeVar
import time
import threading
from collections import defaultdict, deque, OrderedDict
from dataclasses import dataclass
from enum import Enum
import json
import weakref
from functools import wraps
import inspect
import copy
import re
import math
from contextlib import contextmanager

__version__ = "4.2.0"
__all__ = [
    'PyUIWizard', 'Stream', 'Component', 'create_element', 'useState',
    'DESIGN_TOKENS', 'PERFORMANCE', 'ERROR_BOUNDARY', 'TIME_TRAVEL',
    'useEffect', 'useContext', 'useRef', 'create_context', 'Provider'
]

T = TypeVar('T')

# ===============================
# Thread Safety with Timeouts
# ===============================
class ThreadSafeMixin:
    """Mixin for thread-safe operations with deadlock prevention"""
    def __init__(self):
        self._lock = threading.RLock()
        self._lock_timeout = 5.0  # seconds
    
    def synchronized(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            acquired = self._lock.acquire(timeout=self._lock_timeout)
            if not acquired:
                raise RuntimeError(f"Timeout acquiring lock for {func.__name__}")
            try:
                return func(*args, **kwargs)
            finally:
                self._lock.release()
        return wrapper
    
    @contextmanager
    def atomic(self):
        """Context manager for atomic operations"""
        acquired = self._lock.acquire(timeout=self._lock_timeout)
        if not acquired:
            raise RuntimeError("Timeout acquiring lock for atomic operation")
        try:
            yield
        finally:
            self._lock.release()

# ===============================
# Performance Monitor with Export
# ===============================
class PerformanceMonitor:
    def __init__(self):
        self.operation_times = defaultdict(list)
        self.operation_counts = defaultdict(int)
        self.memory_usage = []
        self._lock = threading.Lock()
        self.start_time = time.time()
    
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
    
    @contextmanager
    def measure(self, operation_name: str):
        """Context manager for performance measurement"""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = (end_time - start_time) * 1000
            with self._lock:
                self.operation_times[operation_name].append(duration)
                self.operation_counts[operation_name] += 1
    
    def record_memory(self):
        """Record memory usage (simplified)"""
        import sys
        memory = sys.getsizeof(self) // 1024  # KB
        with self._lock:
            self.memory_usage.append({
                'timestamp': time.time(),
                'memory_kb': memory
            })
        return memory
    
    def get_stats(self):
        with self._lock:
            stats = {}
            for op_name, times in self.operation_times.items():
                count = self.operation_counts[op_name]
                if times:
                    avg_time = sum(times) / len(times)
                    min_time = min(times)
                    max_time = max(times)
                    p95 = sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else avg_time
                    p99 = sorted(times)[int(len(times) * 0.99)] if len(times) > 1 else avg_time
                else:
                    avg_time = min_time = max_time = p95 = p99 = 0
                
                stats[op_name] = {
                    'count': count,
                    'avg_ms': round(avg_time, 2),
                    'min_ms': round(min_time, 2),
                    'max_ms': round(max_time, 2),
                    'p95_ms': round(p95, 2),
                    'p99_ms': round(p99, 2),
                    'total_ms': round(sum(times), 2)
                }
            
            if self.memory_usage:
                last_mem = self.memory_usage[-1]['memory_kb']
                stats['memory'] = {'current_kb': last_mem, 'samples': len(self.memory_usage)}
            
            stats['uptime_seconds'] = round(time.time() - self.start_time, 2)
            return stats
    
    def export_stats(self, filepath: str):
        """Export statistics to JSON file"""
        stats = self.get_stats()
        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)
        return stats
    
    def print_stats(self):
        print("\n" + "="*60)
        print("PYUIWIZARD PERFORMANCE STATISTICS")
        print("="*60)
        stats = self.get_stats()
        for op_name, stat in sorted(stats.items()):
            if op_name not in ['memory', 'uptime_seconds']:
                print(f"\n{op_name}:")
                print(f"  Calls:  {stat['count']}")
                print(f"  Avg:    {stat['avg_ms']:.2f}ms")
                print(f"  Min:    {stat['min_ms']:.2f}ms")
                print(f"  Max:    {stat['max_ms']:.2f}ms")
                print(f"  P95:    {stat['p95_ms']:.2f}ms")
                print(f"  P99:    {stat['p99_ms']:.2f}ms")
                print(f"  Total:  {stat['total_ms']:.2f}ms")
        
        if 'memory' in stats:
            print(f"\nMemory: {stats['memory']['current_kb']}KB ({stats['memory']['samples']} samples)")
        
        print(f"\nUptime: {stats['uptime_seconds']} seconds")
        print("="*60 + "\n")
    
    def reset(self):
        with self._lock:
            self.operation_times.clear()
            self.operation_counts.clear()
            self.memory_usage.clear()
            self.start_time = time.time()

PERFORMANCE = PerformanceMonitor()

# ===============================
# Diff Types
# ===============================
class DiffType(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    REPLACE = "REPLACE"
    REMOVE = "REMOVE"
    REORDER = "REORDER"
    NONE = "NONE"
    MOVE = "MOVE"

# ===============================
# Functional Differ with Optimization
# ===============================
class FunctionalDiffer:
    """Pure functional diffing with memoization and batching"""
    
    def __init__(self):
        self.stats = defaultdict(int)
        self.patch_cache = OrderedDict()
        self.memo = {}
    
    @PERFORMANCE.measure_time('functional_diff')
    def diff(self, old_vdom: Optional[Dict], new_vdom: Optional[Dict]) -> List[Dict]:
        """Main diff function with caching"""
        self.stats['diffs'] += 1
        
        if not new_vdom:
            return [{'type': DiffType.REMOVE, 'path': [], 'old': old_vdom}]
        
        if not old_vdom:
            return [{'type': DiffType.CREATE, 'path': [], 'node': new_vdom}]
        
        # Cache key for memoization
        cache_key = (json.dumps(old_vdom, sort_keys=True, default=str), 
                    json.dumps(new_vdom, sort_keys=True, default=str))
        
        if cache_key in self.patch_cache:         
            self.stats['cache_hits'] += 1
            # move to end to mark as recently used 
            self.patch_cache.move_to_end(cache_key)
            
            return copy.deepcopy(self.patch_cache[cache_key])
        
        patches = self._diff_node(old_vdom, new_vdom, [])
        self.stats['patches'] += len(patches)
        
        # Cache the result
        if len(patches) < 50:  # Only cache small diffs
            self.patch_cache[cache_key] = copy.deepcopy(patches)
            if len(self.patch_cache) > 1000:
                # Remove Oldest (first) item in OrderedDict
                self.patch_cache.popitem(last=False)
        
        return patches
    
    def _diff_node(self, old: Dict, new: Dict, path: List) -> List[Dict]:
        """Diff a single node with memoization"""
        # Use JSON Serialisation for stable hashing
        try:
            old_hash = hash(json.dumps(old, sort_keys=True, default=str))
            new_hash = hash(json.dumps(new, sort_keys=True, default=str))
            memo_key = (old_hash, new_hash, tuple(path))
        except (TypeError, ValueError):
            # if unhashable, skip memoization for this node
            #old_hash= hash(str(old))
            #new_hash= hash(str(new))
            #memo_key= (old_hash, new_hash, tuple(path))
            memo_key=None
            
        
        if memo_key and memo_key in self.memo:
            return copy.deepcopy(self.memo[memo_key])
        
        patches = []
        
        # Fast path: same object reference
        if old is new:
            return []
        
        # log what we're diffing 
        old_type = old.get('type')
        new_type = new.get('type')
        old_key = old.get('key')
        new_key = new.get('key')
        print(f" _diff_node at {path}: type={old_type}->{new_type}, key={old_key}->{new_key} ")
        
        if old.get('type') != new.get('type'):
            self.stats['replace_ops'] += 1
            patches = [{'type': DiffType.REPLACE, 'path': path, 'old': old, 'new': new}]
            self.memo[memo_key] = copy.deepcopy(patches)
            return patches
        
        if old.get('key') != new.get('key'):
            self.stats['replace_ops'] += 1
            patches = [{'type': DiffType.REPLACE, 'path': path, 'old': old, 'new': new}]
            self.memo[memo_key] = copy.deepcopy(patches)
            return patches
        # Diff props
        props_patch = self._diff_props(old.get('props', {}), new.get('props', {}), path)
        if props_patch:
            patches.append(props_patch)
            self.stats['update_ops'] += 1
            print(f"Props changed at {path}: {props_patch['props']['changed'].keys()}")
        # Diff children 
        children_patches = self._diff_children(old.get('children', []), new.get('children', []), path)
        patches.extend([p for p in children_patches if p])
        if children_patches:
            print(f" Children patches at {path}: {len(children_patches)} patches")
        
        if memo_key:
            self.memo[memo_key] = copy.deepcopy(patches)
        
        return patches
    
    def _get_event_handler_props(self):
        """Return set of all known event handler property names"""
        return {
            'onClick', 'onDoubleClick', 'onRightClick', 'onMouseEnter',
            'onMouseLeave', 'onMouseMove', 'onMouseDown', 'onMouseUp',
            'onMouseWheel', 'onFocus', 'onBlur', 'onKeyPress', 'onKeyRelease',
            'onKeyDown', 'onKeyUp', 'onChange', 'onSubmit', 'onEscape',
            'onTab', 'onShiftTab', 'onDragStart', 'onDrag', 'onDragEnd',
            'onDrop', 'onResize'
        }
    
    def _diff_props(self, old_props: Dict, new_props: Dict, path: List) -> Optional[Dict]:
        """Diff properties with deep equality check - FIXED VERSION"""
        changed = {}
        event_handlers = self._get_event_handler_props() # New
        for key in new_props:
            old_val = old_props.get(key)
            new_val = new_props[key]
            
            # Text/Value properties always check explicitly
            if key in ['text', 'value']:
                # Force string comparison to catch numeric/string differences
                if str(old_val) != str(new_val):
                    changed[key] = new_val
                    print(f"  🔍 Text change detected at {path}: '{old_val}' -> '{new_val}'")
                             
            # Event handlers: Compare by function identity 
            elif key in event_handlers:
                if callable(old_val) and callable(new_val):
                    # Only Skip if there literally the same function 
                    if old_val is not new_val:
                        changed[key]=new_val
                        print(f"Event handler changed: {key} at {path}")
                    elif old_val != new_val:
                        # One is callable other isn't, definitely changed 
                        changed[key]= new_val
            # Regular properties         
            elif old_val != new_val:
                # Deep equality check for objects
                if isinstance(old_val, dict) and isinstance(new_val, dict):
                    if json.dumps(old_val, sort_keys=True) != json.dumps(new_val, sort_keys=True):
                        changed[key] = new_val
                elif isinstance(old_val, list) and isinstance(new_val, list):
                    if json.dumps(old_val, sort_keys=True) != json.dumps(new_val, sort_keys=True):
                        changed[key] = new_val
                else:
                    changed[key] = new_val
        
        removed = [k for k in old_props if k not in new_props]
        
        if changed or removed:
            return {
                'type': DiffType.UPDATE,
                'path': path,
                'props': {'changed': changed, 'removed': removed}
            }
        
        return None
    
    def _diff_children(self, old_children: List, new_children: List, path: List) -> List[Dict]:
        """Diff children with key optimization"""
        # Check if any children have keys
        has_keys = any(c.get('key') is not None for c in new_children)
        print(f" Diff children at {path}: {len(old_children)} old, {len(new_children)} new, has_key={has_keys}")
        if has_keys:
            return self._diff_keyed_children(old_children, new_children, path)
        else:
            return self._diff_indexed_children(old_children, new_children, path)
    
    def _diff_indexed_children(self, old_children: List, new_children: List, path: List) -> List[Dict]:
        """Diff children by index"""
        max_len = max(len(old_children), len(new_children))
        patches = []
        
        for i in range(max_len):
            old_child = old_children[i] if i < len(old_children) else None
            new_child = new_children[i] if i < len(new_children) else None
            child_path = path + [i]
            
            if old_child is None and new_child is None:
                continue
            elif old_child is None:
                patches.append({'type': DiffType.CREATE, 'path': child_path, 'node': new_child})
                self.stats['create_ops'] += 1
            elif new_child is None:
                patches.append({'type': DiffType.REMOVE, 'path': child_path, 'old': old_child})
                self.stats['remove_ops'] += 1
            else:
                patches.extend(self._diff_node(old_child, new_child, child_path))
        
        return patches
    
    def _diff_keyed_children(self, old_children: List, new_children: List, path: List) -> List[Dict]:
        """Diff keyed children with move detection - FIXED VERSION"""
        old_by_key = {c.get('key'): (i, c) for i, c in enumerate(old_children) if c.get('key') is not None}
        new_by_key = {c.get('key'): (i, c) for i, c in enumerate(new_children) if c.get('key') is not None}
    
        patches = []
    
        print(f"  🔍 _diff_keyed_children at {path}:")
        print(f"     Old keys: {list(old_by_key.keys())}")
        print(f"     New keys: {list(new_by_key.keys())}")
    
        # Handle new children
        for key, (new_idx, new_child) in new_by_key.items():
            # Use the key directly in the path
            child_path = path + [key]
        
            if key in old_by_key:
                old_idx, old_child = old_by_key[key]
            
                print(f"     ✅ Diffing existing child '{key}' at {child_path}")
            
                # Recursively diff this child AND all its descendants
                child_patches = self._diff_node(old_child, new_child, child_path)
            
                if child_patches:
                    print(f"     ✅ Found {len(child_patches)} patches for '{key}'")
                    patches.extend(child_patches)
                else:
                    print(f"     ℹ️  No changes for '{key}'")
            
                # Check if moved
                if old_idx != new_idx:
                    patches.append({
                        'type': DiffType.MOVE,
                        'path': path,
                        'key': key,
                        'from_index': old_idx,
                        'to_index': new_idx
                    })
                    self.stats['reorder_ops'] += 1
                    print(f"     🔄 Child '{key}' moved from {old_idx} to {new_idx}")
            else:
                patches.append({'type': DiffType.CREATE, 'path': child_path, 'node': new_child})
                self.stats['create_ops'] += 1
                print(f"     ➕ New child '{key}' created")
    
        # Handle removed children
        for key, (old_idx, old_child) in old_by_key.items():
            if key not in new_by_key:
                patches.append({'type': DiffType.REMOVE, 'path': path + [key], 'old': old_child})
                self.stats['remove_ops'] += 1
                print(f"     ➖ Child '{key}' removed")
    
        return patches
    
    def get_stats(self):
        return dict(self.stats)
    
    def reset_stats(self):
        self.stats.clear()
        self.patch_cache.clear()
        self.memo.clear()

# ===============================
# Hook System with Thread Safety
# ===============================
# Thread-safe global state
_component_state_manager = threading.local()

def _get_state_manager():
    """Get thread-local state manager, initializing if needed."""
    if not hasattr(_component_state_manager, 'initialized'):
        _component_state_manager.state = {}
        _component_state_manager.current_path = []
        _component_state_manager.hook_index = 0
        _component_state_manager.render_stack = []
        _component_state_manager.component_instances = {}  # Regular dict, keyed by path tuple
        _component_state_manager.effect_queue = []
        _component_state_manager.initialized = True
    return _component_state_manager

   
# Context system
_context_registry = threading.local()

# initialise for main thread immediately 
mgr= _get_state_manager() 

def _get_context_registry():
    """Get thread-local context registry, initializing if needed."""
    if not hasattr(_context_registry, 'initialized'):
        _context_registry.contexts = {}
        _context_registry.initialized = True
    return _context_registry
    
registry= _get_context_registry()

def useState(initial_value, key=None):
    """
    React-like useState hook with thread safety and lifecycle management.
    
    Args:
        initial_value: Initial state value
        key: Optional unique key for the state
    
    Returns:
        tuple: [current_value, setter_function]
    """
    # Get thread-local state
    mgr = _get_state_manager()
    state = mgr.state
    current_path = mgr.current_path
    hook_index = mgr.hook_index
   
    if not current_path:
        # get render stack for better error message 
        render_stack = mgr.render_stack if hasattr(mgr, 'render_stack') else []
        stack_info = ""
        if render_stack:
            stack_info= f"\nRender stack: {[c.get('type', 'unknown') for c in render_stack]}"
        raise RuntimeError(
            f"useState must be called within a component's render function. "
            f"No component context found.{stack_info}\n"
            f"Make sure you're calling useState at the top level of a component, "
            f"not inside loops, conditions, or callbacks."
        )
        
    # Create unique state identifier
    path_tuple = tuple(current_path)
    state_id = key if key else f"hook_{hook_index}"
    full_state_id = (path_tuple, state_id)
    # Check for duplicate keys 
    if key is not None and full_state_id in state:
        # key already exists - check correct usage 
        existing= state[full_state_id]
        if existing.get('key') != key:
            raise RuntimeError(
            f"useState key collision: '{key}' is being used inconsistently"
            f"in component at {path_tuple}. hook keys must be stable across renders.")
    
    # Initialize state if needed
    if full_state_id not in state:
        stream = Stream(initial_value, name=f"useState({state_id}) at {path_tuple}")
        state[full_state_id] = {
            'stream': stream,
            'initial': copy.deepcopy(initial_value),
            'key': state_id
        }
    
    # Get current state
    state_info = state[full_state_id]
    stream = state_info['stream']
    current_value = stream.value
    
    # Create setter with batching
    def setState(new_value):
        current_value= stream.value
        # Functional update
        if callable(new_value):
            try:
                computed_value = new_value(current_value)
                print(f"functional update: {current_value} -> {computed_value}")
                new_value = computed_value
            except Exception as e:
                print(f"Functional update failed: {e}")
                return # Don't update on error
                 
        # check if value actually changed 
        if current_value == new_value:
            print(f"State unchanged, skipping update: {stream.name} = {new_value}")
            return 
        print(f"Setting state: {stream.name} = {current_value} -> {new_value}")
        # update stream value   
        stream.set(new_value)
        
        # Verify the value was set 
        actual_value = stream.value
        print(f"State  actually set to: {actual_value}")
        
        # trigger re-render: check instance existence safely 
        try:
            wizard= PyUIWizard._current_instance
            if wizard and hasattr(wizard, '_render_trigger'):
                # get component path for the targeted update
                mgr = _get_state_manager()
                current_path = mgr.current_path.copy()
                # store state path for targeted update
                state_info = {
                    'path' : current_path,
                    'stream_name' : stream.name,
                    'value' : new_value,
                    'timestamp': time.time()
                }
                
                wizard._component_update_queue.append(state_info)
                # Atomically increment render trigger 
                old_trigger = wizard._render_trigger.value
                wizard._render_trigger.set(old_trigger+1)
                print(f"Re-render Triggered! (trigger: {old_trigger} -> {old_trigger+1}")
                
            else:
                print(f"Warning ⚠️: No wizard or render trigger available")
        except AttributeError as e:
            print(f"Warning!: Could not trigger re-render: {e}")
           
    # Update hook index for next hook
    mgr.hook_index = hook_index + 1
    
    return [current_value, setState]
        
def useEffect(effect_func, dependencies=None):
    """
    React-like useEffect hook for side effects.
    
    Args:
        effect_func: Function to run as side effect
        dependencies: List of dependencies (None = run on every render)
    """
    mgr = _get_state_manager()
    current_path = mgr.current_path
    if not current_path:
        raise RuntimeError("useEffect must be called within a component")
    
    path_tuple = tuple(current_path)
    hook_index = mgr.hook_index
    
    # Store effect in queue
    effect_id = f"effect_{path_tuple}_{hook_index}"
    mgr.effect_queue.append({
        'id': effect_id,
        'func': effect_func,
        'deps': dependencies,
        'path': path_tuple,
        'hook_index': hook_index
    })
    
    mgr.hook_index += 1

class RefObject:
    """Simple ref object that mimics React's ref.current"""
    def __init__(self, initial_value=None):
        self.current = initial_value
    
    def __repr__(self):
        return f"RefObject(current={self.current})"
        
def useRef(initial_value=None):
    """
    React-like useRef hook for mutable references.
    
    Args:
        initial_value: Initial value for the ref
    
    Returns:
        dict: {current: value}
    """
    mgr= _get_state_manager()
    current_path = mgr.current_path
    if not current_path:
        raise RuntimeError("useRef must be called within a component")
    
    path_tuple = tuple(current_path)
    hook_index = mgr.hook_index
    state = mgr.state
    
    ref_id = f"ref_{path_tuple}_{hook_index}"
    full_id = (path_tuple, ref_id)
    
    if full_id not in state:
        ref_obj = type('RefObject', (), {'current': initial_value})()
        state[full_id] = {
            'ref': ref_obj,
            'type': 'useRef', # mark for clean up
            'initial': initial_value
        
        } 
        #RefObject(initial_value)
    
    mgr.hook_index += 1
    return state[full_id]['ref']

class Context:
    """React-like Context for dependency injection"""
    def __init__(self, default_value=None):
        self.default_value = default_value
        self._subscribers = []
    
    def get(self):
        """Get current context value"""
        registry= _get_context_registry()
        contexts = _context_registry.contexts
        return registry.contexts.get(self, self.default_value)
    
    def set(self, value):
        """Set context value and notify subscribers"""
        registry = _get_context_registry()
        contexts = _context_registry.contexts
        registry.contexts[self] = value
        for callback in self._subscribers:
            try:
                callback(value)
            except:
                pass
    
    def subscribe(self, callback):
        """Subscribe to context changes"""
        self._subscribers.append(callback)
        return lambda: self._subscribers.remove(callback)

def create_context(default_value=None):
    """Create a new context"""
    return Context(default_value)

class Provider:
    """Context provider component"""
    def __init__(self, context, value, children):
        self.context = context
        self.value = value
        self.children = children
    
    def render(self):
        # Set context value during render
        self.context.set(self.value)
        return create_element('frame', {}, *self.children)

def useContext(context):
    """
    React-like useContext hook.
    
    Args:
        context: Context object
    
    Returns:
        Current context value
    """
    mgr = _get_state_manager()
    current_path = mgr.current_path
    if not current_path:
        raise RuntimeError("useContext must be called within a component")
    
    # Subscribe to context changes
    [value, set_value] = useState(context.get(), key=f"context_{id(context)}")
    
    def update_context(new_value):
        set_value(new_value)
    
    # Subscribe once
    hook_index = mgr.hook_index
    path_tuple = tuple(current_path)
    sub_id = f"ctx_sub_{path_tuple}_{hook_index}"
    
    if sub_id not in mgr.state:
        unsubscribe = context.subscribe(update_context)
        # Store Subscription info for Cleanup
        mgr.state[sub_id] = {
            'unsubscribe': unsubscribe,
            'type': 'useContext',
            'context': context
        }
        
    mgr.hook_index += 1
    return value

def _with_hook_rendering(component_class_or_func, props, path):
    """
    Wrapper for component rendering with hook context management.
    """
    # Save previous context
    mgr= _get_state_manager()
    prev_path = mgr.current_path.copy()
    prev_hook_index = mgr.hook_index
    prev_stack = mgr.render_stack.copy()
    
    # Push to render stack
    component_info = {
        'path': path.copy(),
        'key': props.get('key'),
        'type': component_class_or_func.__name__ if hasattr(component_class_or_func, '__name__') else str(component_class_or_func),
        'start_time': time.time()
    }
    
    
    try:
        # Set new context
        mgr.current_path =  [str(p) for p in path]
        mgr.hook_index = 0
        
        
        # Handle class components
        if isinstance(component_class_or_func, type):
            # use combined path and props for instance tracking 
            instance_key = f"{str(path)}_{props.get('key', '')}"
            
            if instance_key not in mgr.component_instances:
                # Create new instance
                component = component_class_or_func(props)
                component._path = tuple(path)
                component._mounted = False
                component._instance_key= instance_key
                mgr.component_instances[instance_key]=component
                
            
            
            component = mgr.component_instances[instance_key]
            # Update props
            component.props = props
            
            # Mount if not mounted
            if not component._mounted:
                component._mounted = True
                component.on_mount()
            
            # Render component
            result = component.render()
        else:
            # Function component
            result = component_class_or_func(props)
        
        return result
        
    finally:
        # Restore previous context
        mgr.current_path = prev_path
        mgr.hook_index = prev_hook_index
        mgr.render_stack = prev_stack

def _flush_effects():
    """Flush all queued effects"""
    mgr= _get_state_manager()
    effects = mgr.effect_queue.copy()
    mgr.effect_queue.clear()
    
    for effect in effects:
        try:
            effect['func']()
        except Exception as e:
            ERROR_BOUNDARY.handle_error(ErrorValue(e, time.time()), f"effect_{effect['id']}")

def clear_component_state(component_path=None, state_key=None):
    """
    Clear component state with thread safety.
    
    Args:
        component_path: Clear state for this path
        state_key: Clear specific state key
    """
    with ThreadSafeMixin().atomic():
        mgr= _get_state_manager()
        state = mgr.state
        instances = mgr.component_instances
        
        if component_path is None and state_key is None:
            # Clear everything
            for state_info in state.values():
                # Dispose streams
                if isinstance(state_info, dict) and 'stream' in state_info:
                    state_info['stream'].dispose()
                # Clear Refs
                elif isinstance(state_info, dict) and state_info.get('type') == 'useRef':
                    state_info['ref'].current= None
                # Unsubscribe from context 
                elif state_info.gey('type') == 'useContext':
                    if 'unsubscribe' in state_info:
                        try:
                            state_info('unsubscribe')()
                        except:
                            pass
            state.clear()
            
            for component in instances.values():
                if hasattr(component, '_unmount'):
                    component._unmount()
            instances.clear()
            
            _get_context_registry().contexts.clear()
            
        elif component_path is not None:
            path_tuple = tuple(component_path)
            # Clear state
            keys_to_remove = []
            for key, state_info in state.items():
                if key[0] == path_tuple and (state_key is None or key[1] == state_key):
                    # dispose base on type 
                    if isinstance(state_info, dict):
                        if 'stream' in state_info:
                            state_info['stream'].dispose()
                        elif state_info.get('type') == 'useRef':
                            state_info['ref'].current = None
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del state[key]
            
            # Clear component instance
            path_key = str(path_tuple)
            if path_key in instances:
                component = instances[path_key]
                if hasattr(component, '_unmount'):
                    component._unmount()
                
                del instances[path_key]

def get_hook_debug_info():
    """Get debugging information about hook state"""
    mgr= _get_state_manager()
    return {
        'current_path': mgr.current_path.copy(),
        'hook_index': mgr.hook_index,
        'render_stack': mgr.render_stack.copy(),
        'state_count': len(mgr.state),
        'component_instances': len(mgr.component_instances),
        'contexts': len(_get_context_registry().contexts),
        'effect_queue': len(mgr.effect_queue)
    }

def validate_vdom(node, path= "root"):
    """ Validate VDOM structure to catch errors early"""
    if node is None:
        print(f" ⚠️ VDOM node is None at: {path} - component returned nothing" )
        return True 
    if not isinstance(node, dict):
        raise TypeError(f"VDOM node at {path} must be dict or None, got {type(node).__name__}")
    if 'type' not in node:
        raise ValueError(f"VDOM node at {path} missing required 'type' field")
    node_type = node['type']
    if not isinstance(node_type, (str, type)) and not callable(node_type):
        raise TypeError(f"VDOM type at {path} must be str, class or callable, got {type(node_type).__name__}")
    if 'props' in node and not isinstance(node['props'], dict):
        raise TypeError(f"VDOM props at {path} must be dict, got {type(node['props']).__name__}")
    if 'children' in node:
        if not isinstance(node['children'], list):
            raise TypeError(f"VDOM children at {path} must be list, got {type(node['children']).__name__}")
        for i, child in enumerate(node['children']):
            validate_vdom(child, f"{path}. children[{i}]")
    return True 

# ===============================
# Complete Widget Factory
# ===============================
class WidgetFactory:
    """Factory for creating all Tkinter widgets with full accessibility support"""
    
    # ARIA role mapping
    ARIA_ROLES = {
        'button': 'button',
        'entry': 'textbox',
        'label': 'label',
        'checkbox': 'checkbox',
        'radio': 'radio',
        'listbox': 'listbox',
        'combobox': 'combobox',
        'progressbar': 'progressbar',
        'slider': 'slider',
        'tab': 'tab',
        'menuitem': 'menuitem'
    }
    
    @staticmethod
    def create_widget(node_type: str, parent, props: Dict) -> Optional[tk.Widget]:
        """Create widget with accessibility support"""
        if threading.current_thread() is not threading.main_thread():
            print(f"Warning: Creating widget {node_type} from non-main thread. This may cause issues.")
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
            'spinbox': WidgetFactory._create_spinbox,
            'treeview': WidgetFactory._create_treeview,
            'notebook': WidgetFactory._create_notebook,
            'labelframe': WidgetFactory._create_labelframe,
            'panedwindow': WidgetFactory._create_panedwindow,
        }
        
        creator = creators.get(node_type, WidgetFactory._create_frame)
        widget = creator(parent, props)
        
        # Apply accessibility attributes
        if widget:
            WidgetFactory._apply_accessibility(widget, node_type, props)
        
        return widget
    
    @staticmethod
    def _apply_accessibility(widget, widget_type: str, props: Dict):
        """Apply ARIA attributes and accessibility features"""
        try:
            # ARIA role
            role = WidgetFactory.ARIA_ROLES.get(widget_type, 'widget')
            
            # ARIA labels
            aria_label = props.get('aria-label') or props.get('text', '')
            if aria_label:
                widget.tk.call('tk', 'window', 'accessibility', widget._w, 'description', aria_label)
            
            # Tab order
            tab_index = props.get('tabindex')
            if tab_index is not None:
                widget.tk.call('tk', 'window', 'accessibility', widget._w, 'tabindex', tab_index)
            
            # Keyboard shortcuts
            access_key = props.get('accesskey')
            if access_key:
                widget.bind(f'<Alt-Key-{access_key}>', lambda e: widget.focus_set())
            
            # Screen reader hints
            if props.get('aria-hidden') == 'true':
                widget.tk.call('tk', 'window', 'accessibility', widget._w, 'hidden', 1)
            
        except:
            # Tk accessibility might not be available on all platforms
            pass
    
    @staticmethod
    def _create_frame(parent, props):
        bg = props.get('bg', 'white')
        frame = tk.Frame(
            parent,
            bg=bg,
            relief=props.get('relief', 'flat'),
            bd=props.get('border_width', 0),
            highlightthickness=props.get('highlightthickness', 0)
        )
        
        if props.get('width'):
            frame.config(width=props['width'])
        if props.get('height'):
            frame.config(height=props['height'])
        if props.get('cursor'):
            frame.config(cursor=props['cursor'])
        
        # Border radius simulation
        border_radius = props.get('border_radius', 0)
        if border_radius > 0:
            # best approximation: Add border with padding 
            border_color = props.get('border_color', '#666666')
            frame.config(
                relief= 'solid',
                bd=min(2, border_radius//2), # Scale border width with radius 
                padx=max(1, border_radius//4),
                pady=max(1, border_radius//4),
                  highlightbackground=border_color,    highlightcolor=border_color,
                highlightthickness=1
            )
            # Store radius for potential future use 
            frame._border_radius= border_radius
        
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
            anchor=props.get('anchor', 'w'),
            wraplength=props.get('wraplength', 0),
            underline=props.get('underline', -1)
        )
        
        if props.get('width'):
            label.config(width=props['width'])
        if props.get('height'):
            label.config(height=props['height'])
        if props.get('image'):
            label.config(image=props['image'])
        
        # Ellipsis for overflow
        if props.get('ellipsis'):
            def update_text():
                text = label.cget('text')
                if len(text) > props.get('max_chars', 50):
                    label.config(text=text[:props.get('max_chars', 50)-3] + '...')
            label.after(10, update_text)
        
        return label
    
    @staticmethod
    def _create_button(parent, props):
        font_size = props.get('font_size', 10)
        font_family = props.get('font_family', 'Arial')
        font = (font_family, font_size)
        # Get onClick Handler
        onClick= props.get('onClick')
        button = tk.Button(
            parent,
            text=props.get('text', ''),
            fg=props.get('fg', 'white'),
            bg=props.get('bg', 'gray'),
            activebackground=props.get('active_bg', props.get('bg', 'gray')),
            activeforeground=props.get('active_fg', props.get('fg', 'white')),
            command= lambda: onClick() if onClick else None,
            font=font,
            relief=props.get('relief', 'flat'),
            cursor=props.get('cursor', 'hand2'),
            state=props.get('state', 'normal'),
            compound=props.get('compound', 'none'),
            overrelief=props.get('overrelief', 'raised')
        )
        
        if props.get('width'):
            button.config(width=props['width'])
        if props.get('height'):
            button.config(height=props['height'])
        if props.get('image'):
            button.config(image=props['image'])
        
        # Bind Enter key for accessibility
        button.bind('<Return>', lambda e: button.invoke() if button['state'] == 'normal' else None)
        
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
            show=props.get('show', ''),  # For password fields
            width=props.get('width', 20),
            justify=props.get('justify', 'left'),
            validate=props.get('validate', 'none'),
            validatecommand=props.get('validatecommand'),
            insertbackground=props.get('cursor_color', 'black')
        )
        
        if 'text' in props:
            entry.delete(0, tk.END)
            entry.insert(0, props['text'])
        
        if 'placeholder' in props:
            def add_placeholder():
                if entry.get() == '':
                    entry.insert(0, props['placeholder'])
                    entry.config(fg='gray')
            
            def remove_placeholder(event):
                if entry.get() == props['placeholder']:
                    entry.delete(0, tk.END)
                    entry.config(fg=props.get('fg', 'black'))
            
            def restore_placeholder(event):
                if entry.get() == '':
                    entry.insert(0, props['placeholder'])
                    entry.config(fg='gray')
            
            entry.bind('<FocusIn>', remove_placeholder)
            entry.bind('<FocusOut>', restore_placeholder)
            add_placeholder()
        
        if 'onChange' in props:
            def on_change(event):
                if props.get('placeholder') and entry.get() == props['placeholder']:
                    return
                props['onChange'](entry.get())
            entry.bind('<KeyRelease>', on_change)
        
        if 'onSubmit' in props:
            entry.bind('<Return>', lambda e: props['onSubmit'](entry.get()))
        
        return entry
    
    @staticmethod
    def _create_text(parent, props):
        text_widget = scrolledtext.ScrolledText(
            parent,
            bg=props.get('bg', 'white'),
            fg=props.get('fg', 'black'),
            font=(props.get('font_family', 'Arial'), props.get('font_size', 10)),
            wrap=props.get('wrap', 'word'),
            state=props.get('state', 'normal'),
            width=props.get('width', 50),
            height=props.get('height', 10),
            undo=props.get('undo', True),
            maxundo=props.get('maxundo', 1000)
        )
        
        if 'text' in props:
            text_widget.delete('1.0', tk.END)
            text_widget.insert('1.0', props['text'])
        
        if 'onChange' in props:
            def on_change(event):
                props['onChange'](text_widget.get('1.0', 'end-1c'))
            text_widget.bind('<KeyRelease>', on_change)
        
        # Syntax highlighting for code
        if props.get('language') == 'python':
            WidgetFactory._setup_python_syntax(text_widget)
        
        return text_widget
    
    @staticmethod
    def _setup_python_syntax(text_widget):
        """Setup basic Python syntax highlighting"""
        keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 
                   'import', 'from', 'as', 'try', 'except', 'finally', 
                   'return', 'yield', 'async', 'await', 'with']
        
        def highlight(event=None):
            # Remove previous tags
            text_widget.tag_remove('keyword', '1.0', tk.END)
            text_widget.tag_remove('string', '1.0', tk.END)
            text_widget.tag_remove('comment', '1.0', tk.END)
            
            # Get text
            text = text_widget.get('1.0', tk.END)
            
            # Highlight keywords
            for keyword in keywords:
                start = '1.0'
                while True:
                    start = text_widget.search(r'\b' + keyword + r'\b', start, stopindex=tk.END, regexp=True)
                    if not start:
                        break
                    end = f'{start}+{len(keyword)}c'
                    text_widget.tag_add('keyword', start, end)
                    start = end
            
            # Configure tags
            text_widget.tag_config('keyword', foreground='blue', font=('Courier', 10, 'bold'))
            text_widget.tag_config('string', foreground='green')
            text_widget.tag_config('comment', foreground='gray')
        
        text_widget.bind('<KeyRelease>', highlight)
        text_widget.after(100, highlight)
    
    @staticmethod
    def _create_canvas(parent, props):
        canvas = tk.Canvas(
            parent,
            bg=props.get('bg', 'white'),
            width=props.get('width', 300),
            height=props.get('height', 200),
            relief=props.get('relief', 'flat'),
            bd=props.get('border_width', 0),
            highlightthickness=0,
            scrollregion=props.get('scrollregion')
        )
        
        if 'onDraw' in props:
            props['onDraw'](canvas)
        
        # Add scrollbars if requested
        if props.get('scrollable'):
            h_scroll = tk.Scrollbar(parent, orient='horizontal', command=canvas.xview)
            v_scroll = tk.Scrollbar(parent, orient='vertical', command=canvas.yview)
            canvas.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
            h_scroll.pack(side='bottom', fill='x')
            v_scroll.pack(side='right', fill='y')
        
        return canvas
    
    @staticmethod
    def _create_listbox(parent, props):
        listbox = tk.Listbox(
            parent,
            bg=props.get('bg', 'white'),
            fg=props.get('fg', 'black'),
            font=(props.get('font_family', 'Arial'), props.get('font_size', 10)),
            selectmode=props.get('selectmode', 'single'),
            relief=props.get('relief', 'sunken'),
            height=props.get('height', 10),
            activestyle=props.get('activestyle', 'dotbox')
        )
        
        if 'items' in props:
            for item in props['items']:
                listbox.insert('end', item)
        
        if 'onSelect' in props:
            def on_select(event):
                if listbox.curselection():
                    props['onSelect'](listbox.get(listbox.curselection()[0]))
            listbox.bind('<<ListboxSelect>>', on_select)
        
        if 'onDoubleClick' in props:
            listbox.bind('<Double-Button-1>', lambda e: props['onDoubleClick']())
        
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
            command=lambda: props.get('onChange', lambda x: None)(var.get()),
            indicatoron=props.get('indicatoron', True),
            selectcolor=props.get('selectcolor', 'light blue')
        )
        
        # Store variable reference
        checkbox._py_var = var
        
        # Bind space key for accessibility
        checkbox.bind('<space>', lambda e: var.set(not var.get()))
        
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
            command=lambda: props.get('onChange', lambda x: None)(var.get()),
            indicatoron=props.get('indicatoron', True),
            selectcolor=props.get('selectcolor', 'light blue')
        )
        
        radio._py_var = var
        radio.bind('<space>', lambda e: var.set(props.get('option_value', '')))
        
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
            command=lambda val: props.get('onChange', lambda x: None)(float(val)),
            length=props.get('width', 200),
            showvalue=props.get('showvalue', True),
            tickinterval=props.get('tickinterval'),
            resolution=props.get('resolution', 1),
            sliderlength=props.get('sliderlength', 30)
        )
        
        if 'value' in props:
            scale.set(props['value'])
        
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
            state=props.get('state', 'readonly'),
            height=props.get('height', 10),
            width=props.get('width', 20)
        )
        
        if 'value' in props:
            combobox.set(props['value'])
        
        if 'onChange' in props:
            combobox.bind('<<ComboboxSelected>>', 
                         lambda e: props['onChange'](combobox.get()))
        
        if 'onType' in props:
            combobox.bind('<KeyRelease>', 
                         lambda e: props['onType'](combobox.get()))
        
        return combobox
    
    @staticmethod
    def _create_progressbar(parent, props):
        progressbar = ttk.Progressbar(
            parent,
            orient=props.get('orient', 'horizontal'),
            mode=props.get('mode', 'determinate'),
            maximum=props.get('max', 100),
            value=props.get('value', 0),
            length=props.get('width', 200)
        )
        
        # Pulse animation for indeterminate mode
        if props.get('mode') == 'indeterminate' and props.get('animated', True):
            progressbar.start(50)
        
        return progressbar
    
    @staticmethod
    def _create_separator(parent, props):
        separator = ttk.Separator(
            parent,
            orient=props.get('orient', 'horizontal')
        )
        
        return separator
    
    @staticmethod
    def _create_spinbox(parent, props):
        spinbox = tk.Spinbox(
            parent,
            from_=props.get('min', 0),
            to=props.get('max', 100),
            bg=props.get('bg', 'white'),
            fg=props.get('fg', 'black'),
            font=(props.get('font_family', 'Arial'), props.get('font_size', 12)),
            width=props.get('width', 10)
        )
        
        if 'value' in props:
            spinbox.delete(0, tk.END)
            spinbox.insert(0, str(props['value']))
        
        if 'onChange' in props:
            spinbox.bind('<<Increment>>', lambda e: props['onChange'](spinbox.get()))
            spinbox.bind('<<Decrement>>', lambda e: props['onChange'](spinbox.get()))
        
        return spinbox
    
    @staticmethod
    def _create_treeview(parent, props):
        treeview = ttk.Treeview(
            parent,
            columns=props.get('columns', []),
            height=props.get('height', 10),
            selectmode=props.get('selectmode', 'extended')
        )
        
        # Configure columns
        for col in props.get('columns', []):
            treeview.heading(col, text=col)
            treeview.column(col, width=100)
        
        # Add data
        for item in props.get('data', []):
            treeview.insert('', 'end', values=item)
        
        if 'onSelect' in props:
            def on_select(event):
                selection = treeview.selection()
                if selection:
                    props['onSelect'](treeview.item(selection[0]))
            treeview.bind('<<TreeviewSelect>>', on_select)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(parent, orient='vertical', command=treeview.yview)
        treeview.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        
        return treeview
    
    @staticmethod
    def _create_notebook(parent, props):
        notebook = ttk.Notebook(parent)
        
        for tab in props.get('tabs', []):
            frame = tk.Frame(notebook)
            notebook.add(frame, text=tab.get('title', 'Tab'))
        
        if 'onTabChange' in props:
            notebook.bind('<<NotebookTabChanged>>', 
                         lambda e: props['onTabChange'](notebook.index(notebook.select())))
        
        return notebook
    
    @staticmethod
    def _create_labelframe(parent, props):
        labelframe = tk.LabelFrame(
            parent,
            text=props.get('text', ''),
            bg=props.get('bg', 'white'),
            fg=props.get('fg', 'black'),
            font=(props.get('font_family', 'Arial'), props.get('font_size', 10)),
            relief=props.get('relief', 'groove'),
            bd=props.get('border_width', 2)
        )
        
        return labelframe
    
    @staticmethod
    def _create_panedwindow(parent, props):
        panedwindow = tk.PanedWindow(
            parent,
            orient=props.get('orient', 'horizontal'),
            bg=props.get('bg', 'gray'),
            sashwidth=props.get('sashwidth', 5),
            sashrelief=props.get('sashrelief', 'raised'),
            showhandle=props.get('showhandle', False)
        )
        
        return panedwindow
    
    @staticmethod
    def update_widget_prop(widget, prop: str, value):
        """Update a widget property with comprehensive support"""
        widget_type = widget.__class__.__name__
        # check if value actually changed 
        try:
            current=getattr(widget, prop, None)
            if current ==value :
                return 
        except:
             pass     
        # Common properties for all widgets
        common_props = {
            'bg': lambda w, v: w.config(bg=v) if hasattr(w, 'config') else None,
            'fg': lambda w, v: w.config(fg=v) if hasattr(w, 'config') else None,
            'width': lambda w, v: w.config(width=v) if hasattr(w, 'config') else None,
            'height': lambda w, v: w.config(height=v) if hasattr(w, 'config') else None,
            'relief': lambda w, v: w.config(relief=v) if hasattr(w, 'config') else None,
            'state': lambda w, v: w.config(state=v) if hasattr(w, 'config') else None,
            'cursor': lambda w, v: w.config(cursor=v) if hasattr(w, 'config') else None,
            'font_size': lambda w, v: WidgetFactory._update_font_size(w, v),
            'font_weight': lambda w, v: WidgetFactory._update_font_weight(w, v),
            'font_family': lambda w, v: WidgetFactory._update_font_family(w, v),
        }
        # Text-based widget properties
        text_props = {
            'text': lambda w, v: w.config(text=str(v)),
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
            except Exception as e:
                print(f"Failed to update {prop}: {e}")
        
        # Try text props
        if widget_type in ['Label', 'Button', 'Entry', 'Text', 'Checkbutton', 'Radiobutton'] and prop in text_props:
            try:
                print(f"Updating on {widget_type} to {value}")
                text_props[prop](widget, value)
                print(f"Text updated successfully ")
                return
            except Exception as e:
                print(f"Failed to update text: {e}")
        
        # Try button props
        if widget_type == 'Button' and prop in button_props:
            try:
                button_props[prop](widget, value)
                return
            except Exception as e:
                print(f"failed to update button prop {prop}: {e}")
        
        # Try entry props
        if widget_type == 'Entry' and prop in entry_props:
            try:
                entry_props[prop](widget, value)
                return
            except Exception as e:
                print(f"Failed to update entry prop {prop}: {e}")
        
        # Handle border_width specially
        if prop == 'border_width':
            try:
                if value > 0:
                    widget.config(relief='solid', bd=value)
                else:
                    widget.config(relief='flat', bd=0)
            except:
                pass
        
        # Handle ARIA attributes
        if prop.startswith('aria-'):
            try:
                aria_prop = prop[5:]  # Remove 'aria-' prefix
                if aria_prop == 'label':
                    widget.tk.call('tk', 'window', 'accessibility', widget._w, 'description', value)
            except:
                pass
        
        # Handle data attributes
        if prop.startswith('data-'):
            # Store custom data attributes
            if not hasattr(widget, '_custom_data'):
                widget._custom_data = {}
            widget._custom_data[prop] = value
    
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
    """Handle all layout managers: pack, grid, place with CSS flexbox-like support"""
    
    @staticmethod
    def apply_layout(widget, node: Dict, parent, position):
        """Apply layout with support for pack, grid, and place"""
        props = node.get('props', {})
        layout_type = props.get('layout_manager', 'pack')
        
        if layout_type == 'grid':
            LayoutManager._apply_grid(widget, props, position)
        elif layout_type == 'place':
            LayoutManager._apply_place(widget, props)
        elif layout_type == 'flex':
            LayoutManager._apply_flex(widget, props, position)
        else:
            LayoutManager._apply_pack(widget, props, position)
    
    @staticmethod
    def _apply_pack(widget, props, position):
        """Apply pack layout with CSS-like options"""
        pack_opts = {
            'side': props.get('side', 'top'),
            'padx': props.get('padx', 0),
            'pady': props.get('pady', 0),
            'fill': props.get('fill', 'none'),
            'expand': props.get('expand', False),
            'anchor': props.get('anchor', 'center'),
            'ipadx': props.get('ipadx', 0),
            'ipady': props.get('ipady', 0)
        }
        
        # CSS-like width/height
        if props.get('width_full'):
            pack_opts['fill'] = 'x'
        if props.get('height_full'):
            pack_opts['fill'] = 'y'
        if props.get('fill_both'):
            pack_opts['fill'] = 'both'
            pack_opts['expand'] = True
        
        # CSS margin
        margin = props.get('margin', 0)
        if isinstance(margin, (int, float)):
            pack_opts['padx'] = margin
            pack_opts['pady'] = margin
        elif isinstance(margin, dict):
            pack_opts['padx'] = margin.get('x', 0)
            pack_opts['pady'] = margin.get('y', 0)
        
        widget.pack(**pack_opts)
    
    @staticmethod
    def _apply_grid(widget, props, position):
        """Apply grid layout with CSS grid-like features"""
        # Handle position: Could be int, str(key) or specified in props
        row=props.get('row')
        column=props.get('column')
        # if row is not specified : try to drive from position 
        if row is None:
            if isinstance(position, int):
                row=position 
            elif isinstance(position, str):
                row=int(position)
            else:
                # for keyed children , use a counter or hash
                row=hash(str(position))%100 # Keep in reasonable range 
        # if column not specified, default to 0
        if column is None:
            column=0
        
        grid_opts = {
            'row': int(row),
            'column': int(column),
            'rowspan': props.get('rowspan', 1),
            'columnspan': props.get('columnspan', 1),
            'padx': props.get('padx', 0),
            'pady': props.get('pady', 0),
            'sticky': props.get('sticky', ''),
            'ipadx': props.get('ipadx', 0),
            'ipady': props.get('ipady', 0)
        }
        
        # Convert CSS sticky to Tkinter sticky
        sticky_map = {
            'top': 'n',
            'bottom': 's',
            'left': 'w',
            'right': 'e',
            'center': '',
            'top left': 'nw',
            'top right': 'ne',
            'bottom left': 'sw',
            'bottom right': 'se'
        }
        
        sticky = props.get('sticky', '').lower()
        if sticky in sticky_map:
            grid_opts['sticky'] = sticky_map[sticky]
        
        try:
            widget.grid(**grid_opts)
        except Exception as e:
            print(f"Grid layout failed {e}: falling back to pack")
            widget.pack(side='top', padx=5, pady=5)
    
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
        if 'width' in props:
            place_opts['width'] = props['width']
        if 'height' in props:
            place_opts['height'] = props['height']
        
        widget.place(**place_opts)
    
    @staticmethod
    def _apply_flex(widget, props, position):
        """Apply flexbox-like layout"""
        direction = props.get('flex_direction', 'row')
        justify = props.get('justify_content', 'flex-start')
        align = props.get('align_items', 'stretch')
        
        # Convert flexbox to pack options
        pack_opts = {}
        
        if direction == 'row':
            pack_opts['side'] = 'left'
        elif direction == 'row-reverse':
            pack_opts['side'] = 'right'
        elif direction == 'column':
            pack_opts['side'] = 'top'
        elif direction == 'column-reverse':
            pack_opts['side'] = 'bottom'
        
        # Justify content
        if justify == 'center':
            pack_opts['anchor'] = 'center'
        elif justify == 'flex-end':
            pack_opts['anchor'] = 'e' if direction.startswith('row') else 's'
        elif justify == 'space-between':
            # Tkinter doesn't have exact equivalent
            pass
        
        # Align items
        if align == 'center':
            if direction.startswith('row'):
                pack_opts['anchor'] = 'center'
        elif align == 'flex-start':
            pass
        elif align == 'flex-end':
            if direction.startswith('row'):
                pack_opts['anchor'] = 's'
        
        # Flex grow/shrink
        if props.get('flex_grow', 0) > 0:
            pack_opts['fill'] = 'both'
            pack_opts['expand'] = True
        
        # Apply padding/margin
        pack_opts['padx'] = props.get('padx', 0)
        pack_opts['pady'] = props.get('pady', 0)
        
        widget.pack(**pack_opts)
    
    @staticmethod
    def update_layout(widget, props: Dict):
        """Update widget layout based on new props"""
        # Unpack first
        widget.pack_forget()
        
        # Reapply layout
        LayoutManager.apply_layout(widget, {'props': props}, widget.master, 0)

# ===============================
# Complete Event System
# ===============================
class EventSystem:
    """Comprehensive event handling system with event delegation"""
    
    # Event type mapping
    EVENT_MAP = {
        'onClick': '<Button-1>',
        'onDoubleClick': '<Double-Button-1>',
        'onRightClick': '<Button-3>',
        'onMouseEnter': '<Enter>',
        'onMouseLeave': '<Leave>',
        'onMouseMove': '<Motion>',
        'onMouseDown': '<ButtonPress>',
        'onMouseUp': '<ButtonRelease>',
        'onMouseWheel': '<MouseWheel>',
        'onFocus': '<FocusIn>',
        'onBlur': '<FocusOut>',
        'onKeyPress': '<KeyPress>',
        'onKeyRelease': '<KeyRelease>',
        'onKeyDown': '<KeyPress>',
        'onKeyUp': '<KeyRelease>',
        'onChange': '<KeyRelease>',
        'onSubmit': '<Return>',
        'onEscape': '<Escape>',
        'onTab': '<Tab>',
        'onShiftTab': '<Shift-Tab>',
        'onDragStart': '<B1-Motion>',
        'onDrag': '<B1-Motion>',
        'onDragEnd': '<ButtonRelease-1>',
        'onDrop': '<ButtonRelease-1>',
        'onResize': '<Configure>',
    }
    
    # Event pool for performance
    _event_pool = {}
    
    @staticmethod
    def bind_events(widget, props: Dict):
        """Bind all events from props to widget with event pooling"""
        for prop_name, tk_event in EventSystem.EVENT_MAP.items():
            if prop_name in props:
                handler = props[prop_name]
                
                # Special handling for different event types
                if prop_name == 'onClick' and hasattr(widget, 'config'):
                    # Buttons use command instead of binding
                    if isinstance(widget, tk.Button):
                        widget.config(command=handler)
                        continue
                
                elif prop_name == 'onChange':
                    if isinstance(widget, (tk.Entry, scrolledtext.ScrolledText)):
                        widget.bind(tk_event, 
                                   lambda e, h=handler: h(widget.get() if isinstance(widget, tk.Entry) 
                                                         else widget.get('1.0', 'end-1c')))
                        continue
                
                elif prop_name == 'onSubmit':
                    if isinstance(widget, tk.Entry):
                        widget.bind(tk_event, lambda e, h=handler: h(widget.get()))
                        continue
                
                elif prop_name == 'onMouseWheel':
                    # Cross-platform mouse wheel
                    widget.bind(tk_event, handler)
                    widget.bind('<Button-4>', handler)  # Linux up
                    widget.bind('<Button-5>', handler)  # Linux down
                    continue
                
                # Standard event binding with event pooling
                event_id = f"{id(widget._w)}_{tk_event}"
                # clear old handlers first 
                if event_id in EventSystem._event_pool:
                    # unbind old handlers 
                    for old_handler in EventSystem._event_pool[event_id]:
                        try:
                            widget.unbind(tk_event, old_handler)
                        except:
                            pass
                    # Clear the pool for this event 
                    EventSystem._event_pool[event_id].clear()
                else:
                    EventSystem._event_pool[event_id] = []
                # Create wrapped handler with event normalization
                def create_handler(h):
                    def wrapped_handler(event):
                        # Normalize event object
                        normalized_event = {
                            'type': prop_name,
                            'target': widget,
                            'timeStamp': time.time(),
                            'nativeEvent': event,
                            'key': getattr(event, 'keysym', None),
                            'button': getattr(event, 'num', 1),
                            'x': getattr(event, 'x', 0),
                            'y': getattr(event, 'y', 0),
                            'ctrlKey': bool(event.state & 0x0004),
                            'shiftKey': bool(event.state & 0x0001),
                            'altKey': bool(event.state & 0x20000),
                            'metaKey': bool(event.state & 0x040000),
                        }
                        # Call handler with normalized event
                        return h(normalized_event)
                    return wrapped_handler
                
                wrapped_handler = create_handler(handler)
                EventSystem._event_pool[event_id].append(wrapped_handler)
                widget.bind(tk_event, wrapped_handler)
    
    @staticmethod
    def unbind_events(widget, props: Dict):
        """Unbind events from widget"""
        for prop_name, tk_event in EventSystem.EVENT_MAP.items():
            if prop_name in props:
                try:
                    event_id = f"{id(widget._w)}_{tk_event}"
                    if event_id in EventSystem._event_pool:
                        for handler in EventSystem._event_pool[event_id]:
                            widget.unbind(tk_event, handler)
                        del EventSystem._event_pool[event_id]
                except:
                    pass
    
    @staticmethod
    def cleanup_widget_events(widget):
        """ clean up all events for a destroyed widget"""
        # find all event IDs for this widget 
        widget_id = widget._w
        keys_to_remove = []
        
        for event_id in list(EventSystem._event_pool.keys()):
            # event_id format: "widget_id_event_type"
            if event_id.startswith(f"{widget_id}_"):
                keys_to_remove.append(event_id)
                
        # remove from pool
        for key in keys_to_remove:
             del EventSystem._event_pool[key]
        
    @staticmethod
    def create_custom_event(event_type: str, data: Dict = None):
        """Create a custom event"""
        return {
            'type': event_type,
            'data': data or {},
            'timeStamp': time.time(),
            'isTrusted': True,
            'cancelable': True,
            'defaultPrevented': False
        }
    
    @staticmethod
    def prevent_default(event):
        """Prevent default behavior (if applicable)"""
        event['defaultPrevented'] = True
        if 'nativeEvent' in event:
            event['nativeEvent'].widget.break_propagate = True
    
    @staticmethod
    def stop_propagation(event):
        """Stop event propagation"""
        if 'nativeEvent' in event:
            event['nativeEvent'].widget.break_propagate = True

# ===============================
# Complete VDOM Tree Tracker
# ===============================
class VDOMTreeTracker:
    """Track the complete VDOM tree structure with circular reference detection"""
    
    def __init__(self):
        self.tree = None
        self.node_map = {}  # path -> node
        self.key_map = {}   # key -> node
        self.parent_map = {}  # node -> parent
        self.depth_map = {}   # node -> depth
        self._lock = threading.RLock()
        self.max_depth = 1000  # Prevent infinite recursion
    
    def update(self, vdom: Dict):
        """Update the tracked VDOM tree with circular reference check"""
        with self._lock:
            self.tree = vdom
            self.node_map.clear()
            self.key_map.clear()
            self.parent_map.clear()
            self.depth_map.clear()
            self._index_tree(vdom, [], None, 0)
    
    def _index_tree(self, node: Dict, path: List, parent: Optional[Dict], depth: int):
        """Recursively index the tree with depth limiting"""
        # Check Depth First, before any other operations 
        if depth > self.max_depth:
            raise RuntimeError(f"VDOM tree depth exceeded maximum ({self.max_depth})")
        # validate node is a dict
        if not isinstance(node, dict):
            return 
        
        path_key = tuple(path)
        self.node_map[path_key] = node
        self.depth_map[path_key] = depth
        
        if parent:
            self.parent_map[path_key] = tuple(path[:-1]) if path else None
        
        if 'key' in node:
            self.key_map[node['key']] = node
        
        for i, child in enumerate(node.get('children', [])):
            child_path = path + [child.get('key', i)]
            self._index_tree(child, child_path, node, depth + 1)
    
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
        with self._lock:
            parent_path = self.parent_map.get(tuple(path))
            if parent_path is not None:
                return self.node_map.get(parent_path)
            return None
    
    def get_children(self, path: List) -> List[Dict]:
        """Get child nodes"""
        with self._lock:
            node = self.get_node(path)
            if node:
                return node.get('children', [])
            return []
    
    def get_depth(self, path: List) -> int:
        """Get depth of node"""
        with self._lock:
            return self.depth_map.get(tuple(path), 0)
    
    def find_nodes(self, predicate: Callable) -> List[Dict]:
        """Find all nodes matching predicate"""
        with self._lock:
            results = []
            for path, node in self.node_map.items():
                if predicate(node, list(path)):
                    results.append((list(path), node))
            return results
    
    def serialize(self) -> Dict:
        """Serialize VDOM tree for debugging"""
        with self._lock:
            return {
                'tree': copy.deepcopy(self.tree),
                'node_count': len(self.node_map),
                'key_count': len(self.key_map),
                'max_depth': max(self.depth_map.values()) if self.depth_map else 0
            }

# ===============================
# Thread Safety Decorator for Tkinter
# ===============================
def ensure_main_thread(func):
    """Decorator to ensure function runs on main thread for Tkinter safety."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if threading.current_thread() is threading.main_thread():
            # Already on main thread, execute directly
            return func(self, *args, **kwargs)
        else:
            # We're on a background thread - need to schedule on main thread
            result = [None]
            exception = [None]
            done = [False]
            
            def run_on_main():
                try:
                    result[0] = func(self, *args, **kwargs)
                except Exception as e:
                    exception[0] = e
                finally:
                    done[0] = True
            
            # Try to get root widget from various sources
            root_widget = None
            
            # Check if first arg is a widget
            if args and hasattr(args[0], 'after'):
                root_widget = args[0]
            # Check if self has root or a widget map
            elif hasattr(self, 'widget_map') and self.widget_map:
                # Get any widget from the map
                first_widget = next(iter(self.widget_map.values()), None)
                if first_widget and hasattr(first_widget, 'winfo_toplevel'):
                    root_widget = first_widget.winfo_toplevel()
            
            if root_widget:
                # Schedule on main thread
                root_widget.after(0, run_on_main)
                
                # Wait for completion (with timeout to prevent deadlock)
                timeout = 5.0  # 5 second timeout
                start_time = time.time()
                while not done[0] and (time.time() - start_time) < timeout:
                    time.sleep(0.001)
                
                if not done[0]:
                    raise RuntimeError(f"Timeout waiting for {func.__name__} to execute on main thread")
                
                if exception[0]:
                    raise exception[0]
                return result[0]
            else:
                # No root widget available, execute anyway
                return func(self, *args, **kwargs)
    
    return wrapper
    
# ===============================
# Thread Safety for Tkinter Operations
# ===============================
def safe_widget_operation(widget, operation, *args, **kwargs):
    """
    Safely execute a widget operation, ensuring it runs on the main thread.
    
    Args:
        widget: The Tkinter widget
        operation: String name of the operation (e.g., 'destroy', 'config')
        *args, **kwargs: Arguments to pass to the operation
    
    Returns:
        The result of the operation, or None if it fails
    """
    if not widget or not hasattr(widget, operation):
        return None
    
    if threading.current_thread() is threading.main_thread():
        # Already on main thread, execute directly
        try:
            method = getattr(widget, operation)
            return method(*args, **kwargs)
        except Exception as e:
            print(f"⚠️  Widget operation '{operation}' failed: {e}")
            return None
    else:
        # We're on a background thread - schedule on main thread
        result = [None]
        exception = [None]
        
        def run_on_main():
            try:
                method = getattr(widget, operation)
                result[0] = method(*args, **kwargs)
            except Exception as e:
                exception[0] = e
        
        # Try to schedule on main thread
        try:
            if hasattr(widget, 'after'):
                widget.after(0, run_on_main)
            elif hasattr(widget, 'winfo_toplevel'):
                root = widget.winfo_toplevel()
                if root and hasattr(root, 'after'):
                    root.after(0, run_on_main)
                else:
                    # Can't schedule, execute anyway
                    method = getattr(widget, operation)
                    return method(*args, **kwargs)
            else:
                # Fallback: just execute it
                method = getattr(widget, operation)
                return method(*args, **kwargs)
        except Exception as e:
            print(f"⚠️  Could not schedule widget operation: {e}")
            return None
        
        # Give it a moment to execute
        time.sleep(0.001)
        
        if exception[0]:
            print(f"⚠️  Widget operation '{operation}' failed: {exception[0]}")
        
        return result[0]


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
        self.batch_updates = False
        self.pending_updates = []
        
    @ensure_main_thread
    @PERFORMANCE.measure_time('apply_patches')
    def apply_patches(self, patches: List[Dict], vdom: Dict, root_widget):
        """Apply patches using map and filter with complete tracking"""
        with self._lock:
            # Update VDOM tree tracking
            self.vdom_tracker.update(vdom)
            
            # Group patches by type for optimal application order
            grouped = defaultdict(list)
            for patch in patches:
                grouped[patch['type']].append(patch)
            
            # Apply in optimal order: remove, reorder, create, update, replace
            self._apply_batch_operations(grouped.get(DiffType.REMOVE, []), root_widget, 'remove')
            self._apply_batch_operations(grouped.get(DiffType.REORDER, []), root_widget, 'reorder')
            self._apply_batch_operations(grouped.get(DiffType.MOVE, []), root_widget, 'move')
            self._apply_batch_operations(grouped.get(DiffType.CREATE, []), root_widget, 'create')
            self._apply_batch_operations(grouped.get(DiffType.UPDATE, []), root_widget, 'update')
            self._apply_batch_operations(grouped.get(DiffType.REPLACE, []), root_widget, 'replace')
            
            # Process any pending updates
            if self.pending_updates:
                self._process_pending_updates(root_widget)
    
    def _apply_batch_operations(self, patches: List[Dict], root_widget, op_type: str):
        """Apply a batch of operations of the same type"""
        for patch in patches:
            try:
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
                elif op_type == 'move':
                    self._apply_move(patch, root_widget)
            except Exception as e:
                ERROR_BOUNDARY.handle_error(ErrorValue(e, time.time(), patch), f"patcher_{op_type}")
    
    def _apply_remove(self, patch: Dict, root_widget):
        """Apply REMOVE patch with recursive cleanup"""
        path = patch['path']
        widget = self._get_widget_by_path(path, root_widget)
        
        if widget:
            # Cleanup mappings before destroying widget 
            path_key = tuple(path)
            # Store widget info before cleanup
            widget_key = self.widget_to_key.get(widget)
            
            # Recursively clean up all children
            self._recursive_cleanup(widget, path)
            # Remove from all mappings before destroying 
            self._cleanup_widget_mappings(widget, path)
            # Clear component state
            clear_component_state(component_path=path)
            
            # Destroy widget (thread-safe)
            safe_widget_operation(widget, 'destroy')
            print(f"✅ Removed widget at {path} (key: {widget_key})")
            
            
    
    def _recursive_cleanup(self, widget, path: List):
        """Recursively clean up all child widgets"""
        if hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                child_path = None
                # Find path for this child
                for p, w in self.widget_map.items():
                    if w == child:
                        child_path = list(p)
                        break
                
                if child_path:
                    self._recursive_cleanup(child, child_path)
                    self._cleanup_widget_mappings(child, child_path)
                    
                    # Clear component state for child path
                    clear_component_state(component_path=child_path)
    
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
        
        if widget:
            # Apply layout
            position = path[-1] if path else 0
            LayoutManager.apply_layout(widget, node, parent, position)
    
    def _create_widget_tree(self, node: Dict, parent, path: List):
        """Create widget and all its children"""
        # Handle component rendering with hooks
        node_type = node.get('type', 'frame')
        is_component = (isinstance(node_type, type) or callable(node_type)) and not isinstance(node_type, str)
        
        if is_component:
            # Render component with hooks
            rendered_node = _with_hook_rendering(node_type, node.get('props', {}), path)
            return self._create_widget_tree(rendered_node, parent, path)
        
        # Create the widget
        widget = WidgetFactory.create_widget(
            node_type,
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
        #Debug
        print(f"Applying Update patch at path {path}")
        print(f"changed props: {props.get('changed', {})}")
        print(f"Removed props: {props.get('removed', [])}")
        
        widget = self._get_widget_by_path(path, root_widget)
        if not widget:
            print(f"Widget not found at path {path}")
            return
        print(f" Widget found: {widget.__class__.__name__}")
        
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
                # Update regular property(thread-safe)
                if threading.current_thread() is threading.main_thread():
                    
                    WidgetFactory.update_widget_prop(widget, key, value)
                else:
                    # schedule on main thread 
                    def update():
                        WidgetFactory.update_widget_prop(widget, key, value)
                    if hasattr(widget, 'after'):
                        widget.after(0, update)
        # Handle removed props
        for key in props.get('removed', []):
            if key not in EventSystem.EVENT_MAP:
                self._reset_widget_prop(widget, key)
        
        # Update layout if layout-related props changed
        layout_props = ['side', 'fill', 'expand', 'anchor', 'padx', 'pady', 
                       'width_full', 'height_full', 'margin', 'layout_manager']
        if any(key in layout_props for key in props.get('changed', {}).keys()):
            LayoutManager.update_layout(widget, node.get('props', {}))
        #force widget update
        try:
            widget.update_idletasks()
            print(f" Widget update forced")
        except Exception as e:
            print(f"Could not force update: {e}")
        print(f"Update patch applied")
    
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
        self._recursive_cleanup(widget, path)
        safe_widget_operation(widget, 'destroy')
        self._cleanup_widget_mappings(widget, path)
        # Clear component state for this path
        clear_component_state(component_path=path)
        
        # Create new widget tree
        new_widget = self._create_widget_tree(new_node, parent, path)
        
        if new_widget:
            # Apply layout
            position = path[-1] if path else 0
            LayoutManager.apply_layout(new_widget, new_node, parent, position)
    
    def _apply_reorder(self, patch: Dict, root_widget):
        """Apply REORDER patch"""
        path = patch['path']
        new_order = patch.get('new_order', [])
        
        parent_widget = self._get_widget_by_path(path, root_widget)
        if not parent_widget or not hasattr(parent_widget, 'winfo_children'):
            return
        
        children = parent_widget.winfo_children()
        
        if children and new_order:
            # Remove all children from parent
            for child in children:
                child.pack_forget()
                child.grid_forget()
                child.place_forget()
            
            # Re-add in new order
            for key in new_order:
                widget = self.key_map.get(key)
                if widget and widget.master == parent_widget:
                    LayoutManager.apply_layout(widget, {'props': {}}, parent_widget, 0)
    
    def _apply_move(self, patch: Dict, root_widget):
        """Apply MOVE patch (keyed child moved position)"""
        path = patch['path']
        key = patch['key']
        from_index = patch['from_index']
        to_index = patch['to_index']
        
        parent_widget = self._get_widget_by_path(path, root_widget)
        widget = self.key_map.get(key)
        
        if parent_widget and widget:
            # Remove from current position
            widget.pack_forget()
            widget.grid_forget()
            widget.place_forget()
            
            # Re-add at new position
            LayoutManager.apply_layout(widget, {'props': {}}, parent_widget, to_index)
    
    def _get_widget_by_path(self, path: List, root_widget):
        """Get widget by path trying both path and key lookup"""
        if not path:
            return root_widget
            
        # method 1: Try direct path look up 
        path_key = tuple(path)
        if path_key in self.widget_map:
            widget= self.widget_map[path_key]
            try:
                widget.winfo_exists()
                return widget
            except:
                # widget destroyed: clean up mappings
                self._cleanup_widget_mappings(widget, path)
                         
        # method 2: Try to find by key (if any element is a string key)
        for element in path:
            if isinstance(element, str) and element in self.key_map:
                widget= self.key_map[element]
                # verify widget is live
                try:
                    widget.winfo_exist()
                    return widget 
                except:
                    # widget destroyed, clean up
                    if widget in self.widget_to_path:
                     old_path = list(self.widget_to_path[widget])
                     
                     self._cleanup_widget_mappings(widget, old_path)
                     
        # method 3:Try Numeric index Fallback for last element 
        if path and isinstance(path[-1], int):
            parent_path = path[:-1]
            parent = self._get_widget_by_path(parent_path, root_widget)
            if parent and hasattr(parent, 'winfo_children' ):
                children= parent.winfo_children()
                index= path[-1]
                if 0 <= index < len(children):
                    return children[index]
                    
        # Method 4 : Try key-based lookup if path contain string keys 
        if path and isinstance(path[-1], str):
            # Last element might be a key 
            last_key=path[-1]
            if last_key in self.key_map:
                print(f"Found widget by key: '{last_key}'")
                return self.key_map[last_key]
                
        # Not found 
        print(f"Widget not found at path: {path}")
        print(f" Available paths: {list(self.widget_map.keys())[:5]}")
        print(f"Available keys: {list(self.key_map.keys())[:5]}")
        return None
         
    def _cleanup_widget_mappings(self, widget, path):
        """Clean up mappings for a widget"""
        EventSystem.cleanup_widget_events(widget)
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
            'state': 'normal',
            'cursor': '',
            'font': ('Arial', 12, 'normal')
        }
        
        if prop in defaults:
            try:
                WidgetFactory.update_widget_prop(widget, prop, defaults[prop])
            except:
                pass
    
    def _process_pending_updates(self, root_widget):
        """Process any pending widget updates"""
        for update in self.pending_updates:
            try:
                update(root_widget)
            except Exception as e:
                ERROR_BOUNDARY.handle_error(ErrorValue(e, time.time()), "pending_update")
        
        self.pending_updates.clear()
    
    def begin_batch(self):
        """Begin batch updates"""
        self.batch_updates = True
        self.pending_updates.clear()
    
    def end_batch(self, root_widget):
        """End batch updates and apply all pending changes"""
        self.batch_updates = False
        self._process_pending_updates(root_widget)
    
    def get_stats(self):
        """Get patcher statistics"""
        with self._lock:
            return {
                'widget_count': len(self.widget_map),
                'key_mappings': len(self.key_map),
                'parent_mappings': len(self.parent_map),
                'vdom_nodes': len(self.vdom_tracker.node_map),
                'batch_mode': self.batch_updates,
                'pending_updates': len(self.pending_updates)
            }

# ===============================
# Design Tokens & Theme System
# ===============================
class DesignTokens:
    """Complete Tailwind-inspired design token system with CSS variables"""
    
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
                'cyan': {50: '#ecfeff', 100: '#cffafe', 200: '#a5f3fc', 300: '#67e8f9', 400: '#22d3ee', 500: '#06b6d4', 600: '#0891b2', 700: '#0e7490', 800: '#155e75', 900: '#164e63'},
                'teal': {50: '#f0fdfa', 100: '#ccfbf1', 200: '#99f6e4', 300: '#5eead4', 400: '#2dd4bf', 500: '#14b8a6', 600: '#0d9488', 700: '#0f766e', 800: '#115e59', 900: '#134e4a'},
            },
            'spacing': {
                '0': 0, '1': 4, '2': 8, '3': 12, '4': 16, '5': 20, '6': 24, '8': 32,
                '10': 40, '12': 48, '16': 64, '20': 80, '24': 96, '32': 128, '40': 160, '48': 192, '64': 256, '80': 320, '96': 384
            },
            'font_size': {
                'xs': 10, 'sm': 12, 'base': 14, 'lg': 16, 'xl': 18, '2xl': 20, '3xl': 24, '4xl': 28, '5xl': 32, '6xl': 36, '7xl': 40, '8xl': 48, '9xl': 56
            },
            'font_weight': {
                'thin': 'normal', 'extralight': 'normal', 'light': 'normal', 'normal': 'normal',
                'medium': 'normal', 'semibold': 'bold', 'bold': 'bold', 'extrabold': 'bold', 'black': 'bold'
            },
            'border_radius': {
                'none': 0, 'sm': 2, 'default': 4, 'md': 6, 'lg': 8, 'xl': 12, '2xl': 16, '3xl': 24, 'full': 9999
            },
            'opacity': {
                '0': 0, '5': 0.05, '10': 0.1, '20': 0.2, '25': 0.25, '30': 0.3, '40': 0.4, '50': 0.5,
                '60': 0.6, '70': 0.7, '75': 0.75, '80': 0.8, '90': 0.9, '95': 0.95, '100': 1.0
            },
            'breakpoints': {
                'xs': 0, 'sm': 640, 'md': 768, 'lg': 1024, 'xl': 1280, '2xl': 1536
            },
            'shadows': {
                'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                'default': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
                'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                'inner': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
            },
            'transitions': {
                'duration': {
                    '75': '75ms', '100': '100ms', '150': '150ms', '200': '200ms',
                    '300': '300ms', '500': '500ms', '700': '700ms', '1000': '1000ms'
                },
                'timing': {
                    'linear': 'linear', 'in': 'ease-in', 'out': 'ease-out', 'in-out': 'ease-in-out'
                }
            },
            'z_index': {
                '0': 0, '10': 10, '20': 20, '30': 30, '40': 40, '50': 50, 'auto': 'auto'
            }
        }
        self.current_theme = 'light'
        self.dark_mode = False
        self.css_variables = {}
        self._update_css_variables()
        
    def _update_css_variables(self):
        """Update CSS variables based on current theme"""
        self.css_variables = {
            '--primary-color': self.get_color('blue-500'),
            '--secondary-color': self.get_color('gray-500'),
            '--success-color': self.get_color('green-500'),
            '--danger-color': self.get_color('red-500'),
            '--warning-color': self.get_color('yellow-500'),
            '--info-color': self.get_color('cyan-500'),
            '--background-color': self.get_color('white' if not self.dark_mode else 'gray-900'),
            '--text-color': self.get_color('gray-900' if not self.dark_mode else 'gray-100'),
            '--border-color': self.get_color('gray-300' if not self.dark_mode else 'gray-700'),
            '--shadow-color': 'rgba(0, 0, 0, 0.1)' if not self.dark_mode else 'rgba(0, 0, 0, 0.3)',
        }
    
    def get_color(self, color_name, shade=500):
        """Get color by name and shade"""
        if '-' in color_name:
            try:
                color, shade_str = color_name.split('-')
                shade = int(shade_str)
            except:
                color = color_name
        else:
            color = color_name
        
        colors = self.tokens['colors'].get(color, {})
        if shade in colors:
            return colors[shade]
        elif colors:
            # Return closest shade
            shades = list(colors.keys())
            closest = min(shades, key=lambda x: abs(x - shade))
            return colors[closest]
        
        return '#000000'
    
    def set_theme(self, theme: str):
        """Set theme (light/dark/system)"""
        if theme in ['light', 'dark', 'system']:
            self.current_theme = theme
            self.dark_mode = (theme == 'dark') or (theme == 'system' and self._is_system_dark())
            self._update_css_variables()
            
            # Trigger theme change event
            if hasattr(self, 'theme_stream'):
                self.theme_stream.set({'theme': theme, 'dark_mode': self.dark_mode})
    
    def _is_system_dark(self):
        """Check if system is in dark mode (simplified)"""
        # In a real implementation, this would check system settings
        import tkinter as tk
        root = tk.Tk()
        bg = root.cget('bg')
        root.destroy()
        
        # Simple heuristic based on background color brightness
        if bg.startswith('#'):
            r = int(bg[1:3], 16)
            g = int(bg[3:5], 16)
            b = int(bg[5:7], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return brightness < 128
        
        return False
    
    def get_css_variable(self, name: str):
        """Get CSS variable value"""
        return self.css_variables.get(name, '')
    
    def generate_gradient(self, from_color: str, to_color: str, direction: str = 'to right'):
        """Generate CSS gradient"""
        return f'linear-gradient({direction}, {self.get_color(from_color)}, {self.get_color(to_color)})'
    
    def get_shadow(self, size: str = 'default'):
        """Get shadow definition"""
        return self.tokens['shadows'].get(size, 'none')
    
    def get_transition(self, property: str = 'all', duration: str = '300', timing: str = 'ease-in-out'):
        """Get transition definition"""
        duration_ms = self.tokens['transitions']['duration'].get(duration, '300ms')
        timing_func = self.tokens['transitions']['timing'].get(timing, 'ease-in-out')
        return f'{property} {duration_ms} {timing_func}'

DESIGN_TOKENS = DesignTokens()

# ===============================
# Error Handling with Recovery
# ===============================
@dataclass
class ErrorValue:
    error: Exception
    timestamp: float
    original_value: Any = None
    component_path: List = None
    recovery_attempts: int = 0
    
    def __repr__(self):
        return f"ErrorValue({self.error.__class__.__name__}: {str(self.error)})"

class ErrorBoundary:
    def __init__(self):
        self.errors = deque(maxlen=1000)
        self.error_handlers = []
        self.recovery_strategies = {}
        self._lock = threading.RLock()
        self.max_recovery_attempts = 3
    
    def handle_error(self, error: ErrorValue, stream_name: str = "unknown"):
        """Handle error with recovery strategies"""
        with self._lock:
            error.component_path = _component_state_manager.current_path.copy()
            self.errors.append({
                'stream': stream_name,
                'error': error,
                'timestamp': time.time(),
                'recovery_attempt': error.recovery_attempts
            })
        
        # Try recovery strategies
        recovery_successful = False
        for strategy in self.error_handlers:
            try:
                recovery = strategy(error, stream_name)
                if recovery is not None:
                    error.recovery_attempts += 1
                    if error.recovery_attempts < self.max_recovery_attempts:
                        # Try to recover
                        recovery_successful = True
                        break
            except Exception as e:
                print(f"Error recovery strategy failed: {e}")
        
        if not recovery_successful:
            # Fallback UI
            self._show_fallback_ui(error, stream_name)
    
    def on_error(self, handler: Callable):
        """Register error handler with recovery"""
        self.error_handlers.append(handler)
        return lambda: self.error_handlers.remove(handler)
    
    def add_recovery_strategy(self, error_type: type, strategy: Callable):
        """Add recovery strategy for specific error type"""
        self.recovery_strategies[error_type] = strategy
    
    def _show_fallback_ui(self, error: ErrorValue, stream_name: str):
        """Show fallback UI for unrecoverable errors"""
        print(f"❌ Unrecoverable error in {stream_name}: {error.error}")
        
        # In a real implementation, this would render an error boundary component
        # For now, just log it
        print(f"  Component path: {error.component_path}")
        print(f"  Recovery attempts: {error.recovery_attempts}")
    
    def get_errors(self, stream_name: Optional[str] = None):
        with self._lock:
            if stream_name:
                return [e for e in self.errors if e['stream'] == stream_name]
            return list(self.errors)
    
    def clear_errors(self, stream_name: Optional[str] = None):
        with self._lock:
            if stream_name:
                self.errors = deque([e for e in self.errors if e['stream'] != stream_name], maxlen=1000)
            else:
                self.errors.clear()

ERROR_BOUNDARY = ErrorBoundary()

# ===============================
# Time-Travel Debugging with Actions
# ===============================
class StateSnapshot:
    def __init__(self, stream_name: str, value: Any, timestamp: float, action: str = None, metadata: Dict = None):
        self.stream_name = stream_name
        self.value = value
        self.timestamp = timestamp
        self.action = action
        self.metadata = metadata or {}
    
    def to_dict(self):
        return {
            'stream': self.stream_name,
            'value': str(self.value),
            'timestamp': self.timestamp,
            'time': time.ctime(self.timestamp),
            'action': self.action,
            'metadata': self.metadata
        }

class TimeTravelDebugger:
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)
        self.action_groups: Dict[str, List[int]] = defaultdict(list)
        self.current_index = -1
        self.enabled = True
        self.paused = False
        self._lock = threading.RLock()
        self.compression_enabled = True
    
    def record(self, snapshot: StateSnapshot):
        if self.enabled and not self.paused:
            with self._lock:
                # Compress if similar to previous state
                if self.compression_enabled and self.history:
                    last = self.history[-1]
                    if (last.stream_name == snapshot.stream_name and 
                        json.dumps(last.value, default=str) == json.dumps(snapshot.value, default=str)):
                        # Similar state, update timestamp
                        last.timestamp = snapshot.timestamp
                        return
                
                self.history.append(snapshot)
                self.current_index = len(self.history) - 1
                
                # Group actions
                if snapshot.action:
                    self.action_groups[snapshot.action].append(self.current_index)
    
    def begin_action(self, action_name: str):
        """Begin an action group"""
        return ActionGroup(self, action_name)
    
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
    
    def jump_to(self, index: int):
        with self._lock:
            if 0 <= index < len(self.history):
                self.current_index = index
                return self.history[index]
            return None
    
    def get_current_state(self):
        with self._lock:
            if 0 <= self.current_index < len(self.history):
                return self.history[self.current_index]
            return None
    
    def get_action_group(self, action_name: str):
        with self._lock:
            indices = self.action_groups.get(action_name, [])
            return [self.history[i] for i in indices]
    
    def export_history(self, filepath: str):
        with self._lock:
            data = [snapshot.to_dict() for snapshot in self.history]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ History exported to {filepath}")
    
    def clear(self):
        with self._lock:
            self.history.clear()
            self.action_groups.clear()
            self.current_index = -1
    
    def get_stats(self):
        with self._lock:
            return {
                'history_size': len(self.history),
                'current_index': self.current_index,
                'action_groups': len(self.action_groups),
                'enabled': self.enabled,
                'paused': self.paused,
                'compression': self.compression_enabled
            }

class ActionGroup:
    """Context manager for action grouping"""
    def __init__(self, debugger: TimeTravelDebugger, action_name: str):
        self.debugger = debugger
        self.action_name = action_name
    
    def __enter__(self):
        self.debugger.paused = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.debugger.paused = False
        # Add marker for action completion
        if not exc_type:
            self.debugger.record(StateSnapshot(
                f"action_{self.action_name}",
                {"status": "completed"},
                time.time(),
                action=self.action_name,
                metadata={"type": "action_completion"}
            ))

TIME_TRAVEL = TimeTravelDebugger()

# ===============================
# VDOM Cache with Compression
# ===============================
class VDOMCache:
    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size
        self.access_count = defaultdict(int)
        self.hits = 0
        self.misses = 0
        self.size_history = deque(maxlen=100)
        self._lock = threading.RLock()
        self.compression_enabled = True
    
    def get(self, key: str):
        with self._lock:
            if key in self.cache:
                self.access_count[key] += 1
                self.hits += 1
                return copy.deepcopy(self.cache[key])
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any):
        with self._lock:
            # Check if we need to evict
            if len(self.cache) >= self.max_size:
                # Find least recently used
                min_key = min(self.cache.keys(), key=lambda k: self.access_count.get(k, 0))
                del self.cache[min_key]
                del self.access_count[min_key]
            
            # Compress value if enabled
            if self.compression_enabled and isinstance(value, dict):
                value = self._compress_vdom(value)
            
            self.cache[key] = copy.deepcopy(value)
            self.access_count[key] = 0
            self.size_history.append(len(self.cache))
    
    def _compress_vdom(self, vdom: Dict) -> Dict:
        """Compress VDOM by removing unnecessary data"""
        if not isinstance(vdom, dict):
            return vdom
        
        compressed = vdom.copy()
        
        # Remove empty props
        if 'props' in compressed and not compressed['props']:
            del compressed['props']
        
        # Remove empty children
        if 'children' in compressed and not compressed['children']:
            del compressed['children']
        
        # Compress children recursively
        if 'children' in compressed:
            compressed['children'] = [self._compress_vdom(c) for c in compressed['children']]
        
        return compressed
    
    def clear(self):
        with self._lock:
            self.cache.clear()
            self.access_count.clear()
            self.hits = 0
            self.misses = 0
            self.size_history.clear()
    
    def get_stats(self):
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            
            # Calculate cache efficiency
            if self.size_history:
                avg_size = sum(self.size_history) / len(self.size_history)
                efficiency = (avg_size / self.max_size * 100) if self.max_size > 0 else 0
            else:
                avg_size = len(self.cache)
                efficiency = 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': f"{hit_rate:.1f}%",
                'efficiency': f"{efficiency:.1f}%",
                'avg_size': round(avg_size, 2),
                'compression': self.compression_enabled
            }
    
    def export_cache(self, filepath: str):
        """Export cache contents to file"""
        with self._lock:
            data = {
                'cache': self.cache,
                'stats': self.get_stats(),
                'timestamp': time.time()
            }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return data['stats']

# ===============================
# Thread-Safe Reactive Stream with All Operators
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
        self._local_history = deque(maxlen=100)
        
        # Backpressure
        self._backpressure_limit = 1000
        self._pending_values = deque(maxlen=self._backpressure_limit)
        
        # Performance tracking
        self._emit_count = 0
        self._error_count = 0
    
    @property
    def value(self):
        with self._lock:
            return self._value
    
    def set(self, new_value):
        """Set stream value with thread safety and backpressure"""
        with self._lock:
            if self._disposed:
                print(f"⚠️  Attempting to set disposed stream: {self.name}")
                return
               
            # Add to pending queue
            self._pending_values.append(new_value)
            # Check backpressure - if queue too large, drop
            if len(self._pending_values) > self._backpressure_limit:
                dropped= self._pending_values.popleft()
                print(f"⚠️  Backpressure: dropped value from {self.name}")
                
            # process latest value
            if self._pending_values:
                actual_value = self._pending_values.pop() # take latest 
                self._pending_values.clear()
            else:
                return  # nothing to process 
           # new_value = self._pending_values.popleft()
            
            old_value = self._value
            self._value = actual_value
            
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
                # cancel existing timer safely 
                timer_to_cancel = self._debounce_timer
                if timer_to_cancel:
                    timer_to_cancel.cancel()
                # create new timer 
                new_timer = threading.Timer(
                    self._debounce_delay,
                    lambda: self._notify(old_value, new_value)
                )
                self._debounce_timer = new_timer
                new_timer.start()
                
            else:
                self._notify(old_value, new_value)
    
    def _notify(self, old_value, new_value):
        """Notify subscribers with error handling"""
        with self._lock:
            if self._disposed:
                return 
            subscribers_copy = self._subscribers.copy()
            self._emit_count += 1
        
        for subscriber in subscribers_copy:
            # check disposed state again before each callback 
            if self._disposed:
                break
            try:
                subscriber(new_value, old_value)
            except Exception as e:
                self._error_count += 1
                self._handle_error(ErrorValue(e, time.time(), new_value))
    
    def _handle_error(self, error_value: ErrorValue):
        """Handle errors with recovery strategies"""
        for handler in self._error_handlers:
            try:
                recovery = handler(error_value)
                if recovery is not None:
                    self.set(recovery)
                    return
            except Exception as e:
                print(f"Error handler failed: {e}")
        
        ERROR_BOUNDARY.handle_error(error_value, self.name)
    
    # ========== STREAM OPERATORS ==========
    
    def map(self, transform_fn: Callable) -> 'Stream':
        """Transform stream values"""
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
        """Filter stream values"""
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
        """Handle errors in stream"""
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
    
    def merge(self, *streams: 'Stream') -> 'Stream':
        """Merge multiple streams"""
        derived = Stream(name=f"{self.name}.merge")
        all_streams = [self] + list(streams)
        
        def create_updater(stream):
            def updater(new_val, old_val):
                derived.set(new_val)
            return updater
        
        for stream in all_streams:
            stream.subscribe(create_updater(stream))
        
        return derived
    
    def combine_latest(self, *streams: 'Stream') -> 'Stream':
        """Combine latest values from multiple streams"""
        derived = Stream(name=f"{self.name}.combine_latest")
        all_streams = [self] + list(streams)
        latest = [None] * len(all_streams)
        
        def create_updater(index):
            def updater(new_val, old_val):
                latest[index] = new_val
                if all(v is not None for v in latest):
                    derived.set(tuple(latest))
            return updater
        
        for i, stream in enumerate(all_streams):
            stream.subscribe(create_updater(i))
            if stream.value is not None:
                latest[i] = stream.value
        
        return derived
    
    def with_latest_from(self, *streams: 'Stream') -> 'Stream':
        """Combine with latest values from other streams"""
        derived = Stream(name=f"{self.name}.with_latest_from")
        other_streams = list(streams)
        latest_others = [None] * len(other_streams)
        
        def update_other(index):
            def updater(new_val, old_val):
                latest_others[index] = new_val
            return updater
        
        for i, stream in enumerate(other_streams):
            stream.subscribe(update_other(i))
            if stream.value is not None:
                latest_others[i] = stream.value
        
        def update_self(new_val, old_val):
            derived.set((new_val, *latest_others))
        
        self.subscribe(update_self)
        
        return derived
    
    def switch(self) -> 'Stream':
        """Switch to latest inner stream (for streams of streams)"""
        derived = Stream(name=f"{self.name}.switch")
        current_inner = None
        current_unsubscribe = None
        
        def update_outer(new_stream, old_stream):
            nonlocal current_inner, current_unsubscribe
            
            if current_unsubscribe:
                current_unsubscribe()
            
            if isinstance(new_stream, Stream):
                current_inner = new_stream
                current_unsubscribe = new_stream.subscribe(
                    lambda val, _: derived.set(val)
                )
        
        self.subscribe(update_outer)
        
        return derived
    
    def delay(self, delay_ms: float) -> 'Stream':
        """Delay emissions by specified time"""
        derived = Stream(name=f"{self.name}.delay")
        def update(new_val, old_val):
            threading.Timer(delay_ms / 1000.0, lambda: derived.set(new_val)).start()
        self.subscribe(update)
        return derived
    
    def sample(self, interval_ms: float) -> 'Stream':
        """Sample stream at regular intervals"""
        derived = Stream(name=f"{self.name}.sample")
        last_value = [self._value]
        
        def sampler():
            while not self._disposed:
                time.sleep(interval_ms / 1000.0)
                if last_value[0] is not None:
                    derived.set(last_value[0])
        
        def update(new_val, old_val):
            last_value[0] = new_val
        
        self.subscribe(update)
        threading.Thread(target=sampler, daemon=True).start()
        
        return derived
    
    def retry(self, max_attempts: int = 3, delay_ms: float = 1000) -> 'Stream':
        """Retry on error"""
        derived = Stream(name=f"{self.name}.retry")
        attempt_count = 0
        
        def update(new_val, old_val):
            nonlocal attempt_count
            try:
                derived.set(new_val)
                attempt_count = 0
            except Exception as e:
                attempt_count += 1
                if attempt_count <= max_attempts:
                    print(f"Retry {attempt_count}/{max_attempts} for {self.name}")
                    time.sleep(delay_ms / 1000.0)
                    derived.set(new_val)  # Retry
                else:
                    derived._handle_error(ErrorValue(e, time.time(), new_val))
        
        self.subscribe(update)
        
        return derived
    
    def track_history(self, enabled: bool = True, max_history: int = 100):
        """Track history of values"""
        self._track_history = enabled
        if enabled:
            self._local_history = deque(maxlen=max_history)
        return self
    
    def get_history(self):
        with self._lock:
            return list(self._local_history)
    
    def get_stats(self):
        with self._lock:
            return {
                'name': self.name,
                'id': self.id,
                'value': self._value,
                'subscribers': len(self._subscribers),
                'emit_count': self._emit_count,
                'error_count': self._error_count,
                'history_size': len(self._local_history),
                'disposed': self._disposed,
                'backpressure': len(self._pending_values),
                'debounce_delay': self._debounce_delay,
                'throttle_delay': self._throttle_delay
            }
    
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
# StreamProcessor with Pipeline Management
# ===============================
class StreamProcessor:
    def __init__(self):
        self.streams: Dict[str, Stream] = {}
        self.pipelines: Dict[str, Stream] = {}
        self._lock = threading.RLock()
    
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
                elif op_type == 'merge':
                    current = current.merge(*args)
                elif op_type == 'delay':
                    current = current.delay(args[0])
                elif op_type == 'retry':
                    current = current.retry(*args)
            else:
                current = current.map(op)
        
        current.name = name
        with self._lock:
            self.pipelines[name] = current
        return current
    
    def create_interval(self, name: str, interval_ms: float, initial_value=0):
        """Create a stream that emits incrementing values at intervals"""
        stream = Stream(initial_value, name=name)
        
        def emit():
            value = initial_value
            while True:
                time.sleep(interval_ms / 1000.0)
                value += 1
                stream.set(value)
        
        threading.Thread(target=emit, daemon=True).start()
        
        with self._lock:
            self.streams[name] = stream
        
        return stream
    
    def create_from_event(self, name: str, widget, event_type: str):
        """Create a stream from a widget event"""
        stream = Stream(None, name=name)
        
        def handler(event):
            stream.set({
                'type': event_type,
                'target': widget,
                'event': event,
                'timestamp': time.time()
            })
        
        widget.bind(EventSystem.EVENT_MAP.get(event_type, event_type), handler)
        
        with self._lock:
            self.streams[name] = stream
        
        return stream
    
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
        self._lock = threading.RLock()
        self.pseudo_classes = set(['hover', 'focus', 'active', 'disabled', 'visited'])
        self.media_queries = {}
    
    
    def set_breakpoint(self, bp):
        with self._lock:
            self.breakpoint = bp
            self.style_cache.clear()
    def resolve_classes(self, class_string, current_breakpoint=None):
        # input validation 
        if class_string is None:
            return {}
        if not isinstance(class_string, str):
            print(f"Warning: class_string should be str, got {type(class_string).__name__}")
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
        
        # Handle pseudo-classes
        for pseudo in self.pseudo_classes:
            if cls.startswith(f'{pseudo}:'):
                pseudo_props = self._get_props(cls[len(pseudo)+1:])
                if pseudo == 'hover':
                    if 'bg' in pseudo_props:
                        resolved['active_bg'] = pseudo_props['bg']
                    if 'fg' in pseudo_props:
                        resolved['active_fg'] = pseudo_props['fg']
                elif pseudo == 'focus':
                    if 'bg' in pseudo_props:
                        resolved['focus_bg'] = pseudo_props['bg']
                return
        
        # Handle transitions
        if cls.startswith('transition-'):
            prop = cls[11:]
            if prop == 'all':
                resolved['transition'] = self.tokens.get_transition('all')
            elif prop in ['opacity', 'transform', 'colors']:
                resolved['transition'] = self.tokens.get_transition(prop)
        
        resolved.update(self._get_props(cls))
    
    def _get_props(self, cls):
        # Background colors
        if cls.startswith('bg-'):
            color_part = cls[3:]
            if color_part.startswith('gradient-to-'):
                # Gradient backgrounds
                direction = color_part[12:]
                colors = direction.split('-')
                if len(colors) >= 2:
                    from_color = colors[0]
                    to_color = colors[1]
                    return {'bg_gradient': self.tokens.generate_gradient(from_color, to_color, f'to {direction}')}
            return {'bg': self.tokens.get_color(color_part)}
        
        # Text colors
        if cls.startswith('text-'):
            color_part = cls[5:]
            sizes = ['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl', '7xl', '8xl', '9xl']
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
        if cls.startswith('pt-'):
            return {'pady': (self.tokens.tokens['spacing'].get(cls[3:], 0), 0, 0, 0)}
        if cls.startswith('pr-'):
            return {'padx': (0, self.tokens.tokens['spacing'].get(cls[3:], 0), 0, 0)}
        if cls.startswith('pb-'):
            return {'pady': (0, 0, self.tokens.tokens['spacing'].get(cls[3:], 0), 0)}
        if cls.startswith('pl-'):
            return {'padx': (0, 0, 0, self.tokens.tokens['spacing'].get(cls[3:], 0))}
        
        # Margin
        if cls.startswith('m-'):
            val = self.tokens.tokens['spacing'].get(cls[2:], 0)
            return {'margin': val}
        if cls.startswith('mx-'):
            return {'margin_x': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        if cls.startswith('my-'):
            return {'margin_y': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        
        # Width/Height
        if cls.startswith('w-'):
            size = cls[2:]
            if size == 'full':
                return {'width_full': True, 'width': '100%'}
            elif size == 'screen':
                return {'width_full': True}
            elif size == 'auto':
                return {'width': 'auto'}
            return {'width': self.tokens.tokens['spacing'].get(size, size)}
        if cls.startswith('h-'):
            size = cls[2:]
            if size == 'full':
                return {'height_full': True, 'height': '100%'}
            elif size == 'screen':
                return {'height_full': True}
            elif size == 'auto':
                return {'height': 'auto'}
            return {'height': self.tokens.tokens['spacing'].get(size, size)}
        
        # Layout
        if cls == 'flex':
            return {'layout': 'horizontal', 'layout_manager': 'flex'}
        if cls == 'flex-col':
            return {'layout': 'vertical', 'layout_manager': 'flex'}
        if cls.startswith('gap-'):
            return {'spacing': self.tokens.tokens['spacing'].get(cls[4:], 0)}
        if cls == 'grid':
            return {'layout_manager': 'grid'}
        if cls == 'absolute':
            return {'layout_manager': 'place', 'position': 'absolute'}
        if cls == 'relative':
            return {'layout_manager': 'place', 'position': 'relative'}
        if cls == 'fixed':
            return {'layout_manager': 'place', 'position': 'fixed'}
        
        # Flexbox properties
        if cls.startswith('flex-'):
            flex_val = cls[5:]
            if flex_val == '1':
                return {'flex_grow': 1}
            elif flex_val == 'none':
                return {'flex_grow': 0}
            elif flex_val in ['row', 'col', 'row-reverse', 'col-reverse']:
                return {'flex_direction': flex_val}
            elif flex_val in ['wrap', 'nowrap', 'wrap-reverse']:
                return {'flex_wrap': flex_val}
            elif flex_val in ['start', 'end', 'center', 'between', 'around', 'evenly']:
                return {'justify_content': f'flex-{flex_val}' if flex_val in ['start', 'end'] else flex_val}
            elif flex_val in ['stretch', 'start', 'end', 'center', 'baseline']:
                return {'align_items': flex_val}
        
        # Typography
        if cls.startswith('font-'):
            weight = cls[5:]
            if weight in self.tokens.tokens['font_weight']:
                return {'font_weight': self.tokens.tokens['font_weight'][weight]}
            elif weight in ['sans', 'serif', 'mono']:
                families = {
                    'sans': 'Arial, Helvetica, sans-serif',
                    'serif': 'Times New Roman, serif',
                    'mono': 'Courier New, monospace'
                }
                return {'font_family': families[weight]}
        
        # Border
        if cls == 'border':
            return {'border_width': 1, 'border_color': self.tokens.get_color('gray-300')}
        if cls.startswith('border-'):
            parts = cls[7:].split('-')
            if len(parts) == 1 and parts[0].isdigit():
                return {'border_width': int(parts[0])}
            elif len(parts) >= 2:
                if parts[0] in ['t', 'r', 'b', 'l']:
                    side = {'t': 'top', 'r': 'right', 'b': 'bottom', 'l': 'left'}[parts[0]]
                    return {f'border_{side}_width': int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1}
                else:
                    return {'border_color': self.tokens.get_color('-'.join(parts))}
        
        # Rounded corners
        if cls.startswith('rounded'):
            if cls == 'rounded':
                return {'border_radius': self.tokens.tokens['border_radius']['default']}
            elif cls.startswith('rounded-'):
                size = cls[8:]
                if size in ['t', 'r', 'b', 'l', 'tl', 'tr', 'bl', 'br']:
                    corner_map = {
                        't': 'top', 'r': 'right', 'b': 'bottom', 'l': 'left',
                        'tl': 'top_left', 'tr': 'top_right', 'bl': 'bottom_left', 'br': 'bottom_right'
                    }
                    return {f'border_radius_{corner_map[size]}': self.tokens.tokens['border_radius']['default']}
                else:
                    return {'border_radius': self.tokens.tokens['border_radius'].get(size, 4)}
        
        # Opacity
        if cls.startswith('opacity-'):
            opacity = self.tokens.tokens['opacity'].get(cls[8:], 1.0)
            return {'opacity': opacity}
        
        # Shadow
        if cls.startswith('shadow-'):
            size = cls[7:]
            shadow = self.tokens.tokens['shadows'].get(size, 'none')
            return {'shadow': shadow}
        
        # Z-index
        if cls.startswith('z-'):
            z_val = cls[2:]
            if z_val in self.tokens.tokens['z_index']:
                return {'z_index': self.tokens.tokens['z_index'][z_val]}
        
        # Display
        if cls in ['block', 'inline', 'inline-block', 'hidden']:
            if cls == 'hidden':
                return {'visible': False}
            return {'display': cls}
        
        # Overflow
        if cls.startswith('overflow-'):
            overflow = cls[9:]
            if overflow in ['auto', 'hidden', 'visible', 'scroll']:
                return {'overflow': overflow}
        
        # Cursor
        if cls.startswith('cursor-'):
            cursor = cls[7:]
            cursor_map = {
                'pointer': 'hand2',
                'wait': 'watch',
                'text': 'xterm',
                'move': 'fleur',
                'not-allowed': 'X_cursor',
                'help': 'question_arrow',
                'crosshair': 'crosshair',
                'grab': 'hand1',
                'grabbing': 'hand2'
            }
            return {'cursor': cursor_map.get(cursor, cursor)}
        
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
        self.resize_debounce = 100  # ms
        self.root.bind('<Configure>', self._handle_resize)
        
        # Subscribe to theme changes for responsive design
        DESIGN_TOKENS.theme_stream = Stream({'theme': 'light', 'dark_mode': False}, name='theme_changes')
    
    def _handle_resize(self, event):
        if event.widget == self.root:
            current_time = time.time() * 1000
            if current_time - self._last_resize_time > self.resize_debounce:
                self._last_resize_time = current_time
                self._update_breakpoint(event.width)
    
    def _update_breakpoint(self, width):
        breakpoints = DESIGN_TOKENS.tokens['breakpoints']
        new_bp = 'xs'
        
        if width >= breakpoints.get('2xl', 1536):
            new_bp = '2xl'
        elif width >= breakpoints.get('xl', 1280):
            new_bp = 'xl'
        elif width >= breakpoints.get('lg', 1024):
            new_bp = 'lg'
        elif width >= breakpoints.get('md', 768):
            new_bp = 'md'
        elif width >= breakpoints.get('sm', 640):
            new_bp = 'sm'
        
        if new_bp != self.current_breakpoint:
            self.current_breakpoint = new_bp
            self.breakpoint_stream.set(new_bp)
            print(f"📱 Breakpoint changed to: {new_bp} ({width}px)")
    
    def get_breakpoint(self):
        return self.current_breakpoint
    
    def subscribe(self, callback):
        return self.breakpoint_stream.subscribe(callback)

# ===============================
# Component System with Hook Support
# ===============================
class Component:
    """Base class for reusable components with full lifecycle support"""
    
    def __init__(self, props: Dict = None):
        self.props = props or {}
        self.state = {}
        self.streams = {}
        self._mounted = False
        self._path = None
        self._error_boundary = None
        self._refs = {}
        self._context_subscriptions = []
    
    def create_state(self, name: str, initial_value=None) -> Stream:
        """Create a state stream for this component (legacy method)"""
        stream = Stream(initial_value, name=f"{self.__class__.__name__}.{name}")
        self.streams[name] = stream
        return stream
    
    def set_state(self, updater: Union[Dict, Callable]):
        """Update component state (legacy method)"""
        if callable(updater):
            new_state = updater(self.state)
        else:
            new_state = updater
        
        self.state.update(new_state)
        # In a real implementation, this would trigger a re-render
        # For now, we rely on useState hooks
    
    def render(self):
        """Override this method to define component UI"""
        raise NotImplementedError("Component must implement render()")
    
    def on_mount(self):
        """Called when component is first mounted"""
        pass
    
    def on_unmount(self):
        """Called when component is unmounted"""
        pass
    
    def should_update(self, next_props: Dict, next_state: Dict) -> bool:
        """Override to control re-rendering (like React's shouldComponentUpdate)"""
        return True
    
    def get_snapshot_before_update(self, prev_props: Dict, prev_state: Dict):
        """Called before update, return value passed to component_did_update"""
        return None
    
    def component_did_update(self, prev_props: Dict, prev_state: Dict, snapshot):
        """Called after component updates"""
        pass
    
    def component_did_catch(self, error: Exception, error_info: Dict):
        """Error boundary for this component and its children"""
        print(f"Component error: {error}")
        return None  # Return fallback UI
    
    def _mount(self):
        if not self._mounted:
            self._mounted = True
            try:
                self.on_mount()
            except Exception as e:
                self.component_did_catch(e, {'phase': 'mount'})
    
    def _unmount(self):
        if self._mounted:
            self._mounted = False
            try:
                self.on_unmount()
            except Exception as e:
                self.component_did_catch(e, {'phase': 'unmount'})
            
            # Clean up streams
            for stream in self.streams.values():
                stream.dispose()
            self.streams.clear()
            
            # Clean up context subscriptions
            for unsubscribe in self._context_subscriptions:
                unsubscribe()
            self._context_subscriptions.clear()

def create_element(element_type: Union[str, type], props: Dict = None, *children) -> Dict:
    """Helper function to create VDOM elements (like React.createElement)"""
    props = props or {}
    
    # Handle Fragment-like behavior
    if element_type == 'fragment':
        return {
            'type': 'frame',
            'props': {'style': 'fragment'},
            'children': list(children),
            'key': props.get('key')
        }
    
    # If element_type is a Component class, instantiate and render it
    if inspect.isclass(element_type) and issubclass(element_type, Component):
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
        self.render_count = 0
        self.error_boundary = ErrorBoundary()
        self.widget_path_map = {}
    
    @PERFORMANCE.measure_time('hook_aware_render')
    def render(self, diff_result):
        """Render using functional diffing with hook support"""
        render_type = diff_result.get('type', 'full')
        
        # Reset hook context at the start of each render cycle
        global _current_component_path, _hook_index, _component_render_stack
        _current_component_path = []
        _hook_index = 0
        _component_render_stack = []
        
        try:
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
            
            self.render_count += 1
            
            # Flush effects after render
            _flush_effects()
            
        except Exception as e:
            self.error_boundary.handle_error(ErrorValue(e, time.time()), 'renderer')
            # Render error UI
            self._render_error_ui(e)
    
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
            try:
                # Render component with hook context
                rendered = _with_hook_rendering(node_type, props, path)
                return self._render_vdom_with_hooks(rendered, parent, path)
            except Exception as e:
                # Component error boundary
                error_value = ErrorValue(e, time.time(), vdom)
                error_value.component_path = path.copy()
                self.error_boundary.handle_error(error_value, 'component_render')
                # Render fallback UI
                self._render_vdom_with_hooks(self._create_error_vdom(e), parent, path)
                return
        
        # Regular widget rendering
        widget = WidgetFactory.create_widget(node_type, parent, props)

        if widget:
            # CRITICAL: Register widget in patcher's map immediately
            path_key = tuple(path)
            self.patcher.widget_map[path_key] = widget
            self.patcher.widget_to_path[widget] = path_key
            self.patcher.parent_map[widget] = parent
    
            # Register by key if present
            if 'key' in vdom:
                key = vdom['key']
                self.patcher.key_map[key] = widget
                self.patcher.widget_to_key[widget] = key
                print(f"   📍 Widget registered: key='{key}', path={path}, type={node_type}")
            else:
                print(f"   📍 Widget registered: path={path}, type={node_type}")
    
            # Track in debug map
            self.widget_path_map[path_key] = {
                'widget': widget,
                'type': node_type,
                'key': vdom.get('key'),
                'props': props
            }
    
            # Bind events
            EventSystem.bind_events(widget, props)
    
            # Apply layout
            position = path[-1] if path else 0
            LayoutManager.apply_layout(widget, vdom, parent, position)
    
            # Track widget
            self.widgets.append(widget)
            
            # Render children
            for i, child in enumerate(children):
                # use key if available otherwise use index 
                if isinstance(child, dict) and 'key' in child:
                    
                    child_path = path + [child ['key']]
                else:
                    child_path = path+[i]
                print(f"Rendering child at path: {child_path}")
                self._render_vdom_with_hooks(child, widget, child_path)
    
    def _render_error_ui(self, error):
        """Render error UI"""
        error_vdom = self._create_error_vdom(error)
        self._render_full(error_vdom)
    
    def _retry_last_render(self):
        """Retry the last render"""
        if self.current_vdom:
            try:
                self.render({'type': 'full', 'vdom': self.current_vdom})
            except Exception as e:
                print(f"Retry failed: {e}")
        else:
            print("Cannot retry: No previous VDOM available")
    
    def _create_error_vdom(self, error):
        """Create error VDOM"""
        return {
            'type': 'frame',
            'props': {
                'bg': '#fee2e2',
                'padx': 20,
                'pady': 20,
                'class': 'p-4 m-2 border border-red-300 rounded'
            },
            'children': [
                {
                    'type': 'label',
                    'props': {
                        'text': '⚠️ Error Occurred',
                        'fg': '#991b1b',
                        'font_size': 16,
                        'font_weight': 'bold',
                        'class': 'text-red-800 font-bold text-lg'
                    }
                },
                {
                    'type': 'label',
                    'props': {
                        'text': str(error),
                        'fg': '#7f1d1d',
                        'font_size': 12,
                        'class': 'text-red-700 text-sm mt-2'
                    }
                },
                {
                    'type': 'button',
                    'props': {
                        'text': 'Retry',
                        'onClick': lambda: self._retry_last_render(),
                        'class': 'bg-red-500 hover:bg-red-600 text-white px-4 py-2 mt-4 rounded'
                    }
                }
            ]
        }
    
    def get_widget_by_key(self, key):
        """Get widget by its VDOM key"""
        return self.patcher.key_map.get(key)
    
    def get_stats(self):
        """Get renderer statistics"""
        return {
            'render_count': self.render_count,
            'widget_count': len(self.patcher.widget_map),
            'key_mappings': len(self.patcher.key_map),
            'total_widgets': len(self.widgets),
            'current_vdom': bool(self.current_vdom),
            'errors': len(self.error_boundary.errors)
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
    _current_instance = None
    def __init__(self, title="PyUIWizard App", width=800, height=600, use_diffing=True):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        
        self.processor = StreamProcessor()
        self.style_resolver = AdvancedStyleResolver()
        self.layout_engine = ResponsiveLayoutEngine(self.root)
        self.cache = VDOMCache()
        #track wizard instance globally for re-renders 
        self._render_trigger = Stream(0, name='render_trigger')
        self.last_vdom = None  # Ensure clean state
        self._render_scheduled = False # prevent duplicate renders
        self._last_render_time = 0
        PyUIWizard._current_instance = self
       
        self.use_diffing = use_diffing
        self.differ = FunctionalDiffer() if use_diffing else None
        self.renderer = HookAwareVDOMRenderer(self.root) if use_diffing else None
        
        #self.last_vdom = None
        self.render_function = None
        self.render_count = 0
        self.skip_count = 0
        self._component_update_queue = []  # Track component updates
        # Setup error handling
        ERROR_BOUNDARY.on_error(lambda error, stream_name: self._handle_error(error, stream_name))
        
        # Performance monitoring
        self.last_perf_check = time.time()
        self.perf_check_interval = 5  # seconds
        
        print(f"🚀 PyUIWizard {__version__} initialized with useState hook support")
        print(f"   Features: Thread-safe hooks, 18 widget types, Grid/Flex/Place layouts")
        print(f"             CSS Grid, Accessibility, Time-travel debugging")
        print(f"             Responsive design, Error boundaries, Stream operators")
    
    def create_state(self, name: str, initial_value=None) -> Stream:
        """Create a global state stream"""
        return self.processor.create_stream(name, initial_value)
    
    def create_computed(self, name: str, dependencies: List[str], compute_fn: Callable) -> Stream:
        """Create a computed stream from dependencies"""
        return self.processor.combine_latest(dependencies, compute_fn)
    
    def create_interval(self, name: str, interval_ms: float, initial_value=0) -> Stream:
        """Create an interval stream"""
        return self.processor.create_interval(name, interval_ms, initial_value)
    
    def create_from_event(self, name: str, widget, event_type: str) -> Stream:
        """Create a stream from a widget event"""
        return self.processor.create_from_event(name, widget, event_type)
    
    def _has_unexpanded_components(self, vdom):
        """Check if VDOM contains unexpanded components"""
        if not isinstance(vdom, dict):
            return False
      
        node_type = vdom.get('type')
        is_component = (
        (isinstance(node_type, type) and issubclass(node_type, Component)) or
        (callable(node_type) and not isinstance(node_type, str))
    )
    
        if is_component:
            return True
    
        # Check children recursively
        for child in vdom.get('children', []):
             if self._has_unexpanded_components(child):
                 return True
    
        return False

    def _expand_vdom_components(self, node, path, _depth=0):
        """
        Expand all components in VDOM into their rendered DOM.
        Smart path building that prevents duplicates.
        """
        # Depth limit to prevent infinite recursion 
        MAX_DEPTH = 100
        if _depth > MAX_DEPTH:
            raise RuntimeError(
                f" Component expansion depth exceeded {MAX_DEPTH}."
                f"Possible circular component at path: {path}."
                f"Check your components tree for components that render themselves."
            )
        if not isinstance(node, dict):
            return node

        node_type = node.get('type')
        props = node.get('props', {})
    
        is_component = (
        (isinstance(node_type, type) and issubclass(node_type, Component)) or
        (callable(node_type) and not isinstance(node_type, str))
        )

        if is_component:
            component_key = node.get('key')
        
            # SMART PATH BUILDING
            if component_key:
                # Use as path element 
                current_path = path +[component_key]
            else:
                # Generate unique key for this component 
                type_name = getattr(node_type, '__name__', 'component')
                # Use type_name+position to ensure uniqueness 
                unique_key = f"{type_name}_{len([p for p in path if isinstance(p, str) and p.startswith(type_name)])}"
                current_path = path + [unique_key]
        
            print(f"🔧 Expanding component at path {current_path}, key: {component_key}")
        
            # Render component
            rendered = _with_hook_rendering(node_type, props, current_path)
        
            if rendered is None:
                return {'type': 'frame', 'props': {}, 'children': []}
        
            # Preserve original key if needed
            if component_key and 'key' not in rendered:
                rendered = {**rendered, 'key': component_key}
        
            # Expand children
            if 'children' in rendered:
                rendered['children'] = [
                self._expand_vdom_components(child, current_path, _depth + 1)
                for child in rendered['children']
                if child is not None
                ]
        
            return rendered
            
        else:
            # Regular node
            result = node.copy()
        
            # Get or generate key
            node_key = node.get('key')
            if not node_key:
                node_key = node.get('type', 'node')
        
            # Build path: add key if not already present
            if node_key not in path:
                current_path = path + [node_key]
            else:
                current_path = path  # No duplicate
        
            # Expand children
            if 'children' in result:
                result['children'] = [
                self._expand_vdom_components(child, current_path, _depth + 1)
                for child in result['children']
                if child is not None
                ]
        
            return result  
                   
    def _ensure_vdom_expanded(self, vdom):
        """
        Ensure VDOM has all components expanded.
        Returns a fully expanded copy of the VDOM.
        """
        if not isinstance(vdom, dict):
            return vdom
    
        node_type = vdom.get('type')
    
        # Check if this is an unexpanded component
        is_component = (
        (isinstance(node_type, type) and issubclass(node_type, Component)) or
        (callable(node_type) and not isinstance(node_type, str))
        )
        if is_component:
            print(f"  🔧 Expanding unexpanded component {node_type.__name__}")
            # Re-expand this component
            return self._expand_vdom_components(vdom, [])
    
        # Regular node - recursively check children
        result = vdom.copy()
        if 'children' in result:
            result['children'] = [
                self._ensure_vdom_expanded(child) 
            for child in result.get('children', [])
            ]
    
        return result
    
    def render_app(self, render_fn: Callable):
        """Set the main render function"""
        self.render_function = render_fn
        # Subscribe to render trigger for use_state
        def trigger_rerender(val, old_val):
            """Force a re-render when useState updates"""
            # Process components-specific updates first 
            while self._component_update_queue:
                update_info = self._component_update_queue.pop(0)
                
            print(f"🔄 Trigger re-render called: {old_val} -> {val}")  # DEBUG
            # prevent duplicate renders 
            if self._render_scheduled:
                print(f"Re-render already scheduled, skipping ")
                return 
            # Debounce: prevent renders closer than 16ms (60fps)
            current_time = time.time()
            time_since_last = current_time- self._last_render_time
            if time_since_last < 0.016:
                print(f"Too soon since last render ({time_since_last:.3f}s), scheduling...")
                # schedule for later
                def delayed_render():
                    self._render_scheduled = False
                    self._last_render_time= time.time()
                    try:
                        
                        state_names= list(self.processor.streams.keys())
                        state={name: self.processor.streams[name].value for name in state_names} if state_names else {}
                        state['breakpoint'] = self.layout_engine.current_breakpoint
                        state['_render_id'] = time.time()  # Unique ID
                        # create new VDOM 
                        mgr= _get_state_manager()
                        mgr.current_path = []
                        mgr.hook_index =0
                        vdom=self.render_function(state)
                        vdom=self._expand_vdom_components(vdom, [])
                        if vdom:
                            validate_vdom(vdom)
                            vdom = self._resolve_styles(vdom)
                            if self.use_diffing:
                                diff_result= self._diff_with_previous(vdom)
                            else:
                                diff_result=vdom 
                            self._render_to_screen(diff_result)
                    except Exception as e:
                        print(f"❌ Delayed render failed: {e}")
                    finally:
                        self._render_scheduled= False 
                 
                self.root.after(16, delayed_render)
                return 
                
            self._render_scheduled = True
            self._last_render_time = current_time
            # Clear cache to force fresh render with new hook state
            self.cache.clear()
    
            # Get current state
            state_names = list(self.processor.streams.keys())
            if state_names:
                state = {name: self.processor.streams[name].value for name in state_names}
            else:
                state = {}
    
            state['breakpoint'] = self.layout_engine.current_breakpoint
            state['_render_id'] = val #  unique ID 
    
            # Create new VDOM with fresh hook state
            try:
                # Reset Hook context 
                mgr = _get_state_manager()
                mgr.current_path = []
                mgr.hook_index = 0
        
                print(f"🎨 Creating new VDOM...")  
                vdom = self.render_function(state)
                # Expand All Componens
                print(f" Expanding Components..")
                vdom = self._expand_vdom_components(vdom, [])
                print(f" Components Expanded!")
        
                # Validate and resolve styles
                if vdom:
                    validate_vdom(vdom)
                    vdom = self._resolve_styles(vdom)
            
                    print(f"🔍 Diffing VDOM...")  # DEBUG
                    if self.use_diffing:
                        diff_result = self._diff_with_previous(vdom)
                        print(f"📦 Diff result type: {diff_result.get('type')}, patches: {len(diff_result.get('patches', []))}")  # DEBUG
                    else:
                        diff_result = vdom
            
                    print(f"🖼️ Rendering to screen...")  
                    self._render_to_screen(diff_result)
                    print(f"✅ Re-render #{val} complete!")  
            except Exception as e:
                print(f"❌ Re-render failed: {e}")
                import traceback
                traceback.print_exc()
            finally:
                self._render_scheduled = False 

        self._render_trigger.subscribe(trigger_rerender)
    
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
        
            # Trigger initial render immediately
            initial_state = {name: self.processor.streams[name].value for name in state_names}
            initial_state['breakpoint'] = self.layout_engine.current_breakpoint
        
            # Create VDOM and render
            try:
                vdom = self._create_vdom(initial_state)
                if vdom is None:
                    raise ValueError("Render function returned None")
            
                vdom = self._resolve_styles(vdom)
            
                if self.use_diffing:
                    diff_result = self._diff_with_previous(vdom)
                else:
                    diff_result = vdom  # For non-diffing, just pass VDOM directly
            
                self._render_to_screen(diff_result)
            
            except Exception as e:
                print(f"❌ Initial render failed: {e}")
                # Render error UI
                error_vdom = self._error_vdom(ErrorValue(e, time.time()))
                self._render_to_screen(error_vdom if not self.use_diffing else {'type': 'full', 'vdom': error_vdom})
        else:
        # No global state, just render once
            try:
                vdom = self._create_vdom({})
                if vdom is None:
                    raise ValueError("Render function returned None")
            
                vdom = self._resolve_styles(vdom)
            
                if self.use_diffing:
                    diff_result = {'type': 'full', 'vdom': vdom}
                else:
                    diff_result = vdom
            
                self._render_to_screen(diff_result)
            
            except Exception as e:
                print(f"❌ Initial render failed: {e}")
    
         # React to breakpoint changes
            self.layout_engine.breakpoint_stream.subscribe(
         lambda bp, old: (self.style_resolver.set_breakpoint(bp), self.cache.clear())
    )
    
        # React to theme changes
            DESIGN_TOKENS.theme_stream.subscribe(
        lambda theme, old: self.cache.clear()
    )
    
    
    def _debug_paths(self, vdom, label="VDOM Paths"):
        """Debug helper to trace all paths in VDOM"""
        print(f"\n🔍 {label}:")
    
        def trace_paths(node, current_path):
            if not isinstance(node, dict):
                return
        
            node_key = node.get('key', 'no-key')
            node_type = node.get('type', 'unknown')
        
            print(f"  Path: {current_path} -> {node_type}[key={node_key}]")
        
            for i, child in enumerate(node.get('children', [])):
                if isinstance(child, dict):
                    child_key = child.get('key', f"child_{i}")
                    trace_paths(child, current_path + [child_key])
    
        trace_paths(vdom, [])
        print()
    
    @PERFORMANCE.measure_time('create_vdom')
    def _create_vdom(self, state):
        """Create VDOM from render function with hook context reset"""
        # Reset hook context before each render
        mgr = _get_state_manager()
        hook_state_hash = hash(str(sorted(mgr.state.keys()))) if mgr.state else 0
        cache_key = f"{json.dumps(state, sort_keys=True)}_{hook_state_hash}"
        mgr.current_path = []
        mgr.hook_index = 0
        mgr.render_stack = []

        # Get hook state
        mgr_state = mgr.state if hasattr(mgr, 'state') else {}

        # SIMPLIFIED: Disable caching when hooks are in use
        if len(mgr_state) > 0:
            # Hooks are being used - always create fresh VDOM
            self.render_count += 1
            print(f"🎨 Creating fresh VDOM (render #{self.render_count}) - {len(mgr_state)} hooks active")
    
            state['breakpoint'] = self.layout_engine.current_breakpoint
            vdom = self.render_function(state)
        
            # Expand all components into their rendered DOM
            print(f"🔧 Expanding components in VDOM...")
            vdom = self._expand_vdom_components(vdom, [])
            print("✅ Components Expanded!")
            self._debug_paths(vdom, "After Expansion")
        
            # Debug: Print the structure
            self._debug_vdom_structure(vdom, 0)
    
            try:
                validate_vdom(vdom)
            except (TypeError, ValueError) as e:
                raise RuntimeError(f"Invalid VDOM structure: {e}")
    
            return vdom

        # No hooks - use cache as normal
        cache_key = json.dumps(state, sort_keys=True, default=lambda x: str(x) if x is not None else 'null')
        cached = self.cache.get(cache_key)
        if cached:
            self.skip_count += 1
            print(f"📦 Using cached VDOM")
            return cached

        self.render_count += 1
        print(f"🎨 Creating fresh VDOM (render #{self.render_count})")

        state['breakpoint'] = self.layout_engine.current_breakpoint
        vdom = self.render_function(state)
        # Expand all components into their rendered DOM
        vdom = self._expand_vdom_components(vdom, [])
        self._debug_paths(vdom, "After Expansion")

        try:
            validate_vdom(vdom)
        except (TypeError, ValueError) as e:
            raise RuntimeError(f"Invalid VDOM structure: {e}")

        self.cache.set(cache_key, vdom)
        return vdom

    def _debug_vdom_structure(self, node, depth):
        """Debug method to print VDOM structure"""
        indent = "  " * depth
        if isinstance(node, dict):
            node_type = node.get('type', 'unknown')
            key = node.get('key', 'no-key')
            text = node.get('props', {}).get('text', '')
        
            print(f"{indent}{node_type} [key={key}] text='{text}'")
        
            if 'children' in node:
                for child in node['children']:
                    self._debug_vdom_structure(child, depth + 1)
                  
    @PERFORMANCE.measure_time('resolve_styles')
    def _resolve_styles(self, vdom):
        """Resolve Tailwind-style classes with responsive design"""
        def resolve(node):
            if not isinstance(node, dict):
                return node
            
            node = node.copy()
            
            if 'props' in node and 'class' in node['props']:
                resolved = self.style_resolver.resolve_classes(
                    node['props']['class'],
                    self.layout_engine.current_breakpoint
                )
                node_props = node['props'].copy()
                
                # Handle CSS variables
                for key, value in DESIGN_TOKENS.css_variables.items():
                    if key not in node_props:
                        node_props[key] = value
                
                del node_props['class']
                node_props.update(resolved)
                node['props'] = node_props
            
            if 'children' in node:
                node['children'] = [resolve(c) for c in node['children']]
            
            return node
        
        return resolve(vdom.copy())
    
    def _print_label_texts(self, prefix, vdom, path="root"):
        """Debug: Print all label texts in VDOM"""
        if not isinstance(vdom, dict):
            return
    
        if vdom.get('type') == 'label':
            text = vdom.get('props', {}).get('text', '')
            key = vdom.get('key', 'no-key')
            print(f"  {prefix} label[{key}] at {path}: '{text}'")
    
        for i, child in enumerate(vdom.get('children', [])):
            child_key = child.get('key', i) if isinstance(child, dict) else i
            self._print_label_texts(prefix, child, f"{path}/{child_key}")
        
    def _force_component_update(self, component_path):
        """Force update for a specific component path"""
        if not self.use_diffing or not self.renderer:
            return
    
        # Get the current VDOM
        if not self.last_vdom:
            return
    
        # Create a fresh VDOM with current state
        state = {}
        state_names = list(self.processor.streams.keys())
        if state_names:
            state = {name: self.processor.streams[name].value for name in state_names}
        state['breakpoint'] = self.layout_engine.current_breakpoint
    
        # Create new VDOM
        new_vdom = self._create_vdom(state)
        new_vdom = self._resolve_styles(new_vdom)
    
        # Force diff with previous
        diff_result = self._diff_with_previous(new_vdom)
        self._render_to_screen(diff_result)
    
    def _extract_keys(self, vdom, path='root'):
        """ Extract all keys from VDOM for debugging"""
        keys = []
        if isinstance(vdom, dict):
            if 'key' in vdom:
                keys.append(f"{path}.{vdom['key']}")
            if 'children' in vdom:
                for i, child in enumerate(vdom['children']):
                    child_path = f"{path}.child{i}"
                    keys.extend(self._extract_keys(child, child_path))
        return keys 
            
    
    def _diff_with_previous(self, new_vdom):
        """Generate patches using functional diffing"""
        if self.last_vdom is None:
            print(f"first render- no diff")
            self.last_vdom = new_vdom
            return {'type': 'full', 'vdom': new_vdom}     
     
        old_vdom=self.last_vdom
        print(f"\n=== Diff Debug ===")
        print(f"OLD VDOM keys: {list(self._extract_keys(self.last_vdom))}")
        print(f"NEW VDOM keys: {list(self._extract_keys(new_vdom))}")
        print(f"Diffing: old VDOM type={self.last_vdom.get('type')}, new VDOM type={new_vdom.get('type')}")
        # Print Label texts to see if they changed 
        self._print_label_texts("OLD", self.last_vdom)
        self._print_label_texts("New", new_vdom)
        patches = self.differ.diff(old_vdom, new_vdom)
        print(f"Diff produced {len(patches)} patches")
        for i , patch in enumerate(patches[:10]):
            print(f" Patch {i}: {patch.get('type')} at {patch.get('path')}")
            if patch.get('type') == DiffType.UPDATE:
                print(f" Changed: {list(patch.get('props', {}).get('changed' , {}).keys())}")
        
        self.last_vdom = new_vdom
        
        if not patches:
            print(f"No patches generated- VDOMs are identical")
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
            try:
                # Render component with hook context
                rendered = _with_hook_rendering(node_type, props, path)
                return self._render_node_with_hooks(rendered, parent, path)
            except Exception as e:
                # Render error UI
                self._render_node_with_hooks(self._create_error_vdom(e), parent, path)
                return
        
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
            'props': {
                'bg': '#fee2e2',
                'padx': 20,
                'pady': 20,
                'class': 'p-4 m-2 border border-red-300 rounded'
            },
            'children': [
                {
                    'type': 'label',
                    'props': {
                        'text': '⚠️ Error Occurred',
                        'fg': '#991b1b',
                        'font_size': 16,
                        'font_weight': 'bold',
                        'class': 'text-red-800 font-bold text-lg'
                    }
                },
                {
                    'type': 'label',
                    'props': {
                        'text': str(error.error),
                        'fg': '#7f1d1d',
                        'font_size': 12,
                        'class': 'text-red-700 text-sm mt-2'
                    }
                }
            ]
        }
    
    def _create_error_vdom(self, error):
        """Create error VDOM for rendering errors"""
        return {
            'type': 'frame',
            'props': {'bg': '#fee2e2', 'padx': 20, 'pady': 20},
            'children': [
                {'type': 'label', 'props': {
                    'text': f'⚠️ Render Error: {error.__class__.__name__}',
                    'fg': '#991b1b',
                    'font_size': 16,
                    'font_weight': 'bold'
                }},
                {'type': 'label', 'props': {
                    'text': str(error),
                    'fg': '#7f1d1d',
                    'font_size': 12
                }}
            ]
        }
    
    def _handle_error(self, error: ErrorValue, stream_name: str):
        """Handle errors"""
        print(f"❌ Error in {stream_name}: {error.error}")
        if error.component_path:
            print(f"  Component path: {error.component_path}")
        print(f"  Recovery attempts: {error.recovery_attempts}")
    
    def _check_performance(self):
        """Check performance and log if needed"""
        current_time = time.time()
        if current_time - self.last_perf_check > self.perf_check_interval:
            self.last_perf_check = current_time
            
            stats = self.get_stats()
            if stats['performance'].get('create_vdom', {}).get('avg_ms', 0) > 16.67:
                print("⚠️  Performance warning: VDOM creation taking >16.67ms (60fps target)")
            
            if stats['cache']['hit_rate'] < '30%':
                print("⚠️  Performance warning: Cache hit rate below 30%")
    
    def run(self):
        """Start the application"""
        print(f"\n🚀 PyUIWizard {__version__} started")
        print(f"   Mode: {'Functional Diffing with Hooks' if self.use_diffing else 'Full Re-render'}")
        print(f"   Window: {self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")
        print(f"   Breakpoint: {self.layout_engine.get_breakpoint()}")
        
        # Start performance monitoring
        self.root.after(1000, self._check_performance)
        
        self.root.mainloop()
    
    def get_stats(self):
        """Get performance statistics"""
        stats = {
            'renders': self.render_count,
            'skipped': self.skip_count,
            'cache': self.cache.get_stats(),
            'performance': PERFORMANCE.get_stats(),
            'hooks': get_hook_debug_info(),
            'streams': {name: stream.get_stats() for name, stream in self.processor.streams.items()}
        }
        
        if self.use_diffing:
            stats['diffing'] = self.differ.get_stats()
            stats['renderer'] = self.renderer.get_stats()
            stats['patcher'] = self.renderer.patcher.get_stats()
        
        stats['layout'] = {
            'breakpoint': self.layout_engine.get_breakpoint(),
            'responsive': True
        }
        
        stats['design'] = {
            'theme': DESIGN_TOKENS.current_theme,
            'dark_mode': DESIGN_TOKENS.dark_mode,
            'css_variables': len(DESIGN_TOKENS.css_variables)
        }
        
        stats['errors'] = len(ERROR_BOUNDARY.get_errors())
        stats['time_travel'] = TIME_TRAVEL.get_stats()
        
        return stats
    
    def print_stats(self):
        """Print all statistics"""
        print("\n" + "="*80)
        print("PYUIWIZARD 4.2.0 - COMPLETE PRODUCTION STATISTICS")
        print("="*80)
        
        stats = self.get_stats()
        
        print(f"\n📊 RENDERING:")
        print(f"  Total renders: {stats['renders']}")
        print(f"  Skipped (cache): {stats['skipped']}")
        print(f"  Cache: {stats['cache']}")
        
        print(f"\n🎣 HOOKS:")
        print(f"  State count: {stats['hooks']['state_count']}")
        print(f"  Component instances: {stats['hooks']['component_instances']}")
        print(f"  Contexts: {stats['hooks'].get('contexts', 0)}")
        print(f"  Effects pending: {stats['hooks'].get('effect_queue', 0)}")
        
        if 'diffing' in stats:
            print(f"\n🔍 DIFFING:")
            diff_stats = stats['diffing']
            for key, value in diff_stats.items():
                print(f"  {key}: {value}")
        
        print(f"\n🎨 DESIGN:")
        print(f"  Theme: {stats['design']['theme']}")
        print(f"  Dark mode: {stats['design']['dark_mode']}")
        print(f"  CSS Variables: {stats['design']['css_variables']}")
        
        print(f"\n📱 LAYOUT:")
        print(f"  Breakpoint: {stats['layout']['breakpoint']}")
        print(f"  Responsive: {stats['layout']['responsive']}")
        
        print(f"\n⚠️  ERRORS: {stats['errors']}")
        print(f"\n⏱️  TIME TRAVEL: {stats['time_travel']['history_size']} snapshots")
        
        PERFORMANCE.print_stats()
        
        print("\n" + "="*80)
    
    def export_stats(self, filepath: str = "pyuiwizard_stats.json"):
        """Export all statistics to JSON file"""
        stats = self.get_stats()
        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        print(f"✅ Statistics exported to {filepath}")
        return stats
    
    def dispose(self):
        """Clean up resources"""
        self.processor.dispose_all()
        self.cache.clear()
        clear_component_state()  # Clear all hook state
        
        if self.use_diffing and self.renderer:
            self.renderer.patcher = FunctionalPatcher()
        
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
        
        print("🗑️  PyUIWizard disposed")
        
        
