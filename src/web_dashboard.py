"""
Web Dashboard Module
Flask web interface for water quality monitoring
"""

from flask import Flask, render_template_string, jsonify, request
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AquaSentinel-Pi5 Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0093E9 0%, #80D0C7 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header { text-align: center; color: white; margin-bottom: 30px; }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        .card-title { font-size: 1.2em; color: #333; margin-bottom: 15px; }
        .metric { font-size: 3em; font-weight: bold; color: #0093E9; margin: 10px 0; }
        .unit { font-size: 0.5em; color: #666; }
        .status { display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 0.9em; margin-top: 10px; }
        .status-excellent { background: #d4edda; color: #155724; }
        .status-good { background: #d1ecf1; color: #0c5460; }
        .status-fair { background: #fff3cd; color: #856404; }
        .status-poor { background: #f8d7da; color: #721c24; }
        .status-critical { background: #f5c6cb; color: #721c24; font-weight: bold; }
        .events-section { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2); }
        .event-item { padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid; }
        .event-critical { background: #f8d7da; border-left-color: #dc3545; }
        .event-warning { background: #fff3cd; border-left-color: #ffc107; }
        .event-info { background: #d1ecf1; border-left-color: #17a2b8; }
        .timestamp { color: #999; font-size: 0.9em; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>💧 AquaSentinel-Pi5</h1>
            <div>Smart Water Quality Monitoring Dashboard</div>
        </header>
        
        <div class="dashboard">
            <div class="card">
                <div class="card-title">🔬 pH Level</div>
                <div class="metric" id="pH">--</div>
                <div class="status status-good" id="pH-status">Loading...</div>
                <div class="timestamp" id="pH-time">--</div>
            </div>
            
            <div class="card">
                <div class="card-title">💨 Turbidity</div>
                <div class="metric" id="turbidity">--<span class="unit">NTU</span></div>
                <div class="status status-good" id="turbidity-status">Loading...</div>
                <div class="timestamp" id="turbidity-time">--</div>
            </div>
            
            <div class="card">
                <div class="card-title">🌡️ Temperature</div>
                <div class="metric" id="temperature">--<span class="unit">°C</span></div>
                <div class="status status-good" id="temp-status">Loading...</div>
                <div class="timestamp" id="temp-time">--</div>
            </div>
            
            <div class="card">
                <div class="card-title">⭐ Water Quality</div>
                <div class="metric" id="quality-score">--<span class="unit">/100</span></div>
                <div class="status status-good" id="quality-status">Loading...</div>
                <div class="timestamp" id="quality-time">--</div>
            </div>
        </div>
        
        <div class="events-section">
            <h2 style="margin-bottom: 20px;">Recent Events</h2>
            <div id="events-container">
                <div style="text-align: center; padding: 20px; color: #666;">Loading events...</div>
            </div>
        </div>
    </div>
    
    <script>
        const UPDATE_INTERVAL = 10000;
        
        async function updateReadings() {
            try {
                const response = await fetch('/api/current');
                const result = await response.json();
                
                if (result.success) {
                    const data = result.data;
                    const now = new Date().toLocaleTimeString();
                    
                    if (data.pH) {
                        document.getElementById('pH').textContent = data.pH.toFixed(2);
                        updateStatus('pH', data.pH, [6.5, 8.5], [6.0, 9.0], [5.5, 9.5]);
                    }
                    
                    if (data.turbidity) {
                        document.getElementById('turbidity').innerHTML = data.turbidity.toFixed(1) + '<span class="unit">NTU</span>';
                        updateTurbidityStatus(data.turbidity);
                    }
                    
                    if (data.temperature) {
                        document.getElementById('temperature').innerHTML = data.temperature.toFixed(1) + '<span class="unit">°C</span>';
                        updateTempStatus(data.temperature);
                    }
                    
                    if (data.quality_class && data.quality_score) {
                        document.getElementById('quality-score').innerHTML = data.quality_score + '<span class="unit">/100</span>';
                        const statusEl = document.getElementById('quality-status');
                        statusEl.className = 'status status-' + data.quality_class;
                        statusEl.textContent = data.quality_class.charAt(0).toUpperCase() + data.quality_class.slice(1);
                    }
                    
                    ['pH', 'turbidity', 'temp', 'quality'].forEach(id => {
                        document.getElementById(id + '-time').textContent = 'Updated: ' + now;
                    });
                }
            } catch (error) {
                console.error('Error fetching readings:', error);
            }
        }
        
        function updateStatus(prefix, value, excellent, good, fair) {
            const statusEl = document.getElementById(prefix + '-status');
            if (value >= excellent[0] && value <= excellent[1]) {
                statusEl.className = 'status status-excellent';
                statusEl.textContent = 'Excellent';
            } else if (value >= good[0] && value <= good[1]) {
                statusEl.className = 'status status-good';
                statusEl.textContent = 'Good';
            } else if (value >= fair[0] && value <= fair[1]) {
                statusEl.className = 'status status-fair';
                statusEl.textContent = 'Fair';
            } else {
                statusEl.className = 'status status-critical';
                statusEl.textContent = 'Critical';
            }
        }
        
        function updateTurbidityStatus(value) {
            const statusEl = document.getElementById('turbidity-status');
            if (value < 5) {
                statusEl.className = 'status status-excellent';
                statusEl.textContent = 'Excellent';
            } else if (value < 10) {
                statusEl.className = 'status status-good';
                statusEl.textContent = 'Good';
            } else if (value < 25) {
                statusEl.className = 'status status-fair';
                statusEl.textContent = 'Fair';
            } else if (value < 100) {
                statusEl.className = 'status status-poor';
                statusEl.textContent = 'Poor';
            } else {
                statusEl.className = 'status status-critical';
                statusEl.textContent = 'Critical';
            }
        }
        
        function updateTempStatus(value) {
            const statusEl = document.getElementById('temp-status');
            if (value >= 15 && value <= 25) {
                statusEl.className = 'status status-excellent';
                statusEl.textContent = 'Excellent';
            } else if (value >= 10 && value <= 30) {
                statusEl.className = 'status status-good';
                statusEl.textContent = 'Good';
            } else if (value >= 5 && value <= 35) {
                statusEl.className = 'status status-fair';
                statusEl.textContent = 'Fair';
            } else {
                statusEl.className = 'status status-critical';
                statusEl.textContent = 'Critical';
            }
        }
        
        async function updateEvents() {
            try {
                const response = await fetch('/api/events?hours=24');
                const result = await response.json();
                
                if (result.success) {
                    const container = document.getElementById('events-container');
                    
                    if (result.data.length === 0) {
                        container.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">No recent events</div>';
                        return;
                    }
                    
                    container.innerHTML = result.data.slice(0, 10).map(event => `
                        <div class="event-item event-${event.severity}">
                            <strong>${event.severity.toUpperCase()}</strong>: ${event.description}
                            <div style="color: #666; font-size: 0.9em; margin-top: 5px;">
                                ${new Date(event.timestamp).toLocaleString()}
                            </div>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Error fetching events:', error);
            }
        }
        
        updateReadings();
        updateEvents();
        setInterval(updateReadings, UPDATE_INTERVAL);
        setInterval(updateEvents, UPDATE_INTERVAL * 2);
    </script>
</body>
</html>
"""

def create_app(monitor):
    app = Flask(__name__)
    app.config['monitor'] = monitor
    
    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE)
    
    @app.route('/api/current')
    def get_current():
        try:
            readings = monitor.sensor_manager.read_all()
            if readings:
                classification = monitor.classifier.classify(readings)
                readings['quality_class'] = classification['class']
                readings['quality_score'] = classification['score']
                return jsonify({'success': True, 'data': readings})
            return jsonify({'success': False, 'error': 'Failed to read sensors'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/history')
    def get_history():
        try:
            hours = int(request.args.get('hours', 24))
            start = datetime.now() - timedelta(hours=hours)
            readings = monitor.data_handler.get_readings(start_date=start, limit=1000)
            return jsonify({'success': True, 'data': readings})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/events')
    def get_events():
        try:
            hours = int(request.args.get('hours', 24))
            start = datetime.now() - timedelta(hours=hours)
            events = monitor.data_handler.get_events(start_date=start, limit=100)
            return jsonify({'success': True, 'data': events})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return app
