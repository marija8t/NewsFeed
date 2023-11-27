"""
update_database.py

This module defines the database schema, initializes the database, and provides functions for
adding users, handling likes and dislikes, and updating the database with top news items.

Dependencies:
- datetime: Provides functions for working with dates and times.
- logging: Logging library for error tracking.
- sqlalchemy: SQL toolkit and Object-Relational Mapping (ORM) for database interactions.
- requests: HTTP library for making requests.

Usage:
- Run this file to initialize the database schema and update it with the latest top news items.

Database Schema:
- NewsItem: Represents a news item with various properties such as title, author, URL, etc.
- User: Represents a user with a unique username, email, and admin status.
- LikesAndDislikes: Represents the likes and dislikes of users for news items.

Functions:
- get_news_item(item_id): Retrieves details of a news item by its ID from the Hacker News API.
- add_user(username, email): Adds a new user to the database or returns the existing user.
- add_like_dislike(email, news_item_id, like): Adds or updates a user's like or dislike for a
news item.

"""
import datetime
import logging
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests

logging.basicConfig(filename='update_database.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

Base = declarative_base()

# pylint: disable=too-few-public-methods
class NewsItem(Base):
    """
    Database model for storing information about a news item.

    Attributes:
    - id (int): Unique identifier for the news item.
    - title (str): Title of the news item.
    - by (str): Author of the news item.
    - url (str): URL of the news item.
    - descendants (int): Number of comments on the news item.
    - score (int): Score of the news item.
    - time (int): Timestamp of the news item.
    - text (str): Text content of the news item.
    """
    __tablename__ = "news_item"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    by = Column(String)
    url = Column(String)
    descendants = Column(Integer)
    score = Column(Integer)
    time = Column(Integer)
    text = Column(String)

class User(Base):
    """
    Database model for storing information about a user.

    Attributes:
    - id (int): Unique identifier for the user.
    - username (str): Unique username for the user.
    - email (str): Unique email address for the user.
    - admin (bool): Admin status of the user (default is False).
    """
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    admin = Column(Boolean, default=False)

class LikesAndDislikes(Base):
    """
    Database model for storing user preferences for news items.

    Attributes:
    - id (int): Unique identifier for the likes and dislikes entry.
    - user_id (int): Foreign key referencing the User table for the user associated
    with the preference.
    - news_item_id (int): Foreign key referencing the NewsItem table for the news item
    associated with the preference.
    - like (bool): Like status (True for like, False for dislike).
    """
    __tablename__ = 'likes_and_dislikes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    news_item_id = Column(Integer, ForeignKey('news_item.id'), nullable=False)
    like = Column(Boolean, nullable=False)

# Database setup
engine = create_engine('sqlite:////home/marija8t/project_part2/news_database.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Function to get news item
def get_news_item(item_id):
    """
    Fetches a news item from the Hacker News API based on the provided item ID.

    Parameters:
    - item_id (int): The unique identifier of the news item.

    Returns:
    - dict or None: A dictionary containing information about the news item if it exists,
    or None if not found.
    """
    news_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json?print=pretty"
    response = requests.get(news_url)
    if response.status_code == 200:
        news_data = response.json()
        if 'title' in news_data and 'by' in news_data and 'url' in news_data:
            return {
                'id': news_data['id'],
                'title': news_data['title'],
                'by': news_data['by'],
                'url': news_data.get('url', ''),
                'descendants': news_data.get('descendants', 0),
                'score': news_data.get('score', 0),
                'time': news_data.get('time', 0),
                'text': news_data.get('text', '')
            }
    return None

def add_user(username, email):
    """
    Adds a new user to the database.

    Parameters:
    - username (str): The username of the new user.
    - email (str): The email address of the new user.

    Returns:
    - dict: A dictionary containing information about the added user.

    Raises:
    - Exception: Raises an exception if an error occurs during user addition.
    """
    saved_users = 0
    try:
        with Session() as session:
            existing_user = session.query(User).filter_by(email=email).first()
            if existing_user:
                return {'username': existing_user.username, 'email': existing_user.email,
                        'admin': existing_user.admin}

            #Create a new user and then add to the database
            new_user = User(username=username, email=email)
            session.add(new_user)
            session.commit()
            saved_users += 1
            return {'username': new_user.username, 'email': new_user.email, 'admin': new_user.admin}

    except Exception as exception:
        raise Exception(f"Could not add user: {str(exception)}")

def add_like_dislike(email, news_item_id, like):
    """
    Handles user likes or dislikes for a news item.

    Parameters:
    - email (str): The email address of the user providing the like or dislike.
    - news_item_id (int): The ID of the news item.
    - like (bool): True if the user likes, False if dislikes.

    Returns:
    - bool: True if the like or dislike is successfully processed, False otherwise.
    """
    with Session() as session:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            return False

        # Check if the user has already liked or disliked this news item
        existing_record = session.query(
            LikesAndDislikes).filter_by(user_id=user.id, news_item_id=news_item_id).first()
        if existing_record:
            if existing_record.like == like:
                session.delete(existing_record)
            else:
                existing_record.like = like
        else:
            new_like_dislike = LikesAndDislikes(user_id=user.id,
                                                news_item_id=news_item_id, like=like)
            session.add(new_like_dislike)

        try:
            session.commit()
            return True
        except Exception as exception:
            raise Exception(f"Could not add user: {str(exception)}")

# Fetch the list of top story IDs
TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty"
RESPONSE = requests.get(TOP_STORIES_URL)
if RESPONSE.status_code == 200:
    TOP_STORY_IDS = RESPONSE.json()[:50]  # Only first 50 items
    SAVED_ITEMS = 0
    for item_id in TOP_STORY_IDS:
        news_data = get_news_item(item_id)
        if news_data:
            # Check if the item with the same ID already exists in the database
            if not session.query(NewsItem).filter(NewsItem.id == item_id).first():
                # Create a news item object and save it to the database
                news_item = NewsItem(
                    id=news_data['id'],
                    title=news_data['title'],
                    by=news_data['by'],
                    url=news_data['url'],
                    descendants=news_data['descendants'],
                    score=news_data['score'],
                    time=news_data['time'],
                    text=news_data['text']
                    # Add more properties as needed based on the JSON structure
                )
                session.add(news_item)
                SAVED_ITEMS += 1

    session.commit()
    print(f"{SAVED_ITEMS} items saved to the database at {datetime.datetime.now()}")
else:
    print("Failed to fetch top story IDs.")
