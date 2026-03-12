"""
House of Albrite - Flask Web Application with GUI
Complete family system deployment with full suite of features
"""

import os
import json
import time
import asyncio
import numpy as np
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

# Import family system components
import sys
# Add the project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.agents.expert_agents import create_house_of_albrite, AlbriteFamilySystem

app = Flask(__name__)
app.config['SECRET_KEY'] = 'albrite_family_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize House of Albrite
albrite_family = create_house_of_albrite()

# Global state for real-time updates
family_state = {
    'last_update': time.time(),
    'active_agents': {},
    'family_metrics': {},
    'skills_evolution': [],
    'collaboration_events': []
}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html', family_name="House of Albrite")

@app.route('/api/family/overview')
def get_family_overview():
    """Get complete family overview"""
    overview = albrite_family.get_family_overview()
    return jsonify(overview)

@app.route('/api/family/metrics')
def get_family_metrics():
    """Get real-time family metrics"""
    metrics = {
        'harmony_score': albrite_family._calculate_family_harmony(),
        'collective_intelligence': albrite_family._calculate_collective_intelligence(),
        'innovation_potential': albrite_family._calculate_innovation_potential(),
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(metrics)

@app.route('/api/agents/<agent_id>')
def get_agent_details(agent_id):
    """Get specific agent details"""
    agent = albrite_family.expert_agents.get(agent_id)
    if agent:
        return jsonify({
            'id': agent.id,
            'name': agent.name,
            'icon': getattr(agent, 'icon', '🔹'),
            'role': agent.family_role.value,
            'genetic_fitness': agent.genetic_code.calculate_fitness(),
            'capabilities': agent.capabilities,
            'emotional_state': agent.emotional_state,
            'performance_history': agent.performance_history[-10:] if agent.performance_history else []
        })
    return jsonify({'error': 'Agent not found'}), 404

@app.route('/api/skills/evolution')
def get_skills_evolution():
    """Get skills evolution data"""
    evolution_data = albrite_family.family_skills_library.get_family_skill_report()
    return jsonify(evolution_data)

@app.route('/api/family/coordinate', methods=['POST'])
def coordinate_family_efforts():
    """Coordinate family efforts"""
    data = request.get_json()
    task_type = data.get('task_type', 'general')
    
    # Execute family coordination
    coordination_results = albrite_family.coordinate_family_efforts()
    
    # Update family state
    family_state['last_update'] = time.time()
    family_state['collaboration_events'].append({
        'type': 'coordination',
        'task_type': task_type,
        'timestamp': datetime.now().isoformat(),
        'results': coordination_results
    })
    
    return jsonify({
        'success': True,
        'results': coordination_results,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/family/evolve', methods=['POST'])
def evolve_family():
    """Trigger family evolution"""
    data = request.get_json()
    environmental_pressure = data.get('environmental_pressure', {
        'complexity': 0.7,
        'competition': 0.6,
        'innovation_demand': 0.8
    })
    
    # Execute family evolution
    evolution_events = albrite_family.evolve_family_skills(environmental_pressure)
    
    # Update family state
    family_state['last_update'] = time.time()
    family_state['skills_evolution'].extend(evolution_events)
    
    return jsonify({
        'success': True,
        'evolution_events': evolution_events,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('family_update', {
        'type': 'connection',
        'message': 'Connected to House of Albrite',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('subscribe_family_updates')
def handle_subscribe():
    """Subscribe to family updates"""
    join_room('family_updates')
    emit('subscribed', {'room': 'family_updates'})

def broadcast_family_update(update_type, data):
    """Broadcast family updates to all connected clients"""
    socketio.emit('family_update', {
        'type': update_type,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }, room='family_updates')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
