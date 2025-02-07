import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from enum import Enum
from typing import List, Dict, Any, Optional
from google import genai
import base64
from starlette.concurrency import run_in_threadpool
import json
import logging
from dotenv import load_dotenv
from pydantic import BaseModel, Field, RootModel

load_dotenv()

app = FastAPI()

# Pydantic Model for Gemini Response
class GeminiKeywords(RootModel):
    root: Dict[str, Optional[str]] # Changed __root__ to root, and now 'root' is the root

class GeminiResponse(BaseModel):
    category: str = Field(..., description="Document category")
    confidence: float = Field(..., description="Confidence level for category")
    keywords: GeminiKeywords = Field(..., description="Extracted keywords and values")

# Define fixed document types using an Enum
class DocumentCategory(str, Enum):
    business_license = "business license"
    receipt = "receipt"
    invoice = "invoice"
    contract = "contract"
    id_document = "identification document"
    tax_form = "tax form"
    
    @classmethod
    def list_categories(cls):
        return [category.value for category in cls]

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Initialize the client with the new SDK
client = genai.Client(api_key=GOOGLE_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_FILE_TYPES_STR = os.getenv("ALLOWED_FILE_TYPES")
ALLOWED_FILE_TYPES: Dict[str, List[str]] = json.loads(ALLOWED_FILE_TYPES_STR) if ALLOWED_FILE_TYPES_STR else {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "application/pdf": [".pdf"]
}
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

def validate_file_type(file: UploadFile) -> bool:
    file_extension = os.path.splitext(file.filename)[1].lower()
    content_type = file.content_type
    
    if content_type in ALLOWED_FILE_TYPES:
        return file_extension in ALLOWED_FILE_TYPES[content_type]
    return False

def validate_file_size(file: UploadFile, max_size_mb: int = MAX_FILE_SIZE_MB) -> bool:
    max_bytes = max_size_mb * 1024 * 1024
    return file.size <= max_bytes

def validate_keywords(keywords: List[str]) -> bool:
    return bool(keywords)

def create_analysis_prompt(keywords: List[str]) -> str:
    categories = DocumentCategory.list_categories()

    # Create example JSON using Pydantic model
    example_response = GeminiResponse(
        category="example_category",
        confidence=0.85,
        keywords=GeminiKeywords(root={"keyword1": "example_value", "keyword2": None})
    )
    json_example = example_response.model_dump_json(indent=4) # Get indented JSON for readability in prompt

    return f"""
    Analyze this document image and provide the following information in a structured JSON format.
    
    1. Document Classification:
    - Identify the document type from these categories: {', '.join(categories)}
    - Provide confidence level for the classification (0.0 to 1.0).
    
    2. Information Extraction:
    For each of these keywords, extract the corresponding value: {', '.join(keywords)}.
    - If a value is not found, explicitly return null.
    - For dates, use ISO format (YYYY-MM-DD).
    - For currency values, include the currency symbol.
    
    Ensure the response is valid JSON and strictly adheres to this structure:
    
    {json_example}
    
    """

def process_image_with_gemini(image_bytes: bytes, keywords: List[str]) -> Dict[str, Any]:
    """
    Process the image using Gemini model and extract information based on keywords
    """
    # Convert image to base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    # Construct the prompt
    prompt = create_analysis_prompt(keywords)

    # Initialize Gemini model with controlled generation for JSON
    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',
        generation_config={"response_mime_type": "application/json"}
    )

    # Create message with image
    response = model.generate_content(
        contents=[
            {"text": prompt},
            {
                "inline_data": {
                    "mime_type": "image/jpeg", # Assuming JPEG, adjust if needed
                    "data": base64_image
                }
            }
        ]
    )

    # Log the raw response text - UPDATED to use logging
    logger.info(f"Raw API Response: {response.text}")

    try:
        # Parse and validate JSON response using Pydantic
        gemini_response = GeminiResponse.model_validate_json(response.text)
        return gemini_response.model_dump() # Return as standard dictionary

    except json.JSONDecodeError as e:
        logger.error(f"Gemini response was not valid JSON: {e}")
        raise ValueError(f"Failed to parse model response as JSON: {str(e)}")
    except Exception as e: # Pydantic ValidationError or other exceptions
        logger.error(f"Failed to validate or process Gemini response: {e}")
        raise ValueError(f"Failed to process model response: {str(e)}")

@app.post("/ocr", response_model=GeminiResponse)
async def process_document(
    file: UploadFile = File(...),
    keywords: List[str] = Form(...)
):
    if not validate_file_type(file):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {ALLOWED_FILE_TYPES}"
        )
    
    if not validate_file_size(file):
        raise HTTPException(
            status_code=400,
            detail="File size exceeds {MAX_FILE_SIZE_MB}MB limit"
        )
    
    if not validate_keywords(keywords):
        raise HTTPException(
            status_code=400,
            detail="At least one keyword is required"
        )
    
    max_retries = 3 # Set maximum number of retries
    retry_count = 0

    while retry_count <= max_retries:
        try:
            contents = await file.read()
            results = await run_in_threadpool(process_image_with_gemini, contents, keywords)
            return JSONResponse(content=results) # Return valid response

        except ValueError as ve: # Catch ValueError from Pydantic validation in process_image_with_gemini
            retry_count += 1
            logger.warning(f"Invalid JSON response (retry {retry_count}/{max_retries}): {ve}")
            if retry_count > max_retries:
                logger.error(f"Max retries exceeded.  Failed to get valid JSON after {max_retries} attempts.")
                raise HTTPException(status_code=500, detail="Failed to process document due to invalid model response format after multiple retries.")
            else:
                # Optionally add a delay before retrying (e.g., asyncio.sleep(1))
                pass # Retry immediately for now

        except Exception as e: # Catch other exceptions (e.g., API errors, network issues)
            logger.error(f"Error processing document (non-JSON error): {e}")
            raise HTTPException(status_code=500, detail="Document processing failed") 