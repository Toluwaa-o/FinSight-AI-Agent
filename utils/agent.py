import os
from uuid import uuid4
from typing import List, Optional
from dotenv import load_dotenv
from openai import OpenAI

from models.a2a import (
    A2AMessage, TaskResult, TaskStatus, Artifact,
    MessagePart, MessageConfiguration
)

from .utils import chat

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")

client = OpenAI(api_key=GOOGLE_API_KEY, base_url=BASE_URL)


class FinancialAgent:
    def __init__(self):
        """Initialize financial comparison agent"""
        self.client = client
        self.model = MODEL

    async def process_messages(
        self,
        messages: List[A2AMessage],
        context_id: Optional[str] = None,
        task_id: Optional[str] = None,
        config: Optional[MessageConfiguration] = None
    ) -> TaskResult:
        """Processes messages and generates financial comparisons."""

        context_id = context_id or str(uuid4())
        task_id = task_id or str(uuid4())

        user_message = messages[-1] if messages else None
        if not user_message:
            raise ValueError("No message provided")

        input_text = ""
        for part in user_message.parts:
            if part.kind == "text":
                input_text = part.text.strip()
                break

        if not input_text:
            raise ValueError("No valid text input found in message")

        try:
            response_text = chat(self.client, self.model, input_text, history=[])
        except Exception as e:
            response_text = f"Error processing request: {e}"

        response_message = A2AMessage(
            role="agent",
            parts=[MessagePart(kind="text", text=response_text)],
            taskId=task_id
        )

        artifacts = [
            Artifact(
                name="financial_comparison",
                parts=[MessagePart(kind="text", text=response_text)]
            )
        ]

        result = TaskResult(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(state="completed", message=response_message),
            artifacts=artifacts,
            history=messages + [response_message]
        )

        return result

    async def cleanup(self):
        """Clean up any cached data (if needed)"""
        pass
