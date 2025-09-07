from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change_this_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# ------------------ MODELS ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    company = db.Column(db.String(150), nullable=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    resume = db.Column(db.String(300), nullable=True)
    job = db.relationship('Job', backref=db.backref('applications', lazy=True))


# ------------------ LOGIN REQUIRED DECORATOR ------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# ------------------ ROUTES ------------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------- Register ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# ---------- Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# ---------- Post Job ----------
@app.route('/post_job', methods=['GET', 'POST'])
@login_required
def post_job():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        salary = request.form['salary']
        location = request.form['location']
        company = request.form['company']

        new_job = Job(title=title, description=description, salary=salary, location=location, company=company)
        db.session.add(new_job)
        db.session.commit()

        flash('Job posted successfully!', 'success')
        return redirect(url_for('view_jobs'))

    return render_template('post_job.html', job=None)

# ---------- View Jobs ----------
@app.route('/jobs')
def view_jobs():
    search_query = request.args.get('search', '').strip()
    location_filter = request.args.get('location', '').strip()
    company_filter = request.args.get('company', '').strip()

    query = Job.query

    if search_query:
        query = query.filter(Job.title.ilike(f"%{search_query}%") | Job.description.ilike(f"%{search_query}%"))

    if location_filter:
        query = query.filter(Job.location.ilike(f"%{location_filter}%"))

    if company_filter:
        query = query.filter(Job.company.ilike(f"%{company_filter}%"))

    jobs = query.all()

    return render_template('jobs.html', jobs=jobs,
                           search_query=search_query,
                           location_filter=location_filter,
                           company_filter=company_filter)

# ---------- Apply Job ----------
@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        resume = request.form['resume']  # file upload later

        application = Application(job_id=job_id, name=name, email=email, resume=resume)
        db.session.add(application)
        db.session.commit()

        flash('Application submitted successfully!', 'success')
        return redirect(url_for('view_jobs'))

    return render_template('apply.html', job=job)


# ------------------ MAIN ------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
