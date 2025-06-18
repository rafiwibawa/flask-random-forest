from flask import Blueprint, jsonify
from models import db, StressPrediction, PredictionLog

ml_bp = Blueprint('ml_bp', __name__)

@ml_bp.route('/run-model/stress', methods=['GET'])
def run_stress_model():
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