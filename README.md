# AI-Powered Resume Parser and Candidate Analysis System

## Project Overview
This project is an intelligent resume parsing and candidate analysis system that leverages Google's Gemini AI to automate and enhance the recruitment process. The system extracts structured information from resumes, analyzes candidate profiles, and provides an AI-powered HR assistant for candidate evaluation.

### Key Features
- **Intelligent Resume Parsing**: Automatically extracts structured information from various resume formats (PDF, DOCX, TXT)
- **Candidate Analysis**: Ranks and compares candidates based on skills, experience, and requirements
- **HR Assistant**: AI-powered chatbot for candidate evaluation and interview preparation
- **Modern Web Interface**: Clean and intuitive user interface for managing candidates

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Node.js and npm (for frontend development)
- Google Cloud account with Gemini API access

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/resume-parser-ai.git
cd resume-parser-ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```
GEMINI_API_KEY=your_api_key_here
```

5. Start the application:
```bash
uvicorn main:app --reload
```

6. Access the application at `http://localhost:8000`

## System Architecture

### AI Architecture Diagram
```
[Resume Input] → [Resume Parser (Gemini AI)] → [Data Extraction]
       ↓                    ↓                          ↓
[PDF/DOCX/TXT] → [Text Processing] → [Structured Data] → [Candidate Database]
       ↓                    ↓                          ↓
[HR Assistant (Gemini AI)] ← [Candidate Analysis] ← [Data Validation]
       ↓                    ↓                          ↓
[Chat Interface] → [Response Generation] → [Candidate Rankings]
```

### Components
1. **Resume Parser**
   - Uses Gemini AI for text extraction
   - Handles multiple file formats
   - Extracts structured information

2. **Candidate Analyzer**
   - Processes candidate data
   - Ranks candidates
   - Generates comparisons

3. **HR Assistant**
   - Natural language processing
   - Candidate evaluation
   - Interview preparation

4. **Web Interface**
   - Modern React-based UI
   - Real-time chat
   - Candidate management

## Usage Examples

### Resume Upload
1. Navigate to the upload section
2. Select a resume file (PDF, DOCX, or TXT)
3. Click "Upload"
4. View parsed information in the candidate list

### HR Assistant
Example queries:
- "Who is the most skilled in Python?"
- "Rank candidates for an AI role"
- "Compare education backgrounds"
- "Suggest interview questions for candidate #1"

## Assumptions and Limitations

### Assumptions
- Resumes are in English
- Files are in supported formats (PDF, DOCX, TXT)
- Internet connection for AI API access
- Valid Google Cloud API key

### Limitations
- Maximum file size: 10MB
- Supported languages: English only
- Limited to text-based information extraction
- No image or table parsing
- Requires manual verification of extracted data

## Future Improvements

### Planned Features
1. **Enhanced Parsing**
   - Support for more file formats
   - Image and table extraction
   - Multi-language support

2. **Advanced Analysis**
   - Skill gap analysis
   - Salary recommendations
   - Team fit prediction

3. **Integration**
   - ATS system integration
   - Calendar integration for interviews
   - Email notification system

4. **UI/UX**
   - Dark mode
   - Mobile app
   - Advanced filtering
   - Export functionality

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Google Gemini AI
- FastAPI
- React
- All contributors

## Contact
For questions and support, please open an issue in the GitHub repository.