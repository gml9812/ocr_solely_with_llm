import os
from src.config import Settings
from fastapi import UploadFile

class FileValidator:
    def __init__(self, config: Settings):
        self.config = config

    def validate(self, file: UploadFile) -> None:
        self._validate_type(file)
        self._validate_size(file)

    def _validate_type(self, file: UploadFile) -> None:
        file_extension = os.path.splitext(file.filename)[1].lower()
        content_type = file.content_type
        
        if content_type not in self.config.allowed_file_types:
            raise InvalidFileError(f"Invalid content type: {content_type}")
            
        if file_extension not in self.config.allowed_file_types[content_type]:
            raise InvalidFileError(f"Invalid extension for {content_type}")

    def _validate_size(self, file: UploadFile) -> None:
        max_bytes = self.config.max_file_size_mb * 1024 * 1024
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
        
        if size > max_bytes:
            raise InvalidFileError(f"File exceeds {self.config.max_file_size_mb}MB limit") 