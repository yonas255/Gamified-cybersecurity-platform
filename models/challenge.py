# importing the database instance so this model can interact with the database
from models import db

#defines the challenge table/model
class Challenge(db.Model):
    id=db.Column(db.Integer, primary_key=True) # define fields for ID
    title=db.Column(db.String(120), nullable=False) # define title
    description=db.Column(db.Text, nullable=False) # define description
    difficulty=db.Column(db.String(20), default="Beginner") # define difficulty level
    points=db.Column(db.Integer, default=100) # define points
    flag_hash=db.Column(db.String(250), nullable=False)# define stored hashed flag, not plain text
    lab_type = db.Column(db.String(20), default = "none") # define lab type to categorize the challenge.