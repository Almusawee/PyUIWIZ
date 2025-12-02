"""
PyUIWizard - Advanced Reactive GUI Framework with Functional VDOM Diffing
Version: 2.0.0 - With Functional Diffing

Standalone library module - import this for use in your projects
"""

import tkinter as tk
from typing import Callable, Any, List, Dict, Optional, Tuple, Union, TypeVar
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import json

T = TypeVar('T')

# ===============================
# Performance Monitor
# ===============================
class PerformanceMonitor:
    def __init__(self):
        self.operation_times = defaultdict(list)
        self.operation_counts = defaultdict(int)
    
    def measure_time(self, operation_name: str):
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                
                duration = (end_time - start_time) * 1000
                self.operation_times[operation_name].append(duration)
                self.operation_counts[operation_name] += 1
                return result
            return wrapper
        return decorator
    
    def get_stats(self):
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

PERFORMANCE = PerformanceMonitor()

# ===============================
# Diff Operation Types
# ===============================
class DiffType(Enum):
    CREATE = "CREATE"      # Node doesn't exist in old tree
    UPDATE = "UPDATE"      # Node exists but props changed
    REPLACE = "REPLACE"    # Node type changed
    REMOVE = "REMOVE"      # Node exists in old but not new
    REORDER = "REORDER"    # Children order changed
    NONE = "NONE"          # No change

# ===============================
# Functional Diffing Engine
# ===============================
class FunctionalDiffer:
    """
    Pure functional diffing using map, filter, zip, get, update
    """
    
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
        """
        Main diff function - returns list of operations
        Uses functional programming style
        """
        self.stats['diffs'] += 1
        
        # Handle null cases with filter
        if not new_vdom:
            return [{'type': DiffType.REMOVE, 'path': [], 'old': old_vdom}]
        
        if not old_vdom:
            return [{'type': DiffType.CREATE, 'path': [], 'node': new_vdom}]
        
        # Start diffing from root
        patches = self._diff_node(old_vdom, new_vdom, [])
        self.stats['patches'] += len(patches)
        return patches
    
    def _diff_node(self, old: Dict, new: Dict, path: List) -> List[Dict]:
        """
        Diff a single node using functional composition
        """
        patches = []
        
        # 1. Check if node type changed (early exit optimization)
        if old.get('type') != new.get('type'):
            self.stats['replace_ops'] += 1
            return [{'type': DiffType.REPLACE, 'path': path, 'old': old, 'new': new}]
        
        # 2. Check if key changed (for keyed reconciliation)
        if old.get('key') != new.get('key'):
            self.stats['replace_ops'] += 1
            return [{'type': DiffType.REPLACE, 'path': path, 'old': old, 'new': new}]
        
        # 3. Diff props using functional approach
        props_patch = self._diff_props(
            old.get('props', {}),
            new.get('props', {}),
            path
        )
        
        # Filter out empty patches
        if props_patch:
            patches.append(props_patch)
            self.stats['update_ops'] += 1
        
        # 4. Diff children using zip, map, filter
        children_patches = self._diff_children(
            old.get('children', []),
            new.get('children', []),
            path
        )
        
        # Filter and flatten
        patches.extend(filter(lambda p: p is not None, children_patches))
        
        return patches
    
    def _diff_props(self, old_props: Dict, new_props: Dict, path: List) -> Optional[Dict]:
        """
        Diff properties using dict methods (get, update)
        """
        # Find changed/added props using dict comprehension (map + filter combined)
        changed = {
            key: new_props[key]
            for key in new_props
            if old_props.get(key) != new_props.get(key)
        }
        
        # Find removed props using filter
        removed = list(filter(
            lambda key: key not in new_props,
            old_props.keys()
        ))
        
        # Only return patch if there are changes
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
        """
        Diff children using zip, map, filter for maximum efficiency
        """
        # Check if any children have keys
        has_keys = any(c.get('key') is not None for c in new_children)
        
        if has_keys:
            return self._diff_keyed_children(old_children, new_children, path)
        else:
            return self._diff_indexed_children(old_children, new_children, path)
    
    def _diff_indexed_children(self, old_children: List, new_children: List, path: List) -> List[Dict]:
        """
        Diff children by index using zip and map
        Strategy: Use zip to pair up children, then map to diff each pair
        """
        max_len = max(len(old_children), len(new_children))
        
        # Pad shorter list with None
        old_padded = old_children + [None] * (max_len - len(old_children))
        new_padded = new_children + [None] * (max_len - len(new_children))
        
        # Use zip + map to diff each pair
        patches = map(
            lambda indexed: self._diff_child_pair(
                indexed[1][0],  # old child
                indexed[1][1],  # new child
                path + [indexed[0]]  # child index
            ),
            enumerate(zip(old_padded, new_padded))
        )
        
        # Flatten and filter None patches
        return list(filter(lambda p: p, self._flatten(patches)))
    
    def _diff_keyed_children(self, old_children: List, new_children: List, path: List) -> List[Dict]:
        """
        Diff keyed children for optimal list updates
        Strategy: Use dict.get() for O(1) lookups
        """
        # Create key maps using dict comprehension (functional map)
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
        
        # 1. Find updated/added keys using map
        for key, new_child in new_by_key.items():
            old_child = old_by_key.get(key)  # O(1) lookup using get()
            
            if old_child:
                # Key exists - diff the nodes
                child_patches = self._diff_node(old_child, new_child, path + [key])
                patches.extend(child_patches)
            else:
                # New key - create node
                patches.append({
                    'type': DiffType.CREATE,
                    'path': path + [key],
                    'node': new_child
                })
                self.stats['create_ops'] += 1
        
        # 2. Find removed keys using filter
        removed_keys = filter(
            lambda key: key not in new_by_key,
            old_by_key.keys()
        )
        
        # Map removed keys to REMOVE patches
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
        
        # 3. Check for reordering (optional optimization)
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
        """Check if keyed children were reordered using zip"""
        old_keys = [c.get('key') for c in old_children if c.get('key')]
        new_keys = [c.get('key') for c in new_children if c.get('key')]
        
        if len(old_keys) != len(new_keys):
            return False
        
        # Use zip to compare orders
        return not all(map(lambda pair: pair[0] == pair[1], zip(old_keys, new_keys)))
    
    def _flatten(self, nested_list):
        """Flatten nested list using functional approach"""
        result = []
        for item in nested_list:
            if isinstance(item, list):
                result.extend(self._flatten(item))
            else:
                result.append(item)
        return result
    
    def get_stats(self):
        return self.stats.copy()

# ===============================
# Functional Patch Application
# ===============================
class FunctionalPatcher:
    """
    Apply patches using functional composition
    """
    
    def __init__(self):
        self.widget_map = {}  # path -> widget
        self.key_map = {}     # key -> widget
        self.widget_to_path = {}
        self.widget_to_key = {}
        self.parent_map = {}
    
    @PERFORMANCE.measure_time('apply_patches')
    def apply_patches(self, patches: List[Dict], vdom: Dict, root_widget):
        """
        Apply patches using map and filter
        Optimized: batch similar operations together
        """
        # First, ensure we have the full VDOM tree
        self._update_vdom_tree(vdom)
        
        # Group patches by type using filter
        from collections import defaultdict
        grouped = defaultdict(list)
        for patch in patches:
            grouped[patch['type']].append(patch)
        
        # Apply in optimal order: removes first, then creates, then updates, then replaces
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
        """Apply REMOVE patch"""
        path = patch['path']
        widget = self._get_widget_by_path(path, root_widget)
        
        if widget:
            # Destroy widget and clean up mappings
            widget.destroy()
            self._cleanup_widget_mappings(widget, path)
    
    def _apply_create(self, patch: Dict, root_widget):
        """Apply CREATE patch"""
        path = patch['path']
        node = patch['node']
        
        # Find parent widget
        parent_path = path[:-1] if len(path) > 1 else []
        parent = self._get_widget_by_path(parent_path, root_widget)
        
        if parent is None:
            parent = root_widget
        
        # Create widget
        widget = self._create_widget_from_node(node, parent)
        
        # Store mappings
        path_key = tuple(path)
        self.widget_map[path_key] = widget
        if 'key' in node:
            self.key_map[node['key']] = widget
            self.widget_to_key[widget] = node['key']
        self.widget_to_path[widget] = path_key
        self.parent_map[widget] = parent
        
        # Apply layout based on position
        self._apply_layout(widget, node, parent, path[-1] if path else 0)
    
    def _apply_update(self, patch: Dict, root_widget):
        """Apply UPDATE patch"""
        path = patch['path']
        props = patch['props']
        
        widget = self._get_widget_by_path(path, root_widget)
        if widget:
            # Apply property changes
            for key, value in props.get('changed', {}).items():
                self._update_widget_prop(widget, key, value)
            
            # Handle removed props
            for key in props.get('removed', []):
                self._reset_widget_prop(widget, key)
    
    def _apply_replace(self, patch: Dict, root_widget):
        """Apply REPLACE patch"""
        path = patch['path']
        new_node = patch['new']
        
        widget = self._get_widget_by_path(path, root_widget)
        if widget:
            # Store geometry info
            pack_info = widget.pack_info() if widget.pack_info() else {}
            
            # Destroy old widget
            old_key = self.widget_to_key.get(widget)
            widget.destroy()
            
            # Clean up old mappings
            self._cleanup_widget_mappings(widget, path)
            
            # Create new widget
            parent_path = path[:-1] if len(path) > 1 else []
            parent = self._get_widget_by_path(parent_path, root_widget) or root_widget
            new_widget = self._create_widget_from_node(new_node, parent)
            
            # Update mappings
            path_key = tuple(path)
            self.widget_map[path_key] = new_widget
            if 'key' in new_node:
                self.key_map[new_node['key']] = new_widget
                self.widget_to_key[new_widget] = new_node['key']
            self.widget_to_path[new_widget] = path_key
            self.parent_map[new_widget] = parent
            
            # Restore geometry
            if pack_info:
                new_widget.pack(**pack_info)
    
    def _apply_reorder(self, patch: Dict, root_widget):
        """Apply REORDER patch"""
        path = patch['path']
        new_order = patch['new_order']
        
        parent_widget = self._get_widget_by_path(path, root_widget)
        if parent_widget and hasattr(parent_widget, 'winfo_children'):
            # Get current children
            children = parent_widget.winfo_children()
            
            if children and new_order:
                # Remove all children from parent
                for child in children:
                    child.pack_forget()
                
                # Re-add in new order
                for key in new_order:
                    widget = self.key_map.get(key)
                    if widget and widget.master == parent_widget:
                        # Use last known pack config or default
                        widget.pack(side='top', fill='x', padx=5, pady=2)
    
    def _get_widget_by_path(self, path: List, root_widget):
        """Get widget by path"""
        if not path:
            return root_widget
        return self.widget_map.get(tuple(path))
    
    def _create_widget_from_node(self, node: Dict, parent) -> tk.Widget:
        """Create Tkinter widget from VDOM node"""
        node_type = node.get('type', 'frame')
        props = node.get('props', {})
        
        if node_type == 'frame':
            widget = tk.Frame(
                parent,
                bg=props.get('bg', 'white'),
                relief=props.get('relief', 'flat')
            )
            if props.get('border_width', 0) > 0:
                widget.config(relief='solid', bd=props.get('border_width'))
            
        elif node_type == 'label':
            font_size = props.get('font_size', 12)
            font_weight = props.get('font_weight', 'normal')
            font = ('Arial', font_size, font_weight)
            
            widget = tk.Label(
                parent,
                text=props.get('text', ''),
                fg=props.get('fg', 'black'),
                bg=props.get('bg', parent['bg'] if isinstance(parent, tk.Frame) else 'white'),
                font=font
            )
            
        elif node_type == 'button':
            font_size = props.get('font_size', 10)
            font = ('Arial', font_size)
            
            widget = tk.Button(
                parent,
                text=props.get('text', ''),
                fg=props.get('fg', 'white'),
                bg=props.get('bg', 'gray'),
                activebackground=props.get('active_bg', props.get('bg', 'gray')),
                command=props.get('onClick'),
                font=font,
                relief='flat',
                cursor='hand2'
            )
            
        elif node_type == 'entry':
            widget = tk.Entry(
                parent,
                bg=props.get('bg', 'white'),
                fg=props.get('fg', 'black'),
                font=('Arial', props.get('font_size', 12))
            )
            if 'text' in props:
                widget.insert(0, props['text'])
            if 'onChange' in props:
                widget.bind('<KeyRelease>', lambda e: props['onChange'](widget.get()))
        
        else:
            widget = tk.Frame(parent, bg='white')
        
        return widget
    
    def _update_widget_prop(self, widget, prop: str, value):
        """Update a widget property"""
        if isinstance(widget, tk.Label):
            if prop == 'text':
                widget.config(text=value)
            elif prop == 'fg':
                widget.config(fg=value)
            elif prop == 'bg':
                widget.config(bg=value)
            elif prop == 'font_size':
                current_font = widget.cget('font')
                if isinstance(current_font, str):
                    parts = current_font.split()
                    if len(parts) >= 2:
                        parts[1] = str(value)
                        widget.config(font=' '.join(parts))
            
        elif isinstance(widget, tk.Button):
            if prop == 'text':
                widget.config(text=value)
            elif prop == 'fg':
                widget.config(fg=value)
            elif prop == 'bg':
                widget.config(bg=value)
            elif prop == 'active_bg':
                widget.config(activebackground=value)
            elif prop == 'onClick':
                widget.config(command=value)
            
        elif isinstance(widget, tk.Frame):
            if prop == 'bg':
                widget.config(bg=value)
            elif prop == 'border_width':
                if value > 0:
                    widget.config(relief='solid', bd=value)
                else:
                    widget.config(relief='flat', bd=0)
    
    def _reset_widget_prop(self, widget, prop: str):
        """Reset a widget property to default"""
        defaults = {
            'fg': 'black',
            'bg': widget.master['bg'] if hasattr(widget.master, 'cget') else 'white',
            'text': '',
            'font': ('Arial', 10, 'normal'),
            'relief': 'flat',
            'bd': 0
        }
        
        if prop in defaults:
            if prop == 'fg' and isinstance(widget, (tk.Label, tk.Button)):
                widget.config(fg=defaults['fg'])
            elif prop == 'bg':
                widget.config(bg=defaults['bg'])
            elif prop == 'text' and isinstance(widget, (tk.Label, tk.Button)):
                widget.config(text=defaults['text'])
            elif prop == 'font':
                widget.config(font=defaults['font'])
    
    def _apply_layout(self, widget, node, parent, position):
        """Apply layout/packing to widget"""
        props = node.get('props', {})
        
        # Default packing
        pack_opts = {
            'side': 'top',
            'padx': props.get('padx', 5),
            'pady': props.get('pady', 2),
            'fill': 'x' if props.get('width_full') else 'none'
        }
        
        widget.pack(**pack_opts)
    
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
    
    def _update_vdom_tree(self, vdom: Dict):
        """Update internal VDOM tracking (simplified)"""
        # This is a placeholder - in a full implementation, we'd track the VDOM tree
        # For now, we just clear and rebuild from scratch when needed
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
    
    def handle_error(self, error: ErrorValue, stream_name: str = "unknown"):
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
        if stream_name:
            return [e for e in self.errors if e['stream'] == stream_name]
        return self.errors
    
    def clear_errors(self):
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
    
    def record(self, snapshot: StateSnapshot):
        if self.enabled and not self.paused:
            self.history.append(snapshot)
            self.current_index = len(self.history) - 1
    
    def undo(self):
        if self.current_index > 0:
            self.current_index -= 1
            return self.history[self.current_index]
        return None
    
    def redo(self):
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
        return None
    
    def export_history(self, filepath: str):
        data = [snapshot.to_dict() for snapshot in self.history]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ History exported to {filepath}")

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
    
    def get(self, key: str):
        if key in self.cache:
            self.access_count[key] += 1
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any):
        if len(self.cache) >= self.max_size:
            min_key = min(self.access_count, key=self.access_count.get)
            del self.cache[min_key]
            del self.access_count[min_key]
        self.cache[key] = value
        self.access_count[key] = 0
    
    def clear(self):
        self.cache.clear()
        self.access_count.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self):
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%"
        }

# ===============================
# Reactive Stream (Complete)
# ===============================
class Stream:
    _id_counter = 0
    
    def __init__(self, initial_value=None, name: Optional[str] = None):
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
        return self._value
    
    def set(self, new_value):
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
        for subscriber in self._subscribers[:]:
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
        return list(self._local_history)
    
    def subscribe(self, subscriber_fn: Callable):
        if not self._disposed:
            self._subscribers.append(subscriber_fn)
        return lambda: self._subscribers.remove(subscriber_fn) if subscriber_fn in self._subscribers else None
    
    def dispose(self):
        if not self._disposed:
            self._disposed = True
            if self._debounce_timer:
                self._debounce_timer.cancel()
            self._subscribers.clear()
            self._error_handlers.clear()
            print(f"🗑️  Disposed stream: {self.name}")
    
    def __repr__(self):
        status = "disposed" if self._disposed else f"value={self._value}"
        return f"Stream({self.name}, {status}, subs={len(self._subscribers)})"

# ===============================
# StreamProcessor
# ===============================
class StreamProcessor:
    def __init__(self):
        self.streams: Dict[str, Stream] = {}
        self.pipelines: Dict[str, Stream] = {}
    
    def create_stream(self, name: str, initial_value=None) -> Stream:
        stream = Stream(initial_value, name=name)
        self.streams[name] = stream
        return stream
    
    def combine_latest(self, stream_names: List[str], combine_fn: Callable = None) -> Stream:
        result = Stream(name=f"combineLatest({','.join(stream_names)})")
        latest = {}
        
        def update_combined(stream_name):
            def updater(new_val, old_val):
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
        self.pipelines[name] = current
        return current
    
    def dispose_all(self):
        for s in list(self.streams.values()) + list(self.pipelines.values()):
            s.dispose()
        self.streams.clear()
        self.pipelines.clear()

# ===============================
# Advanced Style Resolver (Complete)
# ===============================
class AdvancedStyleResolver:
    def __init__(self):
        self.tokens = DESIGN_TOKENS
        self.breakpoint = 'md'
        self.style_cache = {}
    
    def set_breakpoint(self, bp):
        self.breakpoint = bp
        self.style_cache.clear()
    
    def resolve_classes(self, class_string, current_breakpoint=None):
        if current_breakpoint:
            self.breakpoint = current_breakpoint
        
        cache_key = f"{class_string}_{self.breakpoint}_{self.tokens.current_theme}"
        if cache_key in self.style_cache:
            return self.style_cache[cache_key]
        
        resolved = {}
        for cls in class_string.split():
            self._resolve_class(cls, resolved)
        
        self.style_cache[cache_key] = resolved
        return resolved
    
    def _resolve_class(self, cls, resolved):
        # Handle breakpoint prefixes (FIXED LOGIC)
        if ':' in cls:
            bp_prefix, actual_cls = cls.split(':', 1)
            if bp_prefix in ['sm', 'md', 'lg', 'xl', '2xl']:
                bp_order = ['sm', 'md', 'lg', 'xl', '2xl']
                current_idx = bp_order.index(self.breakpoint) if self.breakpoint in bp_order else 1
                prefix_idx = bp_order.index(bp_prefix)
                # FIXED: md: means "apply at md and above"
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
            # Check if it's a size first
            sizes = ['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl']
            if color_part in sizes:
                return {'font_size': self.tokens.tokens['font_size'][color_part]}
            # Otherwise it's a color
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
            return {'pady_top': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        if cls.startswith('pb-'):
            return {'pady_bottom': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        if cls.startswith('pl-'):
            return {'padx_left': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        if cls.startswith('pr-'):
            return {'padx_right': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        
        # Margin
        if cls.startswith('m-'):
            val = self.tokens.tokens['spacing'].get(cls[2:], 0)
            return {'margin': val}
        if cls.startswith('mx-'):
            return {'margin_x': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        if cls.startswith('my-'):
            return {'margin_y': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        if cls.startswith('mt-'):
            return {'margin_top': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        if cls.startswith('mb-'):
            return {'margin_bottom': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        if cls.startswith('ml-'):
            return {'margin_left': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        if cls.startswith('mr-'):
            return {'margin_right': self.tokens.tokens['spacing'].get(cls[3:], 0)}
        
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
        if cls == 'items-center':
            return {'align_items': 'center'}
        if cls == 'justify-center':
            return {'justify': 'center'}
        
        # Display
        if cls == 'hidden':
            return {'visible': False}
        if cls == 'block':
            return {'visible': True}
        
        # Typography
        if cls.startswith('font-'):
            weight = cls[5:]
            if weight in self.tokens.tokens['font_weight']:
                return {'font_weight': self.tokens.tokens['font_weight'][weight]}
        
        # Border radius
        if cls.startswith('rounded'):
            if cls == 'rounded':
                return {'border_radius': self.tokens.tokens['border_radius']['default']}
            size = cls[8:] if cls.startswith('rounded-') else 'default'
            return {'border_radius': self.tokens.tokens['border_radius'].get(size, 4)}
        
        # Border
        if cls == 'border':
            return {'border_width': 1}
        if cls.startswith('border-'):
            size = cls[7:]
            if size.isdigit():
                return {'border_width': int(size)}
        
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
            print(f"📐 Breakpoint: {new_bp} ({width}px)")

# ===============================
# PyUIWizard Renderer WITH FUNCTIONAL DIFFING
# ===============================
class PyUIWizardRenderer:
    def __init__(self, root_window, use_diffing=True):
        self.processor = StreamProcessor()
        self.style_resolver = AdvancedStyleResolver()
        self.layout_engine = ResponsiveLayoutEngine(root_window)
        self.cache = VDOMCache()
        self.render_count = 0
        self.skip_count = 0
        
        # Functional diffing components
        self.use_diffing = use_diffing
        self.differ = FunctionalDiffer() if use_diffing else None
        self.patcher = FunctionalPatcher() if use_diffing else None
        self.last_vdom = None
        
        # Create state streams
        self.count_stream = self.processor.create_stream('count', 0).track_history()
        self.theme_stream = self.processor.create_stream('theme', 'light')
        
        # Setup pipelines based on diffing mode
        if use_diffing:
            self.setup_functional_pipeline()
        else:
            self.setup_original_pipeline()
    
    def setup_original_pipeline(self):
        """Original pipeline without diffing"""
        combined = self.processor.combine_latest(
            ['count', 'theme'],
            lambda count, theme: {
                'count': count,
                'theme': theme,
                'window_bp': self.layout_engine.current_breakpoint
            }
        ).catch_error(lambda err: {'count': 0, 'theme': 'light', 'window_bp': 'md'})
        
        self.ui_stream = self.processor.create_pipeline(
            'ui_pipeline',
            combined,
            ('distinct',),
            ('map', self._create_ui),
            ('map', self._resolve_styles),
            ('catch', lambda err: self._error_ui(err))
        )
        
        # React to breakpoint changes
        self.layout_engine.breakpoint_stream.subscribe(
            lambda bp, old: (self.style_resolver.set_breakpoint(bp), self.cache.clear())
        )
    
    def setup_functional_pipeline(self):
        """Enhanced pipeline with functional diffing"""
        combined = self.processor.combine_latest(
            ['count', 'theme'],
            lambda count, theme: {
                'count': count,
                'theme': theme,
                'window_bp': self.layout_engine.current_breakpoint
            }
        ).catch_error(lambda err: {'count': 0, 'theme': 'light', 'window_bp': 'md'})
        
        # Functional pipeline with diffing
        self.ui_stream = self.processor.create_pipeline(
            'ui_functional_pipeline',
            combined,
            ('distinct',),
            ('map', self._create_keyed_ui),  # Uses keys for diffing
            ('map', self._resolve_styles),
            ('debounce', 0.016),  # 60fps batching
            ('map', self._diff_with_previous),  # Functional diffing
            ('catch', lambda err: self._error_ui(err))
        )
        
        # React to breakpoint changes
        self.layout_engine.breakpoint_stream.subscribe(
            lambda bp, old: (self.style_resolver.set_breakpoint(bp), self.cache.clear())
        )
    
    @PERFORMANCE.measure_time('create_ui')
    def _create_ui(self, state):
        """Original UI creation without keys"""
        count, theme, bp = state['count'], state['theme'], state['window_bp']
        
        # Check cache
        cache_key = f"{count}_{theme}_{bp}"
        cached = self.cache.get(cache_key)
        if cached:
            self.skip_count += 1
            return cached
        
        self.render_count += 1
        
        # Responsive button sizing
        btn_size = 'px-6 py-3 text-lg' if bp in ['lg', 'xl', '2xl'] else 'px-4 py-2 text-base'
        layout = 'flex gap-4' if bp in ['md', 'lg', 'xl', '2xl'] else 'flex-col gap-2'
        
        vdom = {
            'type': 'frame',
            'props': {'class': f"bg-{'gray-800' if theme == 'dark' else 'gray-100'} p-6 rounded-lg"},
            'children': [
                {'type': 'label', 'props': {
                    'text': f'Count: {count}',
                    'class': f"text-{'white' if theme == 'dark' else 'gray-900'} text-3xl font-bold"
                }},
                {'type': 'label', 'props': {
                    'text': f'Breakpoint: {bp} | Theme: {theme}',
                    'class': f"text-{'gray-400' if theme == 'dark' else 'gray-600'} text-sm"
                }},
                {'type': 'frame', 'props': {'class': layout}, 'children': [
                    {'type': 'button', 'props': {
                        'text': '+ Increment',
                        'class': f'bg-blue-500 hover:bg-blue-600 text-white rounded {btn_size}',
                        'onClick': self.increment
                    }},
                    {'type': 'button', 'props': {
                        'text': '- Decrement',
                        'class': f'bg-red-500 hover:bg-red-600 text-white rounded {btn_size}',
                        'onClick': self.decrement
                    }},
                    {'type': 'button', 'props': {
                        'text': '↺ Reset',
                        'class': f'bg-gray-500 hover:bg-gray-600 text-white rounded {btn_size}',
                        'onClick': self.reset
                    }}
                ]}
            ]
        }
        
        # Cache result
        self.cache.set(cache_key, vdom)
        return vdom
    
    @PERFORMANCE.measure_time('create_keyed_ui')
    def _create_keyed_ui(self, state):
        """Create VDOM with stable keys for functional diffing"""
        count, theme, bp = state['count'], state['theme'], state['window_bp']
        
        # Check cache
        cache_key = f"keyed_{count}_{theme}_{bp}"
        cached = self.cache.get(cache_key)
        if cached:
            self.skip_count += 1
            return cached
        
        self.render_count += 1
        
        # Responsive button sizing
        btn_size = 'px-6 py-3 text-lg' if bp in ['lg', 'xl', '2xl'] else 'px-4 py-2 text-base'
        layout = 'flex gap-4' if bp in ['md', 'lg', 'xl', '2xl'] else 'flex-col gap-2'
        
        # Create VDOM with stable keys
        vdom = {
            'type': 'frame',
            'key': 'root',
            'props': {'class': f"bg-{'gray-800' if theme == 'dark' else 'gray-100'} p-6 rounded-lg"},
            'children': [
                {
                    'type': 'label',
                    'key': 'count_display',
                    'props': {
                        'text': f'Count: {count}',
                        'class': f"text-{'white' if theme == 'dark' else 'gray-900'} text-3xl font-bold"
                    }
                },
                {
                    'type': 'label',
                    'key': 'status_info',
                    'props': {
                        'text': f'Breakpoint: {bp} | Theme: {theme}',
                        'class': f"text-{'gray-400' if theme == 'dark' else 'gray-600'} text-sm"
                    }
                },
                {
                    'type': 'frame',
                    'key': 'controls',
                    'props': {'class': layout},
                    'children': [
                        {
                            'type': 'button',
                            'key': 'inc_button',
                            'props': {
                                'text': '+ Increment',
                                'class': f'bg-blue-500 hover:bg-blue-600 text-white rounded {btn_size}',
                                'onClick': self.increment
                            }
                        },
                        {
                            'type': 'button',
                            'key': 'dec_button',
                            'props': {
                                'text': '- Decrement',
                                'class': f'bg-red-500 hover:bg-red-600 text-white rounded {btn_size}',
                                'onClick': self.decrement
                            }
                        },
                        {
                            'type': 'button',
                            'key': 'reset_button',
                            'props': {
                                'text': '↺ Reset',
                                'class': f'bg-gray-500 hover:bg-gray-600 text-white rounded {btn_size}',
                                'onClick': self.reset
                            }
                        }
                    ]
                }
            ]
        }
        
        # Cache result
        self.cache.set(cache_key, vdom)
        return vdom
    
    @PERFORMANCE.measure_time('resolve_styles')
    def _resolve_styles(self, vdom):
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
        return resolve(vdom)
    
    @PERFORMANCE.measure_time('functional_diff')
    def _diff_with_previous(self, new_vdom):
        """Generate patches using functional diffing"""
        if self.last_vdom is None:
            self.last_vdom = new_vdom
            return {'type': 'full', 'vdom': new_vdom}
        
        # Use the functional differ
        patches = self.differ.diff(self.last_vdom, new_vdom)
        self.last_vdom = new_vdom
        
        if not patches:
            return {'type': 'none'}
        
        return {'type': 'patches', 'patches': patches, 'vdom': new_vdom}
    
    def _error_ui(self, error: ErrorValue):
        return {
            'type': 'frame',
            'key': 'error_frame',
            'props': {'class': 'bg-red-100 p-4 rounded border'},
            'children': [
                {'type': 'label', 'key': 'error_title', 'props': {
                    'text': '⚠️ Error Occurred',
                    'class': 'text-red-800 font-bold text-lg'
                }},
                {'type': 'label', 'key': 'error_message', 'props': {
                    'text': str(error.error),
                    'class': 'text-red-700 text-sm'
                }}
            ]
        }
    
    def increment(self):
        self.count_stream.set(self.count_stream.value + 1)
    
    def decrement(self):
        self.count_stream.set(self.count_stream.value - 1)
    
    def reset(self):
        self.count_stream.set(0)
    
    def set_theme(self, theme):
        DESIGN_TOKENS.set_theme(theme)
        self.theme_stream.set(theme)
        self.cache.clear()
    
    def subscribe_to_updates(self, callback):
        return self.ui_stream.subscribe(callback)
    
    def get_stats(self):
        return {
            'renders': self.render_count,
            'skipped': self.skip_count,
            'efficiency': f"{(self.skip_count / max(self.render_count + self.skip_count, 1)) * 100:.1f}%",
            'cache': self.cache.get_stats()
        }
    
    def get_diff_stats(self):
        if self.differ:
            return self.differ.get_stats()
        return {}
    
    def dispose(self):
        self.processor.dispose_all()
        self.cache.clear()

# ===============================
# Functional Tkinter Renderer
# ===============================
class FunctionalTkinterRenderer:
    """Renderer that uses functional diffing for incremental updates"""
    
    def __init__(self, root):
        self.root = root
        self.patcher = FunctionalPatcher()
        self.current_vdom = None
        self.widgets = []  # For backward compatibility
    
    @PERFORMANCE.measure_time('functional_render')
    def render(self, diff_result):
        """Render using functional diffing result"""
        render_type = diff_result.get('type', 'full')
        
        if render_type == 'full':
            # Clear and render full tree
            self._render_full(diff_result['vdom'])
            self.current_vdom = diff_result['vdom']
            
        elif render_type == 'patches':
            # Apply patches incrementally
            patches = diff_result['patches']
            vdom = diff_result['vdom']
            self.patcher.apply_patches(patches, vdom, self.root)
            self.current_vdom = vdom
            
        elif render_type == 'none':
            # No changes needed
            pass
    
    def _render_full(self, vdom):
        """Render full VDOM tree (fallback)"""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Clear patcher state
        self.patcher = FunctionalPatcher()
        
        # Reset widgets list
        self.widgets = []
        
        # Render using patcher as single create
        self.patcher.apply_patches([{
            'type': DiffType.CREATE,
            'path': [],
            'node': vdom
        }], vdom, self.root)
        
        # Track all widgets for backward compatibility
        self._collect_widgets(self.root)
    
    def _collect_widgets(self, parent):
        """Collect all widgets for backward compatibility"""
        for child in parent.winfo_children():
            self.widgets.append(child)
            if hasattr(child, 'winfo_children'):
                self._collect_widgets(child)
    
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
# Original Tkinter Renderer (for backward compatibility)
# ===============================
class TkinterRenderer:
    def __init__(self, root):
        self.root = root
        self.widgets = []
    
    @PERFORMANCE.measure_time('tkinter_render')
    def render(self, vdom):
        # Clear previous widgets
        for w in self.widgets:
            w.destroy()
        self.widgets.clear()
        
        # Render new VDOM
        self._render_node(vdom, self.root)
    
    def _render_node(self, node, parent):
        t, props = node['type'], node.get('props', {})
        widget = None
        
        if t == 'frame':
            widget = self._create_frame(parent, props)
            if widget:
                for child in node.get('children', []):
                    self._render_node(child, widget)
        
        elif t == 'label':
            widget = self._create_label(parent, props)
        
        elif t == 'button':
            widget = self._create_button(parent, props)
        
        elif t == 'entry':
            widget = self._create_entry(parent, props)
        
        if widget and props.get('visible', True):
            self.widgets.append(widget)
        
        return widget
    
    def _create_frame(self, parent, props):
        if not props.get('visible', True):
            return None
        
        bg = props.get('bg', parent['bg'] if isinstance(parent, tk.Frame) else 'white')
        frame = tk.Frame(parent, bg=bg, relief=props.get('relief', 'flat'))
        
        # Apply border
        if props.get('border_width', 0) > 0:
            frame.config(relief='solid', bd=props.get('border_width'))
        
        # Calculate padding/margin
        padx = props.get('padx', 0) + props.get('margin', 0) + props.get('margin_x', 0) + props.get('margin_left', 0)
        pady = props.get('pady', 0) + props.get('margin', 0) + props.get('margin_y', 0) + props.get('margin_top', 0)
        
        # Handle layout
        layout = props.get('layout', 'vertical')
        spacing = props.get('spacing', 0)
        
        pack_opts = {
            'padx': padx,
            'pady': pady,
            'fill': 'both',
            'expand': True
        }
        
        if props.get('width_full'):
            pack_opts['fill'] = 'x'
        if props.get('height_full'):
            pack_opts['fill'] = 'y'
        
        frame.pack(**pack_opts)
        return frame
    
    def _create_label(self, parent, props):
        if not props.get('visible', True):
            return None
        
        font_size = props.get('font_size', 12)
        font_weight = props.get('font_weight', 'normal')
        font = ('Arial', font_size, font_weight)
        
        bg = props.get('bg', parent['bg'] if isinstance(parent, tk.Frame) else 'white')
        
        label = tk.Label(
            parent,
            text=props.get('text', ''),
            fg=props.get('fg', 'black'),
            bg=bg,
            font=font
        )
        
        pady = props.get('pady', 5) + props.get('margin', 0) + props.get('margin_y', 0)
        padx = props.get('padx', 0) + props.get('margin', 0) + props.get('margin_x', 0)
        
        label.pack(pady=pady, padx=padx)
        return label
    
    def _create_button(self, parent, props):
        if not props.get('visible', True):
            return None
        
        font_size = props.get('font_size', 10)
        font = ('Arial', font_size)
        
        button = tk.Button(
            parent,
            text=props.get('text', ''),
            fg=props.get('fg', 'white'),
            bg=props.get('bg', 'gray'),
            activebackground=props.get('active_bg', props.get('bg', 'gray')),
            command=props.get('onClick'),
            font=font,
            relief='flat',
            cursor='hand2'
        )
        
        # Calculate padding/margin
        pady = props.get('pady', 5) + props.get('margin', 0) + props.get('margin_y', 0)
        padx = props.get('padx', 10) + props.get('margin', 0) + props.get('margin_x', 0)
        
        # Layout based on parent
        side = 'left' if props.get('layout') == 'horizontal' else 'top'
        button.pack(side=side, padx=padx, pady=pady)
        return button
    
    def _create_entry(self, parent, props):
        if not props.get('visible', True):
            return None
        
        entry = tk.Entry(
            parent,
            bg=props.get('bg', 'white'),
            fg=props.get('fg', 'black'),
            font=('Arial', props.get('font_size', 12))
        )
        
        if 'text' in props:
            entry.insert(0, props['text'])
        
        if 'onChange' in props:
            entry.bind('<KeyRelease>', lambda e: props['onChange'](entry.get()))
        
        pady = props.get('pady', 5) + props.get('margin', 0)
        padx = props.get('padx', 10) + props.get('margin', 0)
        entry.pack(pady=pady, padx=padx, fill='x')
        return entry