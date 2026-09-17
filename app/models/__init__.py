from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Admin users only"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(UserMixin, db.Model):
    """Students registered by admin - can login as student"""
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True)  # roll / registration no
    name = db.Column(db.String(150), nullable=False)
    class_grade = db.Column(db.String(50))  # e.g. Grade 10, +2 Science
    section = db.Column(db.String(20))
    parent_name = db.Column(db.String(150))
    parent_phone = db.Column(db.String(30), nullable=False)  # used for profile lookup
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    photo = db.Column(db.String(255))
    documents = db.Column(db.String(255))  # any file format path
    password_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"student_{self.id}"


class Teacher(UserMixin, db.Model):
    """Teachers registered by admin - can login as teacher"""
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(150), nullable=False)
    designation = db.Column(db.String(100))
    department = db.Column(db.String(100))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    photo = db.Column(db.String(255))
    documents = db.Column(db.String(255))  # any file format
    bio = db.Column(db.Text)
    password_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"teacher_{self.id}"


class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Hero(db.Model):
    __tablename__ = 'hero'
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), default='LEARN  •  GROW  •  ACHIEVE')
    title = db.Column(db.String(200), default='Welcome to\nMorang Model\nCollege & School')
    subtitle = db.Column(db.Text, default='Quality education, strong values and a brighter future for every student.')
    image = db.Column(db.String(255))
    cta_primary = db.Column(db.String(100), default='Explore Our Programs')
    cta_primary_link = db.Column(db.String(200), default='/programs')
    cta_secondary = db.Column(db.String(100), default='Apply Online')
    cta_secondary_link = db.Column(db.String(200), default='/admission')
    is_active = db.Column(db.Boolean, default=True)


class About(db.Model):
    __tablename__ = 'about'
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), default='ABOUT US')
    title = db.Column(db.String(200), default='Shaping Young Minds for a Better Tomorrow')
    content = db.Column(db.Text)
    image = db.Column(db.String(255))
    established = db.Column(db.String(50), default='2037 B.S.')
    academic_level = db.Column(db.String(100), default='Nursery – Grade 12')
    programs_plus2 = db.Column(db.String(100), default='Science & Management')
    affiliation = db.Column(db.String(150), default='NEB / Higher Education: TU-linked BBS program')


class PrincipalMessage(db.Model):
    __tablename__ = 'principal_message'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='Principal')
    designation = db.Column(db.String(100), default='Principal')
    photo = db.Column(db.String(255))
    message = db.Column(db.Text)
    title = db.Column(db.String(200), default='Building Knowledge, Character & Confidence')


class Program(db.Model):
    __tablename__ = 'programs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True)
    category = db.Column(db.String(50))  # school, plus2, college
    level = db.Column(db.String(100))
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Faculty(db.Model):
    """Public-facing faculty list (can sync from Teacher)"""
    __tablename__ = 'faculty'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100))
    department = db.Column(db.String(100))
    photo = db.Column(db.String(255))
    bio = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class Notice(db.Model):
    __tablename__ = 'notices'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True)
    category = db.Column(db.String(50))
    content = db.Column(db.Text)
    attachment = db.Column(db.String(255))  # any file type
    attachment_name = db.Column(db.String(255))
    date = db.Column(db.Date, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    event_date = db.Column(db.Date)
    location = db.Column(db.String(150))
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class GalleryImage(db.Model):
    __tablename__ = 'gallery'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    category = db.Column(db.String(50))
    image = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Facility(db.Model):
    __tablename__ = 'facilities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    icon = db.Column(db.String(50))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class AdmissionApplication(db.Model):
    __tablename__ = 'admission_applications'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(150), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    parent_name = db.Column(db.String(150))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    previous_school = db.Column(db.String(200))
    applying_for = db.Column(db.String(100))
    grade_program = db.Column(db.String(100))
    academic_info = db.Column(db.Text)
    message = db.Column(db.Text)
    photo = db.Column(db.String(255))
    documents = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Pending')
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContactInfo(db.Model):
    __tablename__ = 'contact_info'
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255), default='Urlabari, Morang, Koshi Province, Nepal')
    phone = db.Column(db.String(50), default='+977-21-542730')
    email = db.Column(db.String(120), default='morangmodel2037@gmail.com')
    website = db.Column(db.String(100), default='morangmodel.com')
    facebook = db.Column(db.String(200))
    instagram = db.Column(db.String(200))
    youtube = db.Column(db.String(200))
    map_embed = db.Column(db.Text)


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)


class Announcement(db.Model):
    """Floating / running marquee text on public site"""
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    style = db.Column(db.String(30), default='marquee')  # marquee, floating
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PageEmbed(db.Model):
    """HTML embeds and multi-image blocks for pages"""
    __tablename__ = 'page_embeds'
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(50), default='home')  # home, about, gallery, etc.
    title = db.Column(db.String(150))
    embed_html = db.Column(db.Text)  # YouTube, map, iframe, raw HTML
    images = db.Column(db.Text)  # JSON list of image paths
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Parent(UserMixin, db.Model):
    """Parents registered by admin - can login as parent"""
    __tablename__ = 'parents'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120))
    student_name = db.Column(db.String(150))  # linked child name
    student_class = db.Column(db.String(50))
    student_id_ref = db.Column(db.Integer)  # optional FK to students.id
    password_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"parent_{self.id}"


class Homework(db.Model):
    """Homework sent by teachers with optional attachment"""
    __tablename__ = 'homework'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer)
    teacher_name = db.Column(db.String(150))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    class_grade = db.Column(db.String(50))  # target class
    attachment = db.Column(db.String(255))
    attachment_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
