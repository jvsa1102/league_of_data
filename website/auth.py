from flask import Blueprint, render_template, url_for, request, flash, redirect
from . import db
from .models import User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Login bem sucedido!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.teams'))
            else:
                flash('Senha incorreta!', category='error')
        else:
            flash('Email não registrado!', category='error')

    return render_template('login.html', user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        email_exists = User.query.filter_by(email=email).first()
        username_exists = User.query.filter_by(username=username).first()
        if email_exists:
            flash('Email já utilizado', category='error')
        elif username_exists:
            flash('Nome de usuário já utilizado', category='error')
        elif password1 != password2:
            flash('Senhas não conferem', category='error')
        else:
            new_user = User(
                email=email, username=username,
                password=generate_password_hash(password1, 'sha256')
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Usuário criado com sucesso!', category='success')
            return redirect(url_for('views.teams'))

    return render_template('signup.html', user=current_user)
