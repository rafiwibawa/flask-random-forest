from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from models import db, QuestionOption, UserProfile, User

bp_survey = Blueprint('bp_survey', __name__)

@bp_survey.route('/dass-21', methods=['GET', 'POST'])
def start_dass21():
    if request.method == "POST":
        email = request.form["email"]
        name = request.form["name"]
        gender = request.form["gender"]
        universitas = request.form.get("universitas")
        jurusan = request.form.get("jurusan")
        semester = request.form.get("semester")

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                password="dass21",
                role="consumer",
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()

        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = UserProfile(
                user_id=user.id,
                name=name,
                gender=gender,
                universitas=universitas,
                jurusan=jurusan,
                semester=semester,
                created_at=datetime.utcnow()
            )
            db.session.add(profile)
            db.session.commit()
 
        return redirect(url_for("bp_survey.dass21_survey", user_id=user.id))

    return render_template("survey_user_form.html")  # GANTI ke file HTML form input user

@bp_survey.route('/dass-21/question', methods=['GET'])
def dass21_survey():
    from models import Survey, SurveyQuestionList, Question, QuestionCategory, QuestionOptionList, QuestionOption

    user_id = request.args.get("user_id")

    survey = Survey.query.filter_by(survey_sluq='dass-21').first_or_404()

    # Ambil semua question_id dari SurveyQuestionList
    question_lists = (
        SurveyQuestionList.query
        .filter_by(survey_id=survey.id)
        .join(QuestionCategory)
        .join(Question, Question.question_category_id == QuestionCategory.id)
        .with_entities(Question.id)
        .distinct()
        .all()
    )
    question_ids = [qid[0] for qid in question_lists]

    # Ambil semua pertanyaan dan opsinya
    questions_data = []
    for qid in question_ids:
        question = Question.query.get(qid)
        option_ids = [qol.question_option_id for qol in QuestionOptionList.query.filter_by(question_id=qid).all()]
        options = QuestionOption.query.filter(QuestionOption.id.in_(option_ids)).all()
        questions_data.append({
            "id": question.id,
            "image": question.image,
            "text": question.question,
            "options": [{"id": opt.id, "text": opt.question_option} for opt in options]
        })

    return render_template('survey.html', questions=questions_data, user_id=user_id)

@bp_survey.route('/submit-dass-21', methods=['POST'])
def submit_dass21():
    from models import SurveyRespondent, SurveyAnswer, Survey
    from datetime import datetime
    import json

    survey = Survey.query.filter_by(survey_sluq='dass-21').first_or_404()
    user_id = request.form.get('user_id')

    answers = request.form.get('answers')
    if not answers:
        return redirect(url_for('bp_survey.dass21_survey'))

    answers = json.loads(answers)  # Format: [{"question_id":1, "option_id":4}, ...]

    respondent = SurveyRespondent(user_id=user_id, survey_id=survey.id, datetime=datetime.utcnow())
    db.session.add(respondent)
    db.session.commit()

    for item in answers: 
        option = db.session.query(QuestionOption).filter_by(id=item['option_id']).first()

        db.session.add(SurveyAnswer(
            question_id=item['question_id'],
            question_option_id=item['option_id'],
            answer=option.value if option else None,
            survey_respondent_id=respondent.id
        ))
    db.session.commit()

    return redirect(url_for('dashboard.index'))

def categorize(score, category):
    if category == 'depresi':
        if score <= 9:
            return "Normal"
        elif score <= 13:
            return "Ringan"
        elif score <= 20:
            return "Sedang"
        elif score <= 27:
            return "Parah"
        else:
            return "Sangat Parah"
    elif category == 'kecemasan':
        if score <= 7:
            return "Normal"
        elif score <= 9:
            return "Ringan"
        elif score <= 14:
            return "Sedang"
        elif score <= 19:
            return "Parah"
        else:
            return "Sangat Parah"
    elif category == 'stres':
        if score <= 14:
            return "Normal"
        elif score <= 18:
            return "Ringan"
        elif score <= 25:
            return "Sedang"
        elif score <= 33:
            return "Parah"
        else:
            return "Sangat Parah"
