from flask import Flask
from flask_cors import CORS
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.application_routes import application_bp

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(application_bp, url_prefix='/applications')

    @app.route('/')
    def home():
        return {"message": "Welcome to Next Century Online School API!"}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
