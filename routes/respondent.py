from flask import Blueprint, render_template, request, redirect, url_for, session
from flask import jsonify
from models import db, StressPrediction

bp_respondent = Blueprint('bp_respondent', __name__)

@bp_respondent.route('/respondent', methods=['GET'])
def index():
    from models import SurveyRespondent, UserProfile, User, StressPrediction

    respondents = db.session.query(
        SurveyRespondent.id,
        User.email,
        UserProfile.name,
        UserProfile.gender,
        UserProfile.universitas,
        UserProfile.jurusan,
        UserProfile.semester,
        StressPrediction.stress_level,
        SurveyRespondent.datetime
    ).join(User, User.id == SurveyRespondent.user_id)\
     .join(UserProfile, UserProfile.user_id == User.id)\
     .outerjoin(StressPrediction, StressPrediction.survey_respondent_id == SurveyRespondent.id)\
     .order_by(SurveyRespondent.id.desc())\
     .all()

    return render_template("respondent.html", respondents=respondents)


@bp_respondent.route('/run-stress', methods=['GET'])
def run_stress():
    try:
        from train_stress_model import main as train_stress_main

        result = train_stress_main()
        if not result:
            return jsonify({'message': '❌ Tidak ada data untuk training.'}), 400

        preds = StressPrediction.query.filter_by(predicted_by_model=True).all()
        prediction_data = [
            {
                'respondent_id': p.survey_respondent_id,
                'stress_level': p.stress_level
            } for p in preds
        ]

        return jsonify({
            'accuracy': f"{result['accuracy']}%",
            'mae': result['mae'],
            'rmse': result['rmse'],
            'train_data': result['train_count'],
            'test_data': result['test_count'],
            'classification_report': result['report'],
            # 'predictions': prediction_data
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500