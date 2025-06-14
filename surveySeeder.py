from app import app, db
from models import Question, QuestionCategory, QuestionType, QuestionOption, QuestionOptionList, Survey, SurveyQuestionList
from datetime import datetime
from slugify import slugify  # pip install python-slugify jika belum ada

questions_data = [
    ("Saya sama sekali tidak dapat merasakan perasaan positif (contoh: merasa gembira, bangga, dsb).", "depression"),
    ("Saya merasa sulit berinisiatif melakukan sesuatu.", "depression"),
    ("Saya merasa tidak ada lagi yang bisa saya harapkan dimasa depan.", "depression"),
    ("Saya merasa sedih dan tertekan.", "depression"),
    ("Saya tidak bisa merasa antusias terhadap hal apapun (kehilangan minat).", "depression"),
    ("Saya merasa diri saya tidak berharga.", "depression"),
    ("Saya merasa hidup ini tidak berarti.", "depression"),
    ("Saya merasa rongga mulut saya kering.", "anxiety"),
    ("Saya merasa kesulitan bernafas (misalnya seringkali terengah-engah atau tidak dapat bernafas padahal tidak melakukan aktivitas fisik sebelumnya).", "anxiety"),
    ("Saya merasa gemetar (misalnya pada tangan).", "anxiety"),
    ("Saya merasa khawatir dengan situasi dimana saya mungkin menjadi panik dan mempermalukan diri sendiri.", "anxiety"),
    ("Saya merasa hampir panik (seperti mau pingsan).", "anxiety"),
    ("Saya menyadari kondisi jantung saya (seperti meningkatnya atau melemahnya detak jantung) meskipun sedang tidak melalukan aktivitas fisik.", "anxiety"),
    ("Saya merasa ketakutan tanpa alasan yang jelas.", "anxiety"),
    ("Saya merasa sulit untuk beristirahat.", "stress"),
    ("Saya cenderung menunjukan reaksi berlebihan terhadap suatu situasi.", "stress"),
    ("Saya merasa energi saya terkuras karena terlalu cemas (sulit untuk bersantai).", "stress"),
    ("Saya merasa gelisah.", "stress"),
    ("Saya merasa sulit untuk merasa tenang.", "stress"),
    ("Saya sulit untuk bersabar dalam menghadapi gangguan yang terjadi ketika sedang melakukan sesuatu.", "stress"),
    ("Perasaan saya mudah tersinggung atau tersentuh.", "stress"),
]

# Skala jawaban
options = [
    ("Sangat tidak setuju", 0),
    ("Tidak setuju", 1),
    ("Setuju", 2),
    ("Sangat setuju", 3),
]

with app.app_context():
    # Pastikan question type 'single' tersedia
    q_type = QuestionType.query.filter_by(name='single').first()
    if not q_type:
        q_type = QuestionType(name='single')
        db.session.add(q_type)
        db.session.commit()

    # Buat opsi skala jika belum ada
    option_objects = []
    for text, value in options:
        option = QuestionOption.query.filter_by(question_option=text).first()
        if not option:
            option = QuestionOption(
                question_option=text,
                value=str(value),
                created_at=datetime.utcnow()
            )
            db.session.add(option)
            db.session.commit()
        option_objects.append(option)

    category_map = {}
    question_objects = []

    # Tambahkan pertanyaan
    for question_text, cat_name in questions_data:
        if cat_name not in category_map:
            cat = QuestionCategory.query.filter_by(name=cat_name).first()
            if not cat:
                cat = QuestionCategory(name=cat_name, created_at=datetime.utcnow())
                db.session.add(cat)
                db.session.commit()
            category_map[cat_name] = cat

        # Hindari duplikat
        existing = Question.query.filter_by(question=question_text).first()
        if not existing:
            q = Question(
                question=question_text,
                question_type_id=q_type.id,
                question_category_id=category_map[cat_name].id,
                other_option=False,
                created_at=datetime.utcnow()
            )
            db.session.add(q)
            db.session.commit()

            # Hubungkan dengan opsi
            for opt in option_objects:
                link = QuestionOptionList(
                    question_id=q.id,
                    question_option_id=opt.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(link)
            question_objects.append(q)

    db.session.commit()

    # Buat Survey DASS-21
    survey_name = "DASS-21"
    survey = Survey.query.filter_by(name=survey_name).first()
    if not survey:
        survey = Survey(
            name=survey_name,
            survey_sluq=slugify(survey_name),
            is_premium=False,
            created_at=datetime.utcnow()
        )
        db.session.add(survey)
        db.session.commit()

    # Tambahkan SurveyQuestionList berdasarkan kategori unik
    for i, cat in enumerate(category_map.values(), start=1):
        exists = SurveyQuestionList.query.filter_by(survey_id=survey.id, question_category_id=cat.id).first()
        if not exists:
            link = SurveyQuestionList(
                survey_id=survey.id,
                question_category_id=cat.id,
                page=i,
                created_at=datetime.utcnow()
            )
            db.session.add(link)

    db.session.commit()
    print("✅ Seeder berhasil menambahkan pertanyaan, opsi jawaban, dan survey DASS-21.")
