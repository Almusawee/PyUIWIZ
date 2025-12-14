
"""
Real-Time Dashboard Example
Features: Multiple data sources, real-time updates, responsive design, theme switching
"""
from pyuiwizard import PyUIWizard, create_element, useState, useEffect, Component, DESIGN_TOKENS
import threading
import random
import time
from datetime import datetime, timedelta
import json

# ======================================
# 1. DATA MODELS & SERVICES
# ======================================
class DataService:
    """Mock data service for dashboard"""
    
    @staticmethod
    def get_system_metrics():
        """Get system performance metrics"""
        return {
            'cpu': random.randint(10, 90),
            'memory': random.randint(20, 95),
            'disk': random.randint(30, 85),
            'network': random.randint(1, 100),
            'uptime': random.randint(1, 1000),
            'active_users': random.randint(100, 5000)
        }
    
    @staticmethod
    def get_recent_events():
        """Get recent system events"""
        events = [
            {'type': 'info', 'message': 'System backup completed', 'time': '2 minutes ago'},
            {'type': 'warning', 'message': 'High memory usage detected', 'time': '15 minutes ago'},
            {'type': 'success', 'message': 'Deployment successful', 'time': '1 hour ago'},
            {'type': 'error', 'message': 'Database connection failed', 'time': '3 hours ago'},
            {'type': 'info', 'message': 'New user registered', 'time': '5 hours ago'}
        ]
        return random.sample(events, random.randint(1, 5))
    
    @staticmethod
    def get_sales_data(days=30):
        """Generate sales data for chart"""
        sales = []
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            sales.append({
                'date': date.strftime('%Y-%m-%d'),
                'revenue': random.randint(1000, 10000),
                'orders': random.randint(10, 200),
                'customers': random.randint(5, 100)
            })
        
        return sales
    
    @staticmethod
    def get_user_activity():
        """Get real-time user activity"""
        activities = ['login', 'purchase', 'view', 'search', 'logout']
        return [{
            'user': f'User_{random.randint(1000, 9999)}',
            'activity': random.choice(activities),
            'time': f'{random.randint(0, 23)}:{random.randint(0, 59):02d}',
            'location': random.choice(['US', 'EU', 'Asia', 'Other'])
        } for _ in range(random.randint(5, 15))]

# ======================================
# 2. REUSABLE COMPONENTS
# ======================================
def MetricCard(props):
    """Dashboard metric card with trend indicator"""
    [value, setValue] = useState(props.get('value', 0), key=f"metric_{props['key']}")
    [trend, setTrend] = useState(props.get('trend', 0), key=f"trend_{props['key']}")
    
    # Format value
    def format_value(val):
        if props.get('format') == 'percent':
            return f"{val}%"
        elif props.get('format') == 'currency':
            return f"${val:,.0f}"
        elif props.get('format') == 'number':
            return f"{val:,}"
        return str(val)
    
    # Determine trend color and icon
    if trend > 0:
        trend_color = 'text-green-600'
        trend_icon = '↗'
        trend_text = f'+{trend}%'
    elif trend < 0:
        trend_color = 'text-red-600'
        trend_icon = '↘'
        trend_text = f'{trend}%'
    else:
        trend_color = 'text-gray-500'
        trend_icon = '→'
        trend_text = '0%'
    
    return create_element('frame', {
        'class': '''
            bg-white dark:bg-gray-800
            rounded-xl
            shadow-sm
            p-6
            transition-all
            hover:shadow-md
            hover:scale-[1.01]
        ''',
        'key': props['key']
    },
        create_element('frame', {'class': 'flex items-start justify-between'},
            create_element('frame', {},
                create_element('label', {
                    'text': props['title'],
                    'class': 'text-gray-500 dark:text-gray-400 text-sm font-medium'
                }),
                create_element('label', {
                    'text': format_value(value),
                    'class': 'text-3xl font-bold text-gray-800 dark:text-gray-200 mt-2'
                })
            ),
            create_element('frame', {'class': 'flex items-center'},
                create_element('label', {
                    'text': trend_icon,
                    'class': f'text-xl {trend_color} mr-1'
                }),
                create_element('label', {
                    'text': trend_text,
                    'class': f'text-sm {trend_color}'
                })
            )
        ),
        create_element('frame', {'class': 'mt-4'},
            create_element('label', {
                'text': props.get('description', ''),
                'class': 'text-gray-400 dark:text-gray-500 text-xs'
            })
        )
    )

def LineChart(props):
    """Simple line chart component"""
    [data, setData] = useState(props.get('data', []), key=f"chart_{props['key']}")
    [hoverIndex, setHoverIndex] = useState(-1, key=f"chart_hover_{props['key']}")
    
    # Calculate chart dimensions and values
    max_value = max([d['value'] for d in data]) if data else 1
    chart_height = props.get('height', 200)
    
    # Generate points for line
    points = []
    if data:
        point_width = chart_height / len(data)
        for i, point in enumerate(data):
            x = i * point_width
            y = chart_height - (point['value'] / max_value * chart_height)
            points.append((x, y))
    
    return create_element('frame', {
        'class': 'relative bg-gray-50 dark:bg-gray-900 rounded-lg p-4',
        'key': props['key']
    },
        # Chart title
        create_element('label', {
            'text': props['title'],
            'class': 'text-gray-700 dark:text-gray-300 font-bold mb-4'
        }),
        
        # Chart container
        create_element('canvas', {
            'width': 400,
            'height': chart_height,
            'onDraw': lambda canvas: LineChart._draw_chart(canvas, data, points, hoverIndex),
            'onMouseMove': lambda e: setHoverIndex(LineChart._get_hover_index(e, data, chart_height)),
            'onMouseLeave': lambda e: setHoverIndex(-1)
        }),
        
        # X-axis labels
        data and create_element('frame', {'class': 'flex justify-between mt-2'},
            *[create_element('label', {
                'text': point['label'],
                'class': 'text-gray-500 dark:text-gray-400 text-xs'
            }) for point in data[::max(1, len(data)//5)]]
        ),
        
        # Hover tooltip
        hoverIndex >= 0 and data and create_element('frame', {
            'class': 'absolute bg-white dark:bg-gray-800 shadow-lg rounded p-2 border',
            'style': {
                'left': f'{hoverIndex * 30}px',
                'top': '50px'
            }
        },
            create_element('label', {
                'text': data[hoverIndex]['label'],
                'class': 'font-bold text-sm'
            }),
            create_element('label', {
                'text': str(data[hoverIndex]['value']),
                'class': 'text-gray-600 dark:text-gray-400'
            })
        )
    )
    
    @staticmethod
    def _draw_chart(canvas, data, points, hover_index):
        """Draw chart on canvas"""
        if not points:
            return
        
        # Draw line
        canvas.create_line(points, fill='#3b82f6', width=2, smooth=True)
        
        # Draw points
        for i, (x, y) in enumerate(points):
            color = '#ef4444' if i == hover_index else '#3b82f6'
            canvas.create_oval(x-3, y-3, x+3, y+3, fill=color, outline=color)
    
    @staticmethod
    def _get_hover_index(event, data, chart_height):
        """Calculate which data point is being hovered"""
        if not data:
            return -1
        
        x = event['x']
        point_width = chart_height / len(data)
        return min(int(x / point_width), len(data) - 1)

def DataTable(props):
    """Interactive data table with sorting and pagination"""
    [data, setData] = useState(props.get('data', []), key=f"table_{props['key']}")
    [sortBy, setSortBy] = useState(None, key=f"table_sort_{props['key']}")
    [sortAsc, setSortAsc] = useState(True, key=f"table_sort_asc_{props['key']}")
    [page, setPage] = useState(0, key=f"table_page_{props['key']}")
    
    items_per_page = props.get('itemsPerPage', 10)
    
    # Sort data
    sorted_data = data.copy()
    if sortBy:
        sorted_data.sort(
            key=lambda x: x.get(sortBy, ''),
            reverse=not sortAsc
        )
    
    # Paginate
    start_idx = page * items_per_page
    paginated_data = sorted_data[start_idx:start_idx + items_per_page]
    total_pages = max(1, (len(sorted_data) + items_per_page - 1) // items_per_page)
    
    def handle_sort(column):
        if sortBy == column:
            setSortAsc(not sortAsc)
        else:
            setSortBy(column)
            setSortAsc(True)
    
    def next_page():
        if page < total_pages - 1:
            setPage(page + 1)
    
    def prev_page():
        if page > 0:
            setPage(page - 1)
    
    return create_element('frame', {
        'class': 'bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden',
        'key': props['key']
    },
        # Table header
        create_element('frame', {'class': 'flex bg-gray-50 dark:bg-gray-900 border-b'},
            *[create_element('button', {
                'text': f'{col} {sortBy==col and ("↑" if sortAsc else "↓") or ""}',
                'onClick': lambda c=col: handle_sort(c),
                'class': '''
                    flex-1 text-left py-3 px-4 font-medium
                    text-gray-700 dark:text-gray-300
                    hover:bg-gray-100 dark:hover:bg-gray-800
                    border-r last:border-r-0
                ''',
                'relief': 'flat'
            }) for col in props['columns']]
        ),
        
        # Table rows
        *[create_element('frame', {
            'class': 'flex border-b hover:bg-gray-50 dark:hover:bg-gray-700 last:border-b-0',
            'key': f'row_{i}'
        },
            *[create_element('label', {
                'text': str(row.get(col, '')),
                'class': 'flex-1 py-3 px-4 truncate',
                'key': f'cell_{i}_{col}'
            }) for col in props['columns']]
        ) for i, row in enumerate(paginated_data)],
        
        # Pagination
        create_element('frame', {'class': 'flex items-center justify-between p-4'},
            create_element('label', {
                'text': f'Showing {start_idx + 1}-{min(start_idx + items_per_page, len(sorted_data))} of {len(sorted_data)}',
                'class': 'text-gray-500 dark:text-gray-400'
            }),
            create_element('frame', {'class': 'flex items-center space-x-2'},
                create_element('button', {
                    'text': '← Previous',
                    'onClick': prev_page,
                    'disabled': page == 0,
                    'class': 'px-3 py-1 rounded disabled:opacity-50 disabled:cursor-not-allowed'
                }),
                create_element('label', {
                    'text': f'{page + 1} / {total_pages}',
                    'class': 'px-3 py-1'
                }),
                create_element('button', {
                    'text': 'Next →',
                    'onClick': next_page,
                    'disabled': page == total_pages - 1,
                    'class': 'px-3 py-1 rounded disabled:opacity-50 disabled:cursor-not-allowed'
                })
            )
        )
    )

# ======================================
# 3. DASHBOARD SECTIONS
# ======================================
def MetricsOverview(props):
    """Top metrics overview section"""
    [metrics, setMetrics] = useState({}, key="dashboard_metrics")
    
    # Fetch metrics periodically
    useEffect(
        lambda: (
            # Initial fetch
            setMetrics(DataService.get_system_metrics()),
            
            # Set up interval
            interval = threading.Timer(5.0, lambda: setMetrics(DataService.get_system_metrics())),
            interval.start(),
            
            # Cleanup
            lambda: interval.cancel()
        ),
        []  # Run once on mount
    )
    
    return create_element('frame', {
        'class': 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4'
    },
        create_element(MetricCard, {
            'key': 'cpu',
            'title': 'CPU Usage',
            'value': metrics.get('cpu', 0),
            'trend': random.randint(-5, 5),
            'format': 'percent',
            'description': 'Total processor utilization'
        }),
        create_element(MetricCard, {
            'key': 'memory',
            'title': 'Memory',
            'value': metrics.get('memory', 0),
            'trend': random.randint(-3, 3),
            'format': 'percent',
            'description': 'RAM usage'
        }),
        create_element(MetricCard, {
            'key': 'disk',
            'title': 'Disk',
            'value': metrics.get('disk', 0),
            'trend': random.randint(-2, 2),
            'format': 'percent',
            'description': 'Storage utilization'
        }),
        create_element(MetricCard, {
            'key': 'network',
            'title': 'Network',
            'value': metrics.get('network', 0),
            'trend': random.randint(-10, 10),
            'format': 'mbps',
            'description': 'Throughput'
        }),
        create_element(MetricCard, {
            'key': 'uptime',
            'title': 'Uptime',
            'value': metrics.get('uptime', 0),
            'trend': 0,
            'format': 'days',
            'description': 'System uptime in days'
        }),
        create_element(MetricCard, {
            'key': 'users',
            'title': 'Active Users',
            'value': metrics.get('active_users', 0),
            'trend': random.randint(-2, 8),
            'format': 'number',
            'description': 'Currently online'
        })
    )

def ActivityFeed(props):
    """Recent activity feed"""
    [activities, setActivities] = useState([], key="activity_feed")
    
    useEffect(
        lambda: (
            setActivities(DataService.get_user_activity()),
            
            # Update every 10 seconds
            interval = threading.Timer(10.0, lambda: (
                new_activities = DataService.get_user_activity(),
                setActivities(new_activities[:10])  # Keep only 10 most recent
            )),
            interval.start(),
            
            lambda: interval.cancel()
        ),
        []
    )
    
    # Color mapping for activity types
    activity_colors = {
        'login': 'bg-green-100 text-green-800',
        'purchase': 'bg-blue-100 text-blue-800',
        'view': 'bg-purple-100 text-purple-800',
        'search': 'bg-yellow-100 text-yellow-800',
        'logout': 'bg-gray-100 text-gray-800'
    }
    
    return create_element('frame', {
        'class': 'bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6'
    },
        create_element('frame', {'class': 'flex items-center justify-between mb-4'},
            create_element('label', {
                'text': 'Recent Activity',
                'class': 'text-lg font-bold text-gray-800 dark:text-gray-200'
            }),
            create_element('button', {
                'text': 'Refresh',
                'onClick': lambda: setActivities(DataService.get_user_activity()),
                'class': 'text-sm text-blue-500 hover:text-blue-700'
            })
        ),
        
        create_element('frame', {'class': 'space-y-3'},
            *[create_element('frame', {
                'class': 'flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700',
                'key': f'activity_{i}'
            },
                create_element('frame', {'class': 'flex items-center'},
                    create_element('frame', {
                        'class': f'w-2 h-2 rounded-full mr-3 {activity_colors.get(act["activity"], "bg-gray-300")}'
                    }),
                    create_element('label', {
                        'text': act['user'],
                        'class': 'font-medium text-gray-700 dark:text-gray-300'
                    })
                ),
                create_element('frame', {'class': 'flex items-center space-x-4'},
                    create_element('label', {
                        'text': act['activity'].title(),
                        'class': 'text-sm text-gray-500 dark:text-gray-400'
                    }),
                    create_element('label', {
                        'text': act['time'],
                        'class': 'text-sm text-gray-400 dark:text-gray-500'
                    }),
                    create_element('label', {
                        'text': act['location'],
                        'class': 'text-sm text-gray-400 dark:text-gray-500'
                    })
                )
            ) for i, act in enumerate(activities)]
        )
    )

def SalesChart(props):
    """Sales data visualization"""
    [salesData, setSalesData] = useState([], key="sales_data")
    [timeRange, setTimeRange] = useState('30d', key="sales_range")
    
    useEffect(
        lambda: (
            days = 7 if timeRange == '7d' else 30 if timeRange == '30d' else 90,
            setSalesData(DataService.get_sales_data(days))
        ),
        [timeRange]  # Re-fetch when time range changes
    )
    
    # Transform data for chart
    chart_data = []
    if salesData:
        # Use only every 3rd data point for readability
        for i, sale in enumerate(salesData[::3]):
            chart_data.append({
                'label': sale['date'][5:],  # MM-DD
                'value': sale['revenue']
            })
    
    return create_element('frame', {
        'class': 'bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 col-span-2'
    },
        create_element('frame', {'class': 'flex items-center justify-between mb-6'},
            create_element('label', {
                'text': 'Revenue Trend',
                'class': 'text-lg font-bold text-gray-800 dark:text-gray-200'
            }),
            create_element('frame', {'class': 'flex space-x-2'},
                *[create_element('button', {
                    'text': text,
                    'onClick': lambda tr=value: setTimeRange(tr),
                    'class': f'''
                        px-3 py-1 rounded text-sm
                        {timeRange == value 
                            and 'bg-blue-500 text-white' 
                            or 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}
                    '''
                }) for text, value in [('7D', '7d'), ('30D', '30d'), ('90D', '90d')]]
            )
        ),
        
        create_element(LineChart, {
            'key': 'sales_chart',
            'title': 'Daily Revenue',
            'data': chart_data,
            'height': 250
        }),
        
        # Summary stats
        salesData and create_element('frame', {'class': 'grid grid-cols-3 gap-4 mt-6'},
            create_element('frame', {'class': 'text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded'},
                create_element('label', {
                    'text': f'${sum(s["revenue"] for s in salesData):,.0f}',
                    'class': 'text-2xl font-bold text-blue-600 dark:text-blue-400'
                }),
                create_element('label', {
                    'text': 'Total Revenue',
                    'class': 'text-sm text-gray-500 dark:text-gray-400'
                })
            ),
            create_element('frame', {'class': 'text-center p-3 bg-green-50 dark:bg-green-900/20 rounded'},
                create_element('label', {
                    'text': f'{sum(s["orders"] for s in salesData):,}',
                    'class': 'text-2xl font-bold text-green-600 dark:text-green-400'
                }),
                create_element('label', {
                    'text': 'Total Orders',
                    'class': 'text-sm text-gray-500 dark:text-gray-400'
                })
            ),
            create_element('frame', {'class': 'text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded'},
                create_element('label', {
                    'text': f'{sum(s["customers"] for s in salesData):,}',
                    'class': 'text-2xl font-bold text-purple-600 dark:text-purple-400'
                }),
                create_element('label', {
                    'text': 'Total Customers',
                    'class': 'text-sm text-gray-500 dark:text-gray-400'
                })
            )
        )
    )

# ======================================
# 4. MAIN DASHBOARD COMPONENT
# ======================================
def DashboardApp(props):
    """Main dashboard application"""
    [sidebarOpen, setSidebarOpen] = useState(True, key="sidebar_open")
    [darkMode, setDarkMode] = useState(DESIGN_TOKENS.dark_mode, key="dark_mode")
    [activeTab, setActiveTab] = useState('overview', key="active_tab")
    
    # Handle theme switching
    def toggleTheme():
        new_mode = not darkMode
        setDarkMode(new_mode)
        DESIGN_TOKENS.set_theme('dark' if new_mode else 'light')
    
    # Navigation items
    nav_items = [
        {'icon': '📊', 'label': 'Overview', 'id': 'overview'},
        {'icon': '📈', 'label': 'Analytics', 'id': 'analytics'},
        {'icon': '👥', 'label': 'Users', 'id': 'users'},
        {'icon': '⚙️', 'label': 'Settings', 'id': 'settings'},
        {'icon': '🔒', 'label': 'Security', 'id': 'security'},
        {'icon': '📋', 'label': 'Reports', 'id': 'reports'},
    ]
    
    return create_element('frame', {
        'class': '''
            min-h-screen
            bg-gray-50 dark:bg-gray-900
            text-gray-900 dark:text-gray-100
            transition-colors duration-300
        '''
    },
        # Header
        create_element('frame', {
            'class': '''
                bg-white dark:bg-gray-800
                shadow-sm
                sticky top-0 z-10
            '''
        },
            create_element('frame', {'class': 'px-6 py-4 flex items-center justify-between'},
                create_element('frame', {'class': 'flex items-center'},
                    create_element('button', {
                        'text': '☰',
                        'onClick': lambda: setSidebarOpen(not sidebarOpen),
                        'class': '''
                            p-2 rounded-lg mr-4
                            hover:bg-gray-100 dark:hover:bg-gray-700
                        '''
                    }),
                    create_element('label', {
                        'text': '📊 PyUIWizard Dashboard',
                        'class': 'text-xl font-bold'
                    })
                ),
                create_element('frame', {'class': 'flex items-center space-x-4'},
                    create_element('button', {
                        'text': darkMode and '☀️ Light' or '🌙 Dark',
                        'onClick': toggleTheme,
                        'class': '''
                            px-4 py-2 rounded-lg
                            bg-gray-100 dark:bg-gray-700
                            hover:bg-gray-200 dark:hover:bg-gray-600
                        '''
                    }),
                    create_element('frame', {'class': 'relative'},
                        create_element('button', {
                            'text': '👤',
                            'class': '''
                                w-10 h-10 rounded-full
                                bg-blue-100 dark:bg-blue-900
                                flex items-center justify-center
                            '''
                        })
                    )
                )
            )
        ),
        
        # Main content
        create_element('frame', {'class': 'flex'},
            # Sidebar
            sidebarOpen and create_element('frame', {
                'class': '''
                    w-64 bg-white dark:bg-gray-800
                    border-r border-gray-200 dark:border-gray-700
                    min-h-[calc(100vh-4rem)]
                    transition-all duration-300
                '''
            },
                create_element('frame', {'class': 'p-4'},
                    *[create_element('button', {
                        'text': f'{item["icon"]} {item["label"]}',
                        'onClick': lambda id=item['id']: setActiveTab(id),
                        'class': f'''
                            w-full text-left px-4 py-3 rounded-lg mb-1
                            {activeTab == item['id'] 
                                and 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                                or 'hover:bg-gray-100 dark:hover:bg-gray-700'}
                        ''',
                        'relief': 'flat'
                    }) for item in nav_items]
                )
            ),
            
            # Dashboard content
            create_element('frame', {'class': 'flex-1 p-6'},
                create_element('frame', {'class': 'mb-6'},
                    create_element('label', {
                        'text': 'Dashboard Overview',
                        'class': 'text-2xl font-bold mb-2'
                    }),
                    create_element('label', {
                        'text': 'Welcome back! Here\'s what\'s happening with your systems today.',
                        'class': 'text-gray-500 dark:text-gray-400'
                    })
                ),
                
                # Metrics grid
                create_element('frame', {'class': 'mb-8'},
                    create_element(MetricsOverview, {'key': 'metrics'})
                ),
                
                # Charts and tables
                create_element('frame', {'class': 'grid grid-cols-1 lg:grid-cols-3 gap-6'},
                    create_element(SalesChart, {'key': 'sales'}),
                    create_element(ActivityFeed, {'key': 'activity'})
                ),
                
                # Recent events table
                create_element('frame', {'class': 'mt-6'},
                    create_element(DataTable, {
                        'key': 'events',
                        'columns': ['Type', 'Message', 'Time'],
                        'data': DataService.get_recent_events(),
                        'itemsPerPage': 5
                    })
                ),
                
                # Footer
                create_element('frame', {'class': 'mt-8 pt-6 border-t border-gray-200 dark:border-gray-700'},
                    create_element('frame', {'class': 'flex justify-between text-sm text-gray-500 dark:text-gray-400'},
                        create_element('label', {
                            'text': 'PyUIWizard Dashboard v4.2.0'
                        }),
                        create_element('label', {
                            'text': f'Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                        })
                    )
                )
            )
        )
    )

# ======================================
# 5. RUN THE DASHBOARD
# ======================================
if __name__ == "__main__":
    print("""
    🚀 PYUIWIZARD REAL-TIME DASHBOARD
    =================================
    Features:
    1. Real-time system metrics
    2. Interactive charts and tables
    3. Dark/light theme switching
    4. Responsive grid layout
    5. Live activity feed
    6. Paginated data tables
    
    Controls:
    - Click sidebar items to switch views
    - Use theme toggle button
    - Charts update automatically
    - Tables are sortable and paginated
    =================================
    """)
    
    # Initialize application
    wizard = PyUIWizard(
        title="PyUIWizard Dashboard",
        width=1400,
        height=900,
        use_diffing=True
    )
    
    # Set initial theme
    DESIGN_TOKENS.set_theme('light')
    
    # Run dashboard
    wizard.render_app(lambda state: DashboardApp({}))
    wizard.run()
    
    # Print performance stats
    wizard.print_stats()