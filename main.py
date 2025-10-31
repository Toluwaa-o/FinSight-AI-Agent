import os
from fastapi import FastAPI, Request
from datetime import datetime
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from utils.agent import FinancialAgent

load_dotenv()

agent = FinancialAgent()

app = FastAPI(
    title="Financial Comparison Agent",
    description="An AI Agent that compares two companies' financial performance using Yahoo Finance data, supporting A2A protocol.",
    version="1.0.0"
)


class JSONRPCRequest(BaseModel):
    jsonrpc: str
    id: str
    method: str
    params: dict


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    result: dict = None
    error: dict = None


@app.get("/")
def check_server():
    return {"msg": "Server running. Use /a2a/financial to call the A2A endpoint."}


@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": "financial_comparison"}


@app.post("/a2a/financial")
async def a2a_endpoint(request: Request):
    try:
        body = await request.json()

        # Validate JSON-RPC format
        if body.get("jsonrpc") != "2.0" or "id" not in body:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: jsonrpc must be '2.0' and id is required"
                    }
                }
            )

        rpc_request = JSONRPCRequest(**body)

        user_input = None
        message_id = None
        task_id = None
        
        if rpc_request.method == "message/send":
            message = rpc_request.params.get("message", {})
            parts = message.get("parts", [])
            message_id = message.get("messageId", f"msg-{datetime.utcnow().timestamp()}")
            task_id = message.get("taskId", f"task-{datetime.utcnow().timestamp()}")
            
            if parts and parts[0].get("kind") == "text":
                user_input = parts[0].get("text")
        elif rpc_request.method == "execute":
            user_input = rpc_request.params.get("input")
            task_id = rpc_request.params.get("taskId", f"task-{datetime.utcnow().timestamp()}")

        if not user_input:
            raise ValueError(
                "Missing 'input' or 'message.parts[0].text' in params")

        result_text = await agent.process_messages(user_input)

        # Generate context ID (you might want to manage this persistently)
        context_id = f"context-{datetime.utcnow().timestamp()}"
        
        response = {
            "jsonrpc": "2.0",
            "id": rpc_request.id,
            "result": {
                "id": task_id,
                "contextId": context_id,
                "status": {
                    "state": "completed",  # or "input-required" if you need more user input
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "message": {
                        "messageId": f"msg-response-{datetime.utcnow().timestamp()}",
                        "role": "agent",
                        "parts": [
                            {
                                "kind": "text",
                                "text": result_text
                            }
                        ],
                        "kind": "message",
                        "taskId": task_id
                    }
                },
                "artifacts": [],  # Add artifacts here if you have any (charts, files, etc.)
                "history": [],    # Add conversation history if you're tracking it
                "kind": "task"
            }
        }

        return JSONResponse(content=response)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": body.get("id") if "body" in locals() else None,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)}
                }
            }
        )
