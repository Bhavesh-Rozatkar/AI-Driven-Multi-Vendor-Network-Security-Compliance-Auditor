import os
from pathlib import Path
from flask import Flask, send_from_directory, redirect, request, session, jsonify
from flask_cors import CORS
from backend.api.routes import bp
from backend.device.adapters.pfsense.fixture import PfSenseFixtureAdapter

# Local administrator credentials for this environment.
# Credentials are environment-configurable for hosted deployments.
# Local defaults preserve the existing prototype login for development/demo use.
APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "admin@123")

PROTECTED_PAGES = {"connection", "compliance", "assessment", "remediation"}


def create_app():
    # Resolve the frontend assets before constructing Flask so the built-in
    # static handler always serves the same CSS/JS bundle as the HTML pages.
    # This is intentionally explicit because the application is distributed
    # as a self-contained project rather than installed as a package.
    root = Path(__file__).resolve().parents[1]
    frontend = root / "frontend"
    static_dir = frontend / "static"

    app = Flask(
        __name__,
        static_folder=str(static_dir),
        static_url_path="/static",
    )
    secret_key = os.getenv("FLASK_SECRET_KEY")
    if not secret_key and os.getenv("RENDER") == "true":
        raise RuntimeError("FLASK_SECRET_KEY must be set in Render Environment Variables.")
    app.secret_key = secret_key or "local-secret-key-change-me"
    CORS(app)
    app.register_blueprint(bp, url_prefix="/api")
    # Reset the local pfSense-compatible state when the application starts so each
    # fresh run begins from the same known configuration state.
    PfSenseFixtureAdapter.reset()
    @app.post('/auth/login')
    def login():
        data = request.get_json(silent=True) or {}
        if data.get('username') == APP_USERNAME and data.get('password') == APP_PASSWORD:
            session['user'] = APP_USERNAME
            return jsonify({'ok': True, 'username': APP_USERNAME})
        return jsonify({'ok': False, 'error': 'Invalid username or password.'}), 401

    @app.post('/auth/logout')
    def logout():
        session.clear()
        return jsonify({'ok': True})

    @app.get('/auth/status')
    def auth_status():
        return jsonify({'authenticated': bool(session.get('user')), 'username': session.get('user')})

    @app.get('/api/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'hexaminds'})

    @app.get('/')
    def index():
        return redirect('/connection' if session.get('user') else '/login')

    @app.get('/login')
    def login_page():
        return send_from_directory(frontend, 'login.html')

    @app.get('/<page>')
    def page(page):
        if page not in PROTECTED_PAGES:
            return ('Not found', 404)
        if not session.get('user'):
            return redirect('/login')
        return send_from_directory(frontend, page + '.html')

    return app
