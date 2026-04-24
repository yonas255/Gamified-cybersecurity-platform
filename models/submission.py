# importing the database instance and related model so this table can link submissions to challenges
from models import challenge, db


class Submission(db.Model):
    # defines the submission model to store each user attempts
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)# define user ID
    challenge_id=db.Column(db.Integer, nullable=False)# define challenge ID
    is_correct=db.Column(db.Boolean, default=False)# define whether the submitted answer is correct.