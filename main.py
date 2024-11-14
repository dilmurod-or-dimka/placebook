from fastapi import FastAPI, APIRouter

import account.auth
import account.admin
import account.restaurant
import account.orders
app = FastAPI()
router = APIRouter()
app.include_router(router)
app.include_router(account.auth.router)
app.include_router(account.admin.router)
app.include_router(account.restaurant.router)
app.include_router(account.orders.router)