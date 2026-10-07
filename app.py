# app.py - Main Flask Web Server & API Handlers
from flask import Flask, render_template, request, jsonify, Response
from simulation import TCPSimulator

app = Flask(__name__)

@app.route('/')
def index():
    """Serves main TCP simulation dashboard HTML."""
    scenarios = TCPSimulator.SCENARIOS
    return render_template('index.html', scenarios=scenarios)

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    """Triggers TCP simulation and returns stats & diagnostic data."""
    data = request.get_json() or {}
    scenario_key = data.get('scenario', 'normal')
    result = TCPSimulator.run_simulation(scenario_key)
    return jsonify(result)

@app.route('/api/download-report', methods=['POST'])
def api_download_report():
    """Generates downloadable text diagnostic report file."""
    sim_data = request.get_json() or {}
    report_text = TCPSimulator.generate_text_report(sim_data)
    filename = f"tcp_diagnostic_report_{sim_data.get('scenario_key', 'run')}.txt"
    
    return Response(
        report_text,
        mimetype="text/plain",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

if __name__ == '__main__':
    print("Starting TCP Simulator Server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
