# Document Analysis with Gemini AI

This project is a FastAPI microservice that processes document images using Google's Gemini AI. It validates incoming files, extracts key information based on user-specified keywords, and returns a structured JSON response with classification results and confidence levels.

## Features

- **Document Classification:** Identify document types (e.g., business license, receipt, invoice, contract, identification document, tax form).
- **Information Extraction:** Automatically extract specified keywords with options for handling null values.
- **File Validation:** Validate file type and size before processing.
- **Robust Error Handling:** Retry mechanism for handling invalid JSON responses from the AI service.
- **Logging:** Detailed logging for debugging and tracking API interactions.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Development](#development)
- [License](#license)

## Installation

### Requirements

- **Python 3.10.x** (as enforced by the setup script)
- [PowerShell](https://docs.microsoft.com/en-us/powershell/) (for running the `setup.ps1` script)
- Other dependencies listed in [requirements.txt](requirements.txt)

### Setup

1. **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python -m venv env
    # On Windows
    env\Scripts\activate
    # On macOS/Linux
    source env/bin/activate
    ```

3. **Run the setup script:**

    ```powershell
    ./setup.ps1
    ```

    This script will:
    - Check that you are running Python 3.10.x.
    - Install the dependencies from `requirements.txt`.

4. **Configure environment variables:**

    Create a `.env` file in the project root with the following contents (adjust as necessary):

    ```
    GOOGLE_API_KEY=your_google_api_key_here
    ALLOWED_FILE_TYPES={"image/jpeg": [".jpg", ".jpeg"], "image/png": [".png"], "application/pdf": [".pdf"]}
    MAX_FILE_SIZE_MB=10
    ```

## Usage

Start the FastAPI server by running:

```bash
python run.py
```

The application will be accessible at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## API Endpoints

### POST `/ocr`

This endpoint processes a document image to determine the document type and extract specified keywords.

**Parameters:**

- **file** (form data): The document file to be processed (supported types: JPEG, PNG, PDF).
- **keywords** (form data): A list of keywords to extract from the document.

**Example Request Using curl:**

```bash
curl -X POST "http://127.0.0.1:8000/ocr" \
  -F "file=@/path/to/your/document.jpg" \
  -F "keywords=keyword1" \
  -F "keywords=keyword2"
```

**Response:**

A successful response will return a JSON object representing the document classification and extracted information. For example:

```json
{
  "category": "invoice",
  "confidence": 0.92,
  "keywords": {
    "keyword1": "extracted_value1",
    "keyword2": null
  }
}
```

## Configuration

- **Environment Variables:**
  - `GOOGLE_API_KEY`: Your API key for the Google Gemini AI service.
  - `ALLOWED_FILE_TYPES`: JSON string specifying allowed MIME types and file extensions.
  - `MAX_FILE_SIZE_MB`: Maximum file size allowed in megabytes.

## Dependencies

See [requirements.txt](requirements.txt) for the list of Python dependencies:

- fastapi>=0.100.0
- uvicorn>=0.22.0
- python-multipart>=0.0.6
- google-genai>=1.0.0
- python-dotenv>=1.0.0
- pydantic>=2.0

## Development

- **Main API Logic:** Implemented in `main.py`.
- **Server Runner:** See `run.py` to start the UVicorn server.
- **Setup Script:** `setup.ps1` ensures proper Python versioning and dependency installation.
- **Logging:** Configured in `main.py` to help track errors and responses from the Gemini AI service.
- **Note:** The functions for validating file size (`validate_file_size`) and keywords (`validate_keywords`) may require further implementation based on your exact requirements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For issues or feature requests, please open an issue in the repository.





cloud run으로 테스트
사전에 user가 제공한 문서양식과 인식된 내용 다를 경우 의견 추가 제공



현재 MDM에서 사용 중인 방식
1--> KeyWord(등록번호, 법인명(단체명), 대표자, 법인등록자....), serviceAuthKey, file_format(.jpg...), language(kr,...), bizLicenseFile을 기입하여 요청 보냄. 

2--> GRP 내 TOBESTAGE.IF_IN_BP_OCR 내에 요청 결과 저장함.(저장시 key는 OCR_TAX_ID_NUM처럼 바꿔서 저장)

3--> TOBESTAGE.IF_IN_BP_OCR에 저장된 형식을 리턴한다고 보면 됨. 


OCR_TAX_ID_NUM(사업자등록번호): 
OCR_BP_NAME_LOCAL(업체명):
OCR_REPRE_NAME(대표자명):
OCR_COMP_REG_NUM(법인등록번호):
OCR_FULL_ADDR_LOCAL(주소):
OCR_BIZ_TYPE(업태):
OCR_INDUSTRY_TYPE(종목): 


cicd 구축 + cloud run 배포
api call 할때 args 수정