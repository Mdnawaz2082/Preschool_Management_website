from flask_mail import Message, Mail
from threading import Thread
from flask import current_app

mail = Mail()

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body=None):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()

def send_admission_confirmation(admission):
    send_email(
        'Admission Application Received',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[admission.email],
        text_body=f'''Dear {admission.parent_name},

Thank you for submitting an admission application for {admission.child_name}.
We have received your application and will review it shortly.

Best regards,
Cocoon Preschool Team
''',
        html_body=f'''
<p>Dear {admission.parent_name},</p>
<p>Thank you for submitting an admission application for {admission.child_name}.</p>
<p>We have received your application and will review it shortly.</p>
<p>Best regards,<br>Cocoon Preschool Team</p>
'''
    )