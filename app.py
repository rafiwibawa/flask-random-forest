import os
from flask import Flask
from dotenv import load_dotenv
from db import db, migrate   
from flask_session import Session

load_dotenv()

app = Flask(__name__)

app.secret_key = 'sUp3rs3cr3t2025'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate.init_app(app, db)

from models import *
from routes import register_blueprints  
register_blueprints(app)  

if not os.path.exists('./.flask_session'):
    os.makedirs('./.flask_session')

app.config['SESSION_FILE_DIR'] = './.flask_session'

if __name__ == '__main__':
    app.run(debug=True)
