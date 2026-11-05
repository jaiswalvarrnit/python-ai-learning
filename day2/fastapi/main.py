from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

@app.get("/health")
async def health_check():

    return {
        "status": "healthy",
        "message": "Application is running"
    }

class EchoRequest(BaseModel):

    message: str = Field(min_length=1, max_length=500)
    user: str = Field(min_length=2)

@app.post("/echo")
async def echo(request: EchoRequest):

    return {
        "received_message": request.message,
        "received_user": request.user,
        "status": "success"
    }