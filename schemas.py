from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

class FloatResponse(BaseModel):
    id: int
    platform_number: str
    file_name: str
    date_created: datetime
    date_updated: datetime
    latitude: Optional[float]
    longitude: Optional[float]
    juld: Optional[datetime]
    parameters: List[str]
    cycle_number: Optional[int]
    data_mode: str
    
    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    response: str
    map_data: Optional[Dict[str, Any]] = None
    visualizations: Optional[Dict[str, Any]] = None