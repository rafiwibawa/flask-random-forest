
from .root import bp_root
from .ml import ml_bp
from .auth import auth_bp
from .dashboard import bp_dashboard  
from .survey import bp_survey  
from .respondent import bp_respondent  
from .question import bp_question  
from .category import bp_category  

def register_blueprints(app):
    app.register_blueprint(bp_root)
    app.register_blueprint(ml_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(bp_dashboard, url_prefix='/dashboard')
    app.register_blueprint(bp_survey, url_prefix='/survey')
    app.register_blueprint(bp_respondent)
    app.register_blueprint(bp_question)
    app.register_blueprint(bp_category)
