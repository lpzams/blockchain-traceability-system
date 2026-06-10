from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_user_by_username, create_user, get_user_by_id

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user_by_username(username)

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session.permanent = True
            flash('登录成功！', 'success')

            if user['role'] == 'manufacturer':
                return redirect(url_for('manufacturer.dashboard'))
            elif user['role'] == 'distributor':
                return redirect(url_for('distributor.dashboard'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user['role'] == 'regulator':
                return redirect(url_for('regulator.dashboard'))
            else:
                return redirect(url_for('consumer.dashboard'))
        else:
            flash('用户名或密码错误', 'danger')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        company_name = request.form.get('company_name')

        if get_user_by_username(username):
            flash('用户名已存在', 'danger')
            return redirect(url_for('auth.register'))

        password_hash = generate_password_hash(password)
        create_user(username, password_hash, role, company_name)

        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))
