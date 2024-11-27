from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

ESKIZ_EMAIL = "ramzanyak0024@gmail.com"
ESKIZ_PASSWORD = "Ez2NEamYcSbHvzRSobSC1f1ztCFunriu7SP5hBOn"
ESKIZ_API_URL = "https://notify.eskiz.uz"


# Function to get Eskiz access token
async def get_access_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ESKIZ_API_URL}/api/auth/login",
            data={
                "email": ESKIZ_EMAIL,
                "password": ESKIZ_PASSWORD,
            },
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Authentication failed")
        return response.json().get("data", {}).get("token")


# Function to send SMS
async def send_sms(phone_number: str, message: str):
    token = await get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ESKIZ_API_URL}/api/message/sms/send",
            headers=headers,
            data={
                "mobile_phone": phone_number,
                "message": message,
                "from": "Mirzabek",  # Replace with your sender name or ID from Eskiz
            },
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
