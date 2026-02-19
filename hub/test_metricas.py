
import sys
import os
import flask
from flask import Flask

# Add current dir to path
sys.path.append(os.getcwd())

from metricas_routes import metricas_bp

app = Flask(__name__, template_folder='templates')
app.register_blueprint(metricas_bp)

def test_files():
    print("Testing /api/metricas/files...")
    with app.test_client() as client:
        rv = client.get('/api/metricas/files')
        print(f"Status: {rv.status_code}")
        print(f"Data: {rv.json[:2] if rv.json else 'No data'}")
        if rv.status_code == 200:
            return rv.json
    return []

def test_dashboard(filename):
    print(f"Testing /api/metricas/dashboard with {filename}...")
    with app.test_client() as client:
        rv = client.get(f'/api/metricas/dashboard?filename={filename}')
        print(f"Status: {rv.status_code}")
        if rv.status_code == 200:
            data = rv.json
            print(f"KPIs: {data.get('kpis')}")
            print(f"Filtros: {len(data.get('filtros', {}).get('analistas', []))} analistas")

if __name__ == "__main__":
    files = test_files()
    if files:
        test_dashboard(files[0]['filename'])
    else:
        print("No files found to test dashboard.")
