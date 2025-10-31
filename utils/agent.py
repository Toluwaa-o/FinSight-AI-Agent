import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class FinancialAgent:
    def __init__(self):
        """Initialize the Financial Agent with OpenAI client"""
        self.client = OpenAI(
            api_key=os.getenv("GOOGLE_API_KEY"),
            base_url=os.getenv("BASE_URL")
        )
        self.model = os.getenv("MODEL")
        
        if not self.client.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        if not self.model:
            raise ValueError("MODEL not found in environment variables")

    async def process_messages(self, user_input: str) -> str:
        """
        Process text input and return the comparison result
        
        Args:
            user_input: The user's question or request as a string
            
        Returns:
            str: The agent's response text
        """
        from .utils import chat, is_comparison_query
        
        try:
            if not user_input or not user_input.strip() or not is_comparison_query(user_input):
                return "Error: Empty input provided. Please ask a question about financial comparison."
            
            result = chat(self.client, self.model, user_input, [])
            print(f"Agent communication finished: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Error processing financial comparison: {str(e)}"
            print(error_msg)
            return error_msg