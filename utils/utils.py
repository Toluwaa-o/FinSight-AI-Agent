import yfinance as yf
from .data import compare_companies_json, system_prompt
from .models import A2AMessage, MessagePart, TaskResult
from typing import Optional, Dict, Any
import json
import re
from uuid import uuid4
import httpx


def compare_companies(ticker1: str, ticker2: str) -> dict:
    """
    Compare two companies' financial performance using Yahoo Finance data.
    Includes error handling for invalid tickers, missing data, and network issues.

    Args:
        ticker1 (str): Stock ticker symbol of the first company (e.g., 'AAPL')
        ticker2 (str): Stock ticker symbol of the second company (e.g., 'MSFT')

    Returns:
        dict: A summary comparison including key metrics and basic insight, 
              or an error message if something fails.
    """
    try:
        if not ticker1 or not ticker2:
            return {"error": "Both ticker symbols must be provided."}

        c1 = yf.Ticker(ticker1).info
        c2 = yf.Ticker(ticker2).info

        if not c1 or "shortName" not in c1:
            return {"error": f"Could not retrieve data for '{ticker1}'. Please check the ticker symbol."}
        if not c2 or "shortName" not in c2:
            return {"error": f"Could not retrieve data for '{ticker2}'. Please check the ticker symbol."}

        metrics = [
            "shortName", "sector", "marketCap", "currentPrice",
            "revenueGrowth", "grossMargins", "profitMargins",
            "trailingPE", "dividendYield"
        ]

        company1_data = {m: c1.get(m, "N/A") for m in metrics}
        company2_data = {m: c2.get(m, "N/A") for m in metrics}

        insight = (
            f"{company1_data['shortName']} vs {company2_data['shortName']}\n"
            f"Sector: {company1_data['sector']} | {company2_data['sector']}\n"
            f"Market Cap: {company1_data['marketCap']} | {company2_data['marketCap']}\n"
            f"Profit Margin: {company1_data['profitMargins']} | {company2_data['profitMargins']}\n"
            f"P/E Ratio: {company1_data['trailingPE']} | {company2_data['trailingPE']}\n"
            f"Dividend Yield: {company1_data['dividendYield']} | {company2_data['dividendYield']}\n"
        )

        return {
            "insight": insight,
        }

    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


tools = [
    {"type": "function", "function": compare_companies_json}
]


def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name

        arguments = json.loads(tool_call.function.arguments)

        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}

        results.append({"role": "tool", "content": json.dumps(
            result), "tool_call_id": tool_call.id})

    return results


def is_comparison_query(text: str) -> bool:
    """
    Detects whether a user's input is a comparison-type query.

    Args:
        text (str): The user's input message.

    Returns:
        bool: True if it seems to be a comparison query, False otherwise.
    """

    comparison_patterns = [
        r"\bbetter\b",
        r"\bworse\b",
        r"\bcompare\b",
        r"\bcomparing\b",
        r"\bcomparison\b",
        r"\bversus\b",
        r"\bvs\b",
        r"\bvs\.\b",
        r"\bagainst\b",
        r"\bbetween\b",
        r"\bdifference\s+(between|of)\b",
        r"\bhow\s+does\b.*\bcompare\b.*\bto\b",
        r"\bhow\s+do\b.*\bcompare\b",
        r"\bwhich\s+(is|has|performs|does)\b.*\b(better|worse|higher|lower|more|less)\b",
        r"\b(is|are)\s+(better|worse|higher|lower|more|less)\b",
        r"\bthan\b",
        r"\brelative\s+to\b",
        r"\bversus\s+each\s+other\b",
        r"\bcompare\s+(the|these|those)\b",
        r"\bhow\s+different\s+(is|are)\b"
    ]

    combined_pattern = "|".join(comparison_patterns)
    return bool(re.search(combined_pattern, text, flags=re.IGNORECASE))


def chat(client, model, message, history):
    try:
        if not is_comparison_query(message):
            return (
                "This AI Agent is designed only for comparing two companies.\n\n"
                "Example inputs:\n"
                "- Compare Apple and Microsoft\n"
                "- How does Tesla compare to Ford?\n"
                "- Which is better, Google or Amazon?\n\n"
                "Please rephrase your request to include two companies for comparison."
            )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        done = False
        while not done:
            response = client.chat.completions.create(
                model=model, messages=messages, tools=tools
            )

            choice = response.choices[0]
            finish_reason = choice.finish_reason

            if finish_reason == 'tool_calls':
                message_obj = choice.message
                tool_calls = message_obj.tool_calls
                results = handle_tool_calls(tool_calls)
                messages.append(message_obj)
                messages.extend(results)
            else:
                done = True
                assistant_message = choice.message
                messages.append(assistant_message)

                history.append({"role": "user", "content": message})
                history.append(
                    {"role": "assistant", "content": assistant_message.content}
                )

                return assistant_message.content, history

    except Exception as e:
        return f"An error occurred while processing your request: {e}"


def convert_history_to_a2a(history):
    """Convert history list into valid A2AMessage objects for JSON-RPC response."""
    a2a_messages = []
    for msg in history:
        role = msg["role"]
        if role == "assistant":
            role = "agent"
        elif role not in ["user", "agent", "system"]:
            role = "system"

        a2a_messages.append(
            A2AMessage(
                kind="message",
                role=role,
                parts=[MessagePart(kind="text", text=msg["content"])],
                messageId=str(uuid4())
            )
        )
    return a2a_messages


async def send_webhook_notification(
    webhook_url: str,
    result: TaskResult,
    auth: Optional[Dict[str, Any]] = None
):
    """Send result to webhook URL"""
    headers = {"Content-Type": "application/json"}

    if auth and auth.get("schemes") == ["TelexApiKey"]:
        headers["Authorization"] = f"Bearer {auth.get('credentials')}"

    async with httpx.AsyncClient() as client:
        await client.post(
            webhook_url,
            json=result.model_dump(),
            headers=headers
        )
