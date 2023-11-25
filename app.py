from flask import Flask, redirect, render_template, request, jsonify, session, url_for, flash
import openai
import json
from dotenv import load_dotenv
import os
import sqlite3
import secrets
import pandas as pd

# ============= IMPORTS FOR USER AUTH ============= #
from flask_bcrypt import Bcrypt
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, ValidationError
from wtforms.validators import EqualTo, InputRequired, Length

# Initialize Flask app
app = Flask(__name__)
load_dotenv()  # take environment variables from .env.

import google.generativeai as palm

palm.configure(api_key='AIzaSyCp37hYiT7Sjb2SbnCrwSl1D_ppKsrtb-c')

models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
model = models[0].name

# Main route, renders the landing page
@app.route('/')
def landing():
    register_form = RegisterForm()
    login_form = LoginForm()
    return render_template('landing.html', register_form=register_form, login_form=login_form)

# Renders the app
@app.route('/app')
def app_main():
    return render_template('app.html')

# Function to check if a job title is real
def is_real_job_title(job_title):
    prompt = f"Is '{job_title}' a real job title? Answer yes or no"

    # Call OpenAI API to generate a response
    response = palm.generateText(
        model=model,
        prompt=prompt,
        temperature=0.5,
        max_output_tokens=800,
    )

    # Process the response and return True if the answer contains 'yes'
    answer = response.result.strip().lower()
    return 'yes' in answer

# Function to get the final decision based on responses and the job title
def get_final_decision(convo, job_title):
    prompt2 = f"""
        You are an interviewer at a big company. 
        A candidate applying for the position of {job_title} has given an interview.
        Analyze the following converstuion of their interview and decide whether the candidate deserves the position or not.
        conversation : {convo}
        Answer in one word only - approved or rejected.
        """
    res = palm.generate_text(
        model=model,
        prompt=prompt2,
        temperature=0.5,
        max_output_tokens=100,
    )
    return "approved" in res.result

# Function to generate interview questions for a job title
def generate_interview_questions(job_title):
    if job_title == "Data Scienist":
        df = pd.read_csv("data_science.csv")
    elif job_title == "DevOps Engineer":
        df = pd.read_csv("dev_ops.csv")
    elif job_title == "Cyber Security Engineer":
        df = pd.read_csv("cyber_data.csv")

    for n in range(0, 5):
        i = random.randint(0,len(df)-1)
        que = df.iloc[i,0]
        ans = df.iloc[i,1]
        questions_lst.append(que)
        answers_lst.append(ans)
    return questions_lst, answers_lst

# Function to check if a user response is genuine
def is_genuine_response(user_response, question):

    # Create a prompt to analyze the response
    prompt = f'Analyze the following response to the question "{question}":\n{user_response}\nIs this a genuine response or a troll response?'

    # Call the OpenAI API to analyze the response
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=10,
        n=1,
        stop=None,
        temperature=0.7,
    )

    # Process the response and return True if it contains 'genuine'
    answer = response.choices[0].text.strip().lower()
    return 'genuine' in answer

# Function to get feedback on a user's response
def get_evaluation(user_response, question, job_title, answer):
    prompt = f"""
    You are an interviewer at a big company. 
    A candidate applying for the position of {job_title} has been asked the question {question}.
    The correct answer to the question is {answer}.
    The candidate has answered to the given question with {user_response}.
    Explain how the candidate has performed in short and kind way.
    Also rate the answer out of 10.
    """
    evaluation = palm.generate_text(
        model=model,
        prompt=prompt,
        temperature=0.5,
        max_output_tokens=800,
    )
    eval = evaluation.result
    return eval

# Route to check if a job title is real
@app.route('/is_real_job_title', methods=['POST'])
def is_real_job_title_route():
    job_title = request.form.get('job_title')
    if not job_title:
        return jsonify({'error': 'Job title is required'}), 400

    is_real = is_real_job_title(job_title)

    return jsonify({'is_real': is_real})

convo = ""

# Route to generate interview questions
@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    job_title = request.form.get('job_title')
    if not job_title:
        return jsonify({'error': 'Job title is required'}), 400

    # Generate interview questions using the OpenAI API
    questions, answers = generate_interview_questions(job_title)
    
    for x in range(0,5):
        yield jsonify({'question': questions[x]})
        user_response = request.form.get('user_response')
        eval = get_evaluation(user_response, questions[x], job_title, answers[x])
        convo = "Question: " + questions[x] + "\nCorrect Answer: " + answers[x] + "\nCandidate Answer: " + user_response + "\nEvaluation: " + eval + "\n\n"
    # Return a response after all questions are asked
    return jsonify({'message': 'All questions asked.'})
##############################################################################################################
# Route to evaluate a user's response
# @app.route('/evaluate_response', methods=['POST'])
# def evaluate_response_route():
#     job_title = request.form.get('job_title')
#     if not job_title:
#         return jsonify({'error': 'Job title is required'}), 400

#     # Evaluate the user's response using the OpenAI API
#     feedback = get_evaluation(user_response, question, job_title, check_genuine_responses)

#     return jsonify(feedback)
##############################################################################################################
# Add the session history of current user to the database
def add_session_to_database(userID, job_title, convo, decision, this_session):
    # Create a new session history instance
    session_history = SessionHistory(userID=userID, jobTitle=job_title, finalDecision=decision)
    this_session.add(session_history)
    this_session.commit()

    # Get the sessionID of the current session
    sessionID = this_session.query(SessionHistory.sessionID).order_by(SessionHistory.sessionID.desc()).first()[0]

    # Insert the chat history into the database
    chat_history = []
    for response in responses:
        chat = ChatHistory(sessionID=sessionID, botQuestion=response['question'], userResponse=response['convo'], botReview=response['feedback'])
        chat_history.append(chat)

    this_session.add_all(chat_history)
    this_session.commit()

# Route to get the final decision based on user responses
@app.route('/final_decision', methods=['POST'])
def final_decision_route():
    job_title = request.form.get('job_title')
    if not job_title or convo == "":
        return jsonify({'error': 'Job title and responses are required'}), 400

    # Get the final decision based on the responses and job title
    decision = get_final_decision(convo, job_title)

    # Below is the code to save the current session to the database
    if current_user.is_authenticated:
        # Only save chat logs if the user is logged in
        userID = current_user.id # Get the userID of the current user
        add_session_to_database(userID, job_title, convo, decision, db_session)
    
    return jsonify(decision)

# Route to show the current user's previous sessions (chat history)
@app.route('/chat_logs')
def chat_logs():
    conn = sqlite3.connect('./instance/database.db')
    c = conn.cursor()

    # Only show the chat logs of the current user. If in guest mode, don't show any chat logs
    if current_user.is_authenticated:
        c.execute("SELECT * FROM chatHistory JOIN sessionHistory ON chatHistory.sessionID = sessionHistory.sessionID WHERE sessionHistory.userID = ?", 
                  (current_user.id,))

    logs = c.fetchall()
    conn.close()

    return render_template('chat_logs.html', logs=logs)

# ========================================================================= #
# ========================== USER AUTHENTICATION ========================== #
# ========================================================================= #

#generate secret key
secret_key = secrets.token_hex(16)
db = SQLAlchemy()
db_session = db.session # session is used to add data to the database
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = secret_key
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'  # type: ignore
login_manager.init_app(app)

# loads a user from the database given their id

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


"""Defines a Flask form for user registration.

This form contains fields for username, password, and confirmation of password.
Each field is validated using various validators from the WTForms library.
If all fields are valid, the user can submit the form to sign up.

Attributes:
    username (StringField): A field for the user's desired username. It is required
        and must be between 4 and 20 characters long.
    password (PasswordField): A field for the user's desired password. It is required
        and must be between 8 and 20 characters long.
    confirm_password (PasswordField): A field for confirming the user's password.
        It is required and must match the value of the password field.
    submit (SubmitField): A button to submit the form and sign up.

"""
class RegisterForm(FlaskForm):
    username = StringField('username', validators=[
                           InputRequired(), Length(min=4, max=20)])
    password = PasswordField('password', validators=[
                             InputRequired(), Length(min=8, max=20)])
    confirm_password = PasswordField('confirm_password', validators=[
                                     InputRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user_object = User.query.filter_by(username=username.data).first()
        if user_object:
            raise ValidationError(
                'Username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('username', validators=[
                           InputRequired(), Length(min=4, max=20)])
    password = PasswordField('password', validators=[
                             InputRequired(), Length(min=8, max=20)])

    submit = SubmitField('Log In')

@app.route('/login', methods=['GET', 'POST'])
def login():
    register_form = RegisterForm()
    login_form = LoginForm()

    if login_form.validate_on_submit():
        # checks if the user actually exists
        user_object = User.query.filter_by(
            username=login_form.username.data).first()
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if user_object and bcrypt.check_password_hash(user_object.password, login_form.password.data):
            login_user(user_object)
            flash('Logged in successfully!', 'success')

            return redirect(url_for('landing'))
        else:
            flash('Invalid username or password.', 'danger')

            # When failed login, show the login modal again
            return render_template('landing.html', 
                                   show_login_modal = True,
                                   register_form=register_form, 
                                   login_form=login_form)

    return render_template('landing.html', register_form=register_form, login_form=login_form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    login_form = LoginForm()

    if register_form.validate_on_submit():
        # Hash the password and create a new user record and add to database
        hashed_password = bcrypt.generate_password_hash(register_form.password.data).decode('utf-8')
        new_user = User(username=register_form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
    else:
        #validation failed
        flash('Username already exists. Please choose a different one.', 'danger')

        # Show the registration modal again after failed registration
        return render_template("landing.html",
                               show_signup_modal=True,
                               register_form=register_form, 
                               login_form=login_form)

    # If the form is valid, render the login modal
    return render_template('landing.html', 
                           show_login_modal=True, 
                           register_form=register_form, 
                           login_form=login_form)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))

# Allows user to see the login modal when "Sign in" is clicked on the app page
@app.route('/show-login-modal')
def show_login_modal():
    register_form = RegisterForm()
    login_form = LoginForm()
    return render_template('landing.html', register_form=register_form, login_form=login_form ,show_login_modal=True)

# ========================================================================= #
# ============================ Database Tables ============================ #
# ========================================================================= #

"""Represents a user in the application.

This class inherits from SQLAlchemy's `db.Model` and Flask-Login's `UserMixin`.
It defines a database table `users` with columns `id`, `username`, and `password`.

Attributes:
    id (int): A unique identifier for the user. This is a primary key in the database.
    username (str): The user's unique username. This is a required field and cannot be
        null or empty. The maximum length of the username is 20 characters.
    password (str): The user's password. This is a required field and cannot be null or
        empty. The password is stored in the database as a hash with a length of 60
        characters.

"""
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

# Represents the chatHistory table in the application.
class ChatHistory(db.Model):
    __tablename__ = 'chatHistory'
    chatID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sessionID = db.Column(db.Integer, db.ForeignKey('sessionHistory.sessionID'), nullable=False)
    botQuestion = db.Column(db.String, nullable=False)
    userResponse = db.Column(db.String, nullable=False)
    botReview = db.Column(db.String, nullable=False)

# Represents the sessionHistory table in the application.
class SessionHistory(db.Model):
    __tablename__ = 'sessionHistory'
    sessionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Integer, nullable=False)
    jobTitle = db.Column(db.String, nullable=False)
    finalDecision = db.Column(db.String)
    timestamp = db.Column(db.TIMESTAMP, server_default=db.text('CURRENT_TIMESTAMP'))

    chats = db.relationship('ChatHistory', backref='session')

# creates the database tables -> only needs to be run once
with app.app_context():
    db.create_all()

# ========================================================================= #

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5001)