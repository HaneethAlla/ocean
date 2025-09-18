from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()

class ArgoFloat(Base):
    __tablename__ = "argo_floats"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_number = Column(String, index=True)
    file_name = Column(String)
    date_created = Column(DateTime)
    date_updated = Column(DateTime)
    latitude = Column(Float)
    longitude = Column(Float)
    juld = Column(DateTime)  # Julian day timestamp
    # location = Column(Geometry('POINT'))
    parameters = Column(JSON)  # Available parameters
    cycle_number = Column(Integer)
    data_mode = Column(String)
    profile_data = Column(JSON)  # Store processed profile data
    
class UserQuery(Base):
    __tablename__ = "user_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String)
    response = Column(String)
    timestamp = Column(DateTime)
    float_id = Column(Integer, ForeignKey("argo_floats.id"))