class FinancialAgent:
    def __init__(self):
        pass

    async def process_messages(self, user_input: str):
        """Process text input and return the comparison result"""
        from .utils import chat
        from openai import OpenAI
        import os
        from dotenv import load_dotenv

        load_dotenv()
        client = OpenAI(
            api_key=os.getenv("GOOGLE_API_KEY"),
            base_url=os.getenv("BASE_URL")
        )
        model = os.getenv("MODEL")

        try:
            result = chat(client, model, user_input, [])
            return result
        except Exception as e:
            return {"error": str(e)}