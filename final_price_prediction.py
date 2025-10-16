import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import json
import os
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load historical predictions
def load_historical_predictions(file_path):
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            required_cols = ['symbol', 'predicted_open', 'predicted_close', 'predicted_average', 'confidence']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing columns in {file_path}: {required_cols}")
                return pd.DataFrame()
            logger.info(f"Loaded historical predictions from {file_path} with {len(df)} entries")
            return df
        logger.warning(f"Historical prediction file {file_path} not found")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading historical predictions: {e}")
        return pd.DataFrame()

# Load sentiment data from CSV and filter to latest update
def load_sentiment_data(sentiment_dir, symbol):
    sentiment_file = os.path.join(sentiment_dir, f"{symbol}_share_sentiment.csv")
    try:
        if os.path.exists(sentiment_file):
            df = pd.read_csv(sentiment_file, encoding="utf-8-sig")
            required_cols = ['articleId', 'publishedDate', 'sentiment_score', 'mediaUrl']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing columns in {sentiment_file}: {required_cols}")
                return None
            df['publishedDate'] = pd.to_datetime(df['publishedDate'])
            latest_date = df['publishedDate'].max()
            df = df[df['publishedDate'] == latest_date]
            logger.info(f"Loaded sentiment data from {sentiment_file} with {len(df)} entries for {latest_date}")
            return df
        logger.warning(f"Sentiment file {sentiment_file} not found")
        return None
    except Exception as e:
        logger.error(f"Error loading sentiment data for {symbol}: {e}")
        return None

# Load media weightage
def load_media_weightage(weightage_file):
    try:
        if os.path.exists(weightage_file):
            with open(weightage_file, 'r', encoding='utf-8') as f:
                weightage = json.load(f)
            logger.info(f"Loaded media weightage from {weightage_file}")
            return weightage
        logger.warning(f"Media weightage file {weightage_file} not found")
        return {}
    except Exception as e:
        logger.error(f"Error loading media weightage: {e}")
        return {}

# Adjust price with sentiment and weightage
def adjust_with_sentiment(historical_price, sentiment_df, weightage):
    if historical_price is None:
        return historical_price, 0.0

    if sentiment_df is not None and not sentiment_df.empty:
        latest_sentiment = sentiment_df.iloc[-1]
        sentiment_score = latest_sentiment['sentiment_score']
        logger.info(f"Sentiment score for adjustment: {sentiment_score}")
        if sentiment_score == 0:
            logger.warning("Sentiment score is zero, no adjustment applied")
            return historical_price, 0.0

        media_domain = urlparse(latest_sentiment['mediaUrl']).netloc
        media_weight = weightage.get(media_domain, {}).get('average_weight', 0.5)
        logger.info(f"Media weight for {media_domain}: {media_weight}")
        if media_weight == 0:
            logger.warning(f"Media weight is zero for {media_domain}, no adjustment applied")
            return historical_price, 0.0

        sentiment_impact = sentiment_score * media_weight
        logger.info(f"Sentiment impact: {sentiment_impact}")
        adjusted_price = historical_price * (1 + sentiment_impact * 0.5)  # Increased impact factor to 0.5
        confidence = min(1.0, media_weight * abs(sentiment_score))
        logger.info(f"Adjusted {historical_price:.2f} to {adjusted_price:.2f} with confidence {confidence}")
        return adjusted_price, confidence
    else:
        return historical_price, 0.0

# Main prediction function
def predict_final_price(sentiment_dir, weightage_file, historical_file, output_file):
    weightage = load_media_weightage(weightage_file)
    historical_df = load_historical_predictions(historical_file)

    if historical_df.empty:
        logger.error("Insufficient historical data for prediction")
        return {}

    # Get unique symbols from historical data
    symbols = historical_df['symbol'].unique()
    all_predictions = []

    for symbol in symbols:
        # Load sentiment data, return None if not found
        sentiment_df = load_sentiment_data(sentiment_dir, symbol)

        # Filter historical prediction for the specific symbol
        historical_pred = historical_df[historical_df['symbol'] == symbol].iloc[-1] if not historical_df.empty else None
        if historical_pred is None:
            logger.warning(f"No historical prediction found for {symbol}")
            continue

        # Extract historical prices
        historical_open = historical_pred['predicted_open']
        historical_close = historical_pred['predicted_close']
        historical_average = historical_pred['predicted_average']
        confidence = historical_pred['confidence']

        # Ensure articleId is string for .str.contains
        if sentiment_df is not None and not sentiment_df.empty:
            sentiment_df['articleId'] = sentiment_df['articleId'].astype(str)

        # Adjust each price type with sentiment, or use historical if no sentiment
        final_open, open_confidence = adjust_with_sentiment(historical_open, sentiment_df[sentiment_df['articleId'].str.contains(symbol, na=False)] if sentiment_df is not None else None, weightage)
        final_close, close_confidence = adjust_with_sentiment(historical_close, sentiment_df[sentiment_df['articleId'].str.contains(symbol, na=False)] if sentiment_df is not None else None, weightage)
        final_average, avg_confidence = adjust_with_sentiment(historical_average, sentiment_df[sentiment_df['articleId'].str.contains(symbol, na=False)] if sentiment_df is not None else None, weightage)

        if final_open is None or final_close is None or final_average is None:
            final_open = historical_open
            final_close = historical_close
            final_average = historical_average
            open_confidence = confidence
            close_confidence = confidence
            avg_confidence = confidence
            logger.warning(f"No valid sentiment adjustment for {symbol}, using historical prices")

        all_predictions.append({
            'symbol': symbol,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'historical_open': historical_open,
            'final_open': final_open,
            'historical_close': historical_close,
            'final_close': final_close,
            'historical_average': historical_average,
            'final_average': final_average,
            'confidence': max(open_confidence, close_confidence, avg_confidence)  # Use max confidence
        })
        logger.info(f"{symbol}: Historical Open = {historical_open:.2f}, Final Open = {final_open:.2f}, "
                    f"Historical Close = {historical_close:.2f}, Final Close = {final_close:.2f}, "
                    f"Historical Average = {historical_average:.2f}, Final Average = {final_average:.2f}, "
                    f"Confidence = {max(open_confidence, close_confidence, avg_confidence):.2f}")

    if not all_predictions:
        logger.error("No valid predictions generated")
        return {}

    pred_df = pd.DataFrame(all_predictions)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    pred_df.to_csv(output_file, index=False, mode='a', header=not os.path.exists(output_file))
    logger.info(f"Saved final predictions to {output_file} with {len(pred_df)} entries at 06:27 PM +0545 on July 29, 2025")

    return {pred['symbol']: {
        'final_open': pred['final_open'],
        'final_close': pred['final_close'],
        'final_average': pred['final_average'],
        'confidence': pred['confidence']
    } for pred in all_predictions}

if __name__ == "__main__":
    sentiment_dir = r"E:\hey\output\sentiment_results"
    weightage_file = r"E:\hey\output\weightage\media_weightage.json"
    historical_file = r"E:\hey\output\history prediction\history_price_prediction.csv"
    output_file = r"E:\hey\output\prediction_with_news\final_prediction\share_prediction.csv"
    logger.info("Starting final price prediction analysis")
    predictions = predict_final_price(sentiment_dir, weightage_file, historical_file, output_file)