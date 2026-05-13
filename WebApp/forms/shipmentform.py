from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField, DateTimeLocalField
from wtforms.validators import DataRequired, ValidationError
from datetime import datetime


class ShipmentForm(FlaskForm):
    expected_at = DateTimeLocalField('Várható szállítás dátuma',
                                     format='%Y-%m-%dT%H:%M',
                                     validators=[DataRequired()])
    note = TextAreaField('Megjegyzés')
    submit = SubmitField('Szállítás rögzítése')

    def validate_expected_at(self, field):
        if field.data and field.data < datetime.now():
            raise ValidationError('❌ Az érkezési idő nem lehet a múltban!')


class ShipmentStatusForm(FlaskForm):
    status = SelectField('Státusz', choices=[
        ('elokeszitve', 'Előkészítve'),
        ('uton', 'Úton'),
        ('megerkezett', 'Megérkezett'),
        ('sikertelen', 'Sikertelen')
    ], validators=[DataRequired()])
    submit = SubmitField('Állapot frissítése')