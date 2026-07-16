from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default='initiator')

class DocumentType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, default='')
    fields = db.relationship('Field', backref='document_type', lazy=True, cascade="all, delete-orphan")

class Field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_type_id = db.Column(db.Integer, db.ForeignKey('document_type.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(20), nullable=False)
    is_required = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)

class DocumentInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_type_id = db.Column(db.Integer, db.ForeignKey('document_type.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document_type = db.relationship('DocumentType', backref='instances')
    creator = db.relationship('User', backref='documents')
    field_values = db.relationship('DocumentFieldValue', backref='document', lazy=True, cascade="all, delete-orphan")

class DocumentFieldValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document_instance.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=False)
    value = db.Column(db.Text, default='')

    field = db.relationship('Field')
