from math import e
import os
import json
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, redirect, request
from dotenv import load_dotenv
from requests import get
from collect_trends import get_top10_youtube_data, get_top10_reddit_data, \
                            get_top10_google_data, get_top10_twitter_data, \
                            get_top10_news_data, collect_all_trends, \
                            get_top10_spotify_data, get_twitter_trends_from_trends24, \
                            get_reddit_trends, get_youtube_trends, \
                            get_news_trends, get_spotify_trends, get_google_trends

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Define data directories
data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)

def load_top_trend_data():
    """Load the latest trend data from JSON files"""
    data = {}
    platforms = ['twitter', 'youtube', 'reddit', 'google', 'news', 'spotify']
    
    for platform in platforms:
        try:
            if platform == 'twitter':
                data[platform] = get_top10_twitter_data()
            elif platform == 'youtube':
                data[platform] = get_top10_youtube_data()
            elif platform == 'reddit':
                data[platform] = get_top10_reddit_data()
            elif platform == 'google':
                data[platform] = get_top10_google_data()
            elif platform == 'news':
                data[platform] = get_top10_news_data()
            elif platform == 'spotify':
                data[platform] = get_top10_spotify_data()
                
        except Exception as e:
            print(f"Error loading {platform} data: {e}")
            data[platform] = None
    
    return data

@app.route('/')
def index():
    """Render the main page with trend data"""
    try:
        trend_data = load_top_trend_data()
        current_date = datetime.now().strftime('%B %d, %Y')
        
        # Check if any platform has data
        if all(data is None for data in trend_data.values()):
            print("No existing data found. Collecting trends...")
            collect_all_trends()
            time.sleep(2)
            # Try loading data again after collection
            trend_data = load_top_trend_data()
            
    except Exception as e:
        print(f"Error loading trend data: {e}")
        trend_data = {p: {"trends": [], "last_updated": None} for p in ['twitter', 'youtube', 'reddit', 'google', 'news']}
    
    return render_template('index.html', 
                          trend_data=trend_data,
                          current_date=current_date)

@app.route('/platform/<platform>')
def platform_trends(platform):
    """Display detailed trends for a specific platform"""
    # Update valid platforms
    valid_platforms = ['twitter', 'reddit', 'google', 'youtube', 'news', 'spotify']
    
    # Update platform display names
    platform_display = {
        'twitter': 'Twitter',
        'reddit': 'Reddit',
        'google': 'Google',
        'youtube': 'YouTube',
        'news': 'News',
        'spotify': 'Spotify'
    }.get(platform, platform.capitalize())
    
    # Load trend data for the platform
    try:
        file_path = os.path.join(data_dir, f'{platform}_trends.json')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                trend_data = json.load(f)

    except Exception as e:
        print(f"Error loading {platform} data: {e}")
        trend_data = {"trends": [], "last_updated": None}
    
    return render_template('platform_trends.html', 
                          platform=platform,
                          platform_display=platform_display,
                          trend_data=trend_data)


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500


# New Refresh endpoints
@app.route('/refresh-data', methods=['GET'])
def refresh_all_data():
    """Endpoint to refresh all platform data except Google Trends"""
    try:
        # Refresh all platforms
        twitter_success = get_twitter_trends_from_trends24()
        reddit_success = get_reddit_trends()
        youtube_success = get_youtube_trends()
        news_success = get_news_trends()
        spotify_success = get_spotify_trends()
        
        return jsonify({
            'status': 'success',
            'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'platforms': {
                'twitter': twitter_success,
                'reddit': reddit_success,
                'youtube': youtube_success,
                'news': news_success,
                'spotify': spotify_success
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/refresh-google-trends', methods=['GET'])
def refresh_google_trends_only():
    """Endpoint to refresh only Google Trends data"""
    try:
        success = get_google_trends()
        return jsonify({
            'status': 'success' if success else 'partial',
            'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'platform': 'google'
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)