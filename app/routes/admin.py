from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import (
    db, User, Hero, About, PrincipalMessage, Program, Faculty, Student, Teacher,
    Notice, Event, GalleryImage, Facility, AdmissionApplication,
    ContactMessage, ContactInfo, NewsletterSubscriber, SiteSetting, Announcement, PageEmbed
)
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from app.mail_utils import notify_subscribers_notice

admin_bp = Blueprint('admin', __name__)

def make_slug(text):
    import re
    text = (text or '').lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:200] or 'item'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_upload(file):
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f'uploads/{filename}'
    return None

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Admin access required.', 'error')
            return redirect(url_for('admin.login'))
        # Admin User model has role; students/teachers use different get_id prefix
        uid = str(current_user.get_id())
        if uid.startswith('student_') or uid.startswith('teacher_') or uid.startswith('parent_'):
            flash('Admin access required.', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and isinstance(current_user, User):
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'notices': Notice.query.count(),
        'events': Event.query.count(),
        'gallery': GalleryImage.query.count(),
        'applications': AdmissionApplication.query.filter_by(status='Pending').count(),
        'messages': ContactMessage.query.filter_by(is_read=False).count(),
        'programs': Program.query.count(),
        'faculty': Faculty.query.count(),
        'students': Student.query.count(),
        'teachers': Teacher.query.count(),
        'subscribers': NewsletterSubscriber.query.count(),
    }
    recent_apps = AdmissionApplication.query.order_by(AdmissionApplication.created_at.desc()).limit(5).all()
    recent_msgs = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, recent_apps=recent_apps, recent_msgs=recent_msgs)

# --- Hero ---
@admin_bp.route('/hero', methods=['GET', 'POST'])
@login_required
@admin_required
def hero():
    hero = Hero.query.first() or Hero()
    if not Hero.query.first():
        db.session.add(hero)
        db.session.commit()
    if request.method == 'POST':
        hero.label = request.form.get('label')
        hero.title = request.form.get('title')
        hero.subtitle = request.form.get('subtitle')
        hero.cta_primary = request.form.get('cta_primary')
        hero.cta_primary_link = request.form.get('cta_primary_link')
        hero.cta_secondary = request.form.get('cta_secondary')
        hero.cta_secondary_link = request.form.get('cta_secondary_link')
        path = save_upload(request.files.get('image'))
        if path:
            hero.image = path
        db.session.commit()
        flash('Hero updated.', 'success')
        return redirect(url_for('admin.hero'))
    return render_template('admin/hero.html', hero=hero)

# --- About ---
@admin_bp.route('/about', methods=['GET', 'POST'])
@login_required
@admin_required
def about():
    about = About.query.first() or About()
    if not About.query.first():
        db.session.add(about)
        db.session.commit()
    if request.method == 'POST':
        about.label = request.form.get('label')
        about.title = request.form.get('title')
        about.content = request.form.get('content')
        about.established = request.form.get('established')
        about.academic_level = request.form.get('academic_level')
        about.programs_plus2 = request.form.get('programs_plus2')
        about.affiliation = request.form.get('affiliation')
        path = save_upload(request.files.get('image'))
        if path:
            about.image = path
        db.session.commit()
        flash('About updated.', 'success')
        return redirect(url_for('admin.about'))
    return render_template('admin/about.html', about=about)

# --- Principal ---
@admin_bp.route('/principal', methods=['GET', 'POST'])
@login_required
@admin_required
def principal():
    pm = PrincipalMessage.query.first() or PrincipalMessage()
    if not PrincipalMessage.query.first():
        db.session.add(pm)
        db.session.commit()
    if request.method == 'POST':
        pm.name = request.form.get('name')
        pm.designation = request.form.get('designation')
        pm.title = request.form.get('title')
        pm.message = request.form.get('message')
        path = save_upload(request.files.get('photo'))
        if path:
            pm.photo = path
        db.session.commit()
        flash('Principal message updated.', 'success')
        return redirect(url_for('admin.principal'))
    return render_template('admin/principal.html', principal=pm)

# --- Programs ---
@admin_bp.route('/programs')
@login_required
@admin_required
def programs():
    items = Program.query.order_by(Program.order).all()
    return render_template('admin/programs.html', items=items)

@admin_bp.route('/programs/add', methods=['GET', 'POST'])
@login_required
@admin_required
def program_add():
    if request.method == 'POST':
        name = request.form.get('name')
        p = Program(name=name, slug=make_slug(name), category=request.form.get('category'),
                    level=request.form.get('level'), description=request.form.get('description'),
                    order=int(request.form.get('order') or 0), is_active=bool(request.form.get('is_active')))
        path = save_upload(request.files.get('image'))
        if path:
            p.image = path
        db.session.add(p)
        db.session.commit()
        flash('Program added.', 'success')
        return redirect(url_for('admin.programs'))
    return render_template('admin/program_form.html', item=None)

@admin_bp.route('/programs/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def program_edit(id):
    item = Program.query.get_or_404(id)
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.slug = make_slug(item.name)
        item.category = request.form.get('category')
        item.level = request.form.get('level')
        item.description = request.form.get('description')
        item.order = int(request.form.get('order') or 0)
        item.is_active = bool(request.form.get('is_active'))
        path = save_upload(request.files.get('image'))
        if path:
            item.image = path
        db.session.commit()
        flash('Program updated.', 'success')
        return redirect(url_for('admin.programs'))
    return render_template('admin/program_form.html', item=item)

@admin_bp.route('/programs/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def program_delete(id):
    item = Program.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Program deleted.', 'success')
    return redirect(url_for('admin.programs'))

# --- Notices (with any file attachment) ---
@admin_bp.route('/notices')
@login_required
@admin_required
def notices():
    items = Notice.query.order_by(Notice.date.desc()).all()
    return render_template('admin/notices.html', items=items)

@admin_bp.route('/notices/add', methods=['GET', 'POST'])
@login_required
@admin_required
def notice_add():
    if request.method == 'POST':
        title = request.form.get('title')
        n = Notice(title=title, slug=make_slug(title), category=request.form.get('category'),
                   content=request.form.get('content'),
                   date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date() if request.form.get('date') else datetime.utcnow().date(),
                   is_published=bool(request.form.get('is_published')))
        f = request.files.get('attachment')
        if f and f.filename:
            path = save_upload(f)
            if path:
                n.attachment = path
                n.attachment_name = f.filename
        db.session.add(n)
        db.session.commit()
        if n.is_published:
            try:
                n_sent = notify_subscribers_notice(n.title, n.slug, n.content or '')
                flash(f'Notice added. Email sent to {n_sent} subscriber(s).', 'success')
            except Exception:
                flash('Notice added. (Email to subscribers could not be sent – check SMTP.)', 'success')
        else:
            flash('Notice added (draft – not emailed).', 'success')
        return redirect(url_for('admin.notices'))
    return render_template('admin/notice_form.html', item=None)

@admin_bp.route('/notices/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def notice_edit(id):
    item = Notice.query.get_or_404(id)
    if request.method == 'POST':
        item.title = request.form.get('title')
        item.slug = make_slug(item.title)
        item.category = request.form.get('category')
        item.content = request.form.get('content')
        if request.form.get('date'):
            item.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        item.is_published = bool(request.form.get('is_published'))
        f = request.files.get('attachment')
        if f and f.filename:
            path = save_upload(f)
            if path:
                item.attachment = path
                item.attachment_name = f.filename
        db.session.commit()
        if item.is_published:
            try:
                n_sent = notify_subscribers_notice(item.title, item.slug, item.content or '')
                flash(f'Notice updated. Email sent to {n_sent} subscriber(s).', 'success')
            except Exception:
                flash('Notice updated. (Subscriber email failed – check SMTP.)', 'success')
        else:
            flash('Notice updated (unpublished – not emailed).', 'success')
        return redirect(url_for('admin.notices'))
    return render_template('admin/notice_form.html', item=item)

@admin_bp.route('/notices/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def notice_delete(id):
    item = Notice.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Notice deleted.', 'success')
    return redirect(url_for('admin.notices'))

# --- Gallery ---
@admin_bp.route('/gallery')
@login_required
@admin_required
def gallery():
    items = GalleryImage.query.order_by(GalleryImage.created_at.desc()).all()
    return render_template('admin/gallery.html', items=items)

@admin_bp.route('/gallery/add', methods=['GET', 'POST'])
@login_required
@admin_required
def gallery_add():
    if request.method == 'POST':
        g = GalleryImage(title=request.form.get('title'), category=request.form.get('category'),
                         description=request.form.get('description'), is_active=bool(request.form.get('is_active')))
        path = save_upload(request.files.get('image'))
        if path:
            g.image = path
            db.session.add(g)
            db.session.commit()
            flash('Image added.', 'success')
        else:
            flash('Please upload a valid image.', 'error')
        return redirect(url_for('admin.gallery'))
    return render_template('admin/gallery_form.html', item=None)

@admin_bp.route('/gallery/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def gallery_delete(id):
    item = GalleryImage.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Image deleted.', 'success')
    return redirect(url_for('admin.gallery'))

# --- Facilities ---
@admin_bp.route('/facilities')
@login_required
@admin_required
def facilities():
    items = Facility.query.order_by(Facility.order).all()
    return render_template('admin/facilities.html', items=items)

@admin_bp.route('/facilities/add', methods=['GET', 'POST'])
@login_required
@admin_required
def facility_add():
    if request.method == 'POST':
        f = Facility(name=request.form.get('name'), description=request.form.get('description'),
                     icon=request.form.get('icon'), order=int(request.form.get('order') or 0),
                     is_active=bool(request.form.get('is_active')))
        path = save_upload(request.files.get('image'))
        if path:
            f.image = path
        db.session.add(f)
        db.session.commit()
        flash('Facility added.', 'success')
        return redirect(url_for('admin.facilities'))
    return render_template('admin/facility_form.html', item=None)

@admin_bp.route('/facilities/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def facility_edit(id):
    item = Facility.query.get_or_404(id)
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.description = request.form.get('description')
        item.icon = request.form.get('icon')
        item.order = int(request.form.get('order') or 0)
        item.is_active = bool(request.form.get('is_active'))
        path = save_upload(request.files.get('image'))
        if path:
            item.image = path
        db.session.commit()
        flash('Facility updated.', 'success')
        return redirect(url_for('admin.facilities'))
    return render_template('admin/facility_form.html', item=item)

# --- Applications (view + EDIT) ---
@admin_bp.route('/applications')
@login_required
@admin_required
def applications():
    status = request.args.get('status')
    query = AdmissionApplication.query
    if status:
        query = query.filter_by(status=status)
    items = query.order_by(AdmissionApplication.created_at.desc()).all()
    return render_template('admin/applications.html', items=items, current_status=status)

@admin_bp.route('/applications/<int:id>', methods=['GET', 'POST'])
@admin_bp.route('/applications/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def application_detail(id):
    item = AdmissionApplication.query.get_or_404(id)
    if request.method == 'POST':
        try:
            item.student_name = (request.form.get('student_name') or item.student_name or '').strip()
            item.parent_name = request.form.get('parent_name')
            item.phone = request.form.get('phone')
            item.email = request.form.get('email')
            item.address = request.form.get('address')
            item.previous_school = request.form.get('previous_school')
            item.applying_for = request.form.get('applying_for')
            item.grade_program = request.form.get('grade_program')
            item.academic_info = request.form.get('academic_info')
            item.message = request.form.get('message')
            item.gender = request.form.get('gender')
            item.status = request.form.get('status') or item.status
            item.admin_notes = request.form.get('admin_notes')
            dob = request.form.get('date_of_birth')
            if dob:
                try:
                    item.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
                except ValueError:
                    pass
            if request.files.get('photo') and request.files['photo'].filename:
                path = save_upload(request.files['photo'])
                if path:
                    item.photo = path
            if request.files.get('documents') and request.files['documents'].filename:
                path2 = save_upload(request.files['documents'])
                if path2:
                    item.documents = path2
            db.session.add(item)
            db.session.commit()
            flash('Application updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Update failed: {e}', 'error')
        return redirect(url_for('admin.application_detail', id=id))
    return render_template('admin/application_detail.html', item=item)

@admin_bp.route('/applications/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def application_delete(id):
    item = AdmissionApplication.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Application deleted.', 'success')
    return redirect(url_for('admin.applications'))

# --- Messages ---
@admin_bp.route('/messages')
@login_required
@admin_required
def messages():
    items = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages.html', items=items)

@admin_bp.route('/messages/<int:id>/read', methods=['POST'])
@login_required
@admin_required
def message_read(id):
    item = ContactMessage.query.get_or_404(id)
    item.is_read = True
    db.session.commit()
    return redirect(url_for('admin.messages'))

# --- Contact Info ---
@admin_bp.route('/contact-info', methods=['GET', 'POST'])
@login_required
@admin_required
def contact_info():
    info = ContactInfo.query.first() or ContactInfo()
    if not ContactInfo.query.first():
        db.session.add(info)
        db.session.commit()
    if request.method == 'POST':
        info.address = request.form.get('address')
        info.phone = request.form.get('phone')
        info.email = request.form.get('email')
        info.website = request.form.get('website')
        info.facebook = request.form.get('facebook')
        info.instagram = request.form.get('instagram')
        info.youtube = request.form.get('youtube')
        info.map_embed = request.form.get('map_embed')
        db.session.commit()
        flash('Contact info updated.', 'success')
        return redirect(url_for('admin.contact_info'))
    return render_template('admin/contact_info.html', info=info)

# --- Faculty (with DELETE) ---
@admin_bp.route('/faculty')
@login_required
@admin_required
def faculty():
    items = Faculty.query.order_by(Faculty.order).all()
    return render_template('admin/faculty.html', items=items)

@admin_bp.route('/faculty/add', methods=['GET', 'POST'])
@login_required
@admin_required
def faculty_add():
    if request.method == 'POST':
        f = Faculty(name=request.form.get('name'), designation=request.form.get('designation'),
                    department=request.form.get('department'), bio=request.form.get('bio'),
                    order=int(request.form.get('order') or 0), is_active=bool(request.form.get('is_active')))
        path = save_upload(request.files.get('photo'))
        if path:
            f.photo = path
        db.session.add(f)
        db.session.commit()
        flash('Faculty added.', 'success')
        return redirect(url_for('admin.faculty'))
    return render_template('admin/faculty_form.html', item=None)

@admin_bp.route('/faculty/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def faculty_edit(id):
    item = Faculty.query.get_or_404(id)
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.designation = request.form.get('designation')
        item.department = request.form.get('department')
        item.bio = request.form.get('bio')
        item.order = int(request.form.get('order') or 0)
        item.is_active = bool(request.form.get('is_active'))
        path = save_upload(request.files.get('photo'))
        if path:
            item.photo = path
        db.session.commit()
        flash('Faculty updated.', 'success')
        return redirect(url_for('admin.faculty'))
    return render_template('admin/faculty_form.html', item=item)

@admin_bp.route('/faculty/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def faculty_delete(id):
    item = Faculty.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Faculty member deleted.', 'success')
    return redirect(url_for('admin.faculty'))

# --- STUDENTS (admin registered only can login) ---
@admin_bp.route('/students')
@login_required
@admin_required
def students():
    items = Student.query.order_by(Student.created_at.desc()).all()
    return render_template('admin/students.html', items=items)

@admin_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
@admin_required
def student_add():
    if request.method == 'POST':
        s = Student(
            student_id=request.form.get('student_id') or None,
            name=request.form.get('name'),
            class_grade=request.form.get('class_grade'),
            section=request.form.get('section'),
            parent_name=request.form.get('parent_name'),
            parent_phone=request.form.get('parent_phone'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            gender=request.form.get('gender'),
            is_active=bool(request.form.get('is_active'))
        )
        if request.form.get('date_of_birth'):
            try:
                s.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            except ValueError:
                pass
        pwd = request.form.get('password')
        if pwd:
            s.set_password(pwd)
        path = save_upload(request.files.get('photo'))
        if path:
            s.photo = path
        path2 = save_upload(request.files.get('documents'))
        if path2:
            s.documents = path2
        db.session.add(s)
        db.session.commit()
        flash('Student added. They can now login with Student ID/Email and password.', 'success')
        return redirect(url_for('admin.students'))
    return render_template('admin/student_form.html', item=None)

@admin_bp.route('/students/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def student_edit(id):
    item = Student.query.get_or_404(id)
    if request.method == 'POST':
        item.student_id = request.form.get('student_id') or item.student_id
        item.name = request.form.get('name')
        item.class_grade = request.form.get('class_grade')
        item.section = request.form.get('section')
        item.parent_name = request.form.get('parent_name')
        item.parent_phone = request.form.get('parent_phone')
        item.phone = request.form.get('phone')
        item.email = request.form.get('email')
        item.address = request.form.get('address')
        item.gender = request.form.get('gender')
        item.is_active = bool(request.form.get('is_active'))
        if request.form.get('date_of_birth'):
            try:
                item.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            except ValueError:
                pass
        pwd = request.form.get('password')
        if pwd:
            item.set_password(pwd)
        path = save_upload(request.files.get('photo'))
        if path:
            item.photo = path
        path2 = save_upload(request.files.get('documents'))
        if path2:
            item.documents = path2
        db.session.commit()
        flash('Student updated.', 'success')
        return redirect(url_for('admin.students'))
    return render_template('admin/student_form.html', item=item)

@admin_bp.route('/students/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def student_delete(id):
    item = Student.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Student deleted.', 'success')
    return redirect(url_for('admin.students'))

# --- TEACHERS ---
@admin_bp.route('/teachers')
@login_required
@admin_required
def teachers():
    items = Teacher.query.order_by(Teacher.order).all()
    return render_template('admin/teachers.html', items=items)

@admin_bp.route('/teachers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def teacher_add():
    if request.method == 'POST':
        t = Teacher(
            teacher_id=request.form.get('teacher_id') or None,
            name=request.form.get('name'),
            designation=request.form.get('designation'),
            department=request.form.get('department'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            bio=request.form.get('bio'),
            order=int(request.form.get('order') or 0),
            is_active=bool(request.form.get('is_active'))
        )
        pwd = request.form.get('password')
        if pwd:
            t.set_password(pwd)
        path = save_upload(request.files.get('photo'))
        if path:
            t.photo = path
        path2 = save_upload(request.files.get('documents'))
        if path2:
            t.documents = path2
        db.session.add(t)
        db.session.commit()
        flash('Teacher added. They can login with Teacher ID/Email and password.', 'success')
        return redirect(url_for('admin.teachers'))
    return render_template('admin/teacher_form.html', item=None)

@admin_bp.route('/teachers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def teacher_edit(id):
    item = Teacher.query.get_or_404(id)
    if request.method == 'POST':
        item.teacher_id = request.form.get('teacher_id') or item.teacher_id
        item.name = request.form.get('name')
        item.designation = request.form.get('designation')
        item.department = request.form.get('department')
        item.phone = request.form.get('phone')
        item.email = request.form.get('email')
        item.bio = request.form.get('bio')
        item.order = int(request.form.get('order') or 0)
        item.is_active = bool(request.form.get('is_active'))
        pwd = request.form.get('password')
        if pwd:
            item.set_password(pwd)
        path = save_upload(request.files.get('photo'))
        if path:
            item.photo = path
        path2 = save_upload(request.files.get('documents'))
        if path2:
            item.documents = path2
        db.session.commit()
        flash('Teacher updated.', 'success')
        return redirect(url_for('admin.teachers'))
    return render_template('admin/teacher_form.html', item=item)

@admin_bp.route('/teachers/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def teacher_delete(id):
    item = Teacher.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Teacher deleted.', 'success')
    return redirect(url_for('admin.teachers'))

# --- Newsletter subscribers ---
@admin_bp.route('/subscribers')
@login_required
@admin_required
def subscribers():
    items = NewsletterSubscriber.query.order_by(NewsletterSubscriber.subscribed_at.desc()).all()
    return render_template('admin/subscribers.html', items=items)


# --- SMTP / Email Settings (from admin) ---
@admin_bp.route('/smtp-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def smtp_settings():
    keys = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USE_TLS', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
    settings = {}
    for k in keys:
        row = SiteSetting.query.filter_by(key=k).first()
        settings[k] = row.value if row else (current_app.config.get(k) or '')
    if request.method == 'POST':
        for k in keys:
            val = request.form.get(k, '')
            row = SiteSetting.query.filter_by(key=k).first()
            if not row:
                row = SiteSetting(key=k, value=val)
                db.session.add(row)
            else:
                row.value = val
            # Apply live to app config (password only if provided)
            if k == 'MAIL_PASSWORD' and not val:
                continue
            if k == 'MAIL_PORT':
                try:
                    current_app.config[k] = int(val or 587)
                except ValueError:
                    current_app.config[k] = 587
            elif k == 'MAIL_USE_TLS':
                current_app.config[k] = val in ('1', 'true', 'True', 'yes', 'on')
            else:
                current_app.config[k] = val
        db.session.commit()
        flash('SMTP settings saved. Emails will use these credentials.', 'success')
        return redirect(url_for('admin.smtp_settings'))
    return render_template('admin/smtp_settings.html', settings=settings)

# --- Announcements (running / floating text) ---
@admin_bp.route('/announcements')
@login_required
@admin_required
def announcements():
    items = Announcement.query.order_by(Announcement.order).all()
    return render_template('admin/announcements.html', items=items)

@admin_bp.route('/announcements/add', methods=['GET', 'POST'])
@login_required
@admin_required
def announcement_add():
    if request.method == 'POST':
        a = Announcement(
            text=request.form.get('text'),
            link=request.form.get('link'),
            style=request.form.get('style') or 'marquee',
            order=int(request.form.get('order') or 0),
            is_active=bool(request.form.get('is_active'))
        )
        db.session.add(a)
        db.session.commit()
        flash('Announcement added.', 'success')
        return redirect(url_for('admin.announcements'))
    return render_template('admin/announcement_form.html', item=None)

@admin_bp.route('/announcements/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def announcement_edit(id):
    item = Announcement.query.get_or_404(id)
    if request.method == 'POST':
        item.text = request.form.get('text')
        item.link = request.form.get('link')
        item.style = request.form.get('style') or 'marquee'
        item.order = int(request.form.get('order') or 0)
        item.is_active = bool(request.form.get('is_active'))
        db.session.commit()
        flash('Announcement updated.', 'success')
        return redirect(url_for('admin.announcements'))
    return render_template('admin/announcement_form.html', item=item)

@admin_bp.route('/announcements/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def announcement_delete(id):
    item = Announcement.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Deleted.', 'success')
    return redirect(url_for('admin.announcements'))

# --- Page Embeds (HTML + multi images) ---
@admin_bp.route('/embeds')
@login_required
@admin_required
def embeds():
    items = PageEmbed.query.order_by(PageEmbed.page, PageEmbed.order).all()
    return render_template('admin/embeds.html', items=items)

@admin_bp.route('/embeds/add', methods=['GET', 'POST'])
@login_required
@admin_required
def embed_add():
    if request.method == 'POST':
        import json
        imgs = []
        files = request.files.getlist('images')
        for f in files:
            if f and f.filename:
                path = save_upload(f)
                if path:
                    imgs.append(path)
        e = PageEmbed(
            page=request.form.get('page') or 'home',
            title=request.form.get('title'),
            embed_html=request.form.get('embed_html'),
            images=json.dumps(imgs) if imgs else None,
            order=int(request.form.get('order') or 0),
            is_active=bool(request.form.get('is_active'))
        )
        db.session.add(e)
        db.session.commit()
        flash('Embed / images block added.', 'success')
        return redirect(url_for('admin.embeds'))
    return render_template('admin/embed_form.html', item=None)

@admin_bp.route('/embeds/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def embed_edit(id):
    import json
    item = PageEmbed.query.get_or_404(id)
    if request.method == 'POST':
        item.page = request.form.get('page') or item.page
        item.title = request.form.get('title')
        item.embed_html = request.form.get('embed_html')
        item.order = int(request.form.get('order') or 0)
        item.is_active = bool(request.form.get('is_active'))
        files = request.files.getlist('images')
        existing = json.loads(item.images) if item.images else []
        for f in files:
            if f and f.filename:
                path = save_upload(f)
                if path:
                    existing.append(path)
        item.images = json.dumps(existing) if existing else item.images
        db.session.commit()
        flash('Updated.', 'success')
        return redirect(url_for('admin.embeds'))
    return render_template('admin/embed_form.html', item=item)

@admin_bp.route('/embeds/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def embed_delete(id):
    item = PageEmbed.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Deleted.', 'success')
    return redirect(url_for('admin.embeds'))


# --- PARENTS ---
@admin_bp.route('/parents')
@login_required
@admin_required
def parents():
    from app.models import Parent
    items = Parent.query.order_by(Parent.created_at.desc()).all()
    return render_template('admin/parents.html', items=items)

@admin_bp.route('/parents/add', methods=['GET', 'POST'])
@login_required
@admin_required
def parent_add():
    from app.models import Parent
    if request.method == 'POST':
        p = Parent(
            parent_id=request.form.get('parent_id') or None,
            name=request.form.get('name'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            student_name=request.form.get('student_name'),
            student_class=request.form.get('student_class'),
            is_active=bool(request.form.get('is_active'))
        )
        pwd = request.form.get('password')
        if pwd:
            p.set_password(pwd)
        db.session.add(p)
        db.session.commit()
        flash('Parent added. They can login with ID/Phone/Email and password.', 'success')
        return redirect(url_for('admin.parents'))
    return render_template('admin/parent_form.html', item=None)

@admin_bp.route('/parents/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def parent_edit(id):
    from app.models import Parent
    item = Parent.query.get_or_404(id)
    if request.method == 'POST':
        item.parent_id = request.form.get('parent_id') or item.parent_id
        item.name = request.form.get('name')
        item.phone = request.form.get('phone')
        item.email = request.form.get('email')
        item.student_name = request.form.get('student_name')
        item.student_class = request.form.get('student_class')
        item.is_active = bool(request.form.get('is_active'))
        pwd = request.form.get('password')
        if pwd:
            item.set_password(pwd)
        db.session.commit()
        flash('Parent updated.', 'success')
        return redirect(url_for('admin.parents'))
    return render_template('admin/parent_form.html', item=item)

@admin_bp.route('/parents/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def parent_delete(id):
    from app.models import Parent
    item = Parent.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Parent deleted.', 'success')
    return redirect(url_for('admin.parents'))
