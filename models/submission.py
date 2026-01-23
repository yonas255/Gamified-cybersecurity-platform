from models import challenge, db


class Submission(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)
    challenge_id=db.Column(db.Integer, nullable=False)
    is_correct=db.Column(db.Boolean, default=False)