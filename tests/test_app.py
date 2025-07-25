import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from app.main import app, url_database, db_lock # Ensure these imports are correct based on your structure
from app.utils import is_valid_url, generate_short_code # Import for direct utility testing

@pytest.fixture
def client():
    # Configure app for testing
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Clear the in-memory database before each test to ensure isolation
        with db_lock:
            url_database.clear()
        yield client # This is where the testing happens
    # No explicit cleanup needed for in-memory after yield, as it's cleared before next test

# --- Core Functionality Tests (Examples, you can add more) ---

def test_health_check(client):
    """Test the root health check endpoint returns 200 OK and expected status."""
    response = client.get('/')
    assert response.status_code == 200
    assert response.json == {"status": "healthy", "service": "URL Shortener API"}

def test_api_health(client):
    """Test the /api/health endpoint returns 200 OK and expected message."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json == {"status": "ok", "message": "URL Shortener API is running"}

# --- 10 Specific Test Cases ---

def test_1_shorten_url_success_new_url(client):
    """1. Test shortening a brand new, valid URL returns a 201 Created status."""
    long_url = "https://www.example.com/new/test/url/1"
    response = client.post('/api/shorten', json={"url": long_url})
    assert response.status_code == 201
    assert response.json['status'] == 'ok'
    assert 'short_code' in response.json
    assert 'short_url' in response.json
    with db_lock:
        assert response.json['short_code'] in url_database
        assert url_database[response.json['short_code']]['long_url'] == long_url
        assert url_database[response.json['short_code']]['clicks'] == 0 # Newly created URL should have 0 clicks initially

def test_2_shorten_url_existing_increments_clicks(client):
    """2. Test shortening an already existing URL increments its click count and returns 200 OK."""
    long_url = "https://www.example.com/existing/url/2"
    client.post('/api/shorten', json={"url": long_url}) # First shorten

    response = client.post('/api/shorten', json={"url": long_url}) # Shorten again
    assert response.status_code == 200
    assert response.json['status'] == 'ok'
    assert response.json['message'] == "URL already shortened and click count incremented"
    with db_lock:
        short_code = response.json['short_code']
        assert url_database[short_code]['clicks'] == 1 # Initial 0 + 1 from this POST

def test_3_shorten_url_invalid_format(client):
    """3. Test POST /api/shorten with an invalid URL format returns 400 Bad Request."""
    response = client.post('/api/shorten', json={"url": "not-a-valid-url"})
    assert response.status_code == 400
    assert response.json['status'] == 'error'
    assert "Invalid URL format" in response.json['message']

def test_4_shorten_url_missing_url_key(client):
    """4. Test POST /api/shorten with missing 'url' key in JSON body returns 400 Bad Request."""
    response = client.post('/api/shorten', json={"not_url": "some_value"})
    assert response.status_code == 400
    assert response.json['status'] == 'error'
    assert "URL not provided" in response.json['message']

def test_5_shorten_url_malformed_json(client):
    """5. Test POST /api/shorten with non-JSON Content-Type returns 415 Unsupported Media Type."""
    response = client.post('/api/shorten', data="this is not json", content_type='text/plain')
    # When Content-Type is not 'application/json', Flask's request.get_json() automatically
    # raises a 415 error before your custom validation code (if not data...) is reached.
    assert response.status_code == 415
    # The response body for a 415 error from Flask is typically HTML, not JSON.
    # So, we cannot assert on `response.json`. Instead, check the text content.
    assert "Unsupported Media Type" in response.get_data(as_text=True)

def test_6_redirect_increments_clicks_and_redirects(client):
    """6. Test GET /<short_code> correctly increments click count and redirects to original URL."""
    long_url = "https://www.google.com/search?q=test_redirect"
    shorten_response = client.post('/api/shorten', json={"url": long_url})
    short_code = shorten_response.json['short_code']

    redirect_response = client.get(f'/{short_code}')
    assert redirect_response.status_code == 302 # Expected redirect status
    assert redirect_response.headers['Location'] == long_url # Verify redirection target

    # Check analytics to confirm click count increment
    stats_response = client.get(f'/api/stats/{short_code}')
    assert stats_response.status_code == 200
    assert stats_response.json['clicks'] == 1 # 0 from initial POST + 1 from this GET redirect

def test_7_get_stats_multiple_clicks(client):
    """7. Test GET /api/stats/<short_code> accurately reflects multiple clicks."""
    long_url = "https://www.github.com/test_clicks"
    shorten_response = client.post('/api/shorten', json={"url": long_url})
    short_code = shorten_response.json['short_code']

    # Simulate multiple clicks
    client.get(f'/{short_code}')
    client.get(f'/{short_code}')
    client.get(f'/{short_code}')

    stats_response = client.get(f'/api/stats/{short_code}')
    assert stats_response.status_code == 200
    assert stats_response.json['url'] == long_url
    assert stats_response.json['clicks'] == 3 # 0 from initial POST + 3 from GET redirects
    assert 'created_at' in stats_response.json

def test_8_get_stats_non_existent_code(client):
    """8. Test GET /api/stats/<short_code> for a non-existent short code returns 404 Not Found."""
    response = client.get('/api/stats/nonexistentcode123')
    assert response.status_code == 404
    assert response.json['status'] == 'error'
    assert "Short code not found" in response.json['message']

def test_9_short_code_length_and_composition(client):
    """9. Test that generated short codes are always 6 characters long and alphanumeric."""
    long_url = "https://www.test.com/length_check"
    response = client.post('/api/shorten', json={"url": long_url})
    assert response.status_code == 201
    short_code = response.json['short_code']
    assert len(short_code) == 6
    assert short_code.isalnum() # Checks if all characters are alphanumeric

def test_10_long_url_with_query_params_preserved(client):
    """10. Test that a long URL with query parameters and fragments is preserved correctly."""
    long_url_with_params = "https://example.com/page?param1=value1&param2=value2#section"
    response = client.post('/api/shorten', json={"url": long_url_with_params})
    assert response.status_code == 201
    short_code = response.json['short_code']

    # Retrieve stats to verify the stored long URL
    stats_response = client.get(f'/api/stats/{short_code}')
    assert stats_response.status_code == 200
    assert stats_response.json['url'] == long_url_with_params # Ensure params and fragment are identical