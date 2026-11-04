import httpx
import asyncio

response = httpx.get(
    "https://jsonplaceholder.typicode.com/users/1"
)

print(response.status_code)
print(response.json())

async def get_user():

    async with httpx.AsyncClient() as client:

        response = await client.get(
            "https://jsonplaceholder.typicode.com/users/1"
        )

        print(response.status_code)
        print(response.json())

asyncio.run(get_user())

async def fetch_user(client, user_id):

    response = await client.get(
        f"https://jsonplaceholder.typicode.com/users/{user_id}"
    )

    response.raise_for_status()

    return response.json()

async def main():

    async with httpx.AsyncClient() as client:

        users = await asyncio.gather(
            fetch_user(client, 1),
            fetch_user(client, 2),
            fetch_user(client, 3)
        )

        for user in users:
            print(user["name"])

asyncio.run(main())