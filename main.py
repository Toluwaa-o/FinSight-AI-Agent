import os
import httpx
from fastapi import FastAPI, Request
from datetime import datetime
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from utils.utils import convert_history_to_a2a, send_webhook_notification
from utils.agent import FinancialAgent
from utils.models import (
    JSONRPCRequest,
    JSONRPCResponse,
    TaskResult,
    TaskStatus,
    A2AMessage,
    MessagePart,
    MessageParams,
    ExecuteParams,
)
from uuid import uuid4

load_dotenv()

agent = FinancialAgent()

app = FastAPI(
    title="Financial Comparison Agent",
    description="An AI Agent that compares two companies' financial performance using Yahoo Finance data, supporting A2A protocol.",
    version="1.0.0"
)


@app.get("/")
def check_server():
    return {"msg": "Server running. Use POST / for A2A protocol."}


@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": "financial_comparison"}


@app.post("/a2a/financial")
async def a2a_endpoint(rpc_request: JSONRPCRequest):
    """A2A protocol endpoint following JSON-RPC 2.0 specification"""
    try:
        user_input = None
        task_id = None
        context_id = None
        message_id = None

        print("method: " + rpc_request.method)
        if rpc_request.method == "message/send":
            if not isinstance(rpc_request.params, MessageParams):
                params = MessageParams(**rpc_request.params)
            else:
                params = rpc_request.params

            print(f"params: {params}")
            message = params.message
            message_id = message.messageId
            task_id = getattr(message, "taskId", None) or str(uuid4())

            user_input = None
            conversation_history = []

            for part in message.parts:
                if part.kind == "text" and getattr(part, "text", None):
                    user_input = part.text
                elif part.kind == "data" and getattr(part, "data", None):
                    for data_item in part.data:
                        if data_item.kind == "text" and getattr(data_item, "text", None):
                            conversation_history.append(data_item.text)

            print(f"user_input: {user_input}")
            print(f"conversation_history: {conversation_history[:3]} ...")

        elif rpc_request.method == "execute":
            if not isinstance(rpc_request.params, ExecuteParams):
                params = ExecuteParams(**rpc_request.params)
            else:
                params = rpc_request.params

            task_id = getattr(params, "taskId", None) or str(uuid4())
            context_id = getattr(params, "contextId", None) or str(uuid4())

            user_input = None
            if getattr(params, "messages", None):
                last_message = params.messages[-1]
                for part in last_message.parts:
                    if part.kind == "text" and getattr(part, "text", None):
                        user_input = part.text
                        break

            print(f"user_input: {user_input}")

        else:
            return JSONRPCResponse(
                id=rpc_request.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {rpc_request.method}"
                }
            )

        if not user_input:
            return JSONRPCResponse(
                id=rpc_request.id,
                error={
                    "code": -32602,
                    "message": "Invalid params: No text input found in message"
                }
            )

        print(f"Starting agent communication, string: {user_input}")
        result_text, history = await agent.process_messages(user_input)
        print(f"result: {result_text}")

        if isinstance(result_text, dict) and "error" in result_text:
            return JSONRPCResponse(
                id=rpc_request.id,
                error={
                    "code": -32603,
                    "message": "Agent processing error",
                    "data": result_text
                }
            )

        # Generate IDs if not provided
        context_id = context_id or str(uuid4())
        task_id = task_id or str(uuid4())

        # Create response message
        response_message = A2AMessage(
            role="agent",
            parts=[MessagePart(kind="text", text=str(result_text))],
            taskId=task_id
        )

        # Create task result
        task_result = TaskResult(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(
                state="completed",
                message=response_message
            ),
            artifacts=[],
            history=convert_history_to_a2a(history)
        )

        if hasattr(params.configuration, "pushNotificationConfig") and params.configuration.pushNotificationConfig:
            webhook_url = params.configuration.pushNotificationConfig.url
            if webhook_url:
                await send_webhook_notification(webhook_url, task_result)
                return JSONRPCResponse(
                    id=rpc_request.id,
                    result=task_result
                )
        else:
            return JSONRPCResponse(
                id=rpc_request.id,
                result=task_result
            )

    except ValueError as e:
        return JSONRPCResponse(
            id=rpc_request.id if hasattr(rpc_request, 'id') else "unknown",
            error={
                "code": -32602,
                "message": "Invalid params",
                "data": {"details": str(e)}
            }
        )
    except Exception as e:
        return JSONRPCResponse(
            id=rpc_request.id if hasattr(rpc_request, 'id') else "unknown",
            error={
                "code": -32603,
                "message": "Internal error",
                "data": {"details": str(e)}
            }
        )
