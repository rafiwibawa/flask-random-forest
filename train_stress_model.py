import pandas as pd
import joblib
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import text
from sklearn.metrics import (
    classification_report, accuracy_score,
    mean_absolute_error, mean_squared_error
)

from sklearn.model_selection import train_test_split

from app import app
from db import db
from models import (
    SurveyRespondent,
    SurveyAnswer,
    QuestionCategory,
    Question,
    StressPrediction,
    PredictionLog
)

STRESS_LEVEL_SCORE = {
    "normal": 0,
    "mild": 1,
    "moderate": 2,
    "severe": 3,
    "extremely severe": 4
}

def categorize_stress(score):
    if score <= 14:
        return "normal"
    elif score <= 18:
        return "mild"
    elif score <= 25:
        return "moderate"
    elif score <= 33:
        return "severe"
    else:
        return "extremely severe"


def get_stress_question_ids():
    category = QuestionCategory.query.filter_by(name='stress').first()
    if not category:
        raise ValueError("❌ Kategori 'stress' tidak ditemukan.")
    return [q.id for q in Question.query.filter_by(question_category_id=category.id).all()]


def load_training_data(use_pseudo=False):
    stress_question_ids = get_stress_question_ids()
    respondents = SurveyRespondent.query.all()

    data, labels, respondent_ids = [], [], []

    for respondent in respondents:
        answers = SurveyAnswer.query.filter(
            SurveyAnswer.survey_respondent_id == respondent.id,
            SurveyAnswer.question_id.in_(stress_question_ids)
        ).all()

        if len(answers) != len(stress_question_ids):
            continue

        sorted_answers = sorted(answers, key=lambda a: a.question_id)
        values = [int(a.answer) for a in sorted_answers]

        label_obj = StressPrediction.query.filter_by(
            survey_respondent_id=respondent.id,
            predicted_by_model=False
        ).first()

        if label_obj:
            label = label_obj.stress_level
        elif use_pseudo:
            score = sum(values) * 2
            label = categorize_stress(score)
        else:
            continue

        data.append(values)
        labels.append(label)
        respondent_ids.append(respondent.id)

    return pd.DataFrame(data), pd.Series(labels), respondent_ids


def save_pseudo_labels():
    print("🔁 Menyimpan pseudo-label ke database...")
    stress_question_ids = get_stress_question_ids()
    engine = db.engine

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT survey_respondent_id
            FROM survey_answers
            WHERE question_id IN :ids
        """), {"ids": tuple(stress_question_ids)})
        user_ids = [row[0] for row in result]

        for user_id in user_ids:
            df = pd.read_sql(text("""
                SELECT question_id, answer
                FROM survey_answers
                WHERE survey_respondent_id = :uid
                  AND question_id IN :ids
            """), conn, params={"uid": user_id, "ids": tuple(stress_question_ids)})

            if df.shape[0] != len(stress_question_ids):
                continue

            df = df.sort_values("question_id")
            score = df["answer"].astype(int).sum() * 2
            label = categorize_stress(score)

            check = conn.execute(text("""
                SELECT COUNT(*) FROM stress_predictions
                WHERE survey_respondent_id = :uid AND predicted_by_model = 1
            """), {"uid": user_id}).scalar()

            if check == 0:
                conn.execute(text("""
                    INSERT INTO stress_predictions (survey_respondent_id, stress_level, predicted_by_model, created_at)
                    VALUES (:uid, :label, 1, :created_at)
                """), {
                    "uid": user_id,
                    "label": label,
                    "created_at": datetime.utcnow()
                })

        conn.commit()
    print("✅ Pseudo-label berhasil disimpan.")

def train_and_save_model(X, y, respondent_ids):
    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    # Split data latih & uji
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.25, random_state=42, stratify=y_encoded
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    joblib.dump((model, encoder), "stress_model.pkl")
    print("✅ Model disimpan ke 'stress_model.pkl'")

    # Evaluasi
    y_pred = model.predict(X_test)
    acc = round(accuracy_score(y_test, y_pred) * 100, 2)
    print(f"🎯 Akurasi model: {acc}%")

    report_dict = classification_report(
        y_test, y_pred, target_names=encoder.classes_, output_dict=True
    )


    # Evaluasi MAE dan RMSE berdasarkan skor stress level
    y_test_labels = encoder.inverse_transform(y_test)
    y_pred_labels = encoder.inverse_transform(y_pred)

    y_test_scores = [STRESS_LEVEL_SCORE[l] for l in y_test_labels]
    y_pred_scores = [STRESS_LEVEL_SCORE[l] for l in y_pred_labels]

    mae = round(mean_absolute_error(y_test_scores, y_pred_scores), 3)
    rmse = round(np.sqrt(mean_squared_error(y_test_scores, y_pred_scores)), 3)


    # Simpan ke PredictionLog hanya untuk seluruh data (bukan split uji)
    full_preds = model.predict(X)
    full_proba = model.predict_proba(X)

    for i, respondent_id in enumerate(respondent_ids):
        pred_label = encoder.inverse_transform([full_preds[i]])[0]
        prob = round(max(full_proba[i]), 4)

        existing = PredictionLog.query.filter_by(
            survey_respondent_id=respondent_id,
            model_name='RandomForest'
        ).first()

        if not existing:
            db.session.add(PredictionLog(
                survey_respondent_id=respondent_id,
                model_name='RandomForest',
                prediction=pred_label,
                probability=prob,
                created_at=datetime.utcnow()
            ))

    db.session.commit()

    return {
        "accuracy": acc,
        "report": report_dict,       
        "mae": mae,
        "rmse": rmse, 
        "train_count": len(X_train),
        "test_count": len(X_test)
    }


def main():
    print("📊 Mencoba training dengan label manual...")
    X, y, respondent_ids = load_training_data(use_pseudo=False)

    if X.empty:
        print("⚠️ Tidak ada label manual. Menggunakan pseudo-label...")
        save_pseudo_labels()
        X, y, respondent_ids = load_training_data(use_pseudo=True)

    if X.empty:
        print("❌ Tidak ada data yang valid untuk training.")
        return None

    print(f"🔧 Melatih model dengan {len(X)} data...")
    result = train_and_save_model(X, y, respondent_ids)
    print("🎉 Selesai. Model siap digunakan!")

    return result
