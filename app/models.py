from datetime import datetime
from app import db

class InboundLead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    qualification = db.Column(db.String(20), default='')
    mqls = db.relationship('MQL', backref='inbound_lead', lazy=True)

class OutboundLead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    qualification = db.Column(db.String(20), default='')
    mqls = db.relationship('MQL', backref='outbound_lead', lazy=True)

class MQL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('inbound_lead.id'), nullable=True)
    outbound_lead_id = db.Column(db.Integer, db.ForeignKey('outbound_lead.id'), nullable=True)
    lead_type = db.Column(db.String(20), nullable=False)  # "inbound" or "outbound"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sqls = db.relationship('SQL', backref='mql', lazy=True)

class SQL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mql_id = db.Column(db.Integer, db.ForeignKey('mql.id'))
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
