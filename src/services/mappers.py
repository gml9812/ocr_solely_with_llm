from src.api.schemas.responses import DocumentAnalysisResponse
from src.domain.models import DomainDocumentAnalysis

def to_response(domain: DomainDocumentAnalysis) -> DocumentAnalysisResponse:
    return DocumentAnalysisResponse(
        country=domain.country,
        form_type=domain.form_type,
        result=domain.result
    ) 