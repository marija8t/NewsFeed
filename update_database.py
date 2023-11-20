from sqlalchemy import create_engine, Column, String, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests
import datetime
import logging

logging.basicConfig(filename='update_database.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

Base = declarative_base()

class NewsItem(Base):
    __tablename__ = "news_item"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    by = Column(String)
    url = Column(String)
    descendants = Column(Integer)
    score = Column(Integer)
    time = Column(Integer)
    text = Column(String)
    # Add more columns as needed based on the JSON structure

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    admin = Column(Boolean, default=False)

class LikesAndDislikes(Base):
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
                # Add more properties as needed based on the JSON structure
            }
    return None

def add_user(username, email):
    saved_users=0
    try:
        with Session() as session:
            existing_user = session.query(User).filter_by(email=email).first()
            if existing_user:
                logging.info(f"User with email {email} already exists. Skipping insertion.")
                return {'username': existing_user.username, 'email': existing_user.email, 'admin': existing_user.admin}

            #Create a new user and then add to the database
            new_user = User(username=username, email=email)
            session.add(new_user)
            session.commit()
            saved_users += 1
            logging.info(f"New user added with username {username}.")
            logging.info(f"{saved_users} users saved to the database at {datetime.datetime.now()}")
            return {'username': new_user.username, 'email': new_user.email, 'admin': new_user.admin}

    except Exception as e:
        logging.error(f"Error adding user: {e}")
        raise

def add_like_dislike(email, news_item_id, like):
    with Session() as session:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            logging.error(f"User with email {email} not found in add_like_dislike")
            return False

        # Check if the user has already liked or disliked this news item
        existing_record = session.query(LikesAndDislikes).filter_by(user_id=user.id, news_item_id=news_item_id).first()
        if existing_record:
            logging.info(f"exists")
            existing_record.like = like
        else:
            print(f"Exists {email}")
            logging.info(f"adding add_like_dislike")
            logging.error(f"adding add_like_dislike")
            new_like_dislike = LikesAndDislikes(user_id=user.id, news_item_id=news_item_id, like=like)
            session.add(new_like_dislike)

        try:
            print(f"Commiting {email}")
            logging.info(f"User with email found in add_like_dislike")
            logging.error(f"User with email found in add_like_dislike")
            session.commit()
            return True
        except Exception as e:
            logging.error(f"Error in add_like_dislike for user {email} and news item ID {news_item_id}: {e}")
            return False

# Fetch the list of top story IDs
top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty"
response = requests.get(top_stories_url)
if response.status_code == 200:
    top_story_ids = response.json()[:50]  # Only first 50 items
    saved_items = 0
    for item_id in top_story_ids:
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
                saved_items += 1

    session.commit()
    print(f"{saved_items} items saved to the database at {datetime.datetime.now()}")
else:
    print("Failed to fetch top story IDs.")
