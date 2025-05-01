import google.generativeai as genai
from models import ChatMessage, ChatResponse, CandidateRanking
from candidate_analyzer import CandidateAnalyzer
import os
from dotenv import load_dotenv
import logging
import json

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

class HRChatbot:
    def __init__(self, candidate_analyzer: CandidateAnalyzer):
        self.model = model
        self.candidate_analyzer = candidate_analyzer
        self.system_prompt = """
        You are an expert HR assistant with deep knowledge of recruitment and candidate evaluation.
        Your task is to help HR professionals find the best candidates for their needs.
        Follow these guidelines:
        1. Be professional and helpful
        2. Provide detailed analysis of candidates
        3. Consider both technical skills and soft skills
        4. Explain your reasoning clearly
        5. Suggest relevant questions for interviews
        6. Highlight key strengths and potential concerns
        7. Consider cultural fit and team dynamics
        8. Provide actionable insights
        """

    def process_message(self, message: ChatMessage) -> ChatResponse:
        """Process a chat message and return a response."""
        try:
            # Get candidate summaries
            candidate_summaries = []
            for candidate_id in self.candidate_analyzer.candidates.keys():
                summary = self.candidate_analyzer.get_candidate_summary(candidate_id)
                candidate_summaries.append(f"Candidate {candidate_id}:\n{summary}")

            # Create prompt for Gemini
            prompt = f"""
            {self.system_prompt}

            User Message: {message.message}

            Available Candidates:
            {'\n\n'.join(candidate_summaries)}

            Instructions:
            1. Analyze the user's request
            2. If they're asking about specific candidates or skills, provide detailed analysis
            3. If they're asking for rankings, explain your reasoning
            4. If they're asking for interview questions, provide relevant questions
            5. If they're asking about team fit, consider both technical and soft skills
            6. Always be professional and helpful
            7. Provide actionable insights

            Return your response in a clear, structured format.
            """

            # Get response from Gemini
            logger.info("Sending request to Gemini API for chat response")
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.error("Empty response from Gemini API")
                raise Exception("Empty response from Gemini API")

            # If the message is about ranking candidates, get rankings
            rankings = None
            if any(keyword in message.message.lower() for keyword in ['rank', 'best', 'top', 'compare', 'who is']):
                try:
                    rankings = self.candidate_analyzer.rank_candidates(message.message)
                except Exception as e:
                    logger.error(f"Failed to get rankings: {str(e)}")
                    # Continue without rankings if they fail

            # Create response
            return ChatResponse(
                response=response.text,
                rankings=rankings
            )

        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            raise Exception(f"Failed to process message: {str(e)}") 