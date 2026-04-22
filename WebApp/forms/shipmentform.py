from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField, DateTimeLocalField
from wtforms.validators import DataRequired


class ShipmentForm(FlaskForm):
    expected_at = DateTimeLocalField('Várható szállítás dátuma',
                                     format='%Y-%m-%dT%H:%M')
    note = TextAreaField('Megjegyzés')
    submit = SubmitField('Szállítás rögzítése')


class ShipmentStatusForm(FlaskForm):
    status = SelectField('Státusz', choices=[
        ('elokeszitve', 'Előkészítve'),
        ('uton', 'Úton'),
        ('megerkezett', 'Megérkezett'),
        ('sikertelen', 'Sikertelen')
    ], validators=[DataRequired()])
    submit = SubmitField('Állapot frissítése')
