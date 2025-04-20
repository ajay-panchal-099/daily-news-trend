import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

def upload_to_s3(file_path, bucket_name, s3_key=None):
    """Upload a file to S3 bucket"""
    try:
        if s3_key is None:
            s3_key = os.path.basename(file_path)
            
        s3_client = boto3.client('s3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'ap-south-1')
        )
        
        s3_client.upload_file(file_path, bucket_name, s3_key)
        print(f"✅ Successfully uploaded {s3_key} to S3")
        return True
    except ClientError as e:
        print(f"⚠️ Error uploading to S3: {e}")
        return False

def store_trends_in_s3(data_dir, bucket_name):
    """Store all trend files in S3"""
    try:
        print("📤 Uploading trends to S3...")
        trend_files = [
            'twitter_trends.json',
            'reddit_trends.json',
            'youtube_trends.json',
            'google_trends.json',
            'spotify_trends.json',
            'news_trends.json'
        ]
        
        success = True
        timestamp = datetime.now().strftime('%Y-%m-%d/%H_%M_%S')
        for file_name in trend_files:
            file_path = os.path.join(data_dir, file_name)
            if os.path.exists(file_path):
                s3_key = f"trends/{timestamp}/{file_name}"
                if not upload_to_s3(file_path, bucket_name, s3_key):
                    success = False
        
        return success
    except Exception as e:
        print(f"⚠️ Error storing trends in S3: {e}")
        return False