from flask import Blueprint, render_template, session, redirect, url_for
from db import db
from sqlalchemy import func
from models import QuestionCategory, Question, QuestionOption, SurveyRespondent, StressPrediction

bp_dashboard = Blueprint('dashboard', __name__)

@bp_dashboard.route('/index', methods=['GET'])
def index():     
    # Summary count
    total_categories = QuestionCategory.query.count()
    total_questions = Question.query.count()
    total_options = QuestionOption.query.count()
    total_respondents = SurveyRespondent.query.count()

    # Bar chart: jumlah pertanyaan per kategori
    category_counts = db.session.query(
        QuestionCategory.name, func.count(Question.id)
    ).join(Question, Question.question_category_id == QuestionCategory.id) \
     .group_by(QuestionCategory.name).all()

    # Pie chart: distribusi stres
    stress_counts = db.session.query(
        StressPrediction.stress_level, func.count(StressPrediction.id)
    ).group_by(StressPrediction.stress_level).all()

    # Siapkan data untuk Chart.js
    chart_bar_labels = [item[0] for item in category_counts]
    chart_bar_data = [item[1] for item in category_counts]

    chart_pie_labels = [item[0].capitalize() for item in stress_counts]
    chart_pie_data = [item[1] for item in stress_counts]

    return render_template('dashboard.html',
                           total_categories=total_categories,
                           total_questions=total_questions,
                           total_options=total_options,
                           total_respondents=total_respondents,
                           chart_bar_labels=chart_bar_labels,
                           chart_bar_data=chart_bar_data,
                           chart_pie_labels=chart_pie_labels,
                           chart_pie_data=chart_pie_data)


