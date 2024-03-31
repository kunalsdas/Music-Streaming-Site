from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, TextAreaField, SelectMultipleField, SelectField,IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange
from wtforms.fields import SelectMultipleField
from wtforms.widgets import ListWidget, CheckboxInput
from flask_wtf.file import FileField, FileRequired

class UserRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class UserLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SongForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    singer = StringField('Singer', validators=[DataRequired()])
    release_date = DateField('Release Date', format='%Y-%m-%d', validators=[DataRequired()])
    lyrics = TextAreaField('Lyrics')
    genre = StringField('Genre', validators=[DataRequired()])
    audio_file = FileField('Audio File', validators=[FileRequired()])

class AlbumForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    release_date = DateField('Release Date', format='%Y-%m-%d', validators=[DataRequired()])
    songs = SelectMultipleField('Songs', coerce=int)
    submit = SubmitField('Submit')

class SongRatingForm(FlaskForm):
    rating = IntegerField('Rating (out of 5)', validators=[DataRequired(), NumberRange(min=1, max=5)])

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class PlaylistForm(FlaskForm):
    title = StringField('Playlist Title', validators=[DataRequired()])
    songs = MultiCheckboxField('Songs')
    submit = SubmitField('Save Playlist')