from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Student, Teacher, Parent, User, ContactInfo, Homework, Notice
from werkzeug.utils import secure_filename
from datetime import datetime
import os

auth_bp = Blueprint('auth', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', set())

def save_upload(file):
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f'uploads/{filename}'
    return None

@auth_bp.route('/login')
def login_choice():
    if current_user.is_authenticated:
        uid = str(current_user.get_id())
        if uid.startswith('student_'):
            return redirect(url_for('auth.student_dashboard'))
        if uid.startswith('teacher_'):
            return redirect(url_for('auth.teacher_dashboard'))
        if uid.startswith('parent_'):
            return redirect(url_for('auth.parent_dashboard'))
        return redirect(url_for('admin.dashboard'))
    return render_template('auth/login_choice.html')

@auth_bp.route('/login/student', methods=['GET', 'POST'])
def login_student():
    if current_user.is_authenticated:
        return redirect(url_for('auth.student_dashboard'))
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        password = request.form.get('password', '')
        student = Student.query.filter(
            (Student.student_id == student_id) | (Student.email == student_id)
        ).filter_by(is_active=True).first()
        if student and student.password_hash and student.check_password(password):
            login_user(student)
            flash('Welcome! Logged in as student.', 'success')
            return redirect(url_for('auth.student_dashboard'))
        flash('Invalid Student ID/Email or password. Only registered students can login.', 'error')
    return render_template('auth/login_student.html')

@auth_bp.route('/login/teacher', methods=['GET', 'POST'])
def login_teacher():
    if current_user.is_authenticated:
        return redirect(url_for('auth.teacher_dashboard'))
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id', '').strip()
        password = request.form.get('password', '')
        teacher = Teacher.query.filter(
            (Teacher.teacher_id == teacher_id) | (Teacher.email == teacher_id)
        ).filter_by(is_active=True).first()
        if teacher and teacher.password_hash and teacher.check_password(password):
            login_user(teacher)
            flash('Welcome! Logged in as teacher.', 'success')
            return redirect(url_for('auth.teacher_dashboard'))
        flash('Invalid Teacher ID/Email or password.', 'error')
    return render_template('auth/login_teacher.html')

@auth_bp.route('/login/parent', methods=['GET', 'POST'])
def login_parent():
    if current_user.is_authenticated:
        return redirect(url_for('auth.parent_dashboard'))
    if request.method == 'POST':
        parent_id = request.form.get('parent_id', '').strip()
        password = request.form.get('password', '')
        parent = Parent.query.filter(
            (Parent.parent_id == parent_id) | (Parent.email == parent_id) | (Parent.phone == parent_id)
        ).filter_by(is_active=True).first()
        if parent and parent.password_hash and parent.check_password(password):
            login_user(parent)
            flash('Welcome! Logged in as parent.', 'success')
            return redirect(url_for('auth.parent_dashboard'))
        flash('Invalid Parent ID/Phone/Email or password. Only registered parents can login.', 'error')
    return render_template('auth/login_parent.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))

@auth_bp.route('/student/dashboard')
@login_required
def student_dashboard():
    if not isinstance(current_user, Student):
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))
    homework = Homework.query.filter_by(is_active=True).order_by(Homework.created_at.desc()).limit(20).all()
    # filter by class if set
    if current_user.class_grade:
        hw_class = [h for h in homework if not h.class_grade or h.class_grade.lower() in (current_user.class_grade or '').lower()]
        if hw_class:
            homework = hw_class
    notices = Notice.query.filter_by(is_published=True).order_by(Notice.date.desc()).limit(10).all()
    return render_template('auth/student_dashboard.html', student=current_user, homework=homework, notices=notices)

@auth_bp.route('/teacher/dashboard', methods=['GET', 'POST'])
@login_required
def teacher_dashboard():
    if not isinstance(current_user, Teacher):
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        class_grade = request.form.get('class_grade', '').strip()
        if not title:
            flash('Homework title is required.', 'error')
        else:
            hw = Homework(
                teacher_id=current_user.id,
                teacher_name=current_user.name,
                title=title,
                description=description,
                class_grade=class_grade
            )
            f = request.files.get('attachment')
            if f and f.filename:
                path = save_upload(f)
                if path:
                    hw.attachment = path
                    hw.attachment_name = f.filename
            db.session.add(hw)
            db.session.commit()
            flash('Homework sent successfully!', 'success')
            return redirect(url_for('auth.teacher_dashboard'))
    my_hw = Homework.query.filter_by(teacher_id=current_user.id).order_by(Homework.created_at.desc()).limit(15).all()
    notices = Notice.query.filter_by(is_published=True).order_by(Notice.date.desc()).limit(8).all()
    return render_template('auth/teacher_dashboard.html', teacher=current_user, homework_list=my_hw, notices=notices)

@auth_bp.route('/parent/dashboard')
@login_required
def parent_dashboard():
    if not isinstance(current_user, Parent):
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))
    homework = Homework.query.filter_by(is_active=True).order_by(Homework.created_at.desc()).limit(20).all()
    if current_user.student_class:
        hw_f = [h for h in homework if not h.class_grade or h.class_grade.lower() in (current_user.student_class or '').lower()]
        if hw_f:
            homework = hw_f
    notices = Notice.query.filter_by(is_published=True).order_by(Notice.date.desc()).limit(10).all()
    return render_template('auth/parent_dashboard.html', parent=current_user, homework=homework, notices=notices)

@auth_bp.route('/view-student-profile', methods=['GET', 'POST'])
def view_student_profile():
    student = None
    searched = False
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        class_grade = request.form.get('class_grade', '').strip()
        parent_phone = request.form.get('parent_phone', '').strip()
        searched = True
        if name and class_grade and parent_phone:
            phone_clean = parent_phone.replace(' ', '').replace('-', '')
            for s in Student.query.filter_by(is_active=True).all():
                s_phone = (s.parent_phone or '').replace(' ', '').replace('-', '')
                if (s.name.lower() == name.lower() and
                    (s.class_grade or '').lower() == class_grade.lower() and
                    s_phone == phone_clean):
                    student = s
                    break
            if not student:
                flash('No matching student found.', 'error')
        else:
            flash('Please fill Name, Class and Parent Contact Number.', 'error')
    return render_template('auth/view_student_profile.html', student=student, searched=searched)


# ========== PUBLIC REGISTRATION ==========

@auth_bp.route('/register')
def register_choice():
    """Choose Student / Parent / Teacher registration"""
    return render_template('auth/register_choice.html')


@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    """
    Student registration ONLY if data matches an existing admin-created Student record.
    Match by: Student ID, OR (Name + Class + Parent Phone).
    Then student sets their own login password.
    """
    if current_user.is_authenticated:
        return redirect(url_for('auth.student_dashboard'))

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        name = request.form.get('name', '').strip()
        class_grade = request.form.get('class_grade', '').strip()
        parent_phone = request.form.get('parent_phone', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        if not password or len(password) < 4:
            flash('Password must be at least 4 characters.', 'error')
            return render_template('auth/register_student.html')
        if password != password2:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register_student.html')

        # Find matching admin student record
        matched = None
        if student_id:
            matched = Student.query.filter(
                (Student.student_id == student_id) | (Student.email == student_id)
            ).first()

        if not matched and name and class_grade and parent_phone:
            phone_clean = parent_phone.replace(' ', '').replace('-', '')
            for s in Student.query.all():
                s_phone = (s.parent_phone or '').replace(' ', '').replace('-', '')
                if (s.name or '').lower() == name.lower() and \
                   (s.class_grade or '').lower() == class_grade.lower() and \
                   s_phone == phone_clean:
                    matched = s
                    break

        if not matched:
            flash('No matching student found in school records. Your Name, Class and Parent Phone (or Student ID) must match the data entered by admin. Contact the school office.', 'error')
            return render_template('auth/register_student.html')

        if matched.password_hash:
            flash('This student account is already registered. Please login instead.', 'error')
            return redirect(url_for('auth.login_student'))

        # Claim account – set password (and optional email update)
        matched.set_password(password)
        if email:
            matched.email = email
        matched.is_active = True
        db.session.commit()
        flash('Registration successful! You can now login as student.', 'success')
        return redirect(url_for('auth.login_student'))

    return render_template('auth/register_student.html')


@auth_bp.route('/register/parent', methods=['GET', 'POST'])
def register_parent():
    """Parent can self-register. Optional link to child name/class."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.parent_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        student_name = request.form.get('student_name', '').strip()
        student_class = request.form.get('student_class', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        if not name or not phone:
            flash('Name and phone are required.', 'error')
            return render_template('auth/register_parent.html')
        if not password or len(password) < 4:
            flash('Password must be at least 4 characters.', 'error')
            return render_template('auth/register_parent.html')
        if password != password2:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register_parent.html')

        # If admin already created this parent (by phone), claim it
        existing = Parent.query.filter(
            (Parent.phone == phone) | (Parent.email == email if email else False)
        ).first()
        if existing:
            if existing.password_hash:
                flash('This parent account already exists. Please login.', 'error')
                return redirect(url_for('auth.login_parent'))
            existing.set_password(password)
            existing.name = name or existing.name
            if email:
                existing.email = email
            if student_name:
                existing.student_name = student_name
            if student_class:
                existing.student_class = student_class
            existing.is_active = True
            db.session.commit()
            flash('Registration successful! You can now login as parent.', 'success')
            return redirect(url_for('auth.login_parent'))

        # New parent self-registration
        if email and Parent.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register_parent.html')

        p = Parent(
            name=name,
            phone=phone,
            email=email or None,
            student_name=student_name or None,
            student_class=student_class or None,
            is_active=True
        )
        p.set_password(password)
        db.session.add(p)
        db.session.commit()
        flash('Parent registration successful! You can now login.', 'success')
        return redirect(url_for('auth.login_parent'))

    return render_template('auth/register_parent.html')


@auth_bp.route('/register/teacher', methods=['GET', 'POST'])
def register_teacher():
    """
    Teacher registration:
    - If admin already has a Teacher with matching Teacher ID or Email → claim & set password
    - Otherwise create new teacher with is_active=False (pending admin approval)
    """
    if current_user.is_authenticated:
        return redirect(url_for('auth.teacher_dashboard'))

    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        designation = request.form.get('designation', '').strip()
        department = request.form.get('department', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        if not name:
            flash('Name is required.', 'error')
            return render_template('auth/register_teacher.html')
        if not password or len(password) < 4:
            flash('Password must be at least 4 characters.', 'error')
            return render_template('auth/register_teacher.html')
        if password != password2:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register_teacher.html')

        matched = None
        if teacher_id:
            matched = Teacher.query.filter(
                (Teacher.teacher_id == teacher_id) | (Teacher.email == teacher_id)
            ).first()
        if not matched and email:
            matched = Teacher.query.filter_by(email=email).first()
        if not matched and name:
            # soft match by exact name if only one
            qs = Teacher.query.filter(Teacher.name.ilike(name)).all()
            if len(qs) == 1:
                matched = qs[0]

        if matched:
            if matched.password_hash:
                flash('This teacher account is already registered. Please login.', 'error')
                return redirect(url_for('auth.login_teacher'))
            matched.set_password(password)
            if email:
                matched.email = email
            if phone:
                matched.phone = phone
            matched.is_active = True
            db.session.commit()
            flash('Registration successful! You can now login as teacher.', 'success')
            return redirect(url_for('auth.login_teacher'))

        # New teacher – pending approval
        if email and Teacher.query.filter_by(email=email).first():
            flash('Email already in use.', 'error')
            return render_template('auth/register_teacher.html')

        t = Teacher(
            teacher_id=teacher_id or None,
            name=name,
            email=email or None,
            phone=phone or None,
            designation=designation or None,
            department=department or None,
            is_active=False  # admin must approve
        )
        t.set_password(password)
        db.session.add(t)
        db.session.commit()
        flash('Teacher registration submitted. Please wait for school admin to activate your account before login.', 'success')
        return redirect(url_for('auth.login_teacher'))

    return render_template('auth/register_teacher.html')
