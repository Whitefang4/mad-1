from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash


db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    admin = db.Column(db.Boolean(), nullable=False,default=False)
    is_flagged = db.Column(db.Boolean(), nullable=False, default=False)

    

class Influencer(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    bio = db.Column(db.String(500), nullable=False)
    followers = db.Column(db.Integer, nullable=False)
    niche = db.Column(db.String(50), nullable=False)
    activities = db.Column(db.Integer, nullable=False)
    reach = db.Column(db.Integer, nullable=False)

    adrequest = db.relationship('AdRequest', backref='influencer', lazy=True, cascade="delete, delete-orphan")

    
    
class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(50), nullable=False)
    budget = db.Column(db.Float, nullable=False)

    
    campaigns = db.relationship('Campaign', backref='sponsor', lazy=True, cascade="delete, delete-orphan")


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256), nullable=False)
    niche = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.String(64), nullable=False)
    goals = db.Column(db.String(200), nullable=False)
    is_flagged = db.Column(db.Boolean(), nullable=False, default=False)
    

    adrequest = db.relationship('AdRequest', backref='campaign', lazy=True, cascade="delete, delete-orphan")

class AdRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)
    messages = db.Column(db.String(200), nullable=False)
    requirements = db.Column(db.String(200), nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), nullable=False, default='Pending')
    is_private = db.Column(db.Boolean(), nullable=False, default=False)
    completed = db.Column(db.Boolean(), nullable=True, default=False)
    
  

with app.app_context():
    db.create_all()

    is_admin = User.query.filter_by(admin=True).first()
    if not is_admin:
        password_hash = generate_password_hash('admin')
        new_admin = User(username='admin', passhash=password_hash,user_type='admin',email='admin@gmail.com',admin=True)
        db.session.add(new_admin)
        db.session.commit()

