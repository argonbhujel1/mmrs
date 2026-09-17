import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from app.models import db, User, Student, Teacher, Parent

login_manager = LoginManager()
login_manager.login_view = 'auth.login_choice'
login_manager.login_message_category = 'info'
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Writable uploads: local path or /tmp on Vercel (read-only elsewhere)
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        # Fallback if filesystem is read-only
        app.config['UPLOAD_FOLDER'] = '/tmp/morang_uploads'
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        except OSError:
            pass

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        if not user_id:
            return None
        uid = str(user_id)
        if uid.startswith('student_'):
            return Student.query.get(int(uid.replace('student_', '')))
        if uid.startswith('teacher_'):
            return Teacher.query.get(int(uid.replace('teacher_', '')))
        if uid.startswith('parent_'):
            return Parent.query.get(int(uid.replace('parent_', '')))
        try:
            return User.query.get(int(uid))
        except (ValueError, TypeError):
            return None

    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.admission import admission_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(admission_bp)
    app.register_blueprint(auth_bp)

    with app.app_context():
        try:
            db.create_all()
            seed_data()
        except Exception as e:
            app.logger.warning('DB init/seed skipped: %s', e)


    @app.context_processor
    def inject_globals():
        from app.models import Announcement, ContactInfo
        try:
            anns = Announcement.query.filter_by(is_active=True).order_by(Announcement.order).all()
        except Exception:
            anns = []
        try:
            contact = ContactInfo.query.first()
        except Exception:
            contact = None
        return dict(announcements=anns, contact=contact)

    return app


def seed_data():
    from app.models import (
        User, Hero, About, PrincipalMessage, Program, Notice,
        Facility, ContactInfo
    )
    from config import Config

    # Always sync admin credentials from environment (Vercel env vars)
    admin_user = Config.ADMIN_USERNAME or 'admin'
    admin_pass = Config.ADMIN_PASSWORD or 'admin123'
    admin = User.query.filter_by(username=admin_user).first()
    if not admin:
        # Also try legacy username "admin" if env username differs
        admin = User.query.filter_by(role='admin').first()
        if admin:
            admin.username = admin_user
            admin.set_password(admin_pass)
        else:
            admin = User(username=admin_user, email='admin@morangmodel.com', role='admin')
            admin.set_password(admin_pass)
            db.session.add(admin)
    else:
        # Update password every boot from env so Vercel env changes take effect
        admin.set_password(admin_pass)
        admin.role = 'admin'


    if not Hero.query.first():
        db.session.add(Hero())

    if not About.query.first():
        db.session.add(About(
            content='''Morang Model Residential Secondary School is a private educational institution in Urlabari, Morang, committed to providing quality, practical, disciplined and value-based education while supporting students' academic and personal development.

The institution has been serving students since 2037 B.S. and provides education from early grades through Grade 12, including +2 programs in Science and Management. The college wing offers Tribhuvan University affiliated Bachelor of Business Studies (BBS) program.'''
        ))

    if not PrincipalMessage.query.first():
        db.session.add(PrincipalMessage(
            message='''Welcome to Morang Model College & School. Our institution is dedicated to nurturing young minds with a balanced approach that values academic excellence, character building and holistic development.

We believe every student has unique potential. Through experienced faculty, modern facilities and a supportive community, we strive to prepare our students not only for examinations but for life.

We invite parents and guardians to partner with us in shaping a brighter future for our children.'''
        ))

    if not ContactInfo.query.first():
        db.session.add(ContactInfo(
            facebook='https://www.facebook.com/morangmodelcollege',
            map_embed='https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3560.5!2d87.6!3d26.65!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjbCsDM5JzAwLjAiTiA4N8KwMzYnMDAuMCJF!5e0!3m2!1sen!2snp!4v1'
        ))

    if Program.query.count() == 0:
        programs = [
            Program(name='Early Childhood / Nursery', slug='early-childhood', category='school', level='Nursery', description='Foundational years focused on play-based learning, social skills and early literacy.', order=1),
            Program(name='Primary Level', slug='primary', category='school', level='Grade 1-5', description='Strong fundamentals in language, mathematics, science and values education.', order=2),
            Program(name='Lower Secondary', slug='lower-secondary', category='school', level='Grade 6-8', description='Building critical thinking, curiosity and confidence for secondary education.', order=3),
            Program(name='Secondary Level', slug='secondary', category='school', level='Grade 9-10', description='SEE preparation with balanced academic and co-curricular focus.', order=4),
            Program(name='+2 Science', slug='plus2-science', category='plus2', level='Grade 11-12', description='NEB affiliated Science stream preparing students for medical, engineering and science careers.', order=5),
            Program(name='+2 Management', slug='plus2-management', category='plus2', level='Grade 11-12', description='NEB affiliated Management stream focusing on business, accounting and entrepreneurship.', order=6),
            Program(name='Bachelor of Business Studies (BBS)', slug='bbs', category='college', level='Undergraduate', description='Tribhuvan University affiliated four-year program with practical training, internships and career support.', order=7),
        ]
        for p in programs:
            db.session.add(p)

    if Facility.query.count() == 0:
        for name, desc, icon, order in [
            ('Computer Lab', 'Modern computer lab with internet access for digital literacy.', 'computer', 1),
            ('Science Lab', 'Well-equipped science laboratory for practical experiments.', 'flask', 2),
            ('Library', 'Resource-rich library with textbooks and quiet study spaces.', 'book', 3),
            ('Classrooms', 'Spacious, well-ventilated classrooms for interactive learning.', 'chalkboard', 4),
            ('Multimedia Learning', 'Multimedia rooms and digital tools for engagement.', 'projector', 5),
            ('Sports', 'Playgrounds and sports facilities for fitness and teamwork.', 'trophy', 6),
            ('Cafeteria', 'Hygienic cafeteria providing nutritious meals.', 'utensils', 7),
            ('Transportation', 'Safe and reliable transport for students.', 'bus', 8),
            ('Conference Hall', 'Hall for assemblies, seminars and cultural programs.', 'users', 9),
            ('Counselling', 'Student counselling and guidance support.', 'heart', 10),
            ('ECA & Clubs', 'Extra-curricular activities and leadership opportunities.', 'star', 11),
        ]:
            db.session.add(Facility(name=name, description=desc, icon=icon, order=order))

    if Notice.query.count() == 0:
        from datetime import date
        for title, slug, cat, content, d in [
            ('Admission Open for Academic Year 2083', 'admission-open-2083', 'Admission', 'Admissions are now open for Nursery to Grade 12 and +2 programs. Apply online or visit the campus.', date(2026, 3, 1)),
            ('SEE Examination Routine 2082', 'see-routine-2082', 'Exam', 'The SEE examination routine has been published. Collect the schedule from the school office.', date(2026, 2, 15)),
            ('Winter Holiday Notice', 'winter-holiday', 'Holiday', 'The school will remain closed for winter holidays. Classes will resume as per the academic calendar.', date(2026, 1, 10)),
            ('Parents Meeting – Grade 11 & 12', 'parents-meeting-plus2', 'Events', 'A parents meeting for +2 students will be held to discuss academic progress.', date(2026, 2, 20)),
        ]:
            db.session.add(Notice(title=title, slug=slug, category=cat, content=content, date=d))


    # Default running / floating announcements
    try:
        from app.models import Announcement
        if Announcement.query.count() == 0:
            db.session.add(Announcement(
                text='Admission Open for Academic Year 2083 — Apply Online or Visit Campus | Morang Model College & School, Urlabari',
                link='/admission', style='marquee', order=1, is_active=True
            ))
            db.session.add(Announcement(
                text='New admissions open! Contact +977-21-542730',
                link='/admission', style='floating', order=2, is_active=True
            ))
    except Exception as e:
        print('Announcement seed skip', e)

    db.session.commit()
