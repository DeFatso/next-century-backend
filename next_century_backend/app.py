from flask import Flask
from flask_cors import CORS
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.application_routes import application_bp
from resources import resources_bp
from routes.dashboard_routes import dashboard_bp

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app,
        resources={
            r"/applications/*": {
                "origins": ["http://localhost:3000"],
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Authorization", "Content-Type"]
            },
            r"/auth/*": {
                "origins": ["http://localhost:3000"],
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Authorization", "Content-Type"]
            },
            r"/users/*": {
                "origins": ["http://localhost:3000"],
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Authorization", "Content-Type"]
            },
            r"/resources/*": {  # 👈 Add this block
             "origins": ["http://localhost:3000"],
             "methods": ["GET", "POST", "OPTIONS"],
             "allow_headers": ["Authorization", "Content-Type"]
         }
        })

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(application_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(dashboard_bp)

    
    @app.route('/')
    def home():
        return {"message": "Welcome to the API!"}
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
