from flask import Flask,send_from_directory
from flask_cors import CORS
from pathlib import Path
from backend.api.routes import bp
def create_app():
 app=Flask(__name__);CORS(app);app.register_blueprint(bp,url_prefix='/api');root=Path(__file__).resolve().parents[1]
 @app.get('/')
 def index():return send_from_directory(root/'frontend','index.html')
 return app
