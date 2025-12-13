"""
Real-Time Collaborative Whiteboard
Features: Multi-user collaboration, real-time sync, drawing tools, chat
"""
from pyuiwizard import PyUIWizard, create_element, use_state, use_effect, use_ref, Component
import json
import time
import uuid
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math

# ======================================
# 1. DATA MODELS
# ======================================
@dataclass
class DrawingPoint:
    x: float
    y: float
    pressure: float = 1.0
    timestamp: float = 0.0
    
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'pressure': self.pressure,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            x=data['x'],
            y=data['y'],
            pressure=data.get('pressure', 1.0),
            timestamp=data.get('timestamp', time.time())
        )

@dataclass
class DrawingStroke:
    id: str
    user_id: str
    color: str
    width: float
    points: List[DrawingPoint]
    tool: str = 'pen'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'color': self.color,
            'width': self.width,
            'points': [p.to_dict() for p in self.points],
            'tool': self.tool
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            color=data['color'],
            width=data['width'],
            points=[DrawingPoint.from_dict(p) for p in data['points']],
            tool=data.get('tool', 'pen')
        )

@dataclass
class WhiteboardUser:
    id: str
    name: str
    color: str
    cursor_x: float = 0
    cursor_y: float = 0
    last_seen: float = time.time()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'cursor_x': self.cursor_x,
            'cursor_y': self.cursor_y,
            'last_seen': self.last_seen
        }

# ======================================
# 2. COLLABORATION SERVICE (MOCK)
# ======================================
class CollaborationService:
    """Mock collaboration service - in production would use WebSockets"""
    
    def __init__(self):
        self.strokes: Dict[str, DrawingStroke] = {}
        self.users: Dict[str, WhiteboardUser] = {}
        self.callbacks = []
        self.user_id = str(uuid.uuid4())
        self.user_name = f"User_{random.randint(1000, 9999)}"
        self.user_color = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
        
        # Add current user
        self.users[self.user_id] = WhiteboardUser(
            id=self.user_id,
            name=self.user_name,
            color=self.user_color
        )
    
    def connect(self, on_update):
        """Connect to collaboration service"""
        self.callbacks.append(on_update)
        
        # Simulate other users joining
        for i in range(3):
            user_id = str(uuid.uuid4())
            self.users[user_id] = WhiteboardUser(
                id=user_id,
                name=f"User_{i+1}",
                color=f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
            )
        
        return self.user_id
    
    def send_stroke(self, stroke: DrawingStroke):
        """Send a drawing stroke to server"""
        self.strokes[stroke.id] = stroke
        
        # Notify local callbacks
        for callback in self.callbacks:
            callback({'type': 'stroke_added', 'stroke': stroke.to_dict()})
    
    def send_cursor_position(self, x: float, y: float):
        """Send cursor position to server"""
        if self.user_id in self.users:
            self.users[self.user_id].cursor_x = x
            self.users[self.user_id].cursor_y = y
            self.users[self.user_id].last_seen = time.time()
    
    def get_strokes(self):
        """Get all strokes"""
        return list(self.strokes.values())
    
    def get_users(self):
        """Get all connected users"""
        # Remove inactive users
        current_time = time.time()
        active_users = {
            uid: user for uid, user in self.users.items()
            if current_time - user.last_seen < 30  # 30 second timeout
        }
        self.users = active_users
        return list(active_users.values())
    
    def clear_whiteboard(self):
        """Clear all strokes"""
        self.strokes.clear()
        for callback in self.callbacks:
            callback({'type': 'whiteboard_cleared'})

# ======================================
# 3. DRAWING COMPONENTS
# ======================================
def DrawingCanvas(props):
    """Interactive drawing canvas"""
    canvas_ref = use_ref(None)
    [isDrawing, setIsDrawing] = use_state(False, key="is_drawing")
    [currentStroke, setCurrentStroke] = use_state(None, key="current_stroke")
    [strokes, setStrokes] = use_state([], key="canvas_strokes")
    [users, setUsers] = use_state([], key="canvas_users")
    
    # Drawing settings
    brush_color = props.get('brush_color', '#000000')
    brush_width = props.get('brush_width', 3)
    current_tool = props.get('tool', 'pen')
    
    # Collaboration service
    collab_service_ref = use_ref(CollaborationService())
    
    # Connect to collaboration service
    use_effect(
        lambda: (
            # Connect and get user ID
            user_id := collab_service_ref.current.connect(
                lambda update: handle_collab_update(update)
            ),
            
            # Load existing strokes
            existing_strokes := collab_service_ref.current.get_strokes(),
            setStrokes(existing_strokes),
            
            # Load existing users
            existing_users := collab_service_ref.current.get_users(),
            setUsers(existing_users),
            
            # Update cursor position periodically
            cursor_interval := threading.Timer(0.1, update_cursor_position),
            cursor_interval.start(),
            
            # Cleanup
            lambda: cursor_interval.cancel()
        ),
        []
    )
    
    def handle_collab_update(update):
        """Handle updates from collaboration service"""
        if update['type'] == 'stroke_added':
            stroke = DrawingStroke.from_dict(update['stroke'])
            setStrokes(prev => [*prev, stroke])
        elif update['type'] == 'whiteboard_cleared':
            setStrokes([])
    
    def update_cursor_position():
        """Update cursor position for collaboration"""
        if canvas_ref.current and not isDrawing:
            # Get mouse position relative to canvas
            # In real implementation, track mouse position
            collab_service_ref.current.send_cursor_position(100, 100)
    
    def start_drawing(event):
        """Start a new stroke"""
        if not canvas_ref.current:
            return
        
        x = event['x']
        y = event['y']
        
        new_stroke = DrawingStroke(
            id=str(uuid.uuid4()),
            user_id=collab_service_ref.current.user_id,
            color=brush_color,
            width=brush_width,
            points=[DrawingPoint(x=x, y=y, timestamp=time.time())],
            tool=current_tool
        )
        
        setCurrentStroke(new_stroke)
        setIsDrawing(True)
    
    def continue_drawing(event):
        """Continue current stroke"""
        if not isDrawing or not current_stroke:
            return
        
        x = event['x']
        y = event['y']
        
        # Add point to current stroke
        updated_stroke = DrawingStroke(
            id=current_stroke.id,
            user_id=current_stroke.user_id,
            color=current_stroke.color,
            width=current_stroke.width,
            points=current_stroke.points + [
                DrawingPoint(x=x, y=y, timestamp=time.time())
            ],
            tool=current_stroke.tool
        )
        
        setCurrentStroke(updated_stroke)
        
        # Redraw canvas
        draw_canvas()
    
    def finish_drawing(event):
        """Finish current stroke"""
        if not isDrawing or not current_stroke:
            return
        
        # Send stroke to collaboration service
        collab_service_ref.current.send_stroke(current_stroke)
        
        # Add to strokes list
        setStrokes(prev => [...prev, current_stroke])
        
        # Reset
        setCurrentStroke(None)
        setIsDrawing(False)
    
    def draw_canvas():
        """Draw all strokes on canvas"""
        if not canvas_ref.current:
            return
        
        canvas = canvas_ref.current
        canvas.delete('all')
        
        # Draw background
        canvas.create_rectangle(0, 0, 800, 600, fill='white', outline='')
        
        # Draw all strokes
        all_strokes = strokes + ([current_stroke] if current_stroke else [])
        
        for stroke in all_strokes:
            if len(stroke.points) < 2:
                continue
            
            # Draw stroke
            points = []
            for point in stroke.points:
                points.extend([point.x, point.y])
            
            if stroke.tool == 'pen':
                canvas.create_line(
                    points,
                    fill=stroke.color,
                    width=stroke.width,
                    capstyle='round',
                    joinstyle='round',
                    smooth=True
                )
            elif stroke.tool == 'eraser':
                # Draw white lines for eraser
                canvas.create_line(
                    points,
                    fill='white',
                    width=stroke.width * 2,
                    capstyle='round',
                    joinstyle='round'
                )
        
        # Draw user cursors
        for user in users:
            if user.id != collab_service_ref.current.user_id:
                draw_user_cursor(canvas, user)
    
    def draw_user_cursor(canvas, user):
        """Draw another user's cursor"""
        x, y = user.cursor_x, user.cursor_y
        
        # Draw cursor circle
        canvas.create_oval(
            x - 5, y - 5,
            x + 5, y + 5,
            fill=user.color,
            outline='black',
            width=1
        )
        
        # Draw user name
        canvas.create_text(
            x, y - 10,
            text=user.name,
            fill=user.color,
            font=('Arial', 8, 'bold')
        )
    
    # Redraw canvas when strokes change
    use_effect(draw_canvas, [strokes, current_stroke, users])
    
    return create_element('frame', {'class': 'relative'},
        create_element('canvas', {
            'width': 800,
            'height': 600,
            'onMouseDown': start_drawing,
            'onMouseMove': continue_drawing,
            'onMouseUp': finish_drawing,
            'onDraw': lambda canvas: canvas_ref.current := canvas,
            'class': 'border rounded-lg shadow-inner cursor-crosshair'
        }),
        
        # Drawing status
        create_element('frame', {
            'class': 'absolute bottom-4 left-4 bg-black/70 text-white rounded px-3 py-1 text-sm'
        },
            create_element('label', {
                'text': f'{"Drawing..." if isDrawing else "Ready"} | {len(strokes)} strokes | {len(users)} users'
            })
        )
    )

def ToolPalette(props):
    """Drawing tools palette"""
    [selectedTool, setSelectedTool] = use_state('pen', key="selected_tool")
    [brushColor, setBrushColor] = use_state('#000000', key="brush_color")
    [brushSize, setBrushSize] = use_state(3, key="brush_size")
    
    tools = [
        {'id': 'pen', 'icon': '✏️', 'label': 'Pen'},
        {'id': 'eraser', 'icon': '🧽', 'label': 'Eraser'},
        {'id': 'line', 'icon': '📏', 'label': 'Line'},
        {'id': 'rectangle', 'icon': '⬜', 'label': 'Rectangle'},
        {'id': 'circle', 'icon': '⭕', 'label': 'Circle'},
        {'id': 'text', 'icon': '🔤', 'label': 'Text'},
    ]
    
    colors = [
        '#000000', '#FF0000', '#00FF00', '#0000FF',
        '#FFFF00', '#FF00FF', '#00FFFF', '#FFA500',
        '#800080', '#008080', '#FFC0CB', '#A52A2A'
    ]
    
    brush_sizes = [1, 2, 3, 5, 8, 13]
    
    return create_element('frame', {
        'class': 'bg-white dark:bg-gray-800 rounded-lg shadow p-4'
    },
        create_element('label', {
            'text': 'Tools',
            'class': 'font-bold text-gray-700 dark:text-gray-300 mb-3'
        }),
        
        # Tool buttons
        create_element('frame', {'class': 'grid grid-cols-3 gap-2 mb-4'},
            *[create_element('button', {
                'text': tool['icon'],
                'onClick': lambda t=tool['id']: (setSelectedTool(t), props.onToolChange and props.onToolChange(t)),
                'class': f'''
                    p-3 rounded-lg text-xl
                    {selectedTool == tool['id']
                        and 'bg-blue-500 text-white'
                        or 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'}
                ''',
                'aria-label': tool['label']
            }) for tool in tools]
        ),
        
        # Color palette
        create_element('label', {
            'text': 'Colors',
            'class': 'font-bold text-gray-700 dark:text-gray-300 mb-2'
        }),
        create_element('frame', {'class': 'grid grid-cols-6 gap-2 mb-4'},
            *[create_element('button', {
                'onClick': lambda c=color: (setBrushColor(c), props.onColorChange and props.onColorChange(c)),
                'class': f'''
                    w-8 h-8 rounded-full border-2
                    {brushColor == color 
                        and 'border-blue-500' 
                        or 'border-gray-300 dark:border-gray-600'}
                ''',
                'style': {'background': color}
            }) for color in colors]
        ),
        
        # Brush size
        create_element('label', {
            'text': 'Size',
            'class': 'font-bold text-gray-700 dark:text-gray-300 mb-2'
        }),
        create_element('frame', {'class': 'flex space-x-2'},
            *[create_element('button', {
                'text': str(size),
                'onClick': lambda s=size: (setBrushSize(s), props.onSizeChange and props.onSizeChange(s)),
                'class': f'''
                    px-3 py-1 rounded
                    {brushSize == size
                        and 'bg-blue-500 text-white'
                        or 'bg-gray-100 dark:bg-gray-700'}
                '''
            }) for size in brush_sizes]
        )
    )

def UserList(props):
    """List of connected users"""
    [users, setUsers] = use_state([], key="user_list")
    
    # Update user list periodically
    use_effect(
        lambda: (
            interval := threading.Timer(2.0, lambda: (
                props.collabService and setUsers(props.collabService.get_users())
            )),
            interval.start(),
            lambda: interval.cancel()
        ),
        []
    )
    
    return create_element('frame', {
        'class': 'bg-white dark:bg-gray-800 rounded-lg shadow p-4'
    },
        create_element('label', {
            'text': f'Users ({len(users)})',
            'class': 'font-bold text-gray-700 dark:text-gray-300 mb-3'
        }),
        
        create_element('frame', {'class': 'space-y-2'},
            *[create_element('frame', {
                'class': 'flex items-center p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-700',
                'key': user.id
            },
                create_element('frame', {
                    'class': 'w-3 h-3 rounded-full mr-3',
                    'style': {'background': user.color}
                }),
                create_element('label', {
                    'text': user.name,
                    'class': 'flex-1'
                }),
                user.id == props.currentUserId and create_element('label', {
                    'text': '(You)',
                    'class': 'text-gray-500 text-sm'
                })
            ) for user in users]
        )
    )

def ChatPanel(props):
    """Chat panel for collaboration"""
    [messages, setMessages] = use_state([], key="chat_messages")
    [inputText, setInputText] = use_state('', key="chat_input")
    
    def send_message():
        if not inputText.strip():
            return
        
        new_message = {
            'id': str(uuid.uuid4()),
            'user': props.currentUserName,
            'text': inputText,
            'timestamp': time.time(),
            'color': props.currentUserColor
        }
        
        setMessages(prev => [new_message, *prev])  # Add to top
        setInputText('')
        
        # In real app, send to server
        print(f"Chat sent: {inputText}")
    
    return create_element('frame', {
        'class': 'bg-white dark:bg-gray-800 rounded-lg shadow flex flex-col h-64'
    },
        # Messages
        create_element('frame', {'class': 'flex-1 overflow-y-auto p-3'},
            *[create_element('frame', {
                'class': 'mb-3',
                'key': msg['id']
            },
                create_element('frame', {'class': 'flex items-center mb-1'},
                    create_element('frame', {
                        'class': 'w-2 h-2 rounded-full mr-2',
                        'style': {'background': msg['color']}
                    }),
                    create_element('label', {
                        'text': msg['user'],
                        'class': 'font-bold text-sm'
                    }),
                    create_element('label', {
                        'text': time.strftime('%H:%M', time.localtime(msg['timestamp'])),
                        'class': 'text-gray-500 text-xs ml-2'
                    })
                ),
                create_element('label', {
                    'text': msg['text'],
                    'class': 'text-gray-700 dark:text-gray-300'
                })
            ) for msg in reversed(messages)]  # Show newest first
        ),
        
        # Input
        create_element('frame', {'class': 'border-t p-3'},
            create_element('frame', {'class': 'flex'},
                create_element('entry', {
                    'value': inputText,
                    'onChange': setInputText,
                    'onSubmit': send_message,
                    'placeholder': 'Type a message...',
                    'class': 'flex-1 border rounded-l px-3 py-2'
                }),
                create_element('button', {
                    'text': 'Send',
                    'onClick': send_message,
                    'class': 'bg-blue-500 text-white px-4 py-2 rounded-r'
                })
            )
        )
    )

# ======================================
# 4. MAIN WHITEBOARD COMPONENT
# ======================================
def CollaborativeWhiteboard(props):
    """Main whiteboard application"""
    [collabService] = use_state(CollaborationService(), key="collab_service")
    [brushColor, setBrushColor] = use_state('#000000', key="whiteboard_color")
    [brushSize, setBrushSize] = use_state(3, key="whiteboard_size")
    [tool, setTool] = use_state('pen', key="whiteboard_tool")
    
    def handleClear():
        """Clear the whiteboard"""
        if confirm("Clear the entire whiteboard?"):
            collabService.clear_whiteboard()
    
    def handleExport():
        """Export whiteboard as image"""
        # In real implementation, save canvas as image
        print("Exporting whiteboard...")
    
    return create_element('frame', {
        'class': 'min-h-screen bg-gray-100 dark:bg-gray-900 p-4'
    },
        create_element('frame', {'class': 'max-w-7xl mx-auto'},
            # Header
            create_element('frame', {'class': 'mb-6'},
                create_element('frame', {'class': 'flex items-center justify-between'},
                    create_element('frame', {},
                        create_element('label', {
                            'text': '🎨 Collaborative Whiteboard',
                            'class': 'text-2xl font-bold text-gray-800 dark:text-gray-200'
                        }),
                        create_element('label', {
                            'text': 'Draw together in real-time',
                            'class': 'text-gray-500 dark:text-gray-400'
                        })
                    ),
                    create_element('frame', {'class': 'flex space-x-2'},
                        create_element('button', {
                            'text': 'Clear',
                            'onClick': handleClear,
                            'class': 'bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded'
                        }),
                        create_element('button', {
                            'text': 'Export',
                            'onClick': handleExport,
                            'class': 'bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded'
                        }),
                        create_element('button', {
                            'text': 'Help',
                            'class': 'bg-gray-300 dark:bg-gray-700 hover:bg-gray-400 dark:hover:bg-gray-600 px-4 py-2 rounded'
                        })
                    )
                )
            ),
            
            # Main content
            create_element('frame', {'class': 'grid grid-cols-1 lg:grid-cols-4 gap-6'},
                # Left sidebar - Tools
                create_element('frame', {'class': 'lg:col-span-1 space-y-6'},
                    create_element(ToolPalette, {
                        'onToolChange': setTool,
                        'onColorChange': setBrushColor,
                        'onSizeChange': setBrushSize
                    }),
                    create_element(UserList, {
                        'collabService': collabService,
                        'currentUserId': collabService.user_id
                    })
                ),
                
                # Center - Canvas
                create_element('frame', {'class': 'lg:col-span-2'},
                    create_element(DrawingCanvas, {
                        'brush_color': brushColor,
                        'brush_width': brushSize,
                        'tool': tool,
                        'collabService': collabService
                    })
                ),
                
                # Right sidebar - Chat
                create_element('frame', {'class': 'lg:col-span-1'},
                    create_element(ChatPanel, {
                        'currentUserName': collabService.user_name,
                        'currentUserColor': collabService.user_color
                    })
                )
            ),
            
            # Footer
            create_element('frame', {'class': 'mt-6 text-center text-gray-500 dark:text-gray-400 text-sm'},
                create_element('label', {
                    'text': 'Tip: Drag to draw. Multiple users can draw simultaneously.'
                })
            )
        )
    )

# ======================================
# 5. RUN THE WHITEBOARD
# ======================================
if __name__ == "__main__":
    print("""
    🎨 COLLABORATIVE WHITEBOARD
    ===========================
    Features:
    1. Real-time multi-user drawing
    2. Multiple drawing tools
    3. Color palette and brush sizes
    4. Live user cursors
    5. Integrated chat
    6. Collaborative editing
    
    Instructions:
    - Select a tool from the left panel
    - Choose a color and brush size
    - Draw on the canvas
    - Other users will see your drawings in real-time
    ===========================
    """)
    
    # Initialize application
    wizard = PyUIWizard(
        title="Collaborative Whiteboard",
        width=1400,
        height=900,
        use_diffing=True
    )
    
    # Run whiteboard
    wizard.render_app(lambda state: CollaborativeWhiteboard({}))
    wizard.run()