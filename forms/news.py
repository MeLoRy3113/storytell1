from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField 
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed, FileField


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    is_private = BooleanField("Личное")
    file = FileField('Загрузить файл', validators=[FileAllowed(['jpg', 'png'])])  
    submit = SubmitField('Применить')
