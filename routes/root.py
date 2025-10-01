from flask import Blueprint, render_template
 
bp_root = Blueprint('root', __name__, url_prefix='/')

@bp_root.route('/')
def index_db(): 
    return render_template( 'home.html' ) 


@bp_root.route('/dass21')
def dass21_db(): 
    return render_template( 'dass21.html' ) 



@bp_root.route('/mulai')
def mulai_db(): 
    return render_template( 'survey_user_form.html' ) 
