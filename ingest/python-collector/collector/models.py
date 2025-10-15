from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field

class ObservabilityData(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str
    data_type: str
    host: str
    database: str
    environment: str = "production"
    tags: Dict[str, str] = Field(default_factory=dict)
    payload: Dict[str, Any]
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
    
    def to_kafka_message(self) -> Dict[str, Any]:
        return self.model_dump(mode='json')
