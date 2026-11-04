from pydantic import BaseModel,EmailStr, Field
import json

class User(BaseModel):
    name: str
    age: int
    email: str

class NewUser(BaseModel):
    name: str = Field(min_length=2)
    age: int = Field(gt=18, lt=100)
    email: str

user = User(
    name="Varrnit",
    age=56,
    email="varrnit@example.com"
)

print(user)

user2 = NewUser(
    name="Varr",
    age="25",
    email="varrnit@example.com"
)


print(user2)



class Employee(BaseModel):
    name: str
    age: int
    department: str

json_data = """
{
    "name": "Varrnit",
    "age": 25,
    "department": "Engineering"
}
"""

employee = Employee.model_validate_json(json_data)

print(employee.name)
print(employee.age)

