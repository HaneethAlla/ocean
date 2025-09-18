from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime

from database import SessionLocal, engine, get_db
from models import Base, ArgoFloat, UserQuery
from schemas import FloatResponse, QueryRequest, QueryResponse
from utils.netcdf_parser import parse_netcdf
from typing import List
from routes.files import router as files_router
from routes.queries import router as queries_router
from routes.visualization import router as visualization_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(debug=True)
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("ocean.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Ensure data directory exists
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

app.include_router(files_router)
app.include_router(queries_router)
app.include_router(visualization_router)

@app.post("/upload-file/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process a NetCDF file"""
    try:
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
        
        return {"message": f"File {file.filename} processed successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")



@app.get("/floats", response_model=List[FloatResponse])
def get_floats(year: int = None, month: int = None, db: Session = Depends(get_db)):
    """Get list of ARGO floats, optionally filtered by year and month"""
    query = db.query(ArgoFloat)
    if year and month:
        from sqlalchemy import extract
        query = query.filter(ArgoFloat.juld != None)
        query = query.filter(extract('year', ArgoFloat.juld) == year)
        query = query.filter(extract('month', ArgoFloat.juld) == month)
    floats = query.all()
    return floats

@app.get("/floats/{float_id}", response_model=FloatResponse)
def get_float(float_id: int, db: Session = Depends(get_db)):
    """Get details for a specific float"""
    argo_float = db.query(ArgoFloat).filter(ArgoFloat.id == float_id).first()
    if not argo_float:
        raise HTTPException(status_code=404, detail="Float not found")
    return argo_float


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)