from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class RegisterForm(FlaskForm):
    name = StringField('Név', validators=[DataRequired(), Length(min=2, max=255)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Telefonszám', validators=[Length(max=50)])
    password = PasswordField('Jelszó', validators=[
        DataRequired(), Length(min=6, message='Minimum 6 karakter!')
    ])
    password2 = PasswordField('Jelszó megerősítése', validators=[
        DataRequired(), EqualTo('password', message='A két jelszó nem egyezik!')
    ])
    role = SelectField('Szerepkör', choices=[
        ('megrendelo', 'Megrendelő'),
        ('beszallito', 'Beszállító'),
        ('fuvarozo', 'Fuvarozó'),
        ('raktaros', 'Raktáros')
    ])
    submit = SubmitField('Regisztráció')
