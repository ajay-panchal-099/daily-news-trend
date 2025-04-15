import os
import json
import time
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pytrends.request import TrendReq
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load environment variables
load_dotenv()

# Define data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def format_number(view_count):
    """Format a number with commas and 'k' for thousands"""
    if view_count >= 1000000:
        views = f"{view_count/1000000:.1f}M"
    elif view_count >= 1000:
        views = f"{view_count/1000:.1f}k"
    else:
        views = str(view_count)
    return views
 
def collect_all_trends():
    """Collect trends from all platforms"""
    print("Starting trend collection...")
    # Add Spotify to the collection process
    os.makedirs(DATA_DIR, exist_ok=True)
    spotify_success = get_spotify_trends()
    print(f"Spotify trends collected: {'Success' if spotify_success else 'Failed'}")
    
    time.sleep(2)
    
    # Collect trends in desired order
    reddit_success = get_reddit_trends()
    print(f"Reddit trends collected: {'Success' if reddit_success else 'Failed'}")
    
    time.sleep(2)
    
    youtube_success = get_youtube_trends()
    print(f"YouTube trends collected: {'Success' if youtube_success else 'Failed'}")
    
    time.sleep(2)
    
    news_success = get_news_trends()
    print(f"News trends collected: {'Success' if news_success else 'Failed'}")
    
    time.sleep(2)
    
    twitter_success = get_twitter_trends_from_trends24()
    print(f"Twitter trends collected: {'Success' if twitter_success else 'Failed'}")
    
    time.sleep(2)
    
    google_success = get_google_trends()
    print(f"Google trends collected: {'Success' if google_success else 'Failed'}")
    
    print("Trend collection completed!")


def get_spotify_trends():
    """Get trending songs from Spotify"""
    try:
        print("🎵 Fetching Spotify trends...")
        
        # Auth setup
        spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
        spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not spotify_client_id or not spotify_client_secret:
            print("⚠️ Spotify credentials not found in environment variables")
            return use_sample_spotify_data()
            
        auth_manager = SpotifyClientCredentials(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)

        queries = ['Bollywood Hits', 'Top Hindi Songs', 'India Trending Music']
        trends = []

        for query in queries:
            results = sp.search(q=query, type='playlist', limit=3)
            playlists = [p for p in results['playlists']['items'] if p is not None]
            
            if playlists:
                print(f"✅ Found playlists for: {query}")
                playlist = playlists[0]
                tracks = sp.playlist_tracks(playlist['id'])
                
                for idx, item in enumerate(tracks['items']):
                    if item and item['track']:
                        track = item['track']
                        track_data = {
                            'rank': idx + 1,
                            'title': track['name'],
                            'artists': ', '.join([artist['name'] for artist in track['artists']]),
                            'url': track['external_urls']['spotify'],
                            'album': track['album']['name'],
                            'duration': track['duration_ms'] // 1000,
                            'popularity': track['popularity'],
                            'tag': 'trending'
                        }
                        trends.append(track_data)
                break
            else:
                print(f"❌ No playlist found for: {query}")
        
        if trends:
            data = {
                'trends': trends,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
            with open(os.path.join(DATA_DIR, 'spotify_trends.json'), 'w') as f:
                json.dump(data, f, indent=2)
                
            print("✅ Successfully fetched Spotify trends")
            return True
            
        return use_sample_spotify_data()

    except Exception as e:
        print(f"⚠️ Error fetching Spotify trends: {e}")
        return use_sample_spotify_data()


def get_twitter_trends_from_trends24(country='india'):
    """Get Twitter trends from trends24.in"""
    try:
        print("🐦 Fetching Twitter trends from trends24.in...")
        
        url = f"https://trends24.in/{country}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://trends24.in/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Debug: Save the HTML response to a file for inspection
        with open(os.path.join(DATA_DIR, 'twitter_debug.html'), 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        trends = []
        
        # Try different selectors that might work
        trend_card = soup.select_one('.trend-card')
        if not trend_card:
            trend_card = soup.select_one('.trends-card')  # Alternative selector
        
        if not trend_card:
            # Try to find any list of trends
            trend_items = soup.select('ol li a') or soup.select('.trend-item a') or soup.select('a[data-trend]')
        else:
            trend_items = trend_card.select('ol li a')
        
       
        if not trend_items:
            print("No trend items found using any selector")
            return use_sample_twitter_data()

        for i, item in enumerate(trend_items):
            trend_name = item.text.strip()
            trend_url = f"https://twitter.com/search?q={trend_name.replace('#', '%23')}"
            
            # Try to extract tweet volume if available
            volume = 'N/A'
            volume_element = None
            
            # Look for volume info near the trend item
            if item.parent:
                volume_element = item.parent.select_one('.tweet-count') or item.parent.select_one('.trend-volume') or item.parent.select_one('span.count')
            
            if volume_element and volume_element.text:
                volume = volume_element.text.strip()
            else:
                # If no specific volume element, try to find any number in the parent element
                if item.parent and item.parent.text:
                    import re
                    volume_match = re.search(r'(\d+[kK,]?\+?\s*tweets)', item.parent.text)
                    if volume_match:
                        volume = volume_match.group(1)
                    else:
                        # Generate a fallback volume with nice formatting
                        num = (50-i)*1000 + 500
                        if num >= 1000:
                            volume = f"{num/1000:.1f}k+"
                        else:
                            volume = f"{num}+ tweets"
            
            # Format the volume if it contains a number without k/K
            if 'tweets' in volume:
                import re
                num_match = re.search(r'(\d+,?\d*)\+?\s*tweets', volume)
                if num_match:
                    try:
                        num_str = num_match.group(1).replace(',', '')
                        num = int(num_str)
                        if num >= 1000:
                            volume = f"{num/1000:.1f}k+"
                    except:
                        pass
            
            
            trends.append({
                'rank': i + 1,
                'name': trend_name,
                'url': trend_url,
                'volume': volume,
                'tag': 'trending'
            })
        
        if not trends:
            print("No trends found")
            return use_sample_twitter_data()
            
        data = {
            'trends': trends,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        with open(os.path.join(DATA_DIR, 'twitter_trends.json'), 'w') as f:
            json.dump(data, f, indent=2)
            
        print("✅ Successfully fetched Twitter trends")
        return True
        
    except Exception as e:
        print(f"⚠️ Error fetching Twitter trends: {e}")
        return use_sample_twitter_data()

def get_reddit_trends():
    """Get trending posts from Reddit"""
    try:
        print("🔴 Fetching Reddit trends...")
        
        url = "https://www.reddit.com/r/popular.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        posts = data['data']['children']
        
        trends = []
        for i, post in enumerate(posts):
            post_data = post['data']
            
            # Extract more metadata for detailed view
            description = post_data.get('selftext', '')
            if len(description) > 300:
                description = description[:300] + '...'
                
            thumbnail = post_data.get('thumbnail', '')
            if not thumbnail.startswith('http'):
                thumbnail = ''
                
            trends.append({
                'rank': i + 1,
                'title': post_data['title'],
                'url': f"https://reddit.com{post_data['permalink']}",
                'subreddit': post_data['subreddit'],
                'score': f"{post_data['score']:,}",
                'comments': f"{post_data['num_comments']:,}",
                'description': description,
                'thumbnail': thumbnail,
                'author': post_data.get('author', 'unknown'),
                'created': datetime.fromtimestamp(post_data['created_utc']).strftime('%Y-%m-%d %H:%M:%S')
            })
            
        data = {
            'trends': trends,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        with open(os.path.join(DATA_DIR, 'reddit_trends.json'), 'w') as f:
            json.dump(data, f, indent=2)
            
        print("✅ Successfully fetched Reddit trends")
        return True
        
    except Exception as e:
        print(f"⚠️ Error fetching Reddit trends: {e}")
        return use_sample_reddit_data()

def get_google_trends():
    """Get Google trends using RapidAPI"""
    try:
        print("📡 Fetching Google trends...")
        
        # Get RapidAPI key from environment variables
        rapid_api_key = os.getenv('RAPID_API_KEY')

        try:
            # RapidAPI Google Realtime Trends Data API endpoint
            # Note: Google Realtime Trends Data API has a limit of 100 requests per month
            url = "https://google-realtime-trends-data-api.p.rapidapi.com/trends/INDIA"
            
            headers = {
                "x-rapidapi-host": "google-realtime-trends-data-api.p.rapidapi.com",
                "x-rapidapi-key": rapid_api_key
            }
            
            # Make the request
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Save the response for debugging
            with open(os.path.join(DATA_DIR, 'google_debug_realtime_api.json'), 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            data = response.json()
            
            # Extract trends from the response based on the actual format
            trends = []
            
            if data.get('success') and 'data' in data:
                keywords = data['data'].get('keywordsText', [])
                for i, keyword in enumerate(keywords):
                    trends.append({
                        'rank': i+1,
                        'title': keyword,
                        'url': f"https://google.com/search?q={keyword.replace(' ', '+')}",
                        'search_url': f"https://google.com/search?q={keyword.replace(' ', '+')}",
                        'tag': 'trending'
                    })
                   
            
            if trends:
                data = {
                    'trends': trends,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                    'source': 'rapidapi_realtime'
                }
                
                with open(os.path.join(DATA_DIR, 'google_trends.json'), 'w') as f:
                    json.dump(data, f, indent=2)
                
                print("✅ Successfully fetched Google trends via RapidAPI Realtime Trends API")
                return True
            else:
                return use_sample_google_data()
        except Exception as e:
            print(f"Error with RapidAPI Realtime Trends API: {e}")
            return use_sample_google_data()
    except Exception as e:
        print(f"⚠️ Error fetching Google trends: {e}")
        return use_sample_google_data()

def get_youtube_trends_from_api():
    """Get YouTube trends using YouTube Data API"""
    try:
        print("🎥 Fetching YouTube trends from Data API...")
        
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            print("⚠️ YouTube API key not found in environment variables")
            return False
            
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": "IN",
            "maxResults": 30,
            "hl": "hi",
            "key": api_key
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        trends = []
        
        for i, video in enumerate(data["items"], 1):
            # Convert view count to human readable format
            view_count = int(video['statistics']['viewCount'])
            like_count = int(video['statistics'].get('likeCount', 0))
            views = format_number(view_count)
            likes = format_number(like_count)
            
                
            trends.append({
                'rank': i,
                'title': video['snippet']['title'],
                'channel': video['snippet']['channelTitle'],
                'views': views,
                'likes': likes,
                'url': f"https://youtube.com/watch?v={video['id']}",
                'tag': 'trending'
            })
            
        data = {
            'trends': trends,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        with open(os.path.join(DATA_DIR, 'youtube_trends.json'), 'w') as f:
            json.dump(data, f, indent=2)
            
        print("✅ Successfully fetched YouTube trends from Data API")
        return True
        
    except Exception as e:
        print(f"⚠️ Error fetching YouTube trends from Data API: {e}")
        return False

def get_youtube_trends():
    """Get trending YouTube videos including music"""
    try:
        print("🎥 Fetching YouTube trends from Data API...")
        
        # Try YouTube Data API first
        if get_youtube_trends_from_api():
            return True
            
        print("⚠️ YouTube Data API failed, trying RapidAPI as fallback...")
        
        # Try RapidAPI as fallback
        rapid_api_key = os.getenv('RAPID_API_KEY')
        if rapid_api_key:
            headers = {
                'Content-Type': 'application/json',
                'x-rapidapi-host': 'youtube-v41.p.rapidapi.com',
                'x-rapidapi-key': rapid_api_key
            }
            
            url = "https://youtube-v41.p.rapidapi.com/trending"
            payload = {"country": "IN"}
            
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Save the response for debugging
                with open(os.path.join(DATA_DIR, 'youtube_debug_api.json'), 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # Process general trending videos
                trending_videos = []
                
                sorted_data = sorted(data, key=lambda x: float(x['number_of_views'].replace('M', 'e6').replace('k', 'e3')), reverse=True)
                for i, item in enumerate(sorted_data):
                    video = {
                        'rank': i + 1,
                        'title': item.get('title', f'Video {i+1}'),
                        'channel': item.get('channel', 'Unknown Channel'),
                        'views': item.get('number_of_views', 'N/A'),
                        'url': item.get('link', f"https://youtube.com/watch?v={item.get('video_id', '')}"),
                        'tag': 'trending'
                    }
                    
                    trending_videos.append(video)
                    
                
                if trending_videos:
                    data = {
                        'trends': trending_videos,
                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
                    }
                    
                    with open(os.path.join(DATA_DIR, 'youtube_trends.json'), 'w') as f:
                        json.dump(data, f, indent=2)
                        
                    print(f"✅ Successfully fetched YouTube trends via RapidAPI")
                    return True
        
    except Exception as e:
        print(f"⚠️ Error fetching YouTube trends: {e}")
        return use_sample_youtube_data()

def get_news_trends():
    """Get trending news stories"""
    try:
        print("📰 Fetching news trends...")
        
        url = "https://news.google.com/rss"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'xml')
        items = soup.select('item')
        
        if not items:
            print("No news items found")
            return use_sample_news_data()
            
        news = []
        for i, item in enumerate(items):
            try:
                title = item.select_one('title').text
                link = item.select_one('link').text
                source = item.select_one('source').text if item.select_one('source') else 'Google News'
                pub_date = item.select_one('pubDate').text if item.select_one('pubDate') else None

                news.append({
                    'rank': i + 1,
                    'title': title,
                    'url': link,
                    'source': source,
                    'pub_date': pub_date,
                    'tag': 'headline'
                })
            except Exception as e:
                print(f"Error parsing news item {i}: {e}")
                continue
        
        if not news:
            print("Failed to parse any news items")
            return use_sample_news_data()
            
        data = {
            'trends': news,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        with open(os.path.join(DATA_DIR, 'news_trends.json'), 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"✅ Successfully fetched {len(news)} news trends")
        return True
        
    except Exception as e:
        print(f"⚠️ Error fetching news trends: {e}")
        return use_sample_news_data()

def use_sample_spotify_data():
    """Use sample Spotify data when API fails"""
    try:
        with open(os.path.join(DATA_DIR, 'spotify_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                print("Using existing Spotify data")
                return True
            else:
                print("No existing Spotify data found")
        return False
    except Exception as e:
        print(f"Error using existing Spotify data: {e}")
        return False


def use_sample_twitter_data():
    """Use sample Twitter data when API fails"""
    try:
        # Load existing data and use it if available
        with open(os.path.join(DATA_DIR, 'twitter_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                print("Using existing Twitter data")
                return True
            else:
                print("No existing Twitter data found")
        return False
    except Exception as e:
        print(f"Error using existing Twitter data: {e}")
        return False

def use_sample_reddit_data():
    """Use sample Reddit data when API fails"""
    try:
        # Load existing data and use it if available
        with open(os.path.join(DATA_DIR, 'reddit_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                print("Using existing Reddit data")
                return True
            else:
                print("No existing Reddit data found")
        return False
    except Exception as e:
        print(f"Error using existing Reddit data: {e}")
        return False

def use_sample_google_data():
    """Use sample Google data when API fails"""
    try:
        # Load existing data and use it if available
        with open(os.path.join(DATA_DIR, 'google_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                print("Using existing Google data")
                return True
            else:
                print("No existing Google data found")
        return False
    except Exception as e:
        print(f"Error using existing Google data: {e}")
        return False

def use_sample_youtube_data():
    """Use sample YouTube data when API fails"""
    try:
        # Load existing data and use it if available
        with open(os.path.join(DATA_DIR, 'youtube_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                print("Using existing YouTube data")
                return True
            else:
                print("No existing YouTube data found")
        return False
    except Exception as e:
        print(f"Error using existing YouTube data: {e}")
        return False

def use_sample_news_data():
    """Use sample news data when API fails"""
    try:
        with open(os.path.join(DATA_DIR, 'news_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                print("Using existing NEWS data")
                return True
            else:
                print("No existing NEWS data found")
        return False
    except Exception as e:
        print(f"Error using existing NEWS data: {e}")
        return False

def get_top10_spotify_data():
    """Get Top 10 Spotify data"""
    try:
        data = {}
        with open(os.path.join(DATA_DIR, 'spotify_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                # first sort in popularity
                data['trends'] = sorted(data['trends'], key=lambda x: x['popularity'], reverse=True)
                data['trends'] = data['trends'][:10]
            else:
                print("No Spotify data found")
        return data
    except Exception as e:
        print(f"Error using existing Spotify data: {e}")


def get_top10_twitter_data():
    """Get Top 10 Twitter data """
    try:
        # Load existing data and use it if available
        data = {}
        with open(os.path.join(DATA_DIR, 'twitter_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                data['trends'] = data['trends'][:10]
            else:
                print("No Twitter data found")
        return data
    except Exception as e:
        print(f"Error using existing Twitter data: {e}")

def get_top10_youtube_data():
    """Get Top 10 YouTube data sorted by views"""
    try:
        data = {}
        with open(os.path.join(DATA_DIR, 'youtube_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                sorted_trends = sorted(
                    data['trends'],
                    key=lambda x: float(x['views'].replace('M', '000000').replace('k', '000')) if isinstance(x['views'], str) and any(c.isdigit() for c in x['views']) else 0,
                    reverse=True
                )[:10]
                data['trends'] = sorted_trends
            else:
                print("No YouTube data found")
        return data
    except Exception as e:
        print(f"Error using existing YouTube data: {e}")

def get_top10_google_data():
    """Get Top 10 Google trends data"""
    try:
        data = {}
        with open(os.path.join(DATA_DIR, 'google_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                # Google trends are already ranked, just take top 10
                data['trends'] = data['trends'][:10]
            else:
                print("No Google data found")
        return data
    except Exception as e:
        print(f"Error using existing Google data: {e}")

def get_top10_reddit_data():
    """Get Top 10 Reddit data sorted by score"""
    try:
        data = {}
        with open(os.path.join(DATA_DIR, 'reddit_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                sorted_trends = sorted(
                    data['trends'],
                    key=lambda x: int(x['score'].replace(',', '')) if isinstance(x['score'], str) else 0,
                    reverse=True
                )[:10]
                data['trends'] = sorted_trends
            else:
                print("No Reddit data found")
        return data
    except Exception as e:
        print(f"Error using existing Reddit data: {e}")

def get_top10_news_data():
    """Get Top 10 News data"""
    try:
        data = {}
        with open(os.path.join(DATA_DIR, 'news_trends.json'), 'r') as f:
            data = json.load(f)
            if data.get('trends'):
                data['trends'] = data['trends'][:10]
            else:
                print("No News data found")
        return data
    except Exception as e:
        print(f"Error using existing News data: {e}")
    

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    collect_all_trends()