from typing import Optional

from fastapi import UploadFile, File
from pydantic import BaseModel


class RestaurantModel(BaseModel):
    id:int
    name: str
    address: str
    phone_number: str
    number_of_people: int
    is_open: bool
    description: str

class RestaurantUpdateModel(BaseModel):
    restaurant_id: int
    name: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    number_of_people: Optional[int] = None
    description: Optional[str] = None
    photo: Optional[UploadFile] = File(None)


class LoginModel(BaseModel):
    email: str
    password: str