import pandas as pd
import requests
import logging
import os
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API endpoint for candle chart data
API_URL = "https://sharehubnepal.com/data/api/v1/candle-chart/history"

# Function to convert publishDate to Unix timestamp (milliseconds)
def to_unix_timestamp(date_str):
    try:
        if not date_str or pd.isna(date_str):
            logger.error(f"Invalid or empty date_str: {date_str}")
            return None
        # Handle various date formats, including ISO 8601 UTC
        for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d-%m-%Y', '%d/%m/%Y', '%B %d, %Y', '%Y-%m-%dT%H:%M:%S.%fZ']:
            try:
                dt = datetime.strptime(str(date_str).strip(), fmt)
                return int(dt.timestamp() * 1000)
            except ValueError:
                continue
        logger.warning(f"Unsupported date format for {date_str}, using current date as fallback")
        return int(datetime.now().timestamp() * 1000)  # Fallback to current date
    except Exception as e:
        logger.error(f"Date conversion failed for {date_str}: {e}")
        return None

# Function to fetch candle data for a symbol
def fetch_candle_data(symbol):
    try:
        params = {
            "symbol": symbol,
            "resolution": "1D",
            "countback": 60,  # Increased to 60 days to ensure coverage
            "isAdjust": "true"
        }
        response = requests.get(API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                logger.info(f"API response for {symbol}: Entries={len(data['data'])}, Sample time={data['data'][0]['time']}")
                return data
            logger.error(f"API success=false or no data for {symbol}: {data}")
            return None
        logger.error(f"Failed to fetch data for {symbol}: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        logger.error(f"Error fetching candle data for {symbol}: {e}")
        return None

# Function to extract domain from mediaUrl
def get_domain(media_url):
    try:
        return urlparse(media_url).netloc if media_url and media_url.strip() else "unknown"
    except Exception:
        return "unknown"

# Function to compare news sentiment with price change and assign average website weight
def analyze_impact(input_dir, output_file, weightage_dir):
    if not os.path.exists(input_dir) or not os.listdir(input_dir):
        logger.error(f"Input directory {input_dir} is empty or does not exist")
        return

    website_stats = {}  # Track correct, incorrect, and total predictions per website
    results = []
    article_buffer = {}  # Buffer to hold articles for pair processing per domain

    # Load existing weights if available
    weightage_file = os.path.join(weightage_dir, "media_weightage.json")
    if os.path.exists(weightage_file):
        with open(weightage_file, 'r', encoding='utf-8') as f:
            website_stats = json.load(f)
            logger.info(f"Loaded existing stats from {weightage_file}")

    for filename in os.listdir(input_dir):
        if filename.endswith("_share_sentiment.csv"):
            file_path = os.path.join(input_dir, filename)
            logger.info(f"Processing file: {filename}")
            try:
                df = pd.read_csv(file_path, encoding="utf-8-sig")
                if df.empty:
                    logger.info(f"No data in {file_path}")
                    continue

                # Validate required columns
                required_cols = ['articleId', 'publishedDate', 'sentiment_score', 'mediaUrl']
                if not all(col in df.columns for col in required_cols):
                    logger.error(f"Missing columns in {file_path}: {required_cols}")
                    continue

                symbol = filename.replace("_share_sentiment.csv", "")
                candle_data = fetch_candle_data(symbol)
                if not candle_data or not candle_data.get("data"):
                    continue

                for index, row in df.iterrows():
                    publish_date = row['publishedDate']
                    logger.debug(f"Processing publishDate: {publish_date}")
                    unix_time = to_unix_timestamp(publish_date)
                    if unix_time is None:
                        continue

                    # Find candle data for publish date and 2 days after
                    candles = [item["time"] for item in candle_data["data"]]
                    prices = [item["close"] for item in candle_data["data"]]
                    matched = False
                    for i, candle_time in enumerate(candles):
                        if abs(candle_time - unix_time) < 259200000:  # 3-day tolerance
                            matched = True
                            logger.debug(f"Matched {publish_date} with API time {candle_time}")
                            # Check price change 2 days later (if data available)
                            if i + 2 < len(candles):
                                price_now = prices[i]
                                price_after_2d = prices[i + 2]
                                price_change = (price_after_2d - price_now) / price_now * 100  # Percentage change
                                sentiment_score = row['sentiment_score']

                                # Determine predicted and actual directions
                                predicted_dir = "positive" if sentiment_score > 0 else "negative" if sentiment_score < 0 else "neutral"
                                actual_dir = "positive" if price_change > 0.1 else "negative" if price_change < -0.1 else "neutral"

                                # Buffer article for pair processing
                                website = get_domain(row['mediaUrl'])
                                if website not in article_buffer:
                                    article_buffer[website] = []
                                article_buffer[website].append({
                                    "articleId": row['articleId'],
                                    "publishDate": publish_date,
                                    "mediaUrl": row['mediaUrl'],
                                    "sentiment_score": sentiment_score,
                                    "price_change_2d (%)": price_change,
                                    "predicted_dir": predicted_dir,
                                    "actual_dir": actual_dir,
                                    "index": index
                                })

                                results.append({
                                    "articleId": row['articleId'],
                                    "symbol": symbol,
                                    "publishDate": publish_date,
                                    "mediaUrl": row['mediaUrl'],
                                    "sentiment_score": sentiment_score,
                                    "price_change_2d (%)": price_change,
                                    "predicted_dir": predicted_dir,
                                    "actual_dir": actual_dir
                                })
                            break
                    if not matched:
                        logger.warning(f"No matching candle data for {publish_date} (unix: {unix_time}) in {symbol}")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

    # Process pairs and update website stats
    for website, articles in article_buffer.items():
        if website not in website_stats:
            website_stats[website] = {"correct": 0, "incorrect": 0, "total_pairs": 0}
        for i in range(0, len(articles), 2):  # Process in pairs
            if i + 1 < len(articles):
                pair1 = articles[i]
                pair2 = articles[i + 1]
                if pair1["predicted_dir"] != "neutral" and pair2["predicted_dir"] != "neutral":
                    website_stats[website]["total_pairs"] += 1
                    # Check if both predictions match their actual directions
                    if (pair1["predicted_dir"] == pair1["actual_dir"] and pair2["predicted_dir"] == pair2["actual_dir"]) or \
                       (pair1["predicted_dir"] != pair1["actual_dir"] and pair2["predicted_dir"] != pair2["actual_dir"]):
                        website_stats[website]["correct"] += 1
                    else:
                        website_stats[website]["incorrect"] += 1

    # Calculate average weight for each website
    for website, stats in website_stats.items():
        total_pairs = stats["total_pairs"]
        correct = stats["correct"]
        stats["average_weight"] = (correct / total_pairs) if total_pairs > 0 else 0.0

    # Save results to share_weightage.csv
    if results:
        output_df = pd.DataFrame(results)
        # Add average weight to results based on website domain
        output_df['media_weight'] = output_df['mediaUrl'].apply(lambda url: website_stats.get(get_domain(url), {}).get('average_weight', 0.0))
        output_df.to_csv(output_file, index=False, encoding="utf-8-sig")
        logger.info(f"Saved weightage results to {output_file} with {len(output_df)} entries")
    else:
        logger.warning(f"No results to save to {output_file}. Check logs for details.")

    # Save website stats to file
    os.makedirs(weightage_dir, exist_ok=True)
    with open(weightage_file, 'w', encoding='utf-8') as f:
        json.dump(website_stats, f, ensure_ascii=False, indent=4)
    logger.info(f"Saved website stats to {weightage_file}")

if __name__ == "__main__":
    input_dir = r"E:\hey\output\sentiment_results"
    output_file = r"E:\hey\output\share_weightage.csv"
    weightage_dir = r"E:\hey\output\weightage"
    logger.info("Starting news price impact analysis at 04:15 PM +0545 on July 29, 2025")
    analyze_impact(input_dir, output_file, weightage_dir)