from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, ForwardRef
from datetime import datetime
import re

class Education(BaseModel):
    institution: str = Field(..., description="Name of the educational institution")
    degree: str = Field(..., description="Degree type (e.g., B.S., M.S., Ph.D.)")
    field_of_study: str = Field(default="Not specified", description="Major or specialization")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="GPA on a 4.0 scale")

    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        if v is None:
            return v
        try:
            # Try to parse the date
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            # If parsing fails, try to extract year and month
            year_match = re.search(r'\d{4}', v)
            month_match = re.search(r'\d{2}', v)
            if year_match and month_match:
                return f"{year_match.group()}-{month_match.group()}-01"
            return None

    @validator('gpa')
    def validate_gpa(cls, v):
        if v is None:
            return v
        try:
            if isinstance(v, str):
                # Handle various GPA formats
                v = v.lower()
                if 'out of' in v:
                    v = v.split('out of')[0].strip()
                elif '/' in v:
                    v = v.split('/')[0].strip()
                v = float(v)
            if not 0.0 <= v <= 4.0:
                return None
            return round(v, 2)
        except (ValueError, TypeError):
            return None

class WorkExperience(BaseModel):
    company: str = Field(..., description="Name of the company")
    position: str = Field(..., description="Job title or position")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    description: str = Field(default="", description="Job responsibilities and achievements")

    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        if v is None:
            return v
        try:    
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            year_match = re.search(r'\d{4}', v)
            month_match = re.search(r'\d{2}', v)
            if year_match and month_match:
                return f"{year_match.group()}-{month_match.group()}-01"
            return None

class Resume(BaseModel):
    first_name: str = Field(..., min_length=1, description="Person's first name")
    last_name: str = Field(..., min_length=1, description="Person's last name")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    education: List[Education] = Field(default_factory=list, description="List of education entries")
    work_experience: List[WorkExperience] = Field(default_factory=list, description="List of work experience entries")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    current_position: str = Field(default="", description="Current job position")
    years_of_experience: float = Field(default=0.0, ge=0.0, description="Total years of work experience")

    @validator('email')
    def validate_email(cls, v):
        if not v:
            return "not.provided@example.com" 
        v = v.strip().lower()
        if '@' in v and '.' in v.split('@')[1]:
            return v
        if '@' in v:
            parts = v.split('@')
            if len(parts) == 2 and '.' not in parts[1]:
                return f"{parts[0]}@{parts[1]}.com"
        return f"{v.replace(' ', '.').lower()}@example.com"

    @validator('phone')
    def validate_phone(cls, v):
        if not v:
            return "0000000000"
        digits = re.sub(r'\D', '', v)
        if len(digits) < 10:
            return "0000000000"
        return digits

    @validator('skills')
    def validate_skills(cls, v):
        if v is None:
            return []
        return list(dict.fromkeys(skill.strip().lower() for skill in v if skill.strip()))

    @validator('education')
    def validate_education(cls, v):
        if v is None:
            return []
        return sorted(v, key=lambda x: x.end_date if x.end_date else "9999-12-31", reverse=True)

    @validator('work_experience')
    def validate_work_experience(cls, v):
        if v is None:
            return []
        return sorted(v, key=lambda x: x.end_date if x.end_date else "9999-12-31", reverse=True)

    @validator('years_of_experience')
    def validate_years_of_experience(cls, v):
        if v is None:
            return 0.0
        try:
            years = float(v)
            return max(0.0, years)
        except (ValueError, TypeError):
            return 0.0

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, description="User's message")
    candidate_id: Optional[str] = Field(None, description="ID of the candidate being discussed")

class CandidateRanking(BaseModel):
    candidate_id: str = Field(..., description="Unique identifier for the candidate")
    name: str = Field(..., description="Candidate's full name")
    score: float = Field(..., ge=0.0, le=100.0, description="Overall score (0-100)")
    match_percentage: float = Field(..., ge=0.0, le=100.0, description="Match percentage with the query")
    reasoning: str = Field(..., description="Explanation for the ranking")
    relevant_skills: List[str] = Field(default_factory=list, description="List of relevant skills")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI's response")
    rankings: Optional[List[CandidateRanking]] = Field(None, description="Ranked candidates if applicable") 