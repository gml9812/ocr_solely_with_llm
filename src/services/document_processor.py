from typing import List, Dict
import base64
import logging
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import OutputParserException
from src.utils.exceptions import ModelResponseError
from src.services.llm_schemas import GeminiResponse
from src.domain.models import DomainDocumentAnalysis
from src.api.schemas.responses import FormType

class DocumentProcessor:
    def __init__(self, llm):
        self.llm = llm
        self.logger = logging.getLogger(__name__)

    async def analyze_document(self, image_bytes: bytes, keywords: List[str]) -> DomainDocumentAnalysis:
        """Orchestrates document analysis workflow"""
        try:
            base64_image = self._encode_image(image_bytes)
            prompt = self._create_analysis_prompt(keywords)
            gemini_response = await self._call_llm(prompt)
            return self._convert_to_domain(gemini_response)
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            raise

    def _encode_image(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode('utf-8')

    def _create_analysis_prompt(self, keywords: List[str]) -> str:
        """Generate analysis instructions for the model"""
        return f"""
        Analyze this document and:
        1. Determine the country of origin (use official names)
        2. Classify the document type from these options: 
           {[t.value for t in FormType]}
        3. Extract these fields (return ONLY these keys):
           {keywords}
        
        Rules:
        - Return null for missing fields
        - Use original language for text values
        - Format numbers without separators
        - Include country even if uncertain
        """

    async def _call_llm(self, prompt: str) -> GeminiResponse:
        try:
            structured_llm = self.llm.with_structured_output(GeminiResponse)
            return await structured_llm.ainvoke(prompt)
            
        except Exception as e:
            self.logger.error(f"LLM processing failed: {str(e)}")
            raise ModelResponseError("Failed to get valid structured response") 

    def _convert_to_domain(self, response) -> DomainDocumentAnalysis:
        return DomainDocumentAnalysis(
            country=response.country,
            form_type=response.form_type,
            result=response.result
        ) 