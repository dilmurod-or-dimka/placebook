from datetime import datetime
from email.policy import default

from sqlalchemy import Table, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, MetaData, DATETIME
from sqlalchemy.sql import func

metadata = MetaData()


users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("firstname", String),
    Column("lastname", String),
    Column("email", String, unique=True, index=True),
    Column("hashed_password", String),
    Column("phone_number", String, unique=True),
    Column("is_admin", Boolean,default=False),
    Column("is_active", Boolean, default=True),
    Column("activation_code", Integer),
    Column("created_at", DateTime, default=datetime.utcnow()),
)

restaurant_owner = Table(
    'restaurants_owner',
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("restaurant_id", Integer, ForeignKey("restaurants.id")),
    Column("owner_id", Integer, ForeignKey("users.id")),
)


restaurant = Table(
    "restaurants",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, index=True),
    Column("address", String),
    Column("phone_number", String),
    Column("number_of_people", Integer),
    Column("seats_left", Integer),
    Column("is_open", Boolean, default=True),
    Column("description", String),
    Column('coordinates',String),
    Column('photo',String),
    Column("created_at", DateTime, default=datetime.utcnow()),
    Column('chat_id', Integer, nullable=True),
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
    Column('restaurant_id', Integer, ForeignKey('restaurants.id')),
    Column("name", String, unique=True, index=True)
)


MenuItem = Table(
    "menu_items",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column('food_categories_id', Integer, ForeignKey('food_categories.id')),
    Column("name", String),
    Column("description", String),
    Column("price", Float),
    Column("image_url", String),
    Column('created_at', DateTime, default=datetime.utcnow()),
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
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("is_active", Boolean, default=False)
)

FavoriteRestaurant = Table(
    "favorite_restaurants",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("restaurant_id", Integer, ForeignKey("restaurants.id"), nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)

Notification = Table(
    "notifications",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("message", String),
    Column("is_read", Boolean, default=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)
