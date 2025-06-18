from flask import Blueprint, render_template
 
bp_root = Blueprint('root', __name__, url_prefix='/')

@bp_root.route('/')
def index_db(): 
    return render_template( 'survey_user_form.html' ) 
