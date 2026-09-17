from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from app.models import db, AdmissionApplication, ContactInfo, Program
from werkzeug.utils import secure_filename
import os
from datetime import datetime

admission_bp = Blueprint('admission', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@admission_bp.route('/admission', methods=['GET', 'POST'])
def admission():
    contact = ContactInfo.query.first()
    programs = Program.query.filter_by(is_active=True).order_by(Program.order).all()
    
    if request.method == 'POST':
        student_name = request.form.get('student_name', '').strip()
        parent_name = request.form.get('parent_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        
        if not student_name or not parent_name or not phone:
            flash('Please fill in all required fields (Student Name, Parent/Guardian Name, Phone).', 'error')
            return render_template('admission.html', contact=contact, programs=programs)
        
        app = AdmissionApplication(
            student_name=student_name,
            date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None,
            gender=request.form.get('gender'),
            parent_name=parent_name,
            phone=phone,
            email=email,
            address=request.form.get('address'),
            previous_school=request.form.get('previous_school'),
            applying_for=request.form.get('applying_for'),
            grade_program=request.form.get('grade_program'),
            academic_info=request.form.get('academic_info'),
            message=request.form.get('message'),
            status='Pending'
        )
        
        # Photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                app.photo = f'uploads/{filename}'
        
        # Documents
        if 'documents' in request.files:
            file = request.files['documents']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                app.documents = f'uploads/{filename}'
        
        db.session.add(app)
        db.session.commit()
        flash('Your admission application has been submitted successfully! We will contact you soon.', 'success')
        return redirect(url_for('admission.admission'))
    
    return render_template('admission.html', contact=contact, programs=programs)
