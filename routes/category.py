from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from models import db, QuestionCategory 

bp_category = Blueprint('bp_category', __name__)

@bp_category.route('/category', methods=['GET'])
def index():  
    categories = QuestionCategory.query.order_by(QuestionCategory.created_at.desc()).all()
    return render_template("category.html", categories=categories)

@bp_category.route('/category/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    category = QuestionCategory.query.get_or_404(id)
    
    if request.method == 'POST':
        category.name = request.form['name']
        db.session.commit()
        return redirect(url_for('bp_category.index'))
    
    return render_template('category_edit.html', category=category)