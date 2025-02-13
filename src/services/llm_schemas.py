from pydantic import BaseModel
from typing import Dict, Optional
from src.api.schemas.responses import FormType

class GeminiResponse(BaseModel):
    country: str
    form_type: FormType 
    result: Dict[str, Optional[str]] 