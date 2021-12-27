import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm, StudentForm, FeesForm
from app.models import User, Student, StudentFees
from flask_login import login_user, current_user, logout_user, login_required



@app.route("/home")
@login_required
def home():
    return render_template('home.html', students=Student.query.all())

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/")
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/student/new", methods=['GET', 'POST'])
@login_required
def new_student():
    form = StudentForm()
    if form.validate_on_submit():
        student = Student(
            # enrollment_number=form.enrollment_number.data,
            student_name=form.student_name.data,
            father_name=form.father_name.data,
            contact_number=form.contact_number.data,
            course_name=form.course_name.data,
            total_fees=form.total_fees.data,
            admin=current_user
        )

        db.session.add(student)
        db.session.commit()
        flash('Your student has been added !', 'success')
        return redirect(url_for('home'))
    return render_template('create_student.html', title='New Student',
                           form=form, legend='New Student')


@app.route("/student/<int:student_id>")
def student(student_id):
    student = Student.query.get_or_404(student_id)
    student_fees = StudentFees.query.filter_by(student_id=student_id)

    # calculate fees
    fees_paid_till = 0
    for sf in student_fees:
        fees_paid_till += sf.fees

    return render_template('student.html', student=student, student_fees=student_fees, fees_paid_till=fees_paid_till)


@app.route("/student/<int:student_id>/update", methods=['GET', 'POST'])
@login_required
def update_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    form = StudentForm()
    if form.validate_on_submit():
        # student.enrollment_number = form.enrollment_number.data
        student.student_name = form.student_name.data
        student.father_name = form.father_name.data
        student.contact_number = form.contact_number.data
        student.course_name = form.course_name.data
        student.total_fees = form.total_fees.data

        db.session.commit()
        flash('Your student has been updated!', 'success')
        return redirect(url_for('student', student_id=student.id))
    elif request.method == 'GET':
        # form.enrollment_number.data = student.enrollment_number
        form.student_name.data = student.student_name
        form.father_name.data = student.father_name
        form.contact_number.data = student.contact_number
        form.course_name.data = student.course_name
        form.total_fees.data = student.total_fees

    return render_template('create_student.html', title='Update Student',
                           form=form, legend='Update Student')


@app.route("/student/<int:student_id>/delete", methods=['POST'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Your student has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/student/<int:student_id>/fees", methods=['GET', 'POST'])
@login_required
def add_fees(student_id):
    form = FeesForm()
    if form.validate_on_submit():
        student_fees = StudentFees(
            fees=form.fees.data,
            student_id=student_id
        )

        db.session.add(student_fees)
        db.session.commit()
        flash('Your student Fees has been added !', 'success')
        return redirect(url_for('student', student_id=student_id))
    return render_template('add_student_fees.html', title='Add Student Fees',
                           form=form)

@app.route("/delete_student_fee/<int:student_id>/<int:student_fee_id>", methods=['POST'])
@login_required
def delete_student_fee(student_id, student_fee_id):
    student_fee = StudentFees.query.get_or_404(student_fee_id)
    db.session.delete(student_fee)
    db.session.commit()
    flash('Your student fee has been deleted!', 'success')
    return redirect(url_for('student', student_id=student_id))