from datetime import datetime
from typing import Optional

from fastapi import UploadFile, File
from pydantic import BaseModel


class UserInfo(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: str
    phone_number:str
    is_admin: bool
    is_active: bool
    created_at: datetime

class RestaurantModel(BaseModel):
    id:int
    name: str
    address: str
    phone_number: str
    number_of_people: int
    seats_left: int
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


class ReviewBase(BaseModel):
    restaurant_id: int
    rating: int
    comment: Optional[str] = None

class ReviewResponse(ReviewBase):
    id: int
    created_at: datetime

class HomePageModel(BaseModel):
    id: int
    name:str
    address:str
    phone_number:str
    number_of_people:int
    description:str


class OwnerInfo(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: str
    phone_number: str

class FoodItemModel(BaseModel):
    id: int
    name:str
    price: float
    description:str
    photo:str
