import json
import boto3
import requests
import os
from datetime import datetime

API_KEY = os.environ['ALPHA_VANTAGE_KEY']
BUCKET_NAME = os.environ['S3_BUCKET_NAME']
s3 = boto3.client('s3')

def lambda_handler(event, context):
    symbols = event.get("symbols", ["MSFT"])

    for symbol in symbols:
        print(f"📦 Fetching {symbol}...")
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"❌ Failed to fetch data for {symbol}")
            continue

        data = response.json()
        if "Time Series (Daily)" not in data:
            print(f"⚠️ No time series data found for {symbol}")
            continue

        time_series = data["Time Series (Daily)"]

        for date, values in time_series.items():
            key = f"raw/symbol={symbol}/date={date}/data.json"

            # Check if already exists (optional)
            try:
                s3.head_object(Bucket=BUCKET_NAME, Key=key)
                print(f"⏭️ Already exists: {key}")
                continue
            except:
                pass

            payload = {
                "Meta Data": {
                    "1. Symbol": symbol,
                    "2. Generated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                },
                "Time Series (Daily)": {
                    date: values
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
        "statusCode": 200,
        "body": "Backfill complete."
    }
