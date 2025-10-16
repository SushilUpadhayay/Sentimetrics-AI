import pandas as pd
import nltk
from deep_translator import GoogleTranslator
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import logging
import os
import time
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Download VADER lexicon (run once)
nltk.download('vader_lexicon', quiet=True)

# Initialize translator and sentiment analyzer
translator = GoogleTranslator(source='ne', target='en')
sid = SentimentIntensityAnalyzer()

# Function to normalize text
def normalize_text(text):
    try:
        return str(text).strip()
    except Exception as e:
        logger.error(f"Text normalization failed: {e}")
        return ""

# Function to analyze sentiment and assign numerical score
def analyze_sentiment(title, summary):
    try:
        if not title and not summary:
            logger.warning("Empty title and summary provided")
            return 0.0
        combined_text = normalize_text(f"{title} {summary}")
        if not combined_text:
            logger.warning("Combined text is empty after normalization")
            return 0.0
        
        # Retry translation up to 3 times
        for attempt in range(3):
            try:
                translated = translator.translate(combined_text)
                if translated is None or not translated.strip():
                    logger.warning(f"Translation returned empty for text: {combined_text[:50]}...")
                    return 0.0
                # Analyze sentiment with VADER
                scores = sid.polarity_scores(translated)
                polarity = scores['compound']  # -1.0 (most negative) to 1.0 (most positive)
                logger.info(f"Text: '{translated[:50]}...' | Polarity: {polarity}")
                return polarity
            except Exception as e:
                logger.warning(f"Translation attempt {attempt + 1} failed: {e}")
                time.sleep(1)  # Wait before retrying
        logger.error(f"All translation attempts failed for text: {combined_text[:50]}...")
        return 0.0
    except Exception as e:
        logger.error(f"Sentiment analysis failed for text '{combined_text[:50]}...': {e}")
        return 0.0

# Function to process news files and generate sentiment results
def process_news_files(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_dir, filename)
            try:
                # Read CSV with robust error handling
                df = pd.read_csv(file_path, encoding="utf-8-sig", on_bad_lines='skip')
                if df.empty:
                    logger.info(f"No data in {file_path}")
                    continue

                # Ensure required columns exist with fallback
                required_columns = ['articleId', 'publishedDate', 'mediaUrl', 'matchedCompany', 'title', 'summary']
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = ['N/A'] * len(df)
                    df[col] = df[col].fillna('N/A')

                # Analyze sentiment based on title and summary
                df['sentiment_score'] = df.apply(lambda row: analyze_sentiment(row['title'], row['summary']), axis=1)

                # Select relevant columns for output
                sentiment_df = df[['articleId', 'matchedCompany', 'publishedDate', 'mediaUrl', 'sentiment_score']]

                # Save to share_sentiment.csv
                sharename = os.path.splitext(filename)[0].replace("_news", "")
                output_file = os.path.join(output_dir, f"{sharename}_share_sentiment.csv")
                sentiment_df.to_csv(output_file, index=False, encoding="utf-8-sig")
                logger.info(f"Generated sentiment results to {output_file} with {len(sentiment_df)} articles")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    input_dir = r"E:\hey\output\news_data"
    output_dir = r"E:\hey\output\sentiment_results"
    logger.info(f"Starting news processing at {datetime.now().strftime('%I:%M %p %z on %B %d, %Y')}")
    process_news_files(input_dir, output_dir)