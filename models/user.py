from models import db
from flask_login import UserMixin



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=True) 
    password_hash = db.Column(db.String(250), nullable=False)
    points = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    failed_login_count = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.Integer, nullable=True)  # unix timestamp (seconds)
    

    
    
#    class Meta:
#        verbose_name = _("")
#        verbose_name_plural = _("s")

#    def __str__(self):
#        return self.name

#    def get_absolute_url(self):
#        return reverse("_detail", kwargs={"pk": self.pk})
#)