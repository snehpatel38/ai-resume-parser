import google.generativeai as genai
from models import Resume, Education, WorkExperience
import os
from dotenv import load_dotenv
import json
from typing import Dict, Any, List
import logging
import PyPDF2
import docx
import io
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configure Gemini API
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=api_key)

# Initialize the model
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    logger.error(f"Failed to initialize Gemini API: {str(e)}")
    raise Exception(f"Failed to initialize Gemini API: {str(e)}")

class ResumeParser:
    def __init__(self):
        self.model = model
        self.system_prompt = """
        You are an expert resume parser with deep understanding of various resume formats and structures.
        Your task is to extract structured information from resumes with high accuracy.
        Follow these strict guidelines:
        1. Extract all available information accurately
        2. Format dates consistently (YYYY-MM-DD)
        3. Clean and normalize all text fields
        4. Convert GPA to float if possible
        5. Calculate years_of_experience based on work history
        6. Extract current_position from most recent work experience
        7. Normalize skills (remove duplicates, standardize format)
        8. Ensure all required fields are present
        9. Handle missing or incomplete information gracefully
        10. Maintain data consistency and quality
        """

    def extract_text_from_file(self, file_content: bytes, file_type: str) -> str:
        """Extract text from different file formats."""
        try:
            if file_type == 'application/pdf':
                pdf_file = io.BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
            elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                docx_file = io.BytesIO(file_content)
                doc = docx.Document(docx_file)
                return "\n".join([paragraph.text for paragraph in doc.paragraphs])
            elif file_type == 'text/plain':
                return file_content.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}")
            raise Exception(f"Error extracting text from file: {str(e)}")

    def clean_text(self, text: str) -> str:
        """Clean and normalize the extracted text."""
        text = ' '.join(text.split())
        text = re.sub(r'[^\w\s@.-]', ' ', text)
        return text

    def validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the extracted data."""
        try:
            if not data.get('first_name'):
                data['first_name'] = "Not Provided"
            if not data.get('last_name'):
                data['last_name'] = "Not Provided"
            if not data.get('email'):
                data['email'] = "not.provided@example.com"
            if not data.get('phone'):
                data['phone'] = "0000000000"

            email = data.get('email', '').strip()
            if not email:
                data['email'] = "not.provided@example.com"
            else:
                email = email.lower()
                if '@' not in email:
                    data['email'] = f"{email.replace(' ', '.')}@example.com"
                elif '.' not in email.split('@')[1]:
                    data['email'] = f"{email}.com"

            phone = data.get('phone', '').strip()
            if not phone:
                data['phone'] = "0000000000"
            else:
                digits = re.sub(r'\D', '', phone)
                data['phone'] = digits if len(digits) >= 10 else "0000000000"

            education = data.get('education', [])
            if not isinstance(education, list):
                education = []
            for edu in education:
                if not edu.get('institution'):
                    edu['institution'] = "Not Specified"
                if not edu.get('degree'):
                    edu['degree'] = "Not Specified"
                if not edu.get('field_of_study'):
                    edu['field_of_study'] = "Not Specified"
                if edu.get('gpa'):
                    try:
                        if isinstance(edu['gpa'], str):
                            edu['gpa'] = edu['gpa'].lower()
                            if 'out of' in edu['gpa']:
                                edu['gpa'] = edu['gpa'].split('out of')[0].strip()
                            elif '/' in edu['gpa']:
                                edu['gpa'] = edu['gpa'].split('/')[0].strip()
                        edu['gpa'] = float(edu['gpa'])
                        if not 0.0 <= edu['gpa'] <= 4.0:
                            edu['gpa'] = None
                    except (ValueError, TypeError):
                        edu['gpa'] = None
                for date_field in ['start_date', 'end_date']:
                    if edu.get(date_field):
                        edu[date_field] = self.clean_date(edu[date_field])
            data['education'] = education

            work_experience = data.get('work_experience', [])
            if not isinstance(work_experience, list):
                work_experience = []
            for exp in work_experience:
                if not exp.get('company'):
                    exp['company'] = "Not Specified"
                if not exp.get('position'):
                    exp['position'] = "Not Specified"
                exp['description'] = str(exp.get('description', '')).strip()
                for date_field in ['start_date', 'end_date']:
                    if exp.get(date_field):
                        exp[date_field] = self.clean_date(exp[date_field])
            data['work_experience'] = work_experience

            skills = data.get('skills', [])
            if not isinstance(skills, list):
                skills = []
            normalized_skills = []
            for skill in skills:
                skill = str(skill).strip().lower()
                if skill and skill not in normalized_skills:
                    normalized_skills.append(skill)
            data['skills'] = normalized_skills

            data['current_position'] = str(data.get('current_position', '')).strip() or "Not Specified"
            try:
                data['years_of_experience'] = float(data.get('years_of_experience', 0.0))
            except (ValueError, TypeError):
                data['years_of_experience'] = 0.0

            return data
        except Exception as e:
            logger.error(f"Error in validate_and_clean_data: {str(e)}")
            return {
                'first_name': data.get('first_name', 'Not Provided'),
                'last_name': data.get('last_name', 'Not Provided'),
                'email': data.get('email', 'not.provided@example.com'),
                'phone': data.get('phone', '0000000000'),
                'education': [],
                'work_experience': [],
                'skills': [],
                'current_position': 'Not Specified',
                'years_of_experience': 0.0
            }

    def clean_date(self, date_str: str) -> str:
        """Clean and standardize date format."""
        if not date_str:
            return None
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            year_match = re.search(r'\d{4}', date_str)
            month_match = re.search(r'\d{2}', date_str)
            if year_match and month_match:
                return f"{year_match.group()}-{month_match.group()}-01"
            return None

    def parse_resume(self, file_content: bytes, file_type: str) -> Resume:
        """Parse resume using Gemini LLM."""
        try:
            text = self.extract_text_from_file(file_content, file_type)
            text = self.clean_text(text)

            # Create prompt for Gemini
            prompt = f"""
            {self.system_prompt}

            Extract structured information from the following resume text. Return the data in JSON format.

            Resume Text:
            {text}

            Required fields and their formats:
            1. first_name (string): Person's first name
            2. last_name (string): Person's last name
            3. email (string): Any valid email format (e.g., user@domain.com, user.name@domain.co.uk)
            4. phone (string): Any valid phone format (e.g., +1-234-567-8900, (123) 456-7890)
            5. education (array of objects):
               - institution (string): School/University name
               - degree (string): Degree type (e.g., B.S., M.S., Ph.D., Bachelor's, Master's)
               - field_of_study (string): Major or specialization
               - start_date (string): Any date format (will be normalized)
               - end_date (string): Any date format (will be normalized)
               - gpa (number): Any GPA format (will be normalized to 4.0 scale)
            6. work_experience (array of objects):
               - company (string): Company name
               - position (string): Job title
               - start_date (string): Any date format (will be normalized)
               - end_date (string): Any date format (will be normalized)
               - description (string): Job responsibilities and achievements
            7. skills (array of strings): Technical and professional skills
            8. current_position (string): Most recent job title
            9. years_of_experience (number): Total years of work experience

            Important guidelines:
            1. Be flexible with date formats - extract what you can
            2. Be flexible with GPA formats - convert to 4.0 scale if possible
            3. Normalize skills (remove duplicates, standardize format)
            4. Order work experience by date (most recent first)
            5. Order education by date (most recent first)
            6. Clean and normalize all text fields
            7. Handle missing or incomplete information gracefully
            8. Ensure all required fields are present
            9. Return only valid JSON data

            Example response format:
            {{
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "1234567890",
                "education": [
                    {{
                        "institution": "University of Example",
                        "degree": "Bachelor of Science",
                        "field_of_study": "Computer Science",
                        "start_date": "2018-09",
                        "end_date": "2022-05",
                        "gpa": 3.8
                    }}
                ],
                "work_experience": [
                    {{
                        "company": "Tech Corp",
                        "position": "Software Engineer",
                        "start_date": "2022-06",
                        "end_date": "2023-12",
                        "description": "Developed and maintained web applications"
                    }}
                ],
                "skills": ["Python", "JavaScript", "React"],
                "current_position": "Software Engineer",
                "years_of_experience": 1.5
            }}

            Return ONLY the JSON object, nothing else.
            """

            # Get response from Gemini
            logger.info("Sending request to Gemini API for resume parsing")
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.error("Empty response from Gemini API")
                raise Exception("Empty response from Gemini API")
            
            # Parse the response
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.text)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from code block: {json_match.group(1)}")
                        raise Exception("Failed to parse JSON from code block")
                else:
                    start_idx = response.text.find('{')
                    end_idx = response.text.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        try:
                            data = json.loads(response.text[start_idx:end_idx])
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse JSON from response: {response.text}")
                            raise Exception("Failed to parse JSON from response")
                    else:
                        logger.error(f"No valid JSON found in response: {response.text}")
                        raise Exception("No valid JSON found in response")

            # Validate and clean the data
            data = self.validate_and_clean_data(data)

            # Convert to Resume object
            return Resume(**data)

        except Exception as e:
            logger.error(f"Failed to parse resume: {str(e)}")
            raise Exception(f"Failed to parse resume: {str(e)}") 