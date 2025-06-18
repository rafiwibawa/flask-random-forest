from flask import Blueprint, request, session, redirect, url_for, flash, render_template
from models import db, User
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            session['user_id'] = user.id
            flash("Login berhasil", "success")
            return redirect(url_for('dashboard.index'))
        else:
            flash("Email atau password salah", "danger")

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST': 
        email = request.form.get('email')
        password = request.form.get('password')
        repeat_password = request.form.get('repeat_password')

        if password != repeat_password:
            flash('Password tidak cocok', 'danger')
            return redirect(url_for('auth_bp.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email sudah terdaftar', 'danger')
            return redirect(url_for('auth_bp.register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash('Akun berhasil dibuat, silakan login', 'success')
        return redirect(url_for('auth_bp.login'))
    
    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth_bp.login'))   
