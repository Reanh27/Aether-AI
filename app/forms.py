"""WTForms used by auth and content pages."""
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, TextAreaField, SubmitField,
                     SelectField, IntegerField)
from wtforms.validators import (DataRequired, Email, EqualTo, Length, Optional,
                                NumberRange)


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Confirm Password",
                            validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class NoteForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    content = TextAreaField("Content", validators=[DataRequired()])
    submit = SubmitField("Save note")


class DeckTopicForm(FlaskForm):
    """Generate a deck by typing a subject name + number of cards."""
    topic = StringField("Subject / Topic",
                        validators=[DataRequired(), Length(max=200)])
    count = IntegerField("Number of flashcards",
                         default=8,
                         validators=[DataRequired(), NumberRange(min=3, max=20)])
    submit = SubmitField("✨ Generate deck")


class DeckTextForm(FlaskForm):
    """Generate a deck from pasted text (kept as an option)."""
    title = StringField("Deck title", validators=[DataRequired(), Length(max=200)])
    source_text = TextAreaField("Paste study text",
                                validators=[DataRequired()])
    count = IntegerField("Number of flashcards",
                         default=8,
                         validators=[DataRequired(), NumberRange(min=3, max=20)])
    submit = SubmitField("Generate from text")


class QuizForm(FlaskForm):
    topic = StringField("Subject / Topic",
                        validators=[DataRequired(), Length(max=200)])
    count = IntegerField("Number of questions",
                        default=5,
                        validators=[DataRequired(), NumberRange(min=3, max=15)])
    difficulty = SelectField("Difficulty",
                             choices=[("easy", "Easy"), ("medium", "Medium"),
                                      ("hard", "Hard")],
                             default="medium")
    submit = SubmitField("✨ Generate quiz")


class PlannerForm(FlaskForm):
    goal = StringField("What do you want to learn?",
                       validators=[DataRequired(), Length(max=200)])
    days = SelectField("Plan duration",
                       choices=[("3", "3 days"), ("5", "5 days"), ("7", "1 week"),
                                ("14", "2 weeks")],
                       default="7")
    submit = SubmitField("Generate plan")


class RoomForm(FlaskForm):
    name = StringField("Room name", validators=[DataRequired(), Length(max=120)])
    subject = StringField("Subject", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional()])
    submit = SubmitField("Create room")


class PdfSummaryForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    content = TextAreaField("Paste the document text here",
                            validators=[DataRequired()])
    submit = SubmitField("✨ Summarize")