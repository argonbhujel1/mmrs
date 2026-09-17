from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify, send_from_directory
from app.models import (
    db, Hero, About, PrincipalMessage, Program, Notice, Event,
    GalleryImage, Facility, ContactInfo, ContactMessage, NewsletterSubscriber,
    Announcement, PageEmbed
)
from app.mail_utils import send_welcome_subscriber
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    hero = Hero.query.filter_by(is_active=True).first()
    about = About.query.first()
    principal = PrincipalMessage.query.first()
    programs = Program.query.filter_by(is_active=True).order_by(Program.order).limit(8).all()
    notices = Notice.query.filter_by(is_published=True).order_by(Notice.date.desc()).limit(5).all()
    events = Event.query.filter_by(is_published=True).order_by(Event.event_date.desc()).limit(4).all()
    gallery = GalleryImage.query.filter_by(is_active=True).order_by(GalleryImage.created_at.desc()).limit(8).all()
    facilities = Facility.query.filter_by(is_active=True).order_by(Facility.order).all()
    contact = ContactInfo.query.first()
    announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.order).all()
    embeds = PageEmbed.query.filter_by(page='home', is_active=True).order_by(PageEmbed.order).all()
    return render_template('home.html',
        hero=hero, about=about, principal=principal,
        programs=programs, notices=notices, events=events,
        gallery=gallery, facilities=facilities, contact=contact,
        announcements=announcements, embeds=embeds
    )

@main_bp.route('/about')
def about():
    about = About.query.first()
    principal = PrincipalMessage.query.first()
    contact = ContactInfo.query.first()
    return render_template('about.html', about=about, principal=principal, contact=contact)

@main_bp.route('/academics')
def academics():
    """Academics page – overview of academic system, levels, approach (different from Programs)"""
    about = About.query.first()
    contact = ContactInfo.query.first()
    school_programs = Program.query.filter_by(is_active=True, category='school').order_by(Program.order).all()
    return render_template('academics.html', about=about, contact=contact, school_programs=school_programs)

@main_bp.route('/programs')
def programs():
    """Programs page – specific courses: +2 Science, +2 Management, BBS etc."""
    all_programs = Program.query.filter_by(is_active=True).order_by(Program.order).all()
    plus2 = [p for p in all_programs if p.category == 'plus2']
    college = [p for p in all_programs if p.category == 'college']
    school = [p for p in all_programs if p.category == 'school']
    contact = ContactInfo.query.first()
    return render_template('programs.html', programs=all_programs, plus2=plus2, college=college, school=school, contact=contact)

@main_bp.route('/programs/<slug>')
def program_detail(slug):
    program = Program.query.filter_by(slug=slug, is_active=True).first_or_404()
    contact = ContactInfo.query.first()
    return render_template('program_detail.html', program=program, contact=contact)

@main_bp.route('/faculty')
def faculty():
    from app.models import Faculty, Teacher
    faculty_list = Faculty.query.filter_by(is_active=True).order_by(Faculty.order).all()
    # Also show active teachers if faculty empty
    if not faculty_list:
        faculty_list = Teacher.query.filter_by(is_active=True).order_by(Teacher.order).all()
    contact = ContactInfo.query.first()
    return render_template('faculty.html', faculty_list=faculty_list, contact=contact)

@main_bp.route('/notices')
def notices():
    category = request.args.get('category')
    query = Notice.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)
    notices = query.order_by(Notice.date.desc()).all()
    contact = ContactInfo.query.first()
    return render_template('notices.html', notices=notices, contact=contact, current_category=category)

@main_bp.route('/notices/<slug>')
def notice_detail(slug):
    notice = Notice.query.filter_by(slug=slug, is_published=True).first_or_404()
    contact = ContactInfo.query.first()
    return render_template('notice_detail.html', notice=notice, contact=contact)

@main_bp.route('/events')
def events():
    events = Event.query.filter_by(is_published=True).order_by(Event.event_date.desc()).all()
    contact = ContactInfo.query.first()
    return render_template('events.html', events=events, contact=contact)

@main_bp.route('/gallery')
def gallery():
    category = request.args.get('category')
    query = GalleryImage.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)
    images = query.order_by(GalleryImage.created_at.desc()).all()
    categories = db.session.query(GalleryImage.category).distinct().all()
    contact = ContactInfo.query.first()
    return render_template('gallery.html', images=images, categories=[c[0] for c in categories if c[0]], contact=contact, current_category=category)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    contact_info = ContactInfo.query.first()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        if name and email and message:
            msg = ContactMessage(name=name, email=email, phone=phone, subject=subject, message=message)
            db.session.add(msg)
            db.session.commit()
            flash('Thank you! Your message has been sent successfully.', 'success')
            return redirect(url_for('main.contact'))
        flash('Please fill in all required fields.', 'error')
    return render_template('contact.html', contact=contact_info)

@main_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """Newsletter subscribe – called from popup on any page"""
    email = request.form.get('email', '').strip().lower()
    if not email or '@' not in email:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'ok': False, 'message': 'Please enter a valid email.'}), 400
        flash('Please enter a valid email.', 'error')
        return redirect(request.referrer or url_for('main.home'))
    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'ok': True, 'message': 'You are already subscribed. Thank you!'})
        flash('You are already subscribed. Thank you!', 'success')
        return redirect(request.referrer or url_for('main.home'))
    sub = NewsletterSubscriber(email=email)
    db.session.add(sub)
    db.session.commit()
    send_welcome_subscriber(email)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': True, 'message': 'Thank you for subscribing! A confirmation email has been sent.'})
    flash('Thank you for subscribing! A confirmation email has been sent.', 'success')
    return redirect(request.referrer or url_for('main.home'))

@main_bp.route('/robots.txt')
def robots():
    return current_app.send_static_file('robots.txt')

@main_bp.route('/sitemap.xml')
def sitemap():
    return render_template('sitemap.xml'), 200, {'Content-Type': 'application/xml'}


@main_bp.route('/view-file/<path:path>')
def view_file(path):
    """Serve uploaded files inline from UPLOAD_FOLDER (works with /tmp on Vercel)."""
    import os
    directory = current_app.config['UPLOAD_FOLDER']
    # Accept "uploads/filename" or bare filename
    if path.startswith('uploads/'):
        path = path[len('uploads/'):]
    path = os.path.basename(path)  # prevent path traversal
    full = os.path.join(directory, path)
    if not os.path.isfile(full):
        # Try under static/uploads for local legacy paths
        alt = os.path.join(current_app.root_path, 'static', 'uploads', path)
        if os.path.isfile(alt):
            return send_from_directory(os.path.dirname(alt), path, as_attachment=False)
        flash('File not found.', 'error')
        return redirect(url_for('main.home'))
    return send_from_directory(directory, path, as_attachment=False)
