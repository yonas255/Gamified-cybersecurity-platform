from models import db


class Challenge(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(120), nullable=False)
    description=db.Column(db.Text, nullable=False)
    difficulty=db.Column(db.String(20), default="Beginner")
    points=db.Column(db.Integer, default=100)
    flag_hash=db.Column(db.String(250), nullable=False)#storing hashed flag, not plain text
    lab_type = db.Column(db.String(20), default = "none")