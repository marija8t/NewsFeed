"""
NewsFeed App

This module implements a Flask web application for displaying and interacting with a news feed.
It integrates with Auth0 for user authentication and provides features such as liking/disliking
news items, user administration, and user profiles.

Dependencies:
- Flask: Web framework for building the application.
- SQLAlchemy: SQL toolkit and Object-Relational Mapping (ORM) for database interactions.
- Authlib: Library for handling OAuth authentication, specifically with Auth0.
- Dotenv: Load environment variables from a .env file.
- JSON: Handling JSON data.
- OS: Provides a way of using operating system-dependent functionality.
- urllib.parse: Parse URLs.
- Math: Mathematical functions.
- Datetime: Manipulate dates and times.
- Logging: Logging library for error tracking.

Usage:
- Run the application by executing this file.
- Access the web interface at the root URL ("/").
- Implements various routes for user authentication, news feed display, liking/disliking news items,
user administration, etc.
"""
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
import math
from datetime import datetime
import logging
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, jsonify, render_template, session, redirect, url_for
from sqlalchemy import func, case
from update_database import NewsItem, Session, add_user, LikesAndDislikes, User, add_like_dislike

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

#Auth0
oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

def get_home_feed(page, per_page=10):
    """
    Retrieve a paginated list of news items with aggregated likes and dislikes.

    Parameters:
    - page (int): Page number to retrieve.
    - per_page (int, optional): Number of items per page (default is 10).

    Returns:
    Tuple[List[Dict[str, Any]], int]: Paginated news items and total count.

    Each news item is represented as a dictionary with keys:
    - 'id' (int): Unique identifier.
    - 'title' (str): Title.
    - 'by' (str): Author.
    - 'url' (str): URL.
    - 'descendants' (int): Number of comments.
    - 'score' (int): Item score.
    - 'time' (int): Timestamp.
    - 'text' (str): Text content.
    - 'likes' (int): Total likes.
    - 'dislikes' (int): Total dislikes.
    """
    session = Session()
    offset = (page - 1) * per_page

    # Subquery for aggregated data
    likes_dislikes_subq = session.query(
        LikesAndDislikes.news_item_id,
        func.coalesce(func.sum(case((LikesAndDislikes.like == True, 1), else_=0)), 0) # pylint: disable=not-callable
        .label('total_likes'),
        func.coalesce(func.sum(case((LikesAndDislikes.like == False, 1), else_=0)), 0) # pylint: disable=not-callable
        .label('total_dislikes')
        ).group_by(LikesAndDislikes.news_item_id).subquery()

    # join NewsItem with aggregated likes/dislikes
    latest_news_query = session.query(NewsItem, likes_dislikes_subq.c.total_likes,
                                      likes_dislikes_subq.c.total_dislikes
                                      ).outerjoin(
                                          likes_dislikes_subq,
                                          NewsItem.id == likes_dislikes_subq.c.news_item_id
                                      ).order_by(
                                          likes_dislikes_subq.c.total_likes.desc(),
                                          likes_dislikes_subq.c.total_dislikes.desc(),
                                          NewsItem.time.desc())

    latest_news_paginated = latest_news_query.offset(offset).limit(per_page).all()

    news_list = []
    for news_item_tuple in latest_news_paginated:
        news_item = news_item_tuple[0]
        total_likes = news_item_tuple[1] if news_item_tuple[1] is not None else 0
        total_dislikes = news_item_tuple[2] if news_item_tuple[2] is not None else 0

        news_list.append({
            'id': news_item.id,
            'title': news_item.title,
            'by': news_item.by,
            'url': news_item.url,
            'descendants': news_item.descendants,
            'score': news_item.score,
            'time': news_item.time,
            'text': news_item.text,
            'likes': total_likes,
            'dislikes': total_dislikes
        })

    session.close()
    total = latest_news_query.count()
    return news_list, total

def handle_like_dislike(news_item_id, like):
    """
    Handle user likes or dislikes for a news item.

    Parameters:
    - news_item_id (int): The ID of the news item.
    - like (bool): True if the user likes, False if dislikes.

    Returns:
    - Redirect: Redirects to the home page or displays an error message.
    """
    if 'user' not in session:
        app.logger.error("User not in session.")
        return redirect(url_for('login'))

    email = session.get('user', {}).get('userinfo', {}).get('email')
    if not email:
        app.logger.error("User email, {email},  not found in session.")
        return redirect(url_for('home', error="User not logged in"))

    if add_like_dislike(email, news_item_id, like):
        return redirect(url_for('home'))

    return redirect(url_for('home', error="Unable to process like/dislike"))

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    """
    Format a timestamp value into a string using the specified format.

    Parameters:
    - value (int): The timestamp value to be formatted.
    - format (str, optional): The format string for the output (default is '%Y-%m-%d %H:%M:%S').

    Returns:
    str: A formatted string representing the timestamp.
    """
    return datetime.utcfromtimestamp(value).strftime(format)

#Error Checking
app.logger.setLevel(logging.ERROR)
FILE_HANDLER = logging.FileHandler("/home/marija8t/project_part2/error.log")
app.logger.addHandler(FILE_HANDLER)

#ROUTES
@app.route('/sessioncheck')
def session_check():
    """
    Write the current session data to a JSON file.

    Returns:
    str: A message indicating that the session data has been written to the file.
    """
    with open('/home/marija8t/project_part2/session_data.txt', 'w') as file_handle:
        json.dump(dict(session), file_handle, indent=2)
    return "Session data written to file."

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """
    Delete a user and associated data by user ID.

    Parameters:
    - user_id (int): The ID of the user to be deleted.

    Returns:
    Redirect: Redirects to the login page if the user is not an admin; otherwise,
    deletes the user and associated data, logs the action, and redirects to the admin page.
    """
    if 'user' not in session or not session['user'].get('admin'):
        return redirect(url_for('login'))

    with Session() as db_session:
        user = db_session.query(User).filter_by(id=user_id).first()
        if user:
            # Delete likes and dislikes first
            db_session.query(LikesAndDislikes).filter_by(user_id=user.id).delete()
            # Now delete user
            db_session.delete(user)
            db_session.commit()
        else:
            app.logger.error("User ID %s not found.", user_id)

    return redirect(url_for('admin'))


@app.route('/make_admin/<user_email>')
def make_admin_route(user_email):
    """
    Grant administrator privileges to a user.

    Parameters:
    - user_email (str): The email address of the user to be granted admin status.

    Returns:
    str: A message confirming the successful elevation of the user to admin status.
    """
    # This should be protected and only accessible to you
    make_user_admin(user_email)
    return f"Made {user_email} an admin."

def make_user_admin(email):
    """
    Set a user with the specified email as an administrator.

    Parameters:
    - email (str): The email address of the user to be granted admin status.

    Returns:
    None
    """
    with Session() as session:
        user = session.query(User).filter_by(email=email).first()
        if user:
            user.admin = True
            session.commit()
        else:
            app.logger.error("User %s not found.", email)

@app.route('/admin')
def admin():
    """
    Display the admin page with a list of all users.

    Returns:
    Redirect: Redirects to the home page if the user is not an admin or not authenticated;
    otherwise, renders the admin page with a list of all users.
    """
    # Accessing the Flask session here
    if 'user' not in session or not session['user'].get('admin'):
        app.logger.error("Non-admin or unauthenticated user attempted to access admin page.")
        return redirect(url_for('home'))

    # Using a different name for the SQLAlchemy session to avoid conflict
    with Session() as db_session:
        users = db_session.query(User).all()
        return render_template('admin.html', users=users)

@app.route('/like/<int:news_item_id>', methods=['POST'])
def like_news_item(news_item_id):
    """
    Handle a user's like action for a specific news item.

    Parameters:
    - news_item_id (int): The ID of the news item to be liked.

    Returns:
    Redirect: Redirects to handle_like_dislike with the specified news item ID and a 'like' action.
    """
    return handle_like_dislike(news_item_id, True)

@app.route('/dislike/<int:news_item_id>', methods=['POST'])
def dislike_news_item(news_item_id):
    """
    Handle a user's dislike action for a specific news item.

    Parameters:
    - news_item_id (int): The ID of the news item to be disliked.

    Returns:
    Redirect: Redirects to handle_like_dislike with the specified
    news item ID and a 'dislike' action.
    """
    return handle_like_dislike(news_item_id, False)


@app.route('/profiles')
def profile():
    """
    Display the user profile page.

    Returns:
    Rendered Template: Renders the 'profiles.html' template with the user session data.
    """
    return render_template('profiles.html', session=session.get('user'))


@app.route("/login")
def login():
    """
    Initiate the OAuth2 authentication process and redirect the user to the authorization endpoint.

    Returns:
    Redirect: Redirects the user to the Auth0 authorization endpoint.
    """
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    """
    Process the OAuth2 callback, handle user information, and set session data.

    Returns:
    Redirect: Redirects to the home page ("/") after processing the OAuth2 callback.

    Notes:
    - Obtains the access token from the Auth0 authorization server.
    - Sets the user session data using the obtained token.
    - Retrieves user information from the ID token and adds the user to the database.
    - Queries the database for the user's admin status and updates the session accordingly.
    - Redirects to the home page after processing the callback.
    """
    token = oauth.auth0.authorize_access_token()
    session["user"] = token

    if session.get("user"):
        nonce = session.get('nonce')
        user_info = oauth.auth0.parse_id_token(token, nonce=nonce)
        username = user_info.get("name")
        email = user_info.get("email")

        add_user(username, email)
        # Query the User table for the admin status
        with Session() as db_session:
            user = db_session.query(User).filter_by(email=email).first()
            if user:
                session['user']['admin'] = user.admin
            else:
                app.logger.error("User %s not found in database for admin status.", email)
        session.pop('nonce', None)

    return redirect("/")

@app.route("/logout")
def logout():
    """
    Clear the user session and initiate the logout process.

    Returns:
    Redirect: Redirects to the Auth0 logout endpoint after clearing the session.

    Notes:
    - Clears all data stored in the user session.
    - Initiates the logout process by redirecting to the Auth0 logout endpoint.
    - Includes the return URL and client ID parameters for a smooth logout experience.
    """
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# Route for the root URL ("/")
@app.route('/')
@app.route('/page/<int:page>')
def home(page=1):
    """
    Display the home page with a paginated news feed.

    Parameters:
    - page (int, optional): Page number to display (default is 1).

    Returns:
    Rendered Template: Renders the 'home.html' template with the paginated
    news feed and session data.
    """
    news_feed, total = get_home_feed(page)
    total_pages = math.ceil(total / 10)
    return render_template('home.html', news_feed=news_feed,
                           total_pages=total_pages, current_page=page, session=session.get('user'),
                           pretty=json.dumps(session.get('user'), indent=4))

# Route to get latest 'k' news items
@app.route('/newsfeed', methods=['GET'])
def get_news_feed():
    """
    Retrieve the latest news items and return them as a JSON response.

    Returns:
    JSON Response: A JSON response containing the details of the latest news items.

    Notes:
    - Queries the database for the latest news items, ordered by ID in descending order.
    - Limits the result to the latest 30 news items.
    - Constructs a list of dictionaries containing details of each news item.
    - Closes the database session after retrieving the data.
    - Returns a JSON response with the list of news items.
    """
    session = Session()
    latest_news = session.query(NewsItem).order_by(NewsItem.id.desc()).limit(30).all()
    news_list = []
    for news_item in latest_news:
        news_list.append({
            'id': news_item.id,
            'title': news_item.title,
            'by': news_item.by,
            'url': news_item.url,
            'descendants': news_item.descendants,
            'score': news_item.score,
            'time': news_item.time,
            'text': news_item.text
        })
    session.close()
    return jsonify(news_list)

if __name__ == '__main__':
    app.run(debug=True)
