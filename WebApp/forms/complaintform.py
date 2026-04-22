from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class ComplaintForm(FlaskForm):
    type = SelectField('Reklamáció típusa', choices=[
        ('hianyos', 'Hiányos szállítmány'),
        ('serult', 'Sérült áru'),
        ('egyeb', 'Egyéb probléma')
    ], validators=[DataRequired()])
    description = TextAreaField('Leírás', validators=[
        DataRequired(), Length(min=10, message='Legalább 10 karakter szükséges!')
    ])
    submit = SubmitField('Reklamáció beküldése')
