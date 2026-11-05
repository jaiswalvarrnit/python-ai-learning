# Assignment 1: Health API
# Easy

# Build a /health endpoint.

# Return:
# {
#   "status": "healthy",
#   "application": "AI Backend",
#   "version": "1.0"
# }

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "application": "AI Backend",
        "version": "1.0"
    }

# Assignment 2: Echo API
# Medium

# Build a /echo POST endpoint.

# Requirements:
# - Accept message, user and timestamp.
# - Validate the request using Pydantic.
# - Message must not be empty.
# - Return the received values.
# - Return a suitable error for invalid input.

class EchoRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    user: str = Field(min_length=2)
    timestamp: str

@app.post("/echo")
async def echo(request: EchoRequest):

    return {
        "received_message": request.message,
        "received_user": request.user,
        "received_timestamp": request.timestamp
    }


# - Assignment 3: External API Integration
#   Medium
  
#   Build a /users/{user_id} endpoint.
# Requirements:
# - Use HTTPX AsyncClient.
# - Fetch a user from JSONPlaceholder.
# - Return their name, email and city.
# - Handle HTTP errors properly.

# https://jsonplaceholder.typicode.com/users/1?utm_source=chatgpt.com

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    url = f"https://jsonplaceholder.typicode.com/users/{user_id}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found") from exc
        raise HTTPException(
            status_code=502,
            detail="User service returned an error",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach user service",
        ) from exc

    user = response.json()
    return {
        "name": user["name"],
        "email": user["email"],
        "city": user["address"]["city"],
    }


# Assignment 4: Dockerize
# Challenge

# - Create a Dockerfile.
# - Build the image.
# - Run the container.
# - Test both endpoints from your browser or Postman.

