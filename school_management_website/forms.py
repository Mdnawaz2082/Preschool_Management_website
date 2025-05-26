from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, FileField, SelectField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileField, FileRequired, FileAllowed
class AdmissionForm(FlaskForm):
    child_name = StringField('Child\'s Name', validators=[DataRequired(), Length(min=2, max=100)])
    parent_name = StringField('Parent\'s Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=20)])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    age = StringField('Age', validators=[DataRequired(), Length(min=1, max=3)])
    address = TextAreaField('Address', validators=[DataRequired()])
    program = SelectField('Program', choices=[
        ('Child Care', 'Child Care'),
        ('Nursery', 'Nursery'),
        ('Play Group', 'Play Group'),
        ('Senior KG', 'Senior KG'),
        ('Junior KG', 'Junior KG'),
    ], validators=[DataRequired()])

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])

class ProgramForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    age_group = StringField('Age Group', validators=[DataRequired()])
    image = FileField('Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])

class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    image = FileField('Image')


