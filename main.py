import os
from fastapi import FastAPI, Request
from datetime import datetime
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from utils.agent import FinancialAgent
from utils.models import (
    JSONRPCRequest,
    JSONRPCResponse,
    TaskResult,
    TaskStatus,
    A2AMessage,
    MessagePart,
    MessageParams,
    ExecuteParams
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
        
        if rpc_request.method == "message/send":
            if not isinstance(rpc_request.params, MessageParams):
                params = MessageParams(**rpc_request.params)
            else:
                params = rpc_request.params
            
            message = params.message
            message_id = message.messageId
            task_id = message.taskId or str(uuid4())
            
            for part in message.parts:
                if part.kind == "text" and part.text:
                    user_input = part.text
                    break
        
        elif rpc_request.method == "execute":
            if not isinstance(rpc_request.params, ExecuteParams):
                params = ExecuteParams(**rpc_request.params)
            else:
                params = rpc_request.params
            
            task_id = params.taskId or str(uuid4())
            context_id = params.contextId or str(uuid4())
            
            if params.messages:
                last_message = params.messages[-1]
                for part in last_message.parts:
                    if part.kind == "text" and part.text:
                        user_input = part.text
                        break
        
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

        result_text = await agent.process_messages(user_input)
        
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
            history=[]
        )
        
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