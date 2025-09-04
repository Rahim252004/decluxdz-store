from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, SelectField, IntegerField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from utils import ALGERIAN_PROVINCES

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class ProductForm(FlaskForm):
    name = StringField('Product Name (English)', validators=[DataRequired(), Length(max=200)])
    name_ar = StringField('Product Name (Arabic)', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description (English)')
    description_ar = TextAreaField('Description (Arabic)')
    price = FloatField('Price (DZD)', validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    image = FileField('Main Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'])])
    in_stock = BooleanField('In Stock')
    featured = BooleanField('Featured Product')

class CheckoutForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=200)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[Email()])
    address = TextAreaField('Address', validators=[DataRequired()])
    wilaya = SelectField('Province', choices=[(w, w) for w in ALGERIAN_PROVINCES], validators=[DataRequired()])
    notes = TextAreaField('Order Notes')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    email = StringField('Email', validators=[Email()])
    phone = StringField('Phone', validators=[Length(max=20)])
    subject = StringField('Subject', validators=[Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired()])

class OrderStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('pending', 'قيد الانتظار'),
        ('in_delivery', 'في التوصيل'),
        ('delivered', 'تم التسليم')
    ], validators=[DataRequired()])
