from db import db
from datetime import datetime 

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'consumer'), default='consumer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    name = db.Column(db.String(255))
    gender = db.Column(db.Enum('male', 'female'))
    universitas = db.Column(db.String(255))
    jurusan = db.Column(db.Text)
    semester = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class QuestionCategory(db.Model):
    __tablename__ = 'question_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class QuestionType(db.Model):
    __tablename__ = 'question_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(500))
    question_type_id = db.Column(db.Integer, db.ForeignKey('question_types.id'))
    question_category_id = db.Column(db.Integer, db.ForeignKey('question_categories.id'))
    other_option = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class QuestionOption(db.Model):
    __tablename__ = 'question_options'

    id = db.Column(db.Integer, primary_key=True)
    question_option = db.Column(db.String(255))
    value = db.Column(db.String(255))
    description = db.Column(db.String(255))
    option_category_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class QuestionOptionList(db.Model):
    __tablename__ = 'question_option_lists'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    question_option_id = db.Column(db.Integer, db.ForeignKey('question_options.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Survey(db.Model):
    __tablename__ = 'surveys'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    survey_sluq = db.Column(db.String(255))
    is_premium = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class SurveyQuestionList(db.Model):
    __tablename__ = 'survey_question_lists'

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    question_category_id = db.Column(db.Integer, db.ForeignKey('question_categories.id'))
    page = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class SurveyRespondent(db.Model):
    __tablename__ = 'survey_respondents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 
    user = db.relationship('User', backref='respondents')
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    answers = db.relationship('SurveyAnswer', backref='respondent', lazy=True)
    datetime = db.Column(db.DateTime) 

class SurveyAnswer(db.Model):
    __tablename__ = 'survey_answers'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    survey_respondent_id = db.Column(db.Integer, db.ForeignKey('survey_respondents.id'))
    question_option_id = db.Column(db.Integer, db.ForeignKey('question_options.id'))
    answer = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class PredictionLog(db.Model):
    __tablename__ = 'prediction_logs'

    id = db.Column(db.Integer, primary_key=True)
    survey_respondent_id = db.Column(db.Integer, db.ForeignKey('survey_respondents.id'))
    model_name = db.Column(db.String(255))
    prediction = db.Column(db.String(255))
    probability = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StressPrediction(db.Model):
    __tablename__ = 'stress_predictions'

    id = db.Column(db.Integer, primary_key=True)
    survey_respondent_id = db.Column(db.Integer, db.ForeignKey('survey_respondents.id'))
    stress_level = db.Column(db.Enum('normal', 'mild', 'moderate', 'severe', 'extremely severe'))
    predicted_by_model = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
