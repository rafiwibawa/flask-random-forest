
python -m venv venv

source venv/bin/activate

pip install flask flask_sqlalchemy flask_migrate python-dotenv pymysql

pip freeze > requirements.txt

flask db init        # hanya sekali di awal
flask db migrate -m "initial tables"
flask db upgrade

pip install pandas scikit-learn joblib sqlalchemy
