class DomainDocumentAnalysis:
    """Business logic representation of analysis results"""
    def __init__(self, country: str, form_type: str, result: dict):
        self.country = country
        self.form_type = form_type
        self.result = result 