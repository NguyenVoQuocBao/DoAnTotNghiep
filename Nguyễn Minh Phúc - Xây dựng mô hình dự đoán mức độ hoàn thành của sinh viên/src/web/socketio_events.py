"""
WebSocket Events for Real-time Updates
Handles real-time communication between server and clients
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import session, request
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

# Store active connections
active_connections = {}
room_members = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    username = session.get('username', 'anonymous')
    user_type = session.get('user_type', 'guest')
    
    active_connections[client_id] = {
        'username': username,
        'user_type': user_type,
        'connected_at': datetime.now().isoformat(),
        'last_activity': datetime.now().isoformat()
    }
    
    logger.info(f"Client connected: {username} ({user_type}) - {client_id}")
    
    # Join appropriate room based on user type
    if user_type in ['student', 'teacher', 'admin']:
        join_room(user_type + 's')
        if user_type + 's' not in room_members:
            room_members[user_type + 's'] = set()
        room_members[user_type + 's'].add(client_id)
    
    # Send welcome message with connection info
    emit('connection_established', {
        'status': 'connected',
        'username': username,
        'user_type': user_type,
        'server_time': datetime.now().isoformat(),
        'active_users': len(active_connections)
    })
    
    # Notify other users in the same room
    if user_type in ['teacher', 'admin']:
        emit('user_joined', {
            'username': username,
            'user_type': user_type,
            'timestamp': datetime.now().isoformat()
        }, room=user_type + 's', include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    
    if client_id in active_connections:
        user_info = active_connections[client_id]
        username = user_info['username']
        user_type = user_info['user_type']
        
        # Remove from room
        if user_type + 's' in room_members:
            room_members[user_type + 's'].discard(client_id)
            if not room_members[user_type + 's']:
                del room_members[user_type + 's']
        
        # Remove from active connections
        del active_connections[client_id]
        
        logger.info(f"Client disconnected: {username} ({user_type}) - {client_id}")
        
        # Notify other users in the same room
        if user_type in ['teacher', 'admin']:
            emit('user_left', {
                'username': username,
                'user_type': user_type,
                'timestamp': datetime.now().isoformat()
            }, room=user_type + 's')

@socketio.on('request_analytics_update')
def handle_analytics_update_request(data):
    """Handle request for analytics update"""
    client_id = request.sid
    username = session.get('username')
    
    if client_id not in active_connections:
        emit('error', {'message': 'Not authenticated'})
        return
    
    try:
        # Update last activity
        active_connections[client_id]['last_activity'] = datetime.now().isoformat()
        
        # Get analytics system from app context
        from flask import current_app
        analytics_system = current_app.config.get('ANALYTICS_SYSTEM')
        
        if not analytics_system:
            emit('error', {'message': 'Analytics system not available'})
            return
        
        # Get user type to determine what data to send
        user_type = session.get('user_type')
        
        if user_type == 'student':
            # Send student-specific analytics
            from src.services.data_service import DataService
            students = DataService.load_students()
            
            if username in students:
                student = students[username]
                result = analytics_system.process_student_data(student.raw_data)
                prediction = analytics_system.predict_completion_level(result['normalized_data'])
                
                emit('analytics_update', {
                    'type': 'student_analytics',
                    'data': {
                        'completion_assessment': result['completion_assessment'],
                        'behavior_label': result['behavior_label'],
                        'recommendation': result['recommendation'],
                        'prediction': prediction['recommended'],
                        'timestamp': datetime.now().isoformat()
                    }
                })
        
        elif user_type in ['teacher', 'admin']:
            # Send teacher dashboard analytics
            from src.services.data_service import DataService
            students = DataService.load_students()
            
            # Get summary statistics
            total_students = len(students)
            completion_levels = {'Cao': 0, 'Trung bình': 0, 'Thấp': 0}
            behavior_groups = {'Tích cực': 0, 'Trì hoãn': 0, 'Thụ động': 0}
            
            for student in students.values():
                result = analytics_system.process_student_data(student.raw_data)
                completion_levels[result['completion_assessment']['completion_level']] += 1
                behavior_groups[result['behavior_label']] += 1
            
            emit('analytics_update', {
                'type': 'teacher_dashboard',
                'data': {
                    'total_students': total_students,
                    'completion_distribution': completion_levels,
                    'behavior_distribution': behavior_groups,
                    'high_performers_percentage': round(completion_levels['Cao'] / total_students * 100, 1) if total_students > 0 else 0,
                    'timestamp': datetime.now().isoformat()
                }
            })
    
    except Exception as e:
        logger.error(f"Error handling analytics update request: {e}")
        emit('error', {'message': 'Failed to get analytics update'})

@socketio.on('request_real_time_metrics')
def handle_real_time_metrics_request():
    """Handle request for real-time system metrics"""
    client_id = request.sid
    user_type = session.get('user_type')
    
    if user_type not in ['teacher', 'admin']:
        emit('error', {'message': 'Unauthorized'})
        return
    
    try:
        # System metrics
        metrics = {
            'active_connections': len(active_connections),
            'connected_students': len([c for c in active_connections.values() if c['user_type'] == 'student']),
            'connected_teachers': len([c for c in active_connections.values() if c['user_type'] == 'teacher']),
            'server_uptime': datetime.now().isoformat(),
            'room_stats': {room: len(members) for room, members in room_members.items()}
        }
        
        emit('real_time_metrics', {
            'type': 'system_metrics',
            'data': metrics,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        emit('error', {'message': 'Failed to get metrics'})

@socketio.on('broadcast_notification')
def handle_broadcast_notification(data):
    """Handle broadcasting notifications to users"""
    user_type = session.get('user_type')
    username = session.get('username')
    
    if user_type not in ['teacher', 'admin']:
        emit('error', {'message': 'Unauthorized to broadcast'})
        return
    
    try:
        notification = {
            'message': data.get('message', ''),
            'type': data.get('type', 'info'),
            'from': username,
            'timestamp': datetime.now().isoformat()
        }
        
        target_room = data.get('target_room', 'students')
        
        # Broadcast to target room
        emit('notification', notification, room=target_room)
        
        logger.info(f"Notification broadcast by {username} to {target_room}: {notification['message']}")
    
    except Exception as e:
        logger.error(f"Error broadcasting notification: {e}")
        emit('error', {'message': 'Failed to broadcast notification'})

@socketio.on('ping')
def handle_ping():
    """Handle ping for connection health check"""
    client_id = request.sid
    if client_id in active_connections:
        active_connections[client_id]['last_activity'] = datetime.now().isoformat()
    
    emit('pong', {'timestamp': datetime.now().isoformat()})

def init_socketio(app):
    """Initialize SocketIO with Flask app"""
    socketio.init_app(app, 
                     cors_allowed_origins="*",
                     async_mode='threading',
                     logger=True,
                     engineio_logger=True)
    return socketio

def broadcast_analytics_update(analytics_data, target_users='all'):
    """Broadcast analytics update to connected users"""
    try:
        notification = {
            'type': 'analytics_broadcast',
            'data': analytics_data,
            'timestamp': datetime.now().isoformat()
        }
        
        if target_users == 'all':
            socketio.emit('analytics_broadcast', notification)
        elif target_users in room_members:
            socketio.emit('analytics_broadcast', notification, room=target_users)
        
        logger.info(f"Analytics update broadcast to {target_users}")
    
    except Exception as e:
        logger.error(f"Error broadcasting analytics update: {e}")

def get_connection_stats():
    """Get current connection statistics"""
    return {
        'total_connections': len(active_connections),
        'by_user_type': {
            'students': len([c for c in active_connections.values() if c['user_type'] == 'student']),
            'teachers': len([c for c in active_connections.values() if c['user_type'] == 'teacher']),
            'admins': len([c for c in active_connections.values() if c['user_type'] == 'admin']),
            'guests': len([c for c in active_connections.values() if c['user_type'] == 'guest'])
        },
        'rooms': {room: len(members) for room, members in room_members.items()},
        'active_connections': active_connections
    }