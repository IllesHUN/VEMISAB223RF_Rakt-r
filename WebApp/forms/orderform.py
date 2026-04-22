from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange


class OrderItemForm(FlaskForm):
    product_id = SelectField('Termék', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Mennyiség', validators=[
        DataRequired(), NumberRange(min=1, message='Minimum 1 darab!')
    ])


class OrderForm(FlaskForm):
    note = TextAreaField('Megjegyzés')
    submit = SubmitField('Megrendelés leadása')
