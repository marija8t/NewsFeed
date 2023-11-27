import json
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_get_news_feed(client):
    response = client.get('/newsfeed')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 302  # Redirects to Auth0 login page

def test_logout_page(client):
    response = client.get('/logout')
    assert response.status_code == 302  # Redirects to Auth0 logout page

def test_profile_page(client):
    response = client.get('/profiles')
    assert response.status_code == 200

def test_admin_page(client):
    response = client.get('/admin')
    assert response.status_code == 302  # Redirects to home page if not an admin

def test_session_check(client):
    response = client.get('/sessioncheck')
    assert response.status_code == 200

def test_delete_user(client):
    response = client.post('/delete_user/1')
    assert response.status_code == 302  # Redirects to login page if not an admin

def test_make_admin_route(client):
    response = client.get('/make_admin/test@example.com')
    assert response.status_code == 200

def test_like_news_item(client):
    response = client.post('/like/1')
    assert response.status_code == 302  # Redirects to login page if not authenticated

def test_dislike_news_item(client):
    response = client.post('/dislike/1')
    assert response.status_code == 302  # Redirects to login page if not authenticated

def test_home_page_with_page_param(client):
    response = client.get('/page/2')
    assert response.status_code == 200

def test_home_page_with_invalid_page_param(client):
    response = client.get('/page/invalid')
    assert response.status_code == 404

def test_error_logging():
    # You can add a test to check if error logging works as expected
    # This might require modifying the app to expose the logger or error log file path
    pass

