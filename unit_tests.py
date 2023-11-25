import json
import unittest
import os
from unittest.mock import patch
from flask_bcrypt import Bcrypt
from app import app, db, User, ChatHistory, SessionHistory, add_session_to_database

os.environ['DATABASE_URL'] = 'sqlite://'

class TestFlaskApp(unittest.TestCase):

    # Set up the application context and create the database
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        self.app = app.test_client() # Flask provides a virtual test environment for testing our application
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.bcrypt = Bcrypt(app)
        db.create_all()

    # Tear down the application context and remove the database
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    # Helper function to register a user
    def register_user(self, username, password):
        return self.app.post('/register', data=dict(username=username, password=password, confirm_password=password), follow_redirects=True)

    # Helper function to login a user
    def login_user(self, username, password):
        return self.app.post('/login', data=dict(username=username, password=password), follow_redirects=True)

    # Helper function to logout a user
    def logout_user(self):
        return self.app.get('/logout', follow_redirects=True)

    # Helper function to add a session to the database
    def test_register_user(self):
        response = self.register_user('testuser', 'testpassword')
        self.assertIn(b'Your account has been created!', response.data)

        # Wrap the code that needs the application context
        with self.app.application.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)
            self.assertTrue(self.bcrypt.check_password_hash(user.password, 'testpassword'))

    # Test cases for user registration
    def test_register_user_existing_username(self):
        self.register_user('testuser', 'testpassword')
        response = self.register_user('testuser', 'testpassword2')
        self.assertIn(b'Username already exists.', response.data)

    # Test cases for user login correct password
    def test_login_logout(self):
        self.register_user('testuser', 'testpassword')
        response = self.login_user('testuser', 'testpassword')
        self.assertIn(b'Logged in successfully!', response.data)
        response = self.logout_user()
        self.assertIn(b'GetHired.ai', response.data)

    # Test cases for user login wrong password
    def test_login_wrong_password(self):
        self.register_user('testuser', 'testpassword')
        response = self.login_user('testuser', 'wrongpassword')
        self.assertIn(b'Invalid username or password.', response.data)

    # Test cases for user login nonexistent user
    def test_login_nonexistent_user(self):
        response = self.login_user('nonexistent', 'testpassword')
        self.assertIn(b'Invalid username or password.', response.data)

    # Test cases for job title validation
    @patch('app.is_real_job_title')
    def test_is_real_job_title(self, mock_is_real_job_title):
        mock_is_real_job_title.return_value = True
        response = self.app.post('/is_real_job_title', data=dict(job_title='Software Engineer'))
        data = json.loads(response.data)
        self.assertTrue(data['is_real'])

    # Test cases for invalid job title
    @patch('app.is_real_job_title')
    def test_is_real_job_title_invalid(self, mock_is_real_job_title):
        mock_is_real_job_title.return_value = False
        response = self.app.post('/is_real_job_title', data=dict(job_title='random job title'))
        data = json.loads(response.data)
        self.assertFalse(data['is_real'])

    # Test cases for no input
    @patch('app.is_real_job_title')
    def test_is_real_job_title_no_input(self, mock_is_real_job_title):
        response = self.app.post('/is_real_job_title', data=dict(job_title=''))
        self.assertEqual(response.status_code, 400)

    # Test cases for interview question generation
    @patch('app.generate_interview_questions')
    def test_generate_interview_questions(self, mock_generate_interview_questions):
        mock_generate_interview_questions.return_value = [
            'Question 1', 'Question 2', 'Question 3']
        response = self.app.post('/generate_questions', data=dict(job_title='Software Engineer'))
        data = json.loads(response.data)
        self.assertEqual(data['questions'], ['Question 1', 'Question 2', 'Question 3'])

    # Test cases for no input
    @patch('app.generate_interview_questions')
    def test_generate_interview_questions_no_input(self, mock_generate_interview_questions):
        response = self.app.post('/generate_questions', data=dict(job_title=''))
        self.assertEqual(response.status_code, 400)

    # Test cases for response evaluation
    @patch('app.get_feedback')
    def test_evaluate_response(self, mock_get_feedback):
        mock_get_feedback.return_value = {
            'score': 0.75,
            'feedback': 'Good answer!'
        }
        response = self.app.post('/evaluate_response', data={
            'user_response': 'I have worked in various positions...',
            'question': 'Tell me about your experience.',
            'job_title': 'Software Developer'
        })
        data = json.loads(response.data)
        self.assertEqual(data['score'], 0.75)
        self.assertEqual(data['feedback'], 'Good answer!')

    # Test cases for no input
    @patch('app.evaluate_response_route')
    def test_evaluate_response_no_input(self, mock_evaluate_response):
        response = self.app.post('/evaluate_response', data=dict(response=''))
        self.assertEqual(response.status_code, 400)

    # Test cases for final decision making
    def test_decide(self):        
        sample_responses = [
            {
                "question": "Tell me about your experience.",
                "response": "I have worked in various positions...",
                "feedback": "Good answer!"
            },
        ]

        response = self.app.post('/final_decision', data={
            'job_title': 'Software Developer',
            'responses': json.dumps(sample_responses)  # Convert the list to a JSON string
        })

        data = json.loads(response.data)
        self.assertIsNotNone(data) # Check that the final decision is not None (i.e. it was calculated)

    # Test cases for final decision making
    @patch('app.final_decision_route')
    def test_decide_no_input(self, mock_decide):
        mock_decide.return_value = None
        response = self.app.post('/final_decision', data=dict(score=None))
        self.assertEqual(response.status_code, 400)

    # Test cases for adding a session to the database
    def test_add_session_to_database(self):
        userID = 100
        job_title = 'Software Engineer'
        responses = [
            {"question": "Tell me about your experience.", 
             "response": "I have worked at Google as a Software Engineer for 10 years", 
             "feedback": "Good answer!"}
        ]
        decision = "10/10 Hired!"
        
        this_session = db.session

        add_session_to_database(userID, job_title, responses, decision, this_session)

        session = SessionHistory.query.order_by(SessionHistory.sessionID.desc()).first()
        self.assertIsNotNone(session)
        self.assertEqual(session.userID, userID)
        self.assertEqual(session.jobTitle, job_title)
        self.assertEqual(session.finalDecision, decision)

        chat_records = ChatHistory.query.filter_by(sessionID=session.sessionID).all()
        self.assertEqual(len(chat_records), len(responses))

        for i, record in enumerate(chat_records):
            self.assertEqual(record.botQuestion, responses[i]['question'])
            self.assertEqual(record.userResponse, responses[i]['response'])
            self.assertEqual(record.botReview, responses[i]['feedback'])

    # Test cases for getting the chat logs and succeeding
    def test_chat_logs_authenticated(self):
        # Add a new user and log them in
        self.register_user('testuser', 'testpassword')
        self.login_user('testuser', 'testpassword')

        response = self.app.get('/chat_logs')

        # Verify the response
        self.assertEqual(response.status_code, 200)

    # Test cases for getting the chat logs and failing
    def test_chat_logs_unauthenticated(self):
        # Run the test without logging in
        response = self.app.get('/chat_logs')

        # Verify the response
        self.assertNotEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()