from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from utils.agent import call_agent

load_dotenv()

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

        if rpc_request.method == "message/send":
            user_input = rpc_request.params.get("message", {}).get("content")
        elif rpc_request.method == "execute":
            user_input = rpc_request.params.get("input")

        if not user_input:
            raise ValueError("Missing 'input' or 'message.content' in params")

        result_text = call_agent(user_input)

        response = JSONRPCResponse(
            id=rpc_request.id,
            result={
                "status": "success",
                "output": result_text
            }
        )

        return response.model_dump()

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
