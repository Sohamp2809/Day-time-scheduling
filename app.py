from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Task
from forms import LoginForm, RegisterForm, TaskForm


app = Flask(__name__)
app.config['SECRET_KEY'] = '4dd4966727a85e0ff31c3fff615228b7'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
db.init_app(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2')
        new_user = User(email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Error creating account. Try again!', 'danger')
            db.session.rollback()

    return render_template('register.html')

@app.route('/home')
@login_required
def home():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('home.html', tasks=tasks)

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        new_task = Task(title=title, description=description, user_id=current_user.id)

        try:
            db.session.add(new_task)
            db.session.commit()
            flash('Task added successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash('Error adding task. Try again!', 'danger')
            db.session.rollback()

    return render_template('add_task.html')

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        flash('You do not have permission to edit this task.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']

        try:
            db.session.commit()
            flash('Task updated successfully!', 'success')
            return redirect(url_for('edit_task', task_id=task.id))  # Redirect back to the edit page
        except Exception as e:
            flash('Error updating task. Try again!', 'danger')
            db.session.rollback()

    return render_template('edit_task.html', task=task)


@app.route('/delete_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        flash('You do not have permission to delete this task.', 'danger')
        return redirect(url_for('home'))

    try:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting task. Try again!', 'danger')
        db.session.rollback()

    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
