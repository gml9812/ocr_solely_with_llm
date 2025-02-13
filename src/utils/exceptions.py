class DocumentProcessingError(Exception):
    """Base exception for document processing errors"""

class InvalidFileError(DocumentProcessingError):
    """Raised when file validation fails"""

class ModelResponseError(DocumentProcessingError):
    """Raised when model returns invalid response""" 
