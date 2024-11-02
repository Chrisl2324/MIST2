from flask import Blueprint, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask_login import UserMixin
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100))
    
    
    def generate_verification_token(self):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(self.email, salt='email-verification')
        self.email_verification_token = token
        db.session.commit()
        return token

    def verify_email(self, token):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt='email-verification', max_age=3600)
            if email == self.email:
                self.is_verified = True
                self.email_verification_token = None
                db.session.commit()
                return True
        except:
            return False
    
    def __repr__(self):
        return f"User <{self.username}>"

class Article(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String, nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    author = db.Column(db.String, nullable=False)
    image = db.Column(db.String)
    is_authenticated = db.Column(db.Boolean, default=False)
    topic = db.Column(db.String(50), nullable=False, default='Blog')
    

    user = db.relationship("User", backref=db.backref("articles", lazy=True))
    comments = db.relationship("Comment", back_populates="article")

    def __repr__(self):
        return f"Article <{self.title}>"
    
   
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=False)

    user = db.relationship("User", backref=db.backref("comments", lazy=True))
    article = db.relationship("Article", back_populates="comments")

    def __repr__(self):
        return f"Comment <{self.text}>"

    
class CommentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    content = StringField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')