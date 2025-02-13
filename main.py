from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
import logging
from src.config import Settings
from src.services.document_processor import DocumentProcessor
from src.validators.file_validator import FileValidator
from src.utils.exceptions import DocumentProcessingError
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from src.services.mappers import to_response
from src.api.schemas.responses import DocumentAnalysisResponse


app = FastAPI()
settings = Settings()

# Initialize services and validators
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.google_api_key)
file_validator = FileValidator(settings)
document_processor = DocumentProcessor(llm)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiKeywords(BaseModel):
    root: dict

@app.post("/ocr", response_model=DocumentAnalysisResponse)
async def process_document(
    file: UploadFile = File(...),
    keywords: List[str] = Form(...)
):
    try:
        file_validator.validate(file)

        logger.info("Document analysis res")
        
        results = await document_processor.analyze_document(
            image_bytes=await file.read(),
            keywords=keywords
        )

        logger.info(f"Document analysis results: {results.__dict__}")

        
        return to_response(results)
        
    except DocumentProcessingError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )