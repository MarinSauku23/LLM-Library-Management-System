from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, Optional, Length


# WTForm for registering a user
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("SIGN ME UP")


# WTForm for loging in a user
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("LOG IN")


# WTForm for adding a new book
class AddBooks(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    author = StringField("Author", validators=[DataRequired()])
    genre = StringField("Genre", validators=[DataRequired()])
    reading_status = SelectField("Reading Status", choices=[("Reading", "Reading"), ("Completed", "Completed")],
                                 validators=[DataRequired()])
    submit = SubmitField("Add")


# WTForm for editing a user as an admin
class EditUser(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField("New Password (leave blank to keep current)", validators=[Optional(), Length(min=6)])
    submit = SubmitField("Save")
