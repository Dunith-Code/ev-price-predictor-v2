from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Prediction(Base):
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(50), nullable=False)
    model_name = Column(String(50), nullable=False)
    battery_capacity = Column(Float)
    range_km = Column(Float)
    year = Column(Integer)
    predicted_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'brand': self.brand,
            'model_name': self.model_name,
            'battery_capacity': self.battery_capacity,
            'range_km': self.range_km,
            'year': self.year,
            'predicted_price': self.predicted_price,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ModelPerformance(Base):
    __tablename__ = 'model_performance'

    id = Column(Integer, primary_key=True)
    model_name = Column(String(100))
    version = Column(String(50))
    r2_score = Column(Float)
    mae = Column(Float)
    rmse = Column(Float)
    trained_at = Column(DateTime, default=datetime.utcnow)

#Database Manager
class DatabaseManager:
    def __init__(self, connection_string: str = None):
        if connection_string is None:
            connection_string = os.environ.get(
                'DATABASE_URL',
                'postgresql://user:password@localhost:5432/ev_predictor'
            )
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def insert_prediction(self, data: dict) -> int:
        session = self.Session()
        try:
            pred = Prediction(
                brand=data.get('brand'),
                model_name=data.get('model_name'),
                battery_capacity=data.get('battery_capacity'),
                range_km=data.get('range_km'),
                year=data.get('year'),
                predicted_price=data.get('predicted_price')
            )
            session.add(pred)
            session.commit()
            return pred.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_history(self, limit: int = 100, offset: int = 0) -> list:
        session = self.Session()
        try:
            count = session.query(Prediction).count()
            avg_price = session.query(
                session.query(Prediction).with_entities(
                    Prediction.predicted_price
                ).subquery()
            ).with_entities(
                func.avg(Prediction.predicted_price)
            ).scalar()
            return {
                'total_predictions': count,
                'average_price': float(avg_price) if avg_price else 0
            }
        finally:
            session.close()
