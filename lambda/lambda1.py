import json
import boto3
import requests
from datetime import datetime
import os

# Lambda environment variables
API_KEY = os.environ['ALPHA_VANTAGE_KEY']
BUCKET_NAME = os.environ['S3_BUCKET_NAME']
s3 = boto3.client('s3')

def lambda_handler(event, context):
    symbol = event.get("symbol", "TSLA")  # Default fallback

    print(f"📦 Fetching data for: {symbol}")

    # Call Alpha Vantage
    url = (
        f"https://www.alphavantage.co/query?"
        f"function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
    )
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ HTTP error from API: {response.status_code}")
        return {
            'statusCode': 500,
            'body': f"API request failed for {symbol}: {response.text}"
        }

    data = response.json()
    time_series = data.get("Time Series (Daily)", {})

    if not time_series:
        print("⚠️ No time series data in response.")
        return {
            'statusCode': 500,
            'body': f"No time series data available for {symbol}"
        }

    # Get most recent available date
    available_dates = sorted(time_series.keys(), reverse=True)
    latest_date = available_dates[0]
    print(f"📅 Latest available trading date: {latest_date}")

    # Skip if already exists in S3
    key = f"raw/symbol={symbol}/date={latest_date}/data.json"
    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=key)
        print(f"⏭️ Skipping, already exists: {key}")
        return {
            'statusCode': 200,
            'body': f"{symbol} data for {latest_date} already exists"
        }
    except s3.exceptions.ClientError:
        pass  # Proceed with storing

    # Build and upload payload
    payload = {
        "Meta Data": {
            "1. Symbol": symbol,
            "2. Retrieved": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        },
        "Time Series (Daily)": {
            latest_date: time_series[latest_date]
        }
    }

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(payload),
        ContentType='application/json'
    )

    print(f"✅ Uploaded: {key}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f"{symbol} data for {latest_date} stored successfully",
            's3_key': key
        })
    }
