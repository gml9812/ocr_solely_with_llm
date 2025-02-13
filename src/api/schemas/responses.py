from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Optional

class FormType(str, Enum):
    BUSINESS_LICENSE = "business license"
    DRIVERS_LICENSE = "driver's license"
    RECEIPT = "receipt"
    PASSPORT = "passport"
    NATIONAL_ID = "national ID"
    OTHER = "other"
    UNKNOWN = "unknown"

class DocumentAnalysisResponse(BaseModel):
    country: str = Field(..., example="South Korea")
    form_type: FormType = Field(..., example="business license")
    result: Dict[str, Optional[str]] = Field(
        ...,
        example={
            "OCR_TAX_ID_NUM": "123-45-67890",
            "OCR_BP_NAME_LOCAL": "예시 회사"
        }
    ) 