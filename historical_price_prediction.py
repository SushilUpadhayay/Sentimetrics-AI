import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import logging
import requests
from datetime import datetime, timedelta
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API endpoint for candle chart data
API_URL = "https://sharehubnepal.com/data/api/v1/candle-chart/history"

# Fetch all available historical candle data from API
def fetch_historical_data(symbol):
    try:
        params = {
            "symbol": symbol,
            "resolution": "1D",
            "isAdjust": "true"
        }
        response = requests.get(API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                df = pd.DataFrame(data["data"])
                df['time'] = pd.to_datetime(df['time'], unit='ms')
                df['Open Price'] = df['open']
                df['Close Price'] = df['close']
                df = df[['time', 'Open Price', 'Close Price']].rename(columns={'time': 'publishDate'})
                logger.info(f"Fetched {len(df)} days of data for {symbol}")
                return df
            logger.error(f"API success=false or no data for {symbol}: {data}")
            return None
        logger.error(f"Failed to fetch data for {symbol}: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None

# Calculate moving average for price trend
def calculate_moving_average(df, window=5):
    df['ma_open'] = df['Open Price'].rolling(window=window).mean()
    df['ma_close'] = df['Close Price'].rolling(window=window).mean()
    return df

# Predict open and close prices based on historical pattern
def predict_historical_price(df):
    if df.empty or len(df) < 5 + 1:  # Use 5 as default window + 1 for shift
        return None, None, None, 0.0

    # Calculate moving average and price change
    df = calculate_moving_average(df, window=5)
    df['open_change'] = df['Open Price'].pct_change()
    df['close_change'] = df['Close Price'].pct_change()

    # Prepare data for linear regression, ensuring consistent samples
    df = df.dropna()  # Remove rows with NaN (after moving average)
    if len(df) < 2:  # Need at least 2 samples for prediction
        return None, None, None, 0.0

    X_open = df['ma_open'].values.reshape(-1, 1)[:-1]  # Features for open, 2D array
    y_open = df['Open Price'].shift(-1).values[:-1]    # Target for open
    X_close = df['ma_close'].values.reshape(-1, 1)[:-1]  # Features for close, 2D array
    y_close = df['Close Price'].shift(-1).values[:-1]  # Target for close

    if len(X_open) != len(y_open) or len(X_close) != len(y_close) or X_open.shape[1] != 1 or X_close.shape[1] != 1:
        logger.warning(f"Inconsistent samples or shape for {df['publishDate'].iloc[0]}: X_open={X_open.shape}, y_open={len(y_open)}, X_close={X_close.shape}, y_close={len(y_close)}")
        return None, None, None, 0.0

    # Predict open price
    model_open = LinearRegression()
    try:
        model_open.fit(X_open, y_open)
        # Ensure correct 2D shape for prediction
        last_ma_open = np.array([df['ma_open'].iloc[-1]]).reshape(1, 1)
        if last_ma_open.shape != (1, 1):
            logger.error(f"Invalid shape for last_ma_open: {last_ma_open.shape}")
            return None, None, None, 0.0
        predicted_open = model_open.predict(last_ma_open)[0]
    except Exception as e:
        logger.error(f"Error fitting open price model for {df['publishDate'].iloc[0]}: {e}")
        return None, None, None, 0.0

    # Predict close price
    model_close = LinearRegression()
    try:
        model_close.fit(X_close, y_close)
        # Ensure correct 2D shape for prediction
        last_ma_close = np.array([df['ma_close'].iloc[-1]]).reshape(1, 1)
        if last_ma_close.shape != (1, 1):
            logger.error(f"Invalid shape for last_ma_close: {last_ma_close.shape}")
            return None, None, None, 0.0
        predicted_close = model_close.predict(last_ma_close)[0]
    except Exception as e:
        logger.error(f"Error fitting close price model for {df['publishDate'].iloc[0]}: {e}")
        return None, None, None, 0.0

    # Calculate average
    predicted_average = (predicted_open + predicted_close) / 2

    # Confidence based on recent trend stability
    recent_open_changes = df['open_change'].tail(5).std()
    recent_close_changes = df['close_change'].tail(5).std()
    confidence = max(0.0, min(1.0, 1.0 - (recent_open_changes + recent_close_changes) / 2))  # Average stability

    return predicted_open, predicted_close, predicted_average, confidence

# Main prediction function
def predict_historical_patterns(symbols, output_file):
    predictions = {}
    os.makedirs(os.path.dirname(output_file) or os.path.dirname(os.path.dirname(output_file)), exist_ok=True)
    for symbol in symbols:
        df = fetch_historical_data(symbol)
        if df is not None and not df.empty:
            predicted_open, predicted_close, predicted_average, confidence = predict_historical_price(df)
            if predicted_open is not None and predicted_close is not None:
                predictions[symbol] = {
                    'predicted_open': predicted_open,
                    'predicted_close': predicted_close,
                    'predicted_average': predicted_average,
                    'confidence': confidence
                }
                pred_df = pd.DataFrame([{
                    'symbol': symbol,
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'predicted_open': predicted_open,
                    'predicted_close': predicted_close,
                    'predicted_average': predicted_average,
                    'confidence': confidence
                }])
                # Save even if partial data is available
                try:
                    pred_df.to_csv(output_file, index=False, mode='a', header=not os.path.exists(output_file))
                    logger.info(f"Predicted {symbol}: Open = {predicted_open:.2f}, Close = {predicted_close:.2f}, Average = {predicted_average:.2f}, Confidence = {confidence:.2f}")
                except Exception as e:
                    logger.error(f"Error saving prediction for {symbol}: {e}")
            else:
                logger.warning(f"No valid prediction for {symbol}")
        else:
            logger.warning(f"No data fetched for symbol {symbol}")

    return predictions

if __name__ == "__main__":
    symbols = ["NABIL", "NIMB", "EBL", "NICA", "MBL", "SHL", "TRH", "OHL", "NHPC", "BPCL",
        "CHCL", "STC", "BBC", "NUBL", "SANIMA", "NABBC", "NICL", "UAIL", "NIL", "IGI",
        "NLIC", "SICL", "UNL", "BFC", "GFCL", "NMB", "PRVU", "GMFIL", "SWBBL", "EDBL",
        "PCBL", "LBBL", "AHPC", "ALICL", "SJLIC", "GBBL", "JBBL", "CORBL", "SADBL", "SHINE",
        "FMDBL", "GBIMEP", "MFIL", "NBL", "NLG", "SKBBL", "RLFL", "RBCLPO", "BARUN", "VLBS",
        "HLBSL", "API", "HEIP", "GILB", "MERO", "HIDCL", "NMFBS", "RSDC", "AKPL", "UMHL",
        "SMATA", "CHL", "HPPL", "MSLB", "SEF", "SMB", "RADHI", "WNLB", "NADEP", "PMHPL",
        "KPCL", "AKJCL", "ALBSL", "GMFBS", "HURJA", "GLBSL", "UNHPL", "ILBS", "NBF2", "RHPL",
        "SIGS2", "SAPDBL", "CMF2", "NICBF", "SCB", "HBL", "SBI", "LSL", "KBL",
        "SBL", "CBBL", "DDBL", "RBCL", "NLICL", "HEI", "SPIL", "PRIN", "SALICO", "LICN",
        "NFS", "BNL", "GUFL", "CIT", "BNT", "HDL", "PFL", "SIFC", "CFCL", "JFL",
        "SFCL", "ICFC", "NTC", "MBLD2085", "NMB50", "NICAD8283", "SFMF", "SRBLD83", "LBLD86", "HDHPC",
        "GWFD83", "ADBLD83", "NICLBSL", "NBLD82", "SMPDA", "LUK", "LEC", "SSHL", "SGIC", "UMRH",
        "CGH", "NIBD84", "KEF", "SHEL", "CHDC", "PSF", "KSBBLD87", "JBLB", "NBLD87", "SAMAJ",
        "NICSF", "PROFL", "GBIME", "CZBIL", "MDB", "HLI", "NMLBBL", "ADBL", "MLBL", "KSBBL",
        "NIMBPO", "MPFL", "MNBBL", "SLBBL", "SINDU", "GBLBS", "SHPC", "KMCDB", "MLBBL", "RIDI",
        "LLBS", "MLBLPO", "MATRI", "JSLBB", "NMBMF", "SWMF", "NGPL", "GRDBL", "KKHC", "MND84/85",
        "MLBS", "MBJC", "GBBD85", "ULBSL", "CYCL", "RFPL", "DORDI", "KDBY", "PBD88", "SGHC",
        "MHL", "USHEC", "DLBS", "BHPL", "SPL", "SMH", "MKHC", "SFEF", "MHCL", "ANLB",
        "MAKAR", "MKHL", "DOLTI", "CITY", "PRSF", "MCHL", "SCBD", "RMF2", "MEL", "RAWA",
        "SIGS3", "NRM", "C30MF", "GCIL", "TSHL", "KBSH", "LBBLD89", "LVF2", "MEHL", "ULHC",
        "CLI", "MANDU", "HATHY", "BGWT", "SONA", "TVCL", "H8020", "VLUCL", "CKHL", "NWCL",
        "NICGF2", "KSY", "SARBTM", "NIBLSTF", "MNMF1", "GMLI", "GSY", "NMIC", "CREST", "MBLEF",
        "PURE", "SANVI", "DHPL", "FOWAD", "SPDL", "NHDL", "USLB", "JOSHI", "ACLBSL", "UPPER",
        "SLBSL", "GHL", "SHIVM", "UPCL", "MHNL", "PPCL", "SAND2085", "SMFBS", "SJCL", "NRIC",
        "SBIBD86", "NRN", "MEN", "PMLI", "NIFRA", "SLCF", "GLH", "MLBSL", "MFLD85", "RURU",
        "NCCD86", "SBCF", "NIBSF2", "RMF1", "SRLI", "PBD85", "MBLD87", "MKJC", "JBBD87", "SAHAS",
        "TPC", "MMF1", "NBF3", "SPC", "NYADI", "NBLD85", "BNHC", "ENL", "NESDO", "EBLD86",
        "GVL", "BHL", "CCBD88", "NICFC", "BHDC", "HHL", "UHEWA", "GIBF1", "RHGCL", "SBID83",
        "PBD84", "AVYAN", "EBLD85", "SPHL", "PPL", "NSIF2", "SIKLES", "KBLD89", "EHPL",
        "SHLB", "PHCL", "NIBLGF", "SAGF", "UNLB", "SMHL", "AHL", "KDL", "EBLEB89", "TAMOR",
        "SMJC", "BEDC", "IHL", "ILI", "USHL", "MLBLD89", "RNLI", "SNLI", "MSHL", "MMKJL",
        "MKCL", "HRL", "ICFCD88", "NMBHF2", "EBLD91", "OMPL", "RSY", "NIFRAGED", "TTL"]
    output_file = r"E:\hey\output\history prediction\history_price_prediction.csv"
    logger.info(f"Starting news processing at {datetime.now().strftime('%I:%M %p %z on %B %d, %Y')}")
    predictions = predict_historical_patterns(symbols, output_file)