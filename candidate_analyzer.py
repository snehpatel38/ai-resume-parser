import google.generativeai as genai
from models import Resume, CandidateRanking
import os
from dotenv import load_dotenv
import json
from typing import Dict, List, Any
import logging
import re

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

class CandidateAnalyzer:
    def __init__(self):
        self.model = model
        self.candidates: Dict[str, Resume] = {}

    def add_candidate(self, candidate_id: str, resume: Resume):
        """Add a candidate to the analyzer."""
        self.candidates[candidate_id] = resume
        logger.info(f"Added candidate {candidate_id} to analyzer")

    def get_candidate_summary(self, candidate_id: str) -> str:
        """Get a summary of a candidate's profile."""
        resume = self.candidates.get(candidate_id)
        if not resume:
            return "Candidate not found"

        summary = f"""
        Name: {resume.first_name} {resume.last_name}
        Current Position: {resume.current_position}
        Years of Experience: {resume.years_of_experience}
        Skills: {', '.join(resume.skills)}
        Education: {', '.join([f"{edu.degree} in {edu.field_of_study} from {edu.institution}" for edu in resume.education])}
        """
        return summary

    def rank_candidates(self, query: str) -> List[CandidateRanking]:
        """Rank candidates based on the given query using Gemini."""
        try:
            if not self.candidates:
                logger.warning("No candidates available for ranking")
                return []

            # Create a summary of all candidates
            candidates_summary = "\n\n".join([
                f"Candidate {candidate_id}:\n{self.get_candidate_summary(candidate_id)}"
                for candidate_id in self.candidates.keys()
            ])

            # Create prompt for Gemini
            prompt = f"""
            You are an expert HR recruiter. Analyze the following candidates and rank them based on the query.
            Return the results in JSON format.

            Query: {query}

            Candidates:
            {candidates_summary}

            Instructions:
            1. Analyze each candidate's profile
            2. Rank them based on relevance to the query
            3. Provide a score (0-100) and match percentage
            4. List relevant skills that match the query
            5. Provide reasoning for the ranking
            6. Return results in the exact format shown below

            Required JSON format:
            [
                {{
                    "candidate_id": "",
                    "name": "",
                    "score": 0.0,
                    "match_percentage": 0.0,
                    "reasoning": "",
                    "relevant_skills": []
                }}
            ]

            Important guidelines:
            1. Score should be between 0 and 100
            2. Match percentage should be between 0 and 100
            3. Only include skills that are relevant to the query
            4. Provide clear reasoning for the ranking
            5. Consider both explicit skills and experience
            6. Order candidates from highest to lowest score

            Return ONLY the JSON array, nothing else.
            """

            # Get response from Gemini
            logger.info("Sending request to Gemini API for candidate ranking")
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.error("Empty response from Gemini API")
                raise Exception("Empty response from Gemini API")
            
            # Parse the response
            try:
                rankings = self.parse_ranking_response(response.text)
            except Exception as e:
                logger.error(f"Failed to parse ranking response: {str(e)}")
                raise Exception(f"Failed to parse ranking response: {str(e)}")

            # Convert to CandidateRanking objects
            return [
                CandidateRanking(
                    candidate_id=rank["candidate_id"],
                    name=rank["name"],
                    score=rank["score"],
                    match_percentage=rank["match_percentage"],
                    reasoning=rank["reasoning"],
                    relevant_skills=rank["relevant_skills"]
                )
                for rank in rankings
            ]

        except Exception as e:
            logger.error(f"Failed to rank candidates: {str(e)}")
            raise Exception(f"Failed to rank candidates: {str(e)}")

    def parse_ranking_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the ranking response from Gemini."""
        try:
            # First try parsing the entire response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from markdown code block
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
                if json_match:
                    try:
                        return json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from code block: {json_match.group(1)}")
                        raise Exception("Failed to parse JSON from code block")
                else:
                    # Try to find JSON content if there's any surrounding text
                    start_idx = response.find('[')
                    end_idx = response.rfind(']') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        try:
                            return json.loads(response[start_idx:end_idx])
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse JSON from response: {response}")
                            raise Exception("Failed to parse JSON from response")
                    else:
                        logger.error(f"No valid JSON found in response: {response}")
                        raise Exception("No valid JSON found in response")
        except Exception as e:
            logger.error(f"Failed to parse ranking response: {str(e)}")
            raise Exception(f"Failed to parse ranking response: {str(e)}")

    def get_candidate_by_id(self, candidate_id: str) -> Resume:
        """Get a candidate's resume by ID."""
        resume = self.candidates.get(candidate_id)
        if not resume:
            raise ValueError(f"Candidate {candidate_id} not found")
        return resume

    def get_all_candidates(self) -> List[Resume]:
        """Get all candidates' resumes."""
        return list(self.candidates.values()) 