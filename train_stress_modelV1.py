import pandas as pd
import joblib
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import text

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
    # =============================
    # 1. Encode label menjadi angka
    # =============================
    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    # =============================
    # 2. Train model Random Forest
    # =============================
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y_encoded)

    # =============================
    # 3. Simpan model dan encoder ke file
    # =============================
    joblib.dump((model, encoder), "stress_model.pkl")
    print("✅ Model disimpan ke 'stress_model.pkl'")

    # =============================
    # 4. Prediksi ulang data training
    # =============================
    y_pred = model.predict(X)              # Prediksi label (encoded)
    y_proba = model.predict_proba(X)       # Probabilitas dari tiap kelas

    # =============================
    # 5. Simpan hasil prediksi ke PredictionLog
    # =============================
    for i, respondent_id in enumerate(respondent_ids):
        predicted_label = encoder.inverse_transform([y_pred[i]])[0]  # Kembalikan label ke bentuk string
        max_proba = round(max(y_proba[i]), 4)                         # Ambil probabilitas tertinggi

        # Cek apakah sudah ada log prediksi sebelumnya untuk responden & model ini
        existing_log = PredictionLog.query.filter_by(
            survey_respondent_id=respondent_id,
            model_name='RandomForest'
        ).first()

        # Jika belum ada, simpan prediksi baru
        if not existing_log:
            log = PredictionLog(
                survey_respondent_id=respondent_id,
                model_name='RandomForest',
                prediction=predicted_label,
                probability=max_proba,
                created_at=datetime.utcnow()
            )
            db.session.add(log)

    # Simpan semua perubahan ke database
    db.session.commit()
    print("📝 Semua hasil prediksi dicatat ke PredictionLog.")


def main():
    print("📊 Mencoba training dengan label manual...")
    X, y, respondent_ids = load_training_data(use_pseudo=False)

    if X.empty:
        print("⚠️ Tidak ada label manual. Menggunakan pseudo-label...")
        save_pseudo_labels()
        X, y, respondent_ids = load_training_data(use_pseudo=True)

    if X.empty:
        print("❌ Tidak ada data yang valid untuk training.")
        return

    print(f"🔧 Melatih model dengan {len(X)} data...")
    train_and_save_model(X, y, respondent_ids)
    print("🎉 Selesai. Model siap digunakan!")
