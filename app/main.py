from flask import Flask, jsonify, request, redirect, url_for, abort
from . import utils
from .models import url_database, URLMap 
import threading


app = Flask(__name__)

#  lock for thread-safe access to url_database
db_lock = threading.Lock()

@app.route('/')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "URL Shortener API"
    })

@app.route('/api/health')
def api_health():
    return jsonify({
        "status": "ok",
        "message": "URL Shortener API is running"
    })

@app.route('/api/shorten', methods=['POST'])
def shortenURL():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"status": "error", "message": "URL not provided"}), 400

    long_url = data['url']

    if not utils.is_valid_url(long_url):
        return jsonify({"status": "error", "message": "Invalid URL format"}), 400

# db_lock to ensure thread safety, only a single change will be made at a time
    with db_lock:
        for short_code, url_map_data in url_database.items():
            if url_map_data['long_url'] == long_url:

                url_map_data['clicks'] += 1 
                url_database[short_code] = url_map_data 
                short_url = url_for('redirect_to_long_url', short_code=short_code, _external=True)
                return jsonify({
                    "status": "ok",
                    "short_code": short_code,
                    "short_url": short_url,
                    "message": "URL already shortened"
                }), 200

        # If long URL does not exist, create a new entry
        short_code = utils.generate_short_code()
        
        while short_code in url_database:
            short_code = utils.generate_short_code()

        new_url_map = URLMap(long_url=long_url, short_code=short_code)
        url_database[short_code] = new_url_map.to_dict() 

    short_url = url_for('redirect_to_long_url', short_code=short_code, _external=True)
    return jsonify({
        "status": "ok",
        "short_code": short_code,
        "short_url": short_url
    }), 201 

@app.route('/<short_code>')
def redirect_to_long_url(short_code):
    with db_lock:
        url_map_data = url_database.get(short_code)

    if not url_map_data:
        abort(404)

    with db_lock:
        
        url_map_data['clicks'] += 1
        url_database[short_code] = url_map_data

    return redirect(url_map_data['long_url'])

@app.route('/api/stats/<short_code>')
def get_url_stats(short_code):
    with db_lock:
        url_map_data = url_database.get(short_code)

    if not url_map_data:
        return jsonify({"status": "error", "message": "Short code not found"}), 404

    return jsonify({
        "url": url_map_data['long_url'],
        "clicks": url_map_data['clicks'],
        "created_at": url_map_data['created_at']
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)