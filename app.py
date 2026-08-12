import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

from models import db, User
from routes.auth import auth_bp
from routes.salman.competitors import competitors_bp
from routes.salman.field_tasks import field_tasks_bp
from routes.salman.ai_chat import ai_chat_bp
from routes.salman.finance_meetings import finance_meetings_bp
from routes.nuha.workspace import workspace_bp
from routes.nuha.news import news_bp
from routes.nuha.todo import todo_bp
from routes.mumtahenah.products import products_bp
from routes.mumtahenah.livelocationtrack import tracking_bp

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketmind.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==============================================================================
# BLUEPRINT REGISTRATION (Modular Routing per Feature)
# ==============================================================================
app.register_blueprint(auth_bp)
app.register_blueprint(competitors_bp)
app.register_blueprint(field_tasks_bp)
app.register_blueprint(ai_chat_bp)
app.register_blueprint(finance_meetings_bp)
app.register_blueprint(workspace_bp)
app.register_blueprint(news_bp)
app.register_blueprint(todo_bp)
app.register_blueprint(products_bp)
app.register_blueprint(tracking_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Port 1518 corresponds to the last 4 digits of Student ID: 23101518 (Salman Farsi)
    port = int(os.getenv('PORT', 1518))
    app.run(debug=True, port=port)
