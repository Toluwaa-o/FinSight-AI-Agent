from fastapi import FastAPI
from pydantic import BaseModel
from utils.agent import call_agent

app = FastAPI()


@app.get('/')
def check_server():
    return {"msg": "server running. use /agent to call agent"}

class RequestBody(BaseModel):
    input: str

@app.post('/agent')
def agent(req: RequestBody):
    try:
        response = call_agent(req.input)
        return {
            "response": response
        }
    except Exception as e:
        return {
            "error": str(e)
        }
