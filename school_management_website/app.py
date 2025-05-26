from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from forms import EventForm
from forms import ProgramForm
from flask_mail import Mail, Message
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cocoon.db'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vanduvarsh103@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'muaa jgxf xszc flaq'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'vanduvarsh103@gmail.com'

mail = Mail(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    age_group = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Program {self.title}>"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    image = db.Column(db.String(255), nullable=False)

class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # Make sure filename is always provided
    caption = db.Column(db.String(255), nullable=True)    # Caption is optional
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)  # Automatically set the upload time
    category = db.Column(db.String(50), nullable=True)    # Category is optional
    order = db.Column(db.Integer, default=0)              # Default order is 0 if not provided

    def __repr__(self):
        return f"<GalleryImage {self.filename}>"


class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, default=0)

class Admission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_name = db.Column(db.String(100), nullable=False)
    parent_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer) 
    address = db.Column(db.Text, nullable=False)
    program = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Public Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    team_members = TeamMember.query.order_by(TeamMember.order).all()
    return render_template('about.html', team_members=team_members)

@app.route('/programs')
def programs():
    # Fetch programs from the database and order by title (or any other column)
    programs = Program.query.order_by(Program.title).all()  # Order by title
    return render_template('programs.html', programs=programs)

@app.route('/gallery')
def gallery():
    images = GalleryImage.query.all()  # Fetch all images
    for image in images:
        # Print the URL to the console for debugging
        print(f"Image Path: {url_for('static', filename='uploads/' + image.filename)}")
    return render_template('gallery.html', images=images)


@app.route('/events')
def events():
    events = Event.query.filter(Event.date >= date.today()).order_by(Event.date).all()
    calendar = Event.query.order_by(Event.date).all()
    return render_template('events.html', events=events, calendar=calendar)

# Route to display the admission form
@app.route('/admissions', methods=['GET'])
def admissions_form():
    return render_template('admissions.html')

# Route to handle admission form submission
@app.route('/admissions/apply', methods=['POST'])
def apply_admission():
    try:
        new_admission = Admission(
            child_name=request.form['childName'],
            parent_name=request.form['parentName'],
            email=request.form['email'],
            phone=request.form['phone'],
            dob=datetime.strptime(request.form['dob'], '%Y-%m-%d').date(),
            age=int(request.form['age']),
            address=request.form['address'],
            program=request.form['program']
        )
        db.session.add(new_admission)
        db.session.commit()

        # Send confirmation email
        send_admission_confirmation(new_admission)

        flash("Application submitted successfully!", "success")
    except Exception as e:
        flash(f"Something went wrong: {str(e)}", "danger")
    
    return redirect(url_for('admissions_form'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            new_message = Contact(
                name=request.form['name'],
                email=request.form['email'],
                message=request.form['message']
            )
            db.session.add(new_message)
            db.session.commit()
            flash('Message sent successfully!', 'success')  # Flash message
            return redirect(url_for('contact'))            # Correct indentation
        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'danger')  # Flash error
            return redirect(url_for('contact'))             # Correct indentation
    return render_template('contact.html')

def send_admission_confirmation(admission):
    try:
        msg = Message(
            subject="Admission Confirmation",
            sender=app.config['MAIL_USERNAME'],
            recipients=[admission.email]
        )
        msg.body = f"""
Dear {admission.parent_name},

Thank you for applying for admission for {admission.child_name} to Cocoon Preschool.
We have received your application and will process it shortly.

Program: {admission.program}
Application Date: {admission.created_at.strftime('%Y-%m-%d')}

Best regards,
Cocoon Preschool Team
        """
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send confirmation email: {str(e)}")

# Admin Authentication
@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')  
        password = request.form.get('password') 

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials", "danger")

    return render_template('admin-login.html')



@app.route('/admin/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Admin Dashboard
@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('dashboard.html')

@app.route('/admin/admissions')
@login_required
def admin_admissions():
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        admissions = Admission.query.order_by(Admission.created_at.desc()).all()
    else:
        admissions = Admission.query.filter_by(status=status_filter.capitalize()).order_by(Admission.created_at.desc()).all()
    
    return render_template('admin/admissions.html', admissions=admissions)

@app.route('/admin/admissions/<int:id>')
@login_required
def get_admission(id):
    admission = Admission.query.get_or_404(id)
    return jsonify({
        'id': admission.id,
        'child_name': admission.child_name,
        'parent_name': admission.parent_name,
        'email': admission.email,
        'phone': admission.phone,
        'dob': admission.dob.strftime('%Y-%m-%d'),
        'age': admission.age,
        'address': admission.address,
        'program': admission.program,
        'status': admission.status,
        'created_at': admission.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/admin/admissions/<int:id>/status', methods=['POST'])
@login_required
def update_admission_status(id):
    admission = Admission.query.get_or_404(id)
    data = request.get_json()
    
    if data and 'status' in data:
        admission.status = data['status'].capitalize()
        db.session.commit()
        
        # Send email notification to parent
        try:
            msg = Message(
                f'Admission Application Status Update - {admission.status}',
                sender='vanduvarsh103@gmail.com',
                recipients=[admission.email]
            )
            msg.body = f"""
Dear {admission.parent_name},

Your admission application for {admission.child_name} has been {admission.status.lower()}.

Program: {admission.program}
Application Date: {admission.created_at.strftime('%Y-%m-%d')}

Thank you for choosing Cocoon Preschool.

Best regards,
Cocoon Preschool Team
            """
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
        
        return jsonify({'message': f'Application status updated to {admission.status}'})
    
    return jsonify({'error': 'Invalid request'}), 400

@app.route('/admin/admissions/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_admission(id):
    admission = Admission.query.get_or_404(id)
    try:
        db.session.delete(admission)
        db.session.commit()
        return '', 204  # Successfully deleted
    except Exception as e:
        db.session.rollback()  # In case of error, rollback the session
        return jsonify({'error': 'Failed to delete admission'}), 500


@app.route('/admin/events')
@login_required
def admin_events():
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template('admin/events.html', events=events)

@app.route('/admin/events/add', methods=['POST'])
@login_required
def add_event():
    title = request.form.get('title')
    description = request.form.get('description')
    date = request.form.get('date')
    image = request.files.get('image')

    if image:
        filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
        filepath = os.path.join('static/images/events', filename)
        image.save(filepath)
        new_event = Event(title=title, description=description, date=datetime.strptime(date, "%Y-%m-%d"), image=filename)
        db.session.add(new_event)
        db.session.commit()
        send_event_email(title, description, date, image)
    
    flash("Event added and notification sent to all subscribers.", "success")
    return redirect(url_for('admin_events'))
 
@app.route('/admin/events/delete/<int:event_id>', methods=['GET'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    try:
        db.session.delete(event)
        db.session.commit()
        flash("Event deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting event: {str(e)}", "danger")
    return redirect(url_for('admin_events'))

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'images', 'gallery')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file types for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

from datetime import datetime

@app.route('/admin/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)  # Get the event by its ID

    if request.method == 'POST':
        # Update event details from the form
        event.title = request.form['title']
        event.description = request.form['description']
        
        # Convert the date string to a datetime object
        event_date_str = request.form['date']
        event.date = datetime.strptime(event_date_str, '%Y-%m-%d').date()  # Convert to date object

        # Handle image update if a new image is provided
        new_image = request.files.get('image')
        if new_image and allowed_file(new_image.filename):
            filename = secure_filename(new_image.filename)
            filepath = os.path.join(app.root_path, 'static', 'images', 'events', filename)
            new_image.save(filepath)
            event.image = filename  # Update the image filename in the database

        try:
            db.session.commit()
            flash('Event updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            flash(f'Error updating event: {str(e)}', 'danger')

        return redirect(url_for('admin_events'))  # Redirect to the event management page

    return render_template('admin/edit_event.html', event=event)

@app.route('/admin/gallery', methods=['GET', 'POST'])
@login_required
def admin_gallery():
    category_filter = request.args.get('category', 'all')  # Default to 'all'

    # Handle category filtering for GET requests
    if category_filter == 'all':
        images = GalleryImage.query.order_by(GalleryImage.uploaded_at.desc()).all()
    else:
        images = GalleryImage.query.filter_by(category=category_filter).order_by(GalleryImage.uploaded_at.desc()).all()

    if request.method == 'POST':
        images_uploaded = request.files.getlist('images')
        caption = request.form.get('caption')
        category = request.form.get('category')

        for image in images_uploaded:
            if image and allowed_file(image.filename):
                filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
                image.save(os.path.join(UPLOAD_FOLDER, filename))

                # Add image record to the database
                db.session.add(GalleryImage(filename=filename, caption=caption, category=category))

        db.session.commit()
        flash('Images uploaded successfully', 'success')
        return redirect(url_for('admin_gallery', category=category_filter))  # Make sure category stays selected

    return render_template('admin/gallery.html', images=images, category_filter=category_filter)   
@app.route('/admin/gallery/upload', methods=['POST'])
@login_required
def upload_gallery():
    images = request.files.getlist('images')
    caption = request.form.get('caption')
    category = request.form.get('category')  # Get category from form

    for image in images:
        if image and allowed_file(image.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
            image.save(os.path.join(UPLOAD_FOLDER, filename))

            # Save image details in the database
            db.session.add(GalleryImage(
                filename=filename,
                caption=caption,
                category=category  # Store category
            ))

    db.session.commit()
    flash('Images uploaded successfully', 'success')
    return redirect(url_for('admin_gallery'))

# Delete an image from the gallery
@app.route('/admin/gallery/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_gallery_image(image_id):
    image = GalleryImage.query.get_or_404(image_id)

    # Delete the image file from the static/images/gallery folder
    image_path = os.path.join(UPLOAD_FOLDER, image.filename)
    if os.path.exists(image_path):
        os.remove(image_path)

    # Delete the record from the database
    db.session.delete(image)
    db.session.commit()

    flash('Image deleted successfully', 'success')
    return redirect(url_for('admin_gallery'))



app.config['UPLOAD_FOLDER'] = 'static/uploads/programs'

@app.route('/admin/programs', methods=['GET', 'POST'])
@login_required
def manage_programs():
    form = ProgramForm()

    if request.method == 'POST' and form.validate():
        try:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image_file.save(image_path)

            new_program = Program(
                title=form.title.data,
                description=form.description.data,
                age_group=form.age_group.data,
                image_filename=filename  # Make sure this field exists in your model
            )
            db.session.add(new_program)
            db.session.commit()
            flash('Program added successfully!', 'success')
            return redirect(url_for('manage_programs'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding program. Please try again.', 'danger')

    programs = Program.query.order_by(Program.title).all()
    return render_template('admin/programs.html', programs=programs, form=form)
@app.route('/admin/programs/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_program(id):
    program = Program.query.get_or_404(id)
    form = ProgramForm(obj=program)
    
    if request.method == 'POST' and form.validate():
        try:
            program.title = form.title.data
            program.description = form.description.data
            program.age_group = form.age_group.data
            db.session.commit()
            flash('Program updated successfully!', 'success')
            return redirect(url_for('manage_programs'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating program. Please try again.', 'danger')
    
    return render_template('admin/edit_program.html', form=form, program=program)

@app.route('/admin/programs/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_program(id):
    try:
        program = Program.query.get_or_404(id)
        db.session.delete(program)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return 'Error deleting program', 500
    
@app.route('/admin/contact')
@login_required
def admin_contact():
    messages = Contact.query.order_by(Contact.created_at.desc()).all()
    return render_template('admin/contact.html', messages=messages)

@app.route('/admin/contact/delete/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact_message(contact_id):
    contact_message = Contact.query.get_or_404(contact_id)
    try:
        db.session.delete(contact_message)
        db.session.commit()
        flash("Contact message deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting contact message: {str(e)}", "danger")
    return redirect(url_for('admin_contact'))  # Corrected route name here

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email').strip().lower()

    if not email:
        flash("Please enter a valid email.", "warning")
        return redirect(request.referrer or '/')

    # Check if already subscribed
    existing = Subscriber.query.filter_by(email=email).first()
    if existing:
        flash("You're already subscribed to our newsletter.", "info")
        return redirect(request.referrer or '/')

    # Store in DB
    new_subscriber = Subscriber(email=email)
    db.session.add(new_subscriber)
    db.session.commit()

    # Send welcome email
    try:
        msg = Message(
            "Welcome to Cocoon The Preschool Newsletter!",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = (
            "Hi there!\n\n"
            "Thanks for subscribing to Cocoon The Preschool. "
            "Stay tuned for our latest updates, events, and joyful moments!\n\n"
            "- The Cocoon Team"
        )
        mail.send(msg)
        flash("You've successfully subscribed! Check your email for a welcome message.", "success")
    except Exception as e:
        flash("Subscription saved, but failed to send welcome email.", "warning")
        print("Email Error:", e)

    return redirect(request.referrer or '/')

@app.route('/admin/subscribers')
def view_subscribers():
    all_subs = Subscriber.query.all()
    return render_template('admin/subscribers.html', subscribers=all_subs)
def send_event_email(title, description, date, image):
    subject = f"New Event: {title}"
    body = f"""
A new event has been announced at Cocoon Preschool!

Title: {title}
Description: {description}
Date: {datetime.strptime(date, "%Y-%m-%d")}

Visit our website for more details.
"""

    subscribers = Subscriber.query.all()
    recipients = [s.email for s in subscribers]

    if not recipients:
        print("No subscribers found.")
        return

    try:
        msg = Message(subject, recipients=recipients, body=body)
        mail.send(msg)
        print("Event notification sent.")
    except Exception as e:
        print(f"Email error: {e}")
app.route('/admin/subscribers')
def view_subscribers():
    all_subs = Subscriber.query.all()
    return render_template('admin/subscribers.html', subscribers=all_subs)


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    with app.app_context():
        # db.drop_all()
        db.create_all() # <-- Then recreate fresh tables
        # Create admin user if not exists
        if not User.query.first():
            admin = User(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)
