from flask_sqlalchemy import SQLAlchemy
from datetime import datetime  # Importa datetime aquí
from sqlalchemy.dialects.mysql import ENUM

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    role = db.Column(db.String(50), nullable=False, default='user')
    membership = db.Column(ENUM('Gratis', 'Premium'), nullable=False, default='Gratis')  # Nuevo atributo
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    url = db.Column(db.String(255))
    date_published = db.Column(db.DateTime)
    image_url = db.Column(db.String(255))
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # Puedes decidir si mantienes category o category_id

class Website(db.Model):
    __tablename__ = 'websites'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    # Relación con los artículos
    articles = db.relationship('Article', backref='website', lazy=True)

