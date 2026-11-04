# Assignment 1: Employee JSON Validator
# Easy

# Create a Pydantic model called Employee.

# Requirements:
# - name: String, minimum 3 characters.
# - age: Integer, between 18 and 60.
# - salary: Float, greater than 0.
# - department: String.
# Input JSON:
# {
#   "name": "Rahul",
#   "age": 25,
#   "salary": 1200000,
#   "department": "Engineering"
# }


# Your program should:
# 1. Validate the JSON.
# 2. Print the employee name.
# 3. Print the salary.
# 4. Handle invalid input using try-except.

from pydantic import BaseModel, Field, ValidationError
import json

class Employee(BaseModel):
    name: str = Field(min_length=3)
    age: int = Field(gt=18, lt=60)
    salary: float = Field(gt=0)
    department: str

json_data = """
{
    "name": "Rahul",
    "age": 25,
    "salary": 1200000,
    "department": "Engineering"
}
"""

try:
    employee = Employee.model_validate_json(json_data)
    print(employee.name)
    print(employee.salary)
except ValidationError as e:
    print("Invalid employee data:")
    for error in e.errors():
        print(f" - {error['msg']}")

# 1. Assignment 2: API Response Validator
#    Medium
   
#    Imagine you're receiving a response from an external API.
# {
#   "status": "success",
#   "data": {
#     "user_id": 101,
#     "username": "varrnit",
#     "skills": ["Java", "Python", "AI"]
#   }
# }


# Requirements:
# - Create a Pydantic model for the user.
# - Create another model for the complete API response.
# - Validate the JSON.
# - Print the username.
# - Print all skills using a list comprehension.


class User(BaseModel):
    user_id: int
    username: str
    skills: list[str]

class ApiResponse(BaseModel):
    status: str
    data: User

api_json = """
{
    "status": "success",
    "data": {
        "user_id": 101,
        "username": "varrnit",
        "skills": ["Java", "Python", "AI"]
    }
}
"""

try:
    response = ApiResponse.model_validate_json(api_json)
    print(response.data.username)
    print([skill for skill in response.data.skills])
except ValidationError as e:
    print("Invalid API response:")
    for error in e.errors():
        print(f" - {error['msg']}")

# - Assignment 3: LLM Output Validator
#   Challenge
  
#   This is closer to what you'll do as an AI engineer.
# Imagine an LLM generates a response containing a list of recommended courses.

# Input:
# {
#   "student": "Varrnit",
#   "courses": [
#     {
#       "name": "Python for AI",
#       "duration_hours": 20,
#       "difficulty": "Beginner"
#     },
#     {
#       "name": "Machine Learning",
#       "duration_hours": 40,
#       "difficulty": "Intermediate"
#     }
#   ]
# }


# Requirements:
# - Create a Pydantic model for a course.
# - Create a Pydantic model for the complete response.
# - duration_hours must be greater than zero.
# - difficulty must only accept Beginner, Intermediate or Advanced.
# - Print all course names using list comprehension.
# - Reject invalid JSON data.