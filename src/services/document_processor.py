from typing import List, Dict, Optional
import base64
import logging
import json
import re
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import OutputParserException
from src.utils.exceptions import ModelResponseError
from src.services.llm_schemas import GeminiResponse
from src.domain.models import DomainDocumentAnalysis
from src.api.schemas.responses import FormType
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

class GeminiResponse(BaseModel):
    country: str
    form_type: FormType 
    result: Dict[str, Optional[str]]
    confidence: Dict[str, float] = Field(default_factory=dict)

class DocumentProcessor:
    def __init__(self, llm):
        self.llm = llm
        self.logger = logging.getLogger(__name__)

    async def analyze_document(self, image_bytes: bytes, keywords: List[str]) -> DomainDocumentAnalysis:
        """Orchestrates document analysis workflow"""
        try:
            base64_image = self._encode_image(image_bytes)
            
            # Create the prompt with image
            prompt = self._create_analysis_prompt(keywords)
            
            # Use message-based approach instead of setting client.image_content
            message_content = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
            
            # Create a Human message with the content
            message = HumanMessage(content=message_content)
            
            # Call LLM with the message
            gemini_response = await self._call_llm_with_image(message)
            
            return self._convert_to_domain(gemini_response)
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            raise

    def _encode_image(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode('utf-8')

    def _create_analysis_prompt(self, keywords: List[str]) -> str:
        """Generate analysis instructions for the model"""
        return f"""
        IMPORTANT: This is an OCR task. Only report text that you can clearly see in the image.
        DO NOT make up or hallucinate any information that is not visible in the document.
        
        1. First, list ALL text you can see in the document, line by line.
        2. Determine the country of origin:
           - Based on visible text, logos, currency symbols, language, or document format
           - Make your best guess even if not explicitly stated
           - Consider phone number formats, address patterns, and language used
        3. Classify the document type from these options ONLY if you're certain: 
           {[t.value for t in FormType]}
        4. Extract ONLY these fields if they are ACTUALLY VISIBLE in the document:
           {keywords}
        
        Rules:
        - If you cannot clearly see a field, return null
        - NEVER invent or hallucinate information for the fields
        - If you're unsure about any text, indicate this with [?]
        - For country, provide your best guess based on all available evidence
        """

    async def _call_llm_with_image(self, message: HumanMessage) -> GeminiResponse:
        try:
            # Create a PydanticOutputParser for the GeminiResponse model
            parser = PydanticOutputParser(pydantic_object=GeminiResponse)
            
            # Get the format instructions
            format_instructions = parser.get_format_instructions()
            
            # Add format instructions to the message text content
            text_part = message.content[0]
            text_part["text"] += f"\n\n{format_instructions}"
            
            # Call the model with the message
            result = await self.llm.ainvoke([message])
            
            # Parse the result
            try:
                content = result.content if hasattr(result, 'content') else result
                return parser.parse(content)
            except OutputParserException as e:
                self.logger.error(f"Failed to parse LLM output: {str(e)}")
                self.logger.debug(f"Raw LLM output: {result}")
                
                # Try fallback parsing
                try:
                    content = result.content if hasattr(result, 'content') else result
                    return self._try_parse_fallback(content)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback parsing failed: {str(fallback_error)}")
                    raise ModelResponseError("Failed to parse structured response")
        
        except Exception as e:
            self.logger.error(f"LLM processing failed: {str(e)}")
            raise ModelResponseError(f"Failed to get valid structured response: {str(e)}")

    def _try_parse_fallback(self, raw_output: str) -> GeminiResponse:
        """Attempt to parse the raw output when the primary parser fails"""
        # Try to extract a JSON object from the text
        json_match = re.search(r'```json\s*(.*?)\s*```', raw_output, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Look for anything that resembles a JSON object
            json_match = re.search(r'{.*}', raw_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("Could not find JSON in output")
        
        try:
            # Parse the JSON
            data = json.loads(json_str)
            
            # Ensure the result field is a dictionary
            if isinstance(data.get('result'), str):
                try:
                    # Try to parse the result if it's a string representation of a dict
                    data['result'] = json.loads(data['result'].replace("'", '"').replace("null", "null"))
                except:
                    # If that fails, create an empty dict
                    data['result'] = {}
            
            # Create and validate the GeminiResponse
            return GeminiResponse(**data)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON: {str(e)}")

    def _convert_to_domain(self, gemini_response: GeminiResponse) -> DomainDocumentAnalysis:
        """Converts the LLM response schema to the domain model"""
        return DomainDocumentAnalysis(
            country=gemini_response.country,
            form_type=gemini_response.form_type.value,
            result=gemini_response.result
        )