from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from models import db, QuestionCategory, Question

bp_question = Blueprint('bp_question', __name__)

@bp_question.route('/question', methods=['GET'])
def index():   
    questions = db.session.query(
        Question.id,
        Question.question,
        Question.description,
        Question.created_at,
        QuestionCategory.name.label('category_name')
    ).join(QuestionCategory, Question.question_category_id == QuestionCategory.id)\
     .order_by(Question.created_at.desc()).all()

    return render_template("question.html", questions=questions)

@bp_question.route('/question/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    question = Question.query.get_or_404(id)
    categories = QuestionCategory.query.all()

    if request.method == 'POST':
        question.question = request.form['question']
        question.description = request.form['description']
        question.question_category_id = request.form['category_id']
        db.session.commit()
        return redirect(url_for('bp_question.index'))

    return render_template('question_edit.html', question=question, categories=categories)
