import json
import boto3
import urllib.parse
import csv
import os
from io import StringIO

s3 = boto3.client('s3')
BUCKET_NAME = os.environ['S3_BUCKET_NAME']  # Set this in Lambda env vars

def lambda_handler(event, context):
    try:
        print("🔔 Lambda triggered by S3 event.")
        print("Event received:", json.dumps(event))

        # Extract bucket and key from S3 event
        record = event['Records'][0]['s3']
        bucket = record['bucket']['name']
        key = record['object']['key']

        print(f"📥 Processing file from bucket: {bucket}, key: {key}")

        key = urllib.parse.unquote(record['object']['key'])
        print(f"📥 Decoded S3 key: {key}")

        # Extract symbol and date from the key
        parts = key.split('/')
        symbol = parts[1].split('=')[1]
        date_str = parts[2].split('=')[1]

        print(f"🧠 Parsed symbol: {symbol}, date: {date_str}")

        # Load raw data from S3
        obj = s3.get_object(Bucket=bucket, Key=key)
        raw_data = json.loads(obj["Body"].read())

        # Log raw data preview
        print("📄 Raw JSON keys:", list(raw_data.keys()))
        print("✅ Raw metadata:", json.dumps(raw_data.get("Meta Data", {})))

        if "Time Series (Daily)" not in raw_data:
            raise ValueError("❌ Missing 'Time Series (Daily)' in raw data.")

        time_series = raw_data["Time Series (Daily)"]

        if not time_series:
            raise ValueError("❌ Time Series data is empty.")

        rows = []
        for date, values in time_series.items():
            rows.append({
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": int(values["5. volume"])
            })

        print(f"📊 Parsed {len(rows)} rows of data.")

        # Write cleaned CSV to memory
        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

        # Upload cleaned CSV to clean/ folder (partitioned)
        clean_key = f"clean/symbol={symbol}/date={date_str}/data.csv"
        s3.put_object(Bucket=bucket, Key=clean_key, Body=csv_buffer.getvalue())

        print(f"✅ Cleaned data written to: {clean_key}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Cleaned data saved to {clean_key}"
            })
        }

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        }
