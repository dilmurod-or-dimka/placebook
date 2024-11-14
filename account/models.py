from datetime import datetime

from sqlalchemy import Table, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, MetaData, DATETIME
from sqlalchemy.sql import func

metadata = MetaData()

# User table
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("firstname", String),
    Column("lastname", String),
    Column("email", String, unique=True, index=True),
    Column("hashed_password", String),
    Column("phone_number", String, unique=True),
    Column("is_admin", Boolean),
    Column("is_active", Boolean, default=True),
    Column("activation_code", Integer),
    Column("created_at", DateTime, default=datetime.utcnow()),
)

# Restaurant table
restaurant = Table(
    "restaurants",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, index=True),
    Column("address", String),
    Column("phone_number", String),
    Column("number_of_people", Integer),
    Column("is_open", Boolean, default=True),
    Column("description", String),
    Column("photo_url", String)
)

restaurants_photos = Table(
    "restaurants_photos",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("restaurant_id", Integer, ForeignKey("restaurants.id"), nullable=False),
    Column("photo_url", String)
)

food_categories = Table(
    "food_categories",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, unique=True, index=True)
)

food_categories_item = Table(
    "food_categories_item",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("category_id", Integer, ForeignKey("food_categories.id"), nullable=False),
    Column("item_id", Integer, ForeignKey("menu_items.id"), nullable=False)
)

MenuItem = Table(
    "menu_items",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("restaurant_id", Integer, ForeignKey("restaurants.id"), nullable=False),
    Column("name", String),
    Column("description", String),
    Column("price", Float),
    Column("image_url", String)
)

Review = Table(
    "reviews",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("restaurant_id", Integer, ForeignKey("restaurants.id"), nullable=False),
    Column("rating", Integer),
    Column("comment", String),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)

Reservation = Table(
    "reservations",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("restaurant_id", Integer, ForeignKey("restaurants.id"), nullable=False),
    Column("reservation_time", DateTime),
    Column("num_people", Integer),
    Column("special_request", String, nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)

# Favorite Restaurant table
FavoriteRestaurant = Table(
    "favorite_restaurants",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("restaurant_id", Integer, ForeignKey("restaurants.id"), nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)

# Notification table
Notification = Table(
    "notifications",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("message", String),
    Column("is_read", Boolean, default=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)
