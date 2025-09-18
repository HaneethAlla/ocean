from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from database import get_db
from models import ArgoFloat

router = APIRouter(prefix="/visualizations", tags=["visualizations"])

@router.get("/float/{float_id}/profile")
def get_float_profile(float_id: int, db: Session = Depends(get_db)):
    """Get profile data for visualization"""
    argo_float = db.query(ArgoFloat).filter(ArgoFloat.id == float_id).first()
    if not argo_float:
        raise HTTPException(status_code=404, detail="Float not found")
    
    if not argo_float.profile_data:
        raise HTTPException(status_code=404, detail="No profile data available")
    
    return {
        "platform_number": argo_float.platform_number,
        "profile_data": argo_float.profile_data
    }

@router.get("/float/{float_id}/temperature")
def get_temperature_profile(float_id: int, db: Session = Depends(get_db)):
    """Get temperature profile data"""
    argo_float = db.query(ArgoFloat).filter(ArgoFloat.id == float_id).first()
    if not argo_float:
        raise HTTPException(status_code=404, detail="Float not found")
    
    if not argo_float.profile_data or 'TEMP' not in argo_float.profile_data:
        raise HTTPException(status_code=404, detail="No temperature data available")
    
    return {
        "platform_number": argo_float.platform_number,
        "temperature_data": argo_float.profile_data['TEMP']
    }

@router.get("/float/{float_id}/salinity")
def get_salinity_profile(float_id: int, db: Session = Depends(get_db)):
    """Get salinity profile data"""
    argo_float = db.query(ArgoFloat).filter(ArgoFloat.id == float_id).first()
    if not argo_float:
        raise HTTPException(status_code=404, detail="Float not found")
    
    if not argo_float.profile_data or 'PSAL' not in argo_float.profile_data:
        raise HTTPException(status_code=404, detail="No salinity data available")
    
    return {
        "platform_number": argo_float.platform_number,
        "salinity_data": argo_float.profile_data['PSAL']
    }

@router.get("/comparison/{float_ids}")
def compare_floats(float_ids: str, db: Session = Depends(get_db)):
    """Compare multiple floats"""
    try:
        ids = [int(id) for id in float_ids.split(",")]
        floats = db.query(ArgoFloat).filter(ArgoFloat.id.in_(ids)).all()
        
        if len(floats) != len(ids):
            raise HTTPException(status_code=404, detail="One or more floats not found")
        
        comparison_data = {}
        for argo_float in floats:
            comparison_data[argo_float.platform_number] = {
                "profile_data": argo_float.profile_data,
                "position": {
                    "latitude": argo_float.latitude,
                    "longitude": argo_float.longitude
                },
                "date": argo_float.juld.isoformat() if argo_float.juld else None,
                "cycle_number": argo_float.cycle_number
            }
        
        return comparison_data
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid float IDs format")