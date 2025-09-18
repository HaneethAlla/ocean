from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime
from typing import List

from database import get_db
from models import ArgoFloat
from schemas import FloatResponse
from utils.netcdf_parser import parse_netcdf

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process a NetCDF file"""
    try:
        # Ensure data directory exists
        DATA_DIR = "data"
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Save file
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse NetCDF
        parsed_data = parse_netcdf(file_path)
        
        # Check if float already exists
        existing_float = db.query(ArgoFloat).filter(
            ArgoFloat.platform_number == parsed_data['platform_number'],
            ArgoFloat.cycle_number == parsed_data['cycle_number']
        ).first()
        
        if existing_float:
            # Update existing record
            for key, value in parsed_data.items():
                setattr(existing_float, key, value)
            existing_float.date_updated = datetime.now()
            db.commit()
            db.refresh(existing_float)
            return {"message": f"Float {existing_float.platform_number} updated successfully"}
        else:
            # Create new record
            new_float = ArgoFloat(
                **parsed_data,
                file_name=file.filename,
                date_created=datetime.now(),
                date_updated=datetime.now()
            )
            db.add(new_float)
            db.commit()
            db.refresh(new_float)
            return {"message": f"Float {new_float.platform_number} added successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/", response_model=List[FloatResponse])
def get_all_floats(db: Session = Depends(get_db)):
    """Get all ARGO floats"""
    return db.query(ArgoFloat).all()

@router.get("/{float_id}", response_model=FloatResponse)
def get_float(float_id: int, db: Session = Depends(get_db)):
    """Get a specific float by ID"""
    argo_float = db.query(ArgoFloat).filter(ArgoFloat.id == float_id).first()
    if not argo_float:
        raise HTTPException(status_code=404, detail="Float not found")
    return argo_float

@router.delete("/{float_id}")
def delete_float(float_id: int, db: Session = Depends(get_db)):
    """Delete a float and its associated file"""
    argo_float = db.query(ArgoFloat).filter(ArgoFloat.id == float_id).first()
    if not argo_float:
        raise HTTPException(status_code=404, detail="Float not found")
    
    # Delete the file
    try:
        if argo_float.file_name:
            file_path = os.path.join("data", argo_float.file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        # Log error but continue with database deletion
        print(f"Error deleting file: {str(e)}")
    
    # Delete from database
    db.delete(argo_float)
    db.commit()
    
    return {"message": f"Float {argo_float.platform_number} deleted successfully"}