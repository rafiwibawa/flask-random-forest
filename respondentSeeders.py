import csv
from datetime import datetime
from app import app, db
from models import (
    User, UserProfile,
    Survey, SurveyRespondent, SurveyAnswer,
    Question, QuestionOption, StressPrediction, PredictionLog
)
from slugify import slugify

CSV_PATH = 'responses.csv'  # sesuaikan dengan nama/letak file

with app.app_context():
    
    db.session.query(SurveyAnswer).delete()
    db.session.query(SurveyRespondent).delete()
    db.session.query(UserProfile).delete()
    db.session.query(User).delete()
    db.session.query(StressPrediction).delete()
    db.session.query(PredictionLog).delete()
    db.session.commit()
    print("✅ Semua data berhasil dihapus.")

    # Pastikan survey DASS-21 sudah ada
    survey = Survey.query.filter_by(name='DASS-21').first()
    if not survey:
        raise RuntimeError("Survey DASS-21 belum tersedia. Jalankan seeder pertanyaan dulu.")

    # Ambil opsi value ke id map
    option_map = { (opt.question_option, opt.value): opt.id for opt in QuestionOption.query.all() }

    # Ambil semua pertanyaan text ke id map
    question_map = { q.question: q.id for q in Question.query.all() }

    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # 1. Buat atau dapatkan user
            email = row['Email'] or row['Email Address']
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(email=email, password='pbkdf2:sha256:…', created_at=datetime.utcnow())
                db.session.add(user)
                db.session.flush()  # untuk dapatkan user.id

                # 2. Buat profil
                gender = row.get('Jenis Kelamin', '').strip().lower()
                gender = 'male' if 'laki' in gender else 'female'
                profile = UserProfile(
                    user_id=user.id,
                    name=row.get('Nama ', row.get('Nama')).strip(),
                    gender=gender,
                    universitas=row.get('Asal Universitas ', '').strip(),
                    jurusan=row.get('Jurusan ', '').strip(),
                    semester=row.get('Tingkat pendidikan / Semester', '').strip(),
                    created_at=datetime.utcnow()
                )
                db.session.add(profile)

            # 3. Buat respondent entri
            timestamp = row['Timestamp']
            dt = datetime.strptime(timestamp, '%d/%m/%Y %H:%M:%S')
            respondent = SurveyRespondent(
                user_id=user.id,
                survey_id=survey.id,
                datetime=dt
            )
            db.session.add(respondent)
            db.session.flush()

            # 4. Masukkan jawaban setiap pertanyaan DASS
            # loop pertanyaan utama (pertanyaan data kolom)
            for question_text, qid in question_map.items():
                if question_text in row:
                    raw_val = row[question_text].strip()
                    if raw_val == '':
                        continue
                    try:
                        val = int(raw_val)  # harus sesuai skala 0–3
                    except ValueError:
                        continue

                    # Temukan opsi id
                    # Opsi mapping menggunakan value sebagai string dan text text
                    opt_key = None
                    for (otxt, oval), oid in option_map.items():
                        if oval == str(val):
                            opt_key = oid
                            break
                    if not opt_key:
                        continue

                    ans = SurveyAnswer(
                        question_id=qid,
                        survey_respondent_id=respondent.id,
                        question_option_id=opt_key,
                        answer=val,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(ans)

        db.session.commit()
    print("✅ Seeder data responden berhasil dimasukkan.")
