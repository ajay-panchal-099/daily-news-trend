# Daily News Update

A real-time dashboard aggregating trending content from multiple platforms with a focus on Indian trends.

<div style="font-size: 0.8em; color: #666; margin-bottom: 1em;">
Note: All data sources, including YouTube trending videos, Reddit topics, Spotify charts, and news headlines, are refreshed every hour. Google Trends data is updated once daily at 8 AM IST, in line with its official update schedule.
</div>

## Features
- **Multi-platform aggregation**: Twitter, YouTube, Spotify, Reddit, Google Trends, News
- **Responsive UI**: Works on desktop and mobile
- **Country-specific**: Focus on Indian trends (configurable)
- **Detailed views**: Expanded information for each trend
- **Automatic updates**: Hourly refresh of all data

## API Integrations

### Twitter Trends
- **Source**: `https://trends24.in/india/`
- **Method**: Web scraping
- **Data Collected**:
  - Top hashtags and topics
  - Estimated tweet volumes
- **Rate Limits**: 
  - No official API limits
  - Recommended: 1 request every 5 minutes

### YouTube Data API
- **Endpoint**: `https://www.googleapis.com/youtube/v3/videos`
- **Parameters**:
  - `chart=mostPopular`
  - `regionCode=IN`
  - `maxResults=50`
- **Rate Limits**:
  - 10,000 quota units/day
  - 1 unit per request
- **Fallback**: RapidAPI YouTube-v41

### Reddit API
- **Endpoint**: `https://www.reddit.com/r/popular.json`
- **Data Collected**:
  - Top posts from r/popular
  - Post metadata (score, comments, author)
- **Rate Limits**:
  - 60 requests/minute (OAuth)
  - 30 requests/minute (without OAuth)

### Google Trends
- **Primary Endpoint**: `https://google-realtime-trends-data-api.p.rapidapi.com/trends/INDIA`
- **Rate Limits**:
  - 100 requests/month (free tier)
  - 5 requests/second
- **Data Collected**:
  - Real-time search trends
  - Related queries

### News Aggregation
- **Source**: Google News RSS (`https://news.google.com/rss`)
- **Data Collected**:
  - Top headlines
  - News source information
- **Rate Limits**: None (recommend 15min intervals)

## Technical Stack

### Backend
- Python 3.9+
- Flask web framework
- Requests library (API calls)
- BeautifulSoup (HTML parsing)
- Spotipy (Spotify API)
- PRAW (Reddit API)

### Frontend
- Vanilla JavaScript
- CSS Grid/Flexbox
- Responsive design
- Platform-specific color schemes

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/daily-news-update.git
   cd daily-news-update
   ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up API keys and credentials:
   - Twitter API
   - YouTube Data API
   - Reddit API
   - Google Trends API


4. Run the Flask app:
    ```bash
    python3 app.py
    ```


Project Structure

```
  daily-news-update/
  ├── app.py                # Main application
  ├── collect_trends.py     # Data collection module
  ├── static/              # CSS/JS assets
  │   ├── css/
  │   └── js/
  ├── templates/           # HTML templates
  ├── utils/               # Helper functions
  │   ├── api_helpers.py
  │   └── cache.py
  ├── data/                # JSON data storage
  └── requirements.txt      # Dependencies
```


LEARNINGS
- Python
- Flask
- API Integration
- Web Scraping
- Data Visualization
- Responsive Design

ISSUES
- Twitter API is not working - Fetched from trends24.in
- Binary data is coming sometimes-  Filtered out using alnum()
- YouTube API is not working (Used Ofiicial RapidAPI YouTube-v41, then from google cloud)
- Spotify API is not working (Used Official RapidAPI Spotify-v1 then Official Spotify API)
- On deploying on Render, the app is not updating - Not Fixed why crom job, because don't have persistent storage
- tried Adding JS logic to update the data on every 60 minutes, but it is not working, same storage issue (stale data)
- Tried to deply on AWS S3 Bucket, I had to add new cron job and change Urls
- Finally addded logic to update github repo on every push(via cron job), that will trigger the redeployment 
- Committing and Pushing to Github didn't work,because all ssh info were getting lost -> Adding ssh info at runtime
- Copying Key to another temp file worked
