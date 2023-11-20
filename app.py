from flask import Flask, jsonify, render_template, session, redirect, url_for
from update_database import NewsItem, Session, add_user, LikesAndDislikes, User, add_like_dislike
from datetime import datetime
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
import logging
import math
from sqlalchemy import func, case

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
    session = Session()
    offset = (page - 1) * per_page
    #latest_news_query = session.query(NewsItem).order_by(NewsItem.id.desc())
    
    # Subquery for aggregated data
    likes_dislikes_subq = session.query(
            LikesAndDislikes.news_item_id,
            func.coalesce(func.sum(case((LikesAndDislikes.like == True, 1), else_=0)), 0).label('total_likes'),
            func.coalesce(func.sum(case((LikesAndDislikes.like == False, 1), else_=0)), 0).label('total_dislikes')
        ).group_by(LikesAndDislikes.news_item_id).subquery()

    # join NewsItem with aggregated likes/dislikes
    latest_news_query = session.query(NewsItem, likes_dislikes_subq.c.total_likes, likes_dislikes_subq.c.total_dislikes
            ).outerjoin(
                    likes_dislikes_subq, NewsItem.id == likes_dislikes_subq.c.news_item_id
            ).order_by(
                    likes_dislikes_subq.c.total_likes.desc(),
                    likes_dislikes_subq.c.total_dislikes.desc(),
                    NewsItem.time.desc()
            )

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
    if 'user' not in session:
        app.logger.error("User not in session.")
        return redirect(url_for('login'))

    email = session.get('user', {}).get('userinfo', {}).get('email')
    if not email:
        app.logger.error("User email, {email},  not found in session.")
        return redirect(url_for('home', error="User not logged in"))

    if add_like_dislike(email, news_item_id, like):
        return redirect(url_for('home'))
    else:
        app.logger.error(f"Failed to add like/dislike for user {user_email}")
        # Handle the error case, perhaps displaying a message to the user
        return redirect(url_for('home', error="Unable to process like/dislike"))

def get_like_dislike_counts(news_item_id):
    with Session() as session:
        totals = session.query(
            LikesAndDislikes.news_item_id,
            func.sum(case((LikesAndDislikes.like == True, 1), else_=0)).label('total_likes'),
            func.sum(case((LikesAndDislikes.like == False, 1), else_=0)).label('total_dislikes')
        ).filter(LikesAndDislikes.news_item_id == news_item_id).group_by(LikesAndDislikes.news_item_id).first()

        if totals:
            return {'likes': totals.total_likes, 'dislikes': totals.total_dislikes}
        else:
            return {'likes': 0, 'dislikes': 0}


@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    return datetime.utcfromtimestamp(value).strftime(format)

#Error Checking
app.logger.setLevel(logging.ERROR)
file_handler = logging.FileHandler("/home/marija8t/project_part2/error.log")
app.logger.addHandler(file_handler)

#ROUTES
@app.route('/sessioncheck')
def session_check():
    with open('/home/marija8t/project_part2/session_data.txt', 'w') as f:
        json.dump(dict(session), f, indent=2)
    return "Session data written to file."

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
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
            app.logger.info(f"User {user.email} deleted successfully.")
        else:
            app.logger.error(f"User ID {user_id} not found.")

    return redirect(url_for('admin'))


@app.route('/make_admin/<user_email>')
def make_admin_route(user_email):
    # This should be protected and only accessible to you
    make_user_admin(user_email)
    return f"Made {user_email} an admin."

def make_user_admin(email):
    with Session() as session:
        user = session.query(User).filter_by(email=email).first()
        if user:
            user.admin = True
            session.commit()
            app.logger.info(f"User {email} set as admin.")
        else:
            app.logger.error(f"User {email} not found.")

@app.route('/admin')
def admin():
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
    return handle_like_dislike(news_item_id, True)

@app.route('/dislike/<int:news_item_id>', methods=['POST'])
def dislike_news_item(news_item_id):
    return handle_like_dislike(news_item_id, False)


@app.route('/profiles')
def profile():
    return render_template('profiles.html', session=session.get('user'))


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token

    if session.get("user"):
        nonce = session.get('nonce')
        user_info=oauth.auth0.parse_id_token(token, nonce=nonce)
        username=user_info.get("name")
        email=user_info.get("email")

        add_user(username, email)
        # Query the User table for the admin status
        with Session() as db_session:
            user = db_session.query(User).filter_by(email=email).first()
            if user:
                session['user']['admin'] = user.admin
                app.logger.info(f"Set admin status for {email}: {user.admin}")
            else:
                app.logger.error(f"User {email} not found in database for admin status.")
        session.pop('nonce', None)

    return redirect("/")

@app.route("/logout")
def logout():
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
    news_feed, total  = get_home_feed(page)
    total_pages = math.ceil(total / 10)
    return render_template('home.html', news_feed=news_feed, total_pages=total_pages, current_page=page, session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

# Route to get latest 'k' news items
@app.route('/newsfeed', methods=['GET'])
def get_news_feed():
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

