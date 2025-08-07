from . import db
from datetime import datetime

class PredictionLog(db.Model):
    __tablename__ = 'prediction_log'
    id = db.Column(db.Integer, db.Sequence('prediction_log_seq', start=1, increment=1), primary_key=True)
    request_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    area_pred_high = db.Column(db.Float)
    area_pred_median = db.Column(db.Float)
    area_pred_low = db.Column(db.Float)
    dir_pred = db.Column(db.Integer)
    fwi_pred = db.Column(db.Float)
    distance_pred = db.Column(db.Float)
    features_json = db.Column(db.Text)
