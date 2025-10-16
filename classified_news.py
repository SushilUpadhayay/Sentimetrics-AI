import pandas as pd # handle data in a table-like structure, manage csv files
import langdetect # to detect language of the text
import schedule # schedules tasks to run at specific intervals, like every 6 hours.
import time
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import unicodedata
import requests
from datetime import datetime
import pytz
import re

# Set up logging with Nepal time zone
nepal_tz = pytz.timezone('Asia/Kathmandu')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s +0545 - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('news_processing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load NEPSE company data from nepse.xlsx
nepse_data = {
    "Symbol": [
        "NABIL", "NIMB", "EBL", "NICA", "MBL", "SHL", "TRH", "OHL", "NHPC", "BPCL",
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
        "MKCL", "HRL", "ICFCD88", "NMBHF2", "EBLD91", "OMPL", "RSY", "NIFRAGED", "TTL"
    ],
    "Security Name": [
        "Nabil Bank Limited", "Nepal Investment Mega Bank Limited", "Everest Bank Limited", "NIC Asia Bank Ltd.",
        "Machhapuchhre Bank Limited", "Soaltee Hotel Limited", "Taragaon Regency Hotel Limited", "Oriental Hotels Limited",
        "National Hydro Power Company Limited", "Butwal Power Company Limited", "Chilime Hydropower Company Limited",
        "Salt Trading Corporation", "Bishal Bazar Company Limited", "Nirdhan Utthan Laghubitta Bittiya Sanstha Limited",
        "Sanima Bank Limited", "Narayani Development Bank Limited", "Nepal Insurance Co. Ltd.", "United Ajod Insurance Limited",
        "Neco Insurance Limited", "IGI Prudential insurance Limited", "Nepal Life Insurance Co. Ltd.", "Shikhar Insurance Co. Ltd.",
        "Unilever Nepal Limited", "Best Finance Company Ltd.", "Goodwill Finance Limited", "NMB Bank Limited",
        "Prabhu Bank Limited", "Guheshowori Merchant Bank & Finance Co. Ltd.", "Swabalamban Laghubitta Bittiya Sanstha Limited",
        "Excel Development Bank Ltd.", "Prime Commercial Bank Ltd.", "Lumbini Bikas Bank Ltd.", "Arun Valley Hydropower Development Co. Ltd.",
        "Asian Life Insurance Co. Limited", "SuryaJyoti Life Insurance Company Limited", "Garima Bikas Bank Limited",
        "Jyoti Bikas Bank Limited", "Corporate Development Bank Limited", "Shangrila Development Bank Ltd.",
        "Shine Resunga Development Bank Ltd.", "First Micro Finance Laghubitta Bittiya Sanstha Limited",
        "Global IME Bank Ltd. Promoter Share", "Manjushree Finance Ltd.", "Nepal Bank Limited", "NLG Insurance Company Ltd.",
        "Sana Kisan Bikas Laghubitta Bittiya Sanstha Limited", "Reliance Finance Ltd.", "Rastriya Beema Company Limited Promoter Share",
        "Barun Hydropower Co. Ltd.", "Vijaya laghubitta Bittiya Sanstha Ltd.", "Himalayan Laghubitta Bittiya Sanstha Limited",
        "Api Power Company Ltd.", "Himalayan Everest Insurance Limited Promoter", "Global IME Laghubitta Bittiya Sanstha Ltd.",
        "Mero Microfinance Bittiya Sanstha Ltd.", "Hydorelectricity Investment and Development Company Ltd",
        "National Laghubitta Bittiya Sanstha Limited", "RSDC Laghubitta Bittiya Sanstha Ltd.", "Arun Kabeli Power Ltd.",
        "United Modi Hydropower Ltd.", "Samata Gharelu Laghubitta Bittiya Sanstha Limited", "Chhyangdi Hydropower Ltd.",
        "Himalayan Power Partner Ltd.", "Mahuli Laghubitta Bittiya Sanstha Limited", "Siddhartha Equity Fund",
        "Support Microfinance Bittiya Sanstha Ltd.", "Radhi Bidyut Company Ltd", "Wean Nepal Laghubitta Bittiya Sanstha Limited",
        "Nadep Laghubittiya bittya Sanstha Ltd.", "Panchakanya Mai Hydropower Ltd", "Kalika power Company Ltd",
        "Ankhu Khola Jalvidhyut Company Ltd", "Asha Laghubitta Bittiya Sanstha Ltd", "Ganapati Laghubitta Bittiya Sanstha Limited",
        "Himalaya Urja Bikas Company Limited", "Gurans Laghubitta Bittiya Sanstha Limited", "Union Hydropower Limited",
        "Infinity Laghubitta Bittiya Sanstha Limited", "NABIL BALANCED FUND-2", "RASUWAGADHI HYDROPOWER COMPANY LIMITED",
        "Siddhartha Investment Growth Scheme - 2", "Saptakoshi Development Bank Ltd", "CITIZENS MUTUAL FUND 2",
        "NIC Asia Balanced Fund", "Standard Chartered Bank Limited", "Himalayan Bank Limited", "Nepal SBI Bank Limited",
        "Laxmi Sunrise Bank Limited", "Kumari Bank Limited", "Siddhartha Bank Limited", "Chhimek Laghubitta Bittiya Sanstha Limited",
        "Deprosc Laghubitta Bittiya Sanstha Limited", "Rastriya Beema Company Limited", "National Life Insurance Co. Ltd.",
        "Himalayan Everest Insurance Limited", "Siddhartha Premier Insurance Limited", "Prabhu Insurance Ltd.",
        "Sagarmatha Lumbini Insurance Co. Limited", "Life Insurance Corporation (Nepal) Limited", "Nepal Finance Ltd.",
        "Bottlers Nepal (Balaju) Limited", "Gurkhas Finance Ltd.", "Citizen Investment Trust", "Bottlers Nepal (Terai) Limited",
        "Himalayan Distillery Limited", "Pokhara Finance Ltd.", "Shree Investment Finance Co. Ltd.", "Central Finance Co. Ltd.",
        "Janaki Finance Company Limited", "Samriddhi Finance Company Limited", "ICFC Finance Limited",
        "Nepal Doorsanchar Company Limited", "10.25% Machhapuchhre Bank Debenture 2085", "NMB 50",
        "11% NIC Asia Debenture 082/83", "Sunrise First Mutual Fund", "10.25% Sunrise Bank Debenture 2083",
        "10% Laxmi Bank Debenture 2086", "Himal Dolakha Hydropower Company Limited", "12 % Goodwill Finance Limited Debenture 2083",
        "10.35% Agricultural Bank Debenture 2083", "NIC ASIA Laghubitta Bittiya Sanstha Limited", "10% Nabil Debenture 2082",
        "Sampada Laghubitta Bittiya Sanstha Limited", "Laxmi Unnati Kosh", "Liberty Energy Company Limited",
        "Shiva Shree Hydropower Ltd", "Sanima GIC Insurance Limited", "United IDI Mardi RB Hydropower Limited",
        "Chandragiri Hills Limited", "8.5% Nepal Investment Bank Debenture 2084", "Kumari Equity Fund",
        "Singati Hydro Energy Limited", "CEDB Holdings Limited", "Prabhu Select Fund", "9% Kamana Sewa Bikas Bank Limited Debenture 2087",
        "Jeevan Bikas Laghubitta Bittya Sanstha Ltd", "8.5% Nepal Bank Debenture 2087", "Samaj Laghubittya Bittiya Sanstha Limited",
        "NIC Asia Select Fund 30", "Progressive Finance Limited", "Global IME Bank Limited", "Citizens Bank International Limited",
        "Miteri Development Bank Limited", "Himalayan Life Insurance Limited", "Nerude Mirmire Laghubitta Bittiya Sanstha Limited",
        "Agricultural Development Bank Limited", "Mahalaxmi Bikas Bank Ltd.", "Kamana Sewa Bikas Bank Limited",
        "Nepal Investment Mega Bank Ltd. Promoter Share", "Multipurpose Finance Company Limited", "Muktinath Bikas Bank Ltd.",
        "Swarojgar Laghubitta Bittiya Sanstha Ltd.", "Sindhu Bikash Bank Ltd.", "Grameen Bikas Laghubitta Bittiya Sanstha Ltd.",
        "Sanima Mai Hydropower Ltd.", "Kalika Laghubitta Bittiya Sanstha Ltd", "Mithila LaghuBitta Bittiya Sanstha Limited",
        "Ridi Power Company Limited", "Laxmi Laghubitta Bittiya Sanstha Ltd.", "Mahalxmi Bikas Bank Ltd. Promotor Share",
        "Matribhumi Lagubitta Bittiya Sanstha Limited", "Janautthan Samudayic Laghubitta Bittya Sanstha Limited",
        "NMB Microfinance Bittiya Sanstha Ltd.", "Suryodaya Womi Laghubitta Bittiya Sanstha Limited",
        "Ngadi Group Power Ltd.", "Green Development Bank Ltd.", "Khanikhola Hydropower Co. Ltd.",
        "Muktinath Debenture 2084/85", "Manushi Laghubitta Bittiya Sanstha Limited", "Madhya Bhotekoshi Jalavidyut Company Limited",
        "Garima Debenture", "Upakar Laghubitta Bittiya Sanstha Limited", "CYC Nepal Laghubitta Bittiya Sanstha Limited",
        "River Falls Power Limited", "Dordi Khola Jal Bidyut Company Limited", "Kumari Dhanabriddhi Yojana",
        "10% Prime Debenture 2088", "Swet-Ganga Hydropower & Construction Limited", "Mandakini Hydropower Limited",
        "Upper Solu Hydro Electric Company Limited", "Dhaulagiri Laghubitta Bittiya Sanstha Limited",
        "Balephi Hydropower Limited", "Shuvam Power Limited", "Super Mai Hydropower Limited",
        "Maya Khola Hydropower Company Limited", "Sunrise Focused Equity Fund", "Molung Hydropower Company Limited",
        "Aatmanirbhar Laghubitta Bittiya Sanstha Limited", "Makar Jitumaya Suri Hydropower Limited",
        "Mai Khola Hydropower Limited", "Dolti Power Company Limited", "City Hotel Limited", "Prabhu Smart Fund",
        "Menchhiyam Hydropower Limited", "10.30% Standard Chartered Bank Limited Debenture", "RBB Mutual Fund 2",
        "Modi Energy Limited", "Rawa Energy Development Limited", "Siddhartha Investment Growth Scheme 3",
        "Nepal Republic Media Limited", "Citizens Super 30 Mutual Fund", "Ghorahi Cement Industry Limited",
        "Three Star Hydropower Limited", "Kutheli Bukhari Small Hydropower Limited", "11% L.B.B.L. Debenture 2089",
        "Laxmi Value Fund 2", "Manakamana Engineering Hydropower Limited", "Upper Lohore Khola Hydropower Company Limited",
        "Citizen Life Insurance Company Limited", "Mandu Hydropower Limited", "Hathway Investment Nepal Limited",
        "Bhagawati Hydropower Development Company Limited", "Sonapur Minerals And Oil Limited",
        "Trishuli Jal Vidhyut Company Limited", "Himalayan 80-20", "Vision Lumbini Urja Company Limited",
        "Chirkhwa Hydropower Limited", "Nepal Warehousing Company Limited", "NIC ASIA Growth Fund-2",
        "Kumari Sabal Yojana", "Sarbottam Cement Limited", "NIBL Stable Fund", "Muktinath Mutual Fund 1",
        "Guardian Micro Life Insurance Limited", "Garima Samriddhi Yojana", "Nepal Micro Insurance Company Limited",
        "Crest Micro Life Insurance Limited", "MBL Equity Fund", "Pure Energy Limited", "Sanvi Energy Limited",
        "Dibyashwori Hydropower Ltd.", "Forward Microfinance Laghubitta Bittiya Sanstha Limited",
        "Synergy Power Development Ltd.", "Nepal Hydro Developers Ltd.", "Unnati Sahakarya Laghubitta Bittiya Sanstha Limited",
        "Joshi Hydropower Development Company Ltd", "Aarambha Chautari Laghubitta Bittiya Sanstha Limited",
        "Upper Tamakoshi Hydropower Ltd", "Samudayik Laghubitta Bittiya Sanstha Limited", "Ghalemdi Hydro Limited",
        "SHIVAM CEMENTS LTD", "UNIVERSAL POWER COMPANY LTD", "Mountain Hydro Nepal Limited",
        "Panchthar Power Compant Limited", "10% Sanima Bank Limited Debenture", "Swabhimaan Laghubitta Bittiya Sanstha Limited",
        "SANJEN JALAVIDHYUT COMPANY LIMITED", "Nepal Reinsurance Company Limited", "10% Nepal SBI Bank Debenture 2086",
        "NRN Infrastructure and Development Limited", "Mountain Energy Nepal Limited", "Prabhu Mahalaxmi Life Insurance Limited",
        "Nepal Infrastructure Bank Limited", "Sanima Large Cap Fund", "GreenLife Hydropower Limited",
        "Mahila Lagubitta Bittiya Sanstha Limited", "9.5% Manjushree Finance Limited Debenture 2085",
        "Ru Ru Jalbidhyut Pariyojana Limited", "9.5% NCC Debenture 2086", "Sunrise Bluechip Fund",
        "NIBL Samriddhi Fund -2", "RBB Mutual Fund 1", "Sanima Reliance Life Insurance Limited",
        "8.75 % Prime Debenture 2085", "8.5% Machhapuchchhre Debenture 2087", "Mailung Khola Jal Vidhyut Company Limited",
        "Jyoti Bikash Bank Bond 2087", "Sahas Urja Limited", "Terhathum Power Company Limited",
        "Mega Mutual Fund -1", "Nabil Balanced Fund-3", "Samling Power Company Limited", "Nyadi Hydropower Limited",
        "Nabil Debenture 2085", "Buddha Bhumi Nepal Hydropower Company Limited", "Emerging Nepal Limited",
        "NESDO Sambridha Laghubitta Bittiya Sanstha Limited", "Everest Bank Limited", "Green Ventures Limited",
        "Balephi Hydropower Limited", "Century Debenture 2088", "NIC Asia Flexi CAP Fund",
        "Bindhyabasini Hydropower Development Company Limited", "Himalayan Hydropower Limited",
        "Upper Hewakhola Hydropower Company Limited", "Global IME Balanced Fund-1",
        "Rapti Hydro And General Construction Limited", "10.25% Nepal SBI Bank Debenture 2083",
        "10.15% Prime Debenture 2084", "Aviyan Laghubitta Bittiya Sanstha Limited", "10.50% Everest Bank Limited Debenture 2085",
        "Sayapatri Hydropower Limited", "People's Power Limited", "NMB Sulav Investment Fund - 2",
        "Sikles Hydropower Limited", "11% KBL Debenture 2089", "Eastern Hydropower Limited",
        "Shrijanshil Laghubitta Bittiya Sanstha Limited", "Peoples Hydropower Company Limited", "NIBL Growth Fund",
        "Sanima Growth Fund", "Unique Nepal Laghubitta Bittiya Sanstha Limited", "Super Madi Hydropower Limited",
        "Asian Hydropower Limited", "Kalinchowk Darshan Limited", "Everest Bank Limited Energy Bond",
        "Sanima Middle Tamor Hydropower Limited", "Sagarmatha Jalabidhyut Company Limited",
        "Bhugol Energy Development Company Limited", "Ingwa Hydropower Limited", "IME Life Insurance Company Limited",
        "Upper Syange Hydropower Limited", "11% Mahalaxmi Debenture 2089", "Reliable Nepal Life Insurance Limited",
        "Sun Nepal Life Insurance Company Limited", "Mid Solu Hydropower Limited",
        "Mathillo Mailun Khola Jalvidhyut Limited", "Muktinath Krishi Company Limited", "Himalayan Reinsurance Limited",
        "9% ICFC Finance Limited Debenture 2088", "NMB Hybrid Fund L- II", "Everest Bank Limited Debenture 2091",
        "Om Megashree Pharmaceuticals Limited", "Reliable Samriddhi Yojana", "Nifra Green Energy Debenture 6% - 2088/89",
        "Trade Tower Limited"
    ]
}
nepse_df = pd.DataFrame(nepse_data)

# Nepali translations (shortened for brevity, expand as needed)
nepali_translations = {
    "Nabil Bank Limited": ["नबिल बैंक लिमिटेड", "नबिल"],
    "Nepal Investment Mega Bank Limited": ["नेपाल इनभेष्टमेन्ट मेगा बैंक लिमिटेड", "निम्ब"],
    "Everest Bank Limited": ["एभरेष्ट बैंक लिमिटेड", "एभरेष्ट"],
    "NIC Asia Bank Ltd.": ["एनआईसी एसिया बैंक लिमिटेड", "एनआईसी"],
    "Machhapuchhre Bank Limited": ["माछापुच्छ्रे बैंक लिमिटेड", "एमबीएल"],
    "Soaltee Hotel Limited": ["सोल्टी होटल लिमिटेड", "सोल्टी"],
    "Taragaon Regency Hotel Limited": ["तारागाउँ रिजेन्सी होटल लिमिटेड", "तारागाउँ"],
    "Oriental Hotels Limited": ["ओरिएन्टल होटल्स लिमिटेड", "ओरिएन्टल"],
    "National Hydro Power Company Limited": ["राष्ट्रीय जलविद्युत कम्पनी लिमिटेड", "राष्ट्रीय जलविद्युत"],
    "Butwal Power Company Limited": ["बुटवल पावर कम्पनी लिमिटेड", "बुटवल पावर"],
    "Chilime Hydropower Company Limited": ["चिलिमे जलविद्युत कम्पनी लिमिटेड", "चिलिमे"],
    "Salt Trading Corporation": ["नमक व्यापार निगम", "नमक व्यापार"],
    "Bishal Bazar Company Limited": ["बिशाल बजार कम्पनी लिमिटेड", "बिशाल बजार"],
    "Nirdhan Utthan Laghubitta Bittiya Sanstha Limited": ["निर्धन उत्थान लघुबित्त बित्तीय संस्था लिमिटेड", "निर्धन उत्थान"],
    "Sanima Bank Limited": ["सनिमा बैंक लिमिटेड", "सनिमा"],
    "Narayani Development Bank Limited": ["नारायणी डेभलपमेन्ट बैंक लिमिटेड", "नारायणी"],
    "Nepal Insurance Co. Ltd.": ["नेपाल इन्स्योरेन्स कम्पनी लिमिटेड", "नेपाल इन्स्योरेन्स"],
    "United Ajod Insurance Limited": ["युनाइटेड अजोड इन्स्योरेन्स लिमिटेड", "अजोड"],
    "Neco Insurance Limited": ["नेको इन्स्योरेन्स लिमिटेड", "नेको"],
    "IGI Prudential Insurance Limited": ["आईजीआई प्रुडेन्सियल इन्स्योरेन्स लिमिटेड", "आईजीआई"],
    "Nepal Life Insurance Co. Ltd.": ["नेपाल लाइफ इन्स्योरेन्स कम्पनी लिमिटेड", "नेपाल लाइफ"],
    "Shikhar Insurance Co. Ltd.": ["शिखर इन्स्योरेन्स कम्पनी लिमिटेड", "शिखर"],
    "Unilever Nepal Limited": ["युनिलिभर नेपाल लिमिटेड", "युनिलिभर"],
    "Best Finance Company Ltd.": ["बेस्ट फाइनान्स कम्पनी लिमिटेड", "बेस्ट"],
    "Goodwill Finance Limited": ["गुडविल फाइनान्स लिमिटेड", "गुडविल"],
    "NMB Bank Limited": ["एनएमबी बैंक लिमिटेड", "एनएमबी"],
    "Prabhu Bank Limited": ["प्रभु बैंक लिमिटेड", "प्रभु"],
    "Guheshowori Merchant Bank & Finance Co. Ltd.": ["गुहेश्वरी मर्चेन्ट बैंक एण्ड फाइनान्स लिमिटेड", "गुहेश्वरी"],
    "Swabalamban Laghubitta Bittiya Sanstha Limited": ["स्वावलम्बन लघुबित्त बित्तीय संस्था लिमिटेड", "स्वावलम्बन"],
    "Excel Development Bank Ltd.": ["एक्सेल डेभलपमेन्ट बैंक लिमिटेड", "एक्सेल"],
    "Prime Commercial Bank Ltd.": ["प्राइम कमर्सियल बैंक लिमिटेड", "प्राइम"],
    "Lumbini Bikas Bank Ltd.": ["लुम्बिनी विकास बैंक लिमिटेड", "लुम्बिनी"],
    "Arun Valley Hydropower Development Co. Ltd.": ["अरुण भ्याली जलविद्युत विकास कम्पनी लिमिटेड", "अरुण"],
    "Asian Life Insurance Co. Limited": ["एशियन लाइफ इन्स्योरेन्स कम्पनी लिमिटेड", "एशियन"],
    "SuryaJyoti Life Insurance Company Limited": ["सूर्यज्योति लाइफ इन्स्योरेन्स कम्पनी लिमिटेड", "सूर्यज्योति"],
    "Garima Bikas Bank Limited": ["गरिमा विकास बैंक लिमिटेड", "गरिमा"],
    "Jyoti Bikas Bank Limited": ["ज्योति विकास बैंक लिमिटेड", "ज्योति"],
    "Corporate Development Bank Limited": ["कर्पोरेट डेभलपमेन्ट बैंक लिमिटेड", "कर्पोरेट"],
    "Shangrila Development Bank Ltd.": ["शंखरिला डेभलपमेन्ट बैंक लिमिटेड", "शंखरिला"],
    "Shine Resunga Development Bank Ltd.": ["शाइन रेसुङगा डेभलपमेन्ट बैंक लिमिटेड", "शाइन"],
    "First Micro Finance Laghubitta Bittiya Sanstha Limited": ["फस्ट माइक्रो फाइनान्स लघुबित्त बित्तीय संस्था लिमिटेड", "फस्ट"],
    "Global IME Bank Ltd. Promoter Share": ["ग्लोबल आइएमई बैंक प्रोमोटर शेयर", "ग्लोबल"],
    "Manjushree Finance Ltd.": ["मान्जुश्री फाइनान्स लिमिटेड", "मान्जुश्री"],
    "Nepal Bank Limited": ["नेपाल बैंक लिमिटेड", "नेपाल बैंक"],
    "NLG Insurance Company Ltd.": ["एनएलजी इन्स्योरेन्स कम्पनी लिमिटेड", "एनएलजी"],
    "Sana Kisan Bikas Laghubitta Bittiya Sanstha Limited": ["साना किसान विकास लघुबित्त बित्तीय संस्था लिमिटेड", "साना किसान"],
    "Reliance Finance Ltd.": ["रिलायन्स फाइनान्स लिमिटेड", "रिलायन्स"],
    "Rastriya Beema Company Limited Promoter Share": ["राष्ट्रीय बीमा कम्पनी लिमिटेड प्रोमोटर शेयर", "राष्ट्रीय बीमा"],
    "Barun Hydropower Co. Ltd.": ["बरुण जलविद्युत कम्पनी लिमिटेड", "बरुण"],
    "Vijaya Laghubitta Bittiya Sanstha Ltd.": ["विजया लघुबित्त बित्तीय संस्था लिमिटेड", "विजया"],
    "Himalayan Laghubitta Bittiya Sanstha Limited": ["हिमालयन लघुबित्त बित्तीय संस्था लिमिटेड", "हिमालयन लघु"],
    "Api Power Company Ltd.": ["अपि पावर कम्पनी लिमिटेड", "अपि"],
    "Himalayan Everest Insurance Limited Promoter": ["हिमालयन एभरेष्ट इन्स्योरेन्स लिमिटेड प्रोमोटर", "हिमालयन एभरेष्ट"],
    "Global IME Laghubitta Bittiya Sanstha Ltd.": ["ग्लोबल आइएमई लघुबित्त बित्तीय संस्था लिमिटेड", "ग्लोबल लघु"],
    "Mero Microfinance Bittiya Sanstha Ltd.": ["मेरो माइक्रोफाइनान्स बित्तीय संस्था लिमिटेड", "मेरो"],
    "Hydorelectricity Investment and Development Company Ltd": ["जलविद्युत लगानी तथा विकास कम्पनी लिमिटेड", "जलविद्युत लगानी"],
    "National Laghubitta Bittiya Sanstha Limited": ["राष्ट्रीय लघुबित्त बित्तीय संस्था लिमिटेड", "राष्ट्रीय लघु"],
    "RSDC Laghubitta Bittiya Sanstha Ltd.": ["आरएसडीसी लघुबित्त बित्तीय संस्था लिमिटेड", "आरएसडीसी"],
    "Arun Kabeli Power Ltd.": ["अरुण काबेली पावर लिमिटेड", "अरुण काबेली"],
    "United Modi Hydropower Ltd.": ["युनाइटेड मोदी जलविद्युत लिमिटेड", "युनाइटेड मोदी"],
    "Samata Gharelu Laghubitta Bittiya Sanstha Limited": ["समता घरेलु लघुबित्त बित्तीय संस्था लिमिटेड", "समता"],
    "Chhyangdi Hydropower Ltd.": ["छ्याङ्दी जलविद्युत लिमिटेड", "छ्याङ्दी"],
    "Himalayan Power Partner Ltd.": ["हिमालयन पावर पार्टनर लिमिटेड", "हिमालयन पावर"],
    "Mahuli Laghubitta Bittiya Sanstha Limited": ["महुली लघुबित्त बित्तीय संस्था लिमिटेड", "महुली"],
    "Siddhartha Equity Fund": ["सिद्धार्थ इक्विटी फन्ड", "सिद्धार्थ"],
    "Support Microfinance Bittiya Sanstha Ltd.": ["सपोर्ट माइक्रोफाइनान्स बित्तीय संस्था लिमिटेड", "सपोर्ट"],
    "Radhi Bidyut Company Ltd": ["राधी विद्युत कम्पनी लिमिटेड", "राधी"],
    "Wean Nepal Laghubitta Bittiya Sanstha Limited": ["वीन नेपाल लघुबित्त बित्तीय संस्था लिमिटेड", "वीन"],
    "Nadep Laghubittiya Bittya Sanstha Ltd.": ["नादेप लघुबित्त बित्तीय संस्था लिमिटेड", "नादेप"],
    "Panchakanya Mai Hydropower Ltd": ["पञ्चकन्या माई जलविद्युत लिमिटेड", "पञ्चकन्या"],
    "Kalika Power Company Ltd": ["कालिका पावर कम्पनी लिमिटेड", "कालिका"],
    "Ankhu Khola Jalvidhyut Company Ltd": ["अन्खु खोला जलविद्युत कम्पनी लिमिटेड", "अन्खु"],
    "Asha Laghubitta Bittiya Sanstha Ltd": ["आशा लघुबित्त बित्तीय संस्था लिमिटेड", "आशा"],
    "Ganapati Laghubitta Bittiya Sanstha Limited": ["गणपति लघुबित्त बित्तीय संस्था लिमिटेड", "गणपति"],
    "Himalaya Urja Bikas Company Limited": ["हिमalaya ऊर्जा विकास कम्पनी लिमिटेड", "हिमalaya ऊर्जा"],
    "Gurans Laghubitta Bittiya Sanstha Limited": ["गुराँस लघुबित्त बित्तीय संस्था लिमिटेड", "गुराँस"],
    "Union Hydropower Limited": ["युनियन जलविद्युत लिमिटेड", "युनियन"],
    "Infinity Laghubitta Bittiya Sanstha Limited": ["इन्फिनिटी लघुबित्त बित्तीय संस्था लिमिटेड", "इन्फिनिटी"],
    "NABIL BALANCED FUND-2": ["नबिल ब्यालेन्स्ड फन्ड-२", "नबिल फन्ड"],
    "RASUWAGADHI HYDROPOWER COMPANY LIMITED": ["रसुवागढी जलविद्युत कम्पनी लिमिटेड", "रसुवागढी"],
    "Siddhartha Investment Growth Scheme - 2": ["सिद्धार्थ लगानी वृद्धि योजना - २", "सिद्धार्थ योजना"],
    "Saptakoshi Development Bank Ltd": ["सप्तकोशी विकास बैंक लिमिटेड", "सप्तकोशी"],
    "CITIZENS MUTUAL FUND 2": ["सिटिजन्स म्युचुअल फन्ड २", "सिटिजन्स"],
    "NIC Asia Balanced Fund": ["एनआईसी एसिया ब्यालेन्स्ड फन्ड", "एनआईसी फन्ड"],
    "Standard Chartered Bank Limited": ["स्टान्डर्ड चार्टर्ड बैंक लिमिटेड", "एससीबी"],
    "Himalayan Bank Limited": ["हिमालयन बैंक लिमिटेड", "हिमालयन"],
    "Nepal SBI Bank Limited": ["नेपाल एसबीआई बैंक लिमिटेड", "एसबीआई"],
    "Laxmi Sunrise Bank Limited": ["लक्ष्मी सनराइज बैंक लिमिटेड", "लक्ष्मी"],
    "Kumari Bank Limited": ["कुमारी बैंक लिमिटेड", "कुमारी"],
    "Siddhartha Bank Limited": ["सिद्धार्थ बैंक लिमिटेड", "सिद्धार्थ"],
    "Chhimek Laghubitta Bittiya Sanstha Limited": ["छिमेक लघुबित्त बित्तीय संस्था लिमिटेड", "छिमेक"],
    "Deprosc Laghubitta Bittiya Sanstha Limited": ["डेप्रोस्क लघुबित्त बित्तीय संस्था लिमिटेड", "डेप्रोस्क"],
    "Rastriya Beema Company Limited": ["राष्ट्रीय बीमा कम्पनी लिमिटेड", "राष्ट्रीय बीमा"],
    "National Life Insurance Co. Ltd.": ["नेशनल लाइफ इन्स्योरेन्स कम्पनी लिमिटेड", "नेशनल"],
    "Himalayan Everest Insurance Limited": ["हिमालयन एभरेष्ट इन्स्योरेन्स लिमिटेड", "एभरेष्ट इन्स्योरेन्स"],
    "Siddhartha Premier Insurance Limited": ["सिद्धार्थ प्रिमियर इन्स्योरेन्स लिमिटेड", "सिद्धार्थ प्रिमियर"],
    "Prabhu Insurance Ltd.": ["प्रभु इन्स्योरेन्स लिमिटेड", "प्रभु"],
    "Sagarmatha Lumbini Insurance Co. Limited": ["सगरमाथा लुम्बिनी इन्स्योरेन्स कम्पनी लिमिटेड", "सगरमाथा"],
    "Life Insurance Corporation (Nepal) Limited": ["लाइफ इन्स्योरेन्स निगम (नेपाल) लिमिटेड", "लाइफ"],
    "Nepal Finance Ltd.": ["नेपाल फाइनान्स लिमिटेड", "नेपाल फाइनान्स"],
    "Bottlers Nepal (Balaju) Limited": ["बोटलर्स नेपाल (बालाजु) लिमिटेड", "बोटलर्स"],
    "Gurkhas Finance Ltd.": ["गुर्खास फाइनान्स लिमिटेड", "गुर्खास"],
    "Citizen Investment Trust": ["सिटिजन इनभेष्टमेन्ट ट्रस्ट", "सिटिजन"],
    "Bottlers Nepal (Terai) Limited": ["बोटलर्स नेपाल (तराई) लिमिटेड", "तराई बोटलर्स"],
    "Himalayan Distillery Limited": ["हिमालयन डिस्टिलरी लिमिटेड", "हिमालयन डिस्टिलरी"],
    "Pokhara Finance Ltd.": ["पोखरा फाइनान्स लिमिटेड", "पोखरा"],
    "Shree Investment Finance Co. Ltd.": ["श्री इनभेष्टमेन्ट फाइनान्स कम्पनी लिमिटेड", "श्री"],
    "Central Finance Co. Ltd.": ["सेन्ट्रल फाइनान्स कम्पनी लिमिटेड", "सेन्ट्रल"],
    "Janaki Finance Company Limited": ["जनकी फाइनान्स कम्पनी लिमिटेड", "जनकी"],
    "Samriddhi Finance Company Limited": ["समृद्धि फाइनान्स कम्पनी लिमिटेड", "समृद्धि"],
    "ICFC Finance Limited": ["आईसीएफसी फाइनान्स लिमिटेड", "आईसीएफसी"],
    "Nepal Doorsanchar Company Limited": ["नेपाल डोरसंचार कम्पनी लिमिटेड", "एनटीसी"],
    "10.25% Machhapuchhre Bank Debenture 2085": ["१०.२५% माछापुच्छ्रे बैंक डिबेन्चर २०८५", "माछापुच्छ्रे डिबेन्चर"],
    "NMB 50": ["एनएमबी ५०", "एनएमबी ५०"],
    "11% NIC Asia Debenture 082/83": ["११% एनआईसी एसिया डिबेन्चर ०८२/८३", "एनआईसी डिबेन्चर"],
    "Sunrise First Mutual Fund": ["सनराइज फस्ट म्युचुअल फन्ड", "सनराइज"],
    "10.25% Sunrise Bank Debenture 2083": ["१०.२५% सनराइज बैंक डिबेन्चर २०८३", "सनराइज डिबेन्चर"],
    "10% Laxmi Bank Debenture 2086": ["१०% लक्ष्मी बैंक डिबेन्चर २०८६", "लक्ष्मी डिबेन्चर"],
    "Himal Dolakha Hydropower Company Limited": ["हिमाल डोलखा जलविद्युत कम्पनी लिमिटेड", "हिमाल डोलखा"],
    "12 % Goodwill Finance Limited Debenture 2083": ["१२% गुडविल फाइनान्स लिमिटेड डिबेन्चर २०८३", "गुडविल डिबेन्चर"],
    "10.35% Agricultural Bank Debenture 2083": ["१०.३५% एग्रिकल्चरल बैंक डिबेन्चर २०८३", "एग्रिकल्चरल"],
    "NIC ASIA Laghubitta Bittiya Sanstha Limited": ["एनआईसी एसिया लघुबित्त बित्तीय संस्था लिमिटेड", "एनआईसी लघु"],
    "10% Nabil Debenture 2082": ["१०% नबिल डिबेन्चर २०८२", "नबिल डिबेन्चर"],
    "Sampada Laghubitta Bittiya Sanstha Limited": ["सम्पदा लघुबित्त बित्तीय संस्था लिमिटेड", "सम्पदा"],
    "Laxmi Unnati Kosh": ["लक्ष्मी उन्नति कोष", "लक्ष्मी कोष"],
    "Liberty Energy Company Limited": ["लिबर्टी एनर्जी कम्पनी लिमिटेड", "लिबर्टी"],
    "Shiva Shree Hydropower Ltd": ["शिव श्री जलविद्युत लिमिटेड", "शिव श्री"],
    "Sanima GIC Insurance Limited": ["सनिमा जीआईसी इन्स्योरेन्स लिमिटेड", "सनिमा जीआईसी"],
    "United IDI Mardi RB Hydropower Limited.": ["युनाइटेड आईडीआई मार्दी आरबी जलविद्युत लिमिटेड", "युनाइटेड मार्दी"],
    "Chandragiri Hills Limited": ["चन्द्रागिरी हिल्स लिमिटेड", "चन्द्रागिरी"],
    "8.5% Nepal Investment Bank Debenture 2084": ["८.५% नेपाल इनभेष्टमेन्ट बैंक डिबेन्चर २०८४", "नेपाल इनभेष्ट डिबेन्चर"],
    "Kumari Equity Fund": ["कुमारी इक्विटी फन्ड", "कुमारी फन्ड"],
    "Singati Hydro Energy Limited": ["सिङ्गाटी हाइड्रो एनर्जी लिमिटेड", "सिङ्गाटी"],
    "CEDB Holdings Limited": ["सीईडीबी होल्डिङ्स लिमिटेड", "सीईडीबी"],
    "Prabhu Select Fund": ["प्रभु सेलेक्ट फन्ड", "प्रभु फन्ड"],
    "9% Kamana Sewa Bikas Bank Limited Debenture 2087": ["९% कमाना सेवा विकास बैंक लिमिटेड डिबेन्चर २०८७", "कमाना डिबेन्चर"],
    "Jeevan Bikas Laghubitta Bittya Sanstha Ltd": ["जीवन विकास लघुबित्त बित्तीय संस्था लिमिटेड", "जीवन"],
    "8.5% Nepal Bank Debenture 2087": ["८.५% नेपाल बैंक डिबेन्चर २०८७", "नेपाल डिबेन्चर"],
    "Samaj Laghubittya Bittiya Sanstha Limited": ["समाज लघुबित्त बित्तीय संस्था लिमिटेड", "समाज"],
    "NIC Asia Select Fund 30": ["एनआईसी एसिया सेलेक्ट फन्ड ३०", "एनआईसी सेलेक्ट"],
    "Progressive Finance Limited": ["प्रोग्रेसिभ फाइनान्स लिमिटेड", "प्रोग्रेसिभ"],
    "Global IME Bank Limited": ["ग्लोबल आइएमई बैंक लिमिटेड", "ग्लोबल आइएमई"],
    "Citizens Bank International Limited": ["सिटिजन्स बैंक इन्टरनेशनल लिमिटेड", "सिटिजन्स"],
    "Miteri Development Bank Limited": ["मितेरी डेभलपमेन्ट बैंक लिमिटेड", "मितेरी"],
    "Himalayan Life Insurance Limited": ["हिमालयन लाइफ इन्स्योरेन्स लिमिटेड", "हिमालयन लाइफ"],
    "Nerude Mirmire Laghubitta Bittiya Sanstha Limited": ["नेरुदे मिरमिरे लघुबित्त बित्तीय संस्था लिमिटेड", "मिरमिरे"],
    "Agricultural Development Bank Limited": ["कृषि विकास बैंक लिमिटेड", "कृषि"],
    "Mahalaxmi Bikas Bank Ltd.": ["महालक्ष्मी विकास बैंक लिमिटेड", "महालक्ष्मी"],
    "Kamana Sewa Bikas Bank Limited": ["कमाना सेवा विकास बैंक लिमिटेड", "कमाना सेवा"],
    "Nepal Investment Mega Bank Ltd. Promoter Share": ["नेपाल इनभेष्टमेन्ट मेगा बैंक प्रोमोटर शेयर", "निम्ब प्रोमोटर"],
    "Multipurpose Finance Company Limited": ["मल्टिपर्पस फाइनान्स कम्पनी लिमिटेड", "मल्टिपर्पस"],
    "Muktinath Bikas Bank Ltd.": ["मुक्तिनाथ विकास बैंक लिमिटेड", "मुक्तिनाथ"],
    "Swarojgar Laghubitta Bittiya Sanstha Ltd.": ["स्वरोजगार लघुबित्त बित्तीय संस्था लिमिटेड", "स्वरोजगार"],
    "Sindhu Bikash Bank Ltd": ["सिन्धु विकास बैंक लिमिटेड", "सिन्धु"],
    "Grameen Bikas Laghubitta Bittiya Sanstha Ltd.": ["ग्रामीण विकास लघुबित्त बित्तीय संस्था लिमिटेड", "ग्रामीण"],
    "Sanima Mai Hydropower Ltd.": ["सनिमा माई जलविद्युत लिमिटेड", "सनिमा माई"],
    "Kalika Laghubitta Bittiya Sanstha Ltd": ["कालिका लघुबित्त बित्तीय संस्था लिमिटेड", "कालिका लघु"],
    "Mithila LaghuBitta Bittiya Sanstha Limited": ["मिथिला लघुबित्त बित्तीय संस्था लिमिटेड", "मिथिला"],
    "Ridi Power Company Limited": ["रिडी पावर कम्पनी लिमिटेड", "रिडी"],
    "Laxmi Laghubitta Bittiya Sanstha Ltd.": ["लक्ष्मी लघुबित्त बित्तीय संस्था लिमिटेड", "लक्ष्मी लघु"],
    "Mahalxmi Bikas Bank Ltd. Promotor Share": ["महालक्ष्मी विकास बैंक प्रोमोटर शेयर", "महालक्ष्मी प्रोमोटर"],
    "Matribhumi Lagubitta Bittiya Sanstha Limited": ["मातृभूमि लघुबित्त बित्तीय संस्था लिमिटेड", "मातृभूमि"],
    "Janautthan Samudayic Laghubitta Bittya Sanstha Limited": ["जनउत्थान सामुदायिक लघुबित्त बित्तीय संस्था लिमिटेड", "जनउत्थान"],
    "NMB Microfinance Bittiya Sanstha Ltd.": ["एनएमबी माइक्रोफाइनान्स बित्तीय संस्था लिमिटेड", "एनएमबी माइक्रो"],
    "Suryodaya Womi Laghubitta Bittiya Sanstha Limited": ["सूर्योदय वूमी लघुबित्त बित्तीय संस्था लिमिटेड", "सूर्योदय"],
    "Ngadi Group Power Ltd.": ["ङादी ग्रुप पावर लिमिटेड", "ङादी"],
    "Green Development Bank Ltd.": ["ग्रीन डेभलपमेन्ट बैंक लिमिटेड", "ग्रीन"],
    "Khanikhola Hydropower Co. Ltd.": ["खानीखोला जलविद्युत कम्पनी लिमिटेड", "खानीखोला"],
    "Muktinath Debenture 2084/85": ["मुक्तिनाथ डिबेन्चर २०८४/८५", "मुक्तिनाथ डिबेन्चर"],
    "Manushi Laghubitta Bittiya Sanstha Limited": ["मानुषी लघुबित्त बित्तीय संस्था लिमिटेड", "मानुषी"],
    "Madhya Bhotekoshi Jalavidyut Company Limited": ["मध्य भोटेकोशी जलविद्युत कम्पनी लिमिटेड", "मध्य भोटेकोशी"],
    "Garima Debenture": ["गरिमा डिबेन्चर", "गरिमा"],
    "Upakar Laghubitta Bittiya Sanstha Limited": ["उपकार लघुबित्त बित्तीय संस्था लिमिटेड", "उपकार"],
    "CYC Nepal Laghubitta Bittiya Sanstha Limited": ["सीवाइसी नेपाल लघुबित्त बित्तीय संस्था लिमिटेड", "सीवाइसी"],
    "River Falls Power Limited": ["रिभर फल्स पावर लिमिटेड", "रिभर फल्स"],
    "Dordi Khola Jal Bidyut Company Limited": ["डोर्दी खोला जलविद्युत कम्पनी लिमिटेड", "डोर्दी"],
    "Kumari Dhanabriddhi Yojana": ["कुमारी धनवृद्धि योजना", "कुमारी योजना"],
    "10% Prime Debenture 2088": ["१०% प्राइम डिबेन्चर २०८८", "प्राइम डिबेन्चर"],
    "Swet-Ganga Hydropower & Construction Limited": ["स्वेत-गंगा जलविद्युत एण्ड कन्स्ट्रक्सन लिमिटेड", "स्वेत-गंगा"],
    "Mandakini Hydropower Limited": ["मन्दाकिनी जलविद्युत लिमिटेड", "मन्दाकिनी"],
    "Upper Solu Hydro Electric Company Limited": ["अपर सोलु हाइड्रो इलेक्ट्रिक कम्पनी लिमिटेड", "अपर सोलु"],
    "Dhaulagiri Laghubitta Bittiya Sanstha Limited": ["धौलागिरी लघुबित्त बित्तीय संस्था लिमिटेड", "धौलागिरी"],
    "Barahi Hydropower Public Limited": ["बराही जलविद्युत पब्लिक लिमिटेड", "बराही"],
    "Shuvam Power Limited": ["शुभम पावर लिमिटेड", "शुभम"],
    "Super Mai Hydropower Limited": ["सुपर माई जलविद्युत लिमिटेड", "सुपर माई"],
    "Maya Khola Hydropower Company Limited": ["माया खोला जलविद्युत कम्पनी लिमिटेड", "माया"],
    "Sunrise Focused Equity Fund": ["सनराइज फोकस्ड इक्विटी फन्ड", "सनराइज फोकस्ड"],
    "Molung Hydropower Company Limited": ["मोलुङ जलविद्युत कम्पनी लिमिटेड", "मोलुङ"],
    "Aatmanirbhar Laghubitta Bittiya Sanstha Limited": ["आत्मनिर्भर लघुबित्त बित्तीय संस्था लिमिटेड", "आत्मनिर्भर"],
    "Makar Jitumaya Suri Hydropower Limited": ["मकर जितुमाया सुरी जलविद्युत लिमिटेड", "मकर"],
    "Mai Khola Hydropower Limited": ["माई खोला जलविद्युत लिमिटेड", "माई"],
    "Dolti Power Company Limited": ["डोल्टी पावर कम्पनी लिमिटेड", "डोल्टी"],
    "City Hotel Limited": ["सिटी होटल लिमिटेड", "सिटी"],
    "Prabhu Smart Fund": ["प्रभु स्मार्ट फन्ड", "प्रभु स्मार्ट"],
    "Menchhiyam Hydropower Limited": ["मेन्चियाम जलविद्युत लिमिटेड", "मेन्चियाम"],
    "10.30% Standard Chartered Bank Limited Debenture": ["१०.३०% स्टान्डर्ड चार्टर्ड बैंक लिमिटेड डिबेन्चर", "एससीबी डिबेन्चर"],
    "RBB Mutual Fund 2": ["आरबीबी म्युचुअल फन्ड २", "आरबीबी"],
    "Modi Energy Limited": ["मोदी एनर्जी लिमिटेड", "मोदी"],
    "Rawa Energy Development Limited": ["रावा एनर्जी डेभलपमेन्ट लिमिटेड", "रावा"],
    "Siddhartha Investment Growth Scheme 3": ["सिद्धार्थ लगानी वृद्धि योजना ३", "सिद्धार्थ योजना ३"],
    "Nepal Republic Media Limited": ["नेपाल रिपब्लिक मिडिया लिमिटेड", "नेपाल मिडिया"],
    "Citizens Super 30 Mutual Fund": ["सिटिजन्स सुपर ३० म्युचुअल फन्ड", "सिटिजन्स सुपर"],
    "Ghorahi Cement Industry Limited": ["घोराही सिमेन्ट उद्योग लिमिटेड", "घोराही"],
    "Three Star Hydropower Limited": ["थ्री स्टार जलविद्युत लिमिटेड", "थ्री स्टार"],
    "Kutheli Bukhari Small Hydropower Limited": ["कुथेली बुखारी स्मल जलविद्युत लिमिटेड", "कुथेली"],
    "11% L.B.B.L. Debenture 2089": ["११% एल.बी.बी.एल. डिबेन्चर २०८९", "एलबीबीएल"],
    "Laxmi Value Fund 2": ["लक्ष्मी भ्यालु फन्ड २", "लक्ष्मी भ्यालु"],
    "Manakamana Engineering Hydropower Limited": ["मनकामना इन्जिनियरिङ जलविद्युत लिमिटेड", "मनकामना"],
    "Upper Lohore Khola Hydropower Company Limited": ["अपर लोहोर खोला जलविद्युत कम्पनी लिमिटेड", "अपर लोहोर"],
    "Citizen Life Insurance Company Limited": ["सिटिजन लाइफ इन्स्योरेन्स कम्पनी लिमिटेड", "सिटिजन लाइफ"],
    "Mandu Hydropower Limited": ["माण्डु जलविद्युत लिमिटेड", "माण्डु"],
    "Hathway Investment Nepal Limited": ["ह्याथवे इनभेष्टमेन्ट नेपाल लिमिटेड", "ह्याथवे"],
    "Bhagawati Hydropower Development Company Limited": ["भागवती जलविद्युत विकास कम्पनी लिमिटेड", "भागवती"],
    "Sonapur Minerals And Oil Limited": ["सोनापुर मिनरल्स एण्ड ओयल लिमिटेड", "सोनापुर"],
    "Trishuli Jal Vidhyut Company Limited": ["त्रिशूली जलविद्युत कम्पनी लिमिटेड", "त्रिशूली"],
    "Himalayan 80-20": ["हिमालयन ८०-२०", "हिमालयन ८०"],
    "Vision Lumbini Urja Company Limited": ["भिजन लुम्बिनी ऊर्जा कम्पनी लिमिटेड", "भिजन"],
    "Chirkhwa Hydropower Limited": ["चिरख्वा जलविद्युत लिमिटेड", "चिरख्वा"],
    "Nepal Warehousing Company Limited": ["नेपाल वेयरहाउसिङ कम्पनी लिमिटेड", "वेयरहाउसिङ"],
    "NIC ASIA Growth Fund-2": ["एनआईसी एसिया ग्रोथ फन्ड-२", "एनआईसी ग्रोथ"],
    "Kumari Sabal Yojana": ["कुमारी सबल योजना", "कुमारी सबल"],
    "Sarbottam Cement Limited": ["सर्वोत्तम सिमेन्ट लिमिटेड", "सर्वोत्तम"],
    "NIBL Stable Fund": ["एनआईबीएल स्टेबल फन्ड", "एनआईबीएल"],
    "Muktinath Mutual Fund 1": ["मुक्तिनाथ म्युचुअल फन्ड १", "मुक्तिनाथ फन्ड"],
    "Guardian Micro Life Insurance Limited": ["गार्डियन माइक्रो लाइफ इन्स्योरेन्स लिमिटेड", "गार्डियन"],
    "Garima Samriddhi Yojana": ["गरिमा समृद्धि योजना", "गरिमा योजना"],
    "Nepal Micro Insurance Company Limited": ["नेपाल माइक्रो इन्स्योरेन्स कम्पनी लिमिटेड", "माइक्रो"],
    "Crest Micro Life Insurance Limited": ["क्रेस्ट माइक्रो लाइफ इन्स्योरेन्स लिमिटेड", "क्रेस्ट"],
    "MBL Equity Fund": ["एमबीएल इक्विटी फन्ड", "एमबीएल फन्ड"],
    "Pure Energy Limited": ["प्योर एनर्जी लिमिटेड", "प्योर"],
    "Sanvi Energy Limited": ["सान्वी एनर्जी लिमिटेड", "सान्वी"],
    "Dibyashwori Hydropower Ltd.": ["दिब्यश्वरी जलविद्युत लिमिटेड", "दिब्यश्वरी"],
    "Forward Microfinance Laghubitta Bittiya Sanstha Limited": ["फोरवार्ड माइक्रोफाइनान्स लघुबित्त बित्तीय संस्था लिमिटेड", "फोरवार्ड"],
    "Synergy Power Development Ltd.": ["सिनेर्जी पावर डेभलपमेन्ट लिमिटेड", "सिनेर्जी"],
    "Nepal Hydro Developers Ltd.": ["नेपाल हाइड्रो डेभलपर्स लिमिटेड", "हाइड्रो डेभलपर्स"],
    "Unnati Sahakarya Laghubitta Bittiya Sanstha Limited": ["उन्नति सहकarya लघुबित्त बित्तीय संस्था लिमिटेड", "उन्नति"],
    "Joshi Hydropower Development Company Ltd": ["जोशी जलविद्युत विकास कम्पनी लिमिटेड", "जोशी"],
    "Aarambha Chautari Laghubitta Bittiya Sanstha Limited": ["आरणभ चौतारी लघुबित्त बित्तीय संस्था लिमिटेड", "आरणभ"],
    "Upper Tamakoshi Hydropower Ltd": ["अपर तामाकोशी जलविद्युत लिमिटेड", "अपर तामाकोशी"],
    "Samudayic Laghubitta Bittiya Sanstha Limited": ["सामुदायिक लघुबित्त बित्तीय संस्था लिमिटेड", "सामुदायिक"],
    "Ghalemdi Hydro Limited": ["घलेम्दी हाइड्रो लिमिटेड", "घलेम्दी"],
    "SHIVAM CEMENTS LTD": ["शिवम सिमेन्ट्स लिमिटेड", "शिवम"],
    "UNIVERSAL POWER COMPANY LTD": ["युनिभर्सल पावर कम्पनी लिमिटेड", "युनिभर्सल"],
    "Mountain Hydro Nepal Limited": ["माउन्टेन हाइड्रो नेपाल लिमिटेड", "माउन्टेन"],
    "Panchthar Power Compant Limited": ["पाँचथर पावर कम्पनी लिमिटेड", "पाँचथर"],
    "10% Sanima Bank Limited Debenture": ["१०% सनिमा बैंक लिमिटेड डिबेन्चर", "सनिमा डिबेन्चर"],
    "Swabhimaan Laghubitta Bittiya Sanstha Limited": ["स्वाभिमान लघुबित्त बित्तीय संस्था लिमिटेड", "स्वाभिमान"],
    "SANJEN JALAVIDHYUT COMPANY LIMITED": ["सञ्जेन जलविद्युत कम्पनी लिमिटेड", "सञ्जेन"],
    "Nepal Reinsurance Company Limited": ["नेपाल पुनर्बीमा कम्पनी लिमिटेड", "पुनर्बीमा"],
    "10% Nepal SBI Bank Debenture 2086": ["१०% नेपाल एसबीआई बैंक डिबेन्चर २०८६", "एसबीआई डिबेन्चर"],
    "NRN Infrastructure and Development Limited": ["एनआरएन इनफ्रास्ट्रक्चर एण्ड डेभलपमेन्ट लिमिटेड", "एनआरएन"],
    "Mountain Energy Nepal Limited": ["माउन्टेन एनर्जी नेपाल लिमिटेड", "एनर्जी नेपाल"],
    "Prabhu Mahalaxmi Life Insurance Limited": ["प्रभु महालक्ष्मी लाइफ इन्स्योरेन्स लिमिटेड", "प्रभु महालक्ष्मी"],
    "Nepal Infrastructure Bank Limited": ["नेपाल इनफ्रास्ट्रक्चर बैंक लिमिटेड", "इनफ्रास्ट्रक्चर"],
    "Sanima Large Cap Fund": ["सनिमा लार्ज क्याप फन्ड", "सनिमा क्याप"],
    "GreenLife Hydropower Limited": ["ग्रीनलाइफ जलविद्युत लिमिटेड", "ग्रीनलाइफ"],
    "Mahila Lagubitta Bittiya Sanstha Limited": ["महिला लघुबित्त बित्तीय संस्था लिमिटेड", "महिला"],
    "9.5% Manjushree Finance Limited Debenture 2085": ["९.५% मान्जुश्री फाइनान्स लिमिटेड डिबेन्चर २०८५", "मान्जुश्री डिबेन्चर"],
    "Ru Ru Jalbidhyut Pariyojana Limited": ["रु रु जलविद्युत परियोजना लिमिटेड", "रु रु"],
    "9.5% NCC Debenture 2086": ["९.५% एनसीसी डिबेन्चर २०८६", "एनसीसी"],
    "Sunrise Bluechip Fund": ["सनराइज ब्लुचिप फन्ड", "सनराइज ब्लु"],
    "NIBL Samriddhi Fund -2": ["एनआईबीएल समृद्धि फन्ड -२", "एनआईबीएल समृद्धि"],
    "RBB Mutual Fund 1": ["आरबीबी म्युचुअल फन्ड १", "आरबीबी फन्ड"],
    "Sanima Reliance Life Insurance Limited": ["सनिमा रिलायन्स लाइफ इन्स्योरेन्स लिमिटेड", "सनिमा रिलायन्स"],
    "8.75 % Prime Debenture 2085": ["८.७५% प्राइम डिबेन्चर २०८५", "प्राइम डिबेन्चर ८"],
    "8.5% Machhapuchchhre Debenture 2087": ["८.५% माछापुच्छ्रे डिबेन्चर २०८७", "माछापुच्छ्रे डिबेन्चर ८"],
    "Mailung Khola Jal Vidhyut Company Limited": ["मैलुङ खोला जलविद्युत कम्पनी लिमिटेड", "मैलुङ"],
    "Jyoti Bikash Bank Bond 2087": ["ज्योति विकास बैंक बन्ड २०८७", "ज्योति बन्ड"],
    "Sahas Urja Limited": ["सहस ऊर्जा लिमिटेड", "सहस"],
    "Terhathum Power Company Limited": ["तेह्रथुम पावर कम्पनी लिमिटेड", "तेह्रथुम"],
    "Mega Mutual Fund -1": ["मेगा म्युचुअल फन्ड -१", "मेगा"],
    "Nabil Balanced Fund-3": ["नबिल ब्यालेन्स्ड फन्ड-३", "नबिल फन्ड ३"],
    "Samling Power Company Limited": ["सम्लिङ पावर कम्पनी लिमिटेड", "सम्लिङ"],
    "Nyadi Hydropower Limited": ["न्याडी जलविद्युत लिमिटेड", "न्याडी"],
    "Nabil Debenture 2085": ["नबिल डिबेन्चर २०८५", "नबिल डिबेन्चर २०"],
    "Buddha Bhumi Nepal Hydropower Company Limited": ["बुद्ध भूमि नेपाल जलविद्युत कम्पनी लिमिटेड", "बुद्ध भूमि"],
    "Emerging Nepal Limited": ["इमर्जिङ नेपाल लिमिटेड", "इमर्जिङ"],
    "NESDO Sambridha Laghubitta Bittiya Sanstha Limited": ["नेस्डो समृद्ध लघुबित्त बित्तीय संस्था लिमिटेड", "नेस्डो"],
    "Green Ventures Limited": ["ग्रीन भेन्टर्स लिमिटेड", "ग्रीन भेन्टर्स"],
    "Balephi Hydropower Limited": ["बालेपही जलविद्युत लिमिटेड", "बालेपही"],
    "Century Debenture 2088": ["सेन्चुरी डिबेन्चर २०८८", "सेन्चुरी"],
    "NIC Asia Flexi CAP Fund": ["एनआईसी एसिया फ्लेक्सी क्याप फन्ड", "एनआईसी फ्लेक्सी"],
    "Bindhyabasini Hydropower Development Company Limited": ["बिन्द्यवासिनी जलविद्युत विकास कम्पनी लिमिटेड", "बिन्द्य"],
    "Himalayan Hydropower Limited": ["हिमालयन जलविद्युत लिमिटेड", "हिमालयन जल"],
    "Upper Hewakhola Hydropower Company Limited": ["अपर हेवाखोला जलविद्युत कम्पनी लिमिटेड", "अपर हेवा"],
    "Global IME Balanced Fund-1": ["ग्लोबल आइएमई ब्यालेन्स्ड फन्ड-१", "ग्लोबल ब्यालेन्स्ड"],
    "Rapti Hydro And General Construction Limited": ["राप्ती हाइड्रो एण्ड जनरल कन्स्ट्रक्सन लिमिटेड", "राप्ती"],
    "10.25% Nepal SBI Bank Debenture 2083": ["१०.२५% नेपाल एसबीआई बैंक डिबेन्चर २०८३", "एसबीआई डिबेन्चर २०"],
    "Hydorelectricity Investment and Development Company Limited Promoter": ["जलविद्युत लगानी तथा विकास कम्पनी लिमिटेड प्रोमोटर", "जलविद्युत प्रोमोटर"],
    "10.15% Prime Debenture 2084": ["१०.१५% प्राइम डिबेन्चर २०८४", "प्राइम डिबेन्चर २"],
    "Aviyan Laghubitta Bittiya Sanstha Limited": ["अवियान लघुबित्त बित्तीय संस्था लिमिटेड", "अवियान"],
    "10.50% Everest Bank Limited Debenture 2085": ["१०.५०% एभरेष्ट बैंक लिमिटेड डिबेन्चर २०८५", "एभरेष्ट डिबेन्चर"],
    "Sayapatri Hydropower Limited": ["सयपत्री जलविद्युत लिमिटेड", "सयपत्री"],
    "People's Power Limited": ["पिपुल्स पावर लिमिटेड", "पिपुल्स"],
    "NMB Sulav Investment Fund - 2": ["एनएमबी सुलभ लगानी फन्ड - २", "एनएमबी सुलभ"],
    "Sikles Hydropower Limited": ["सिक्लेस जलविद्युत लिमिटेड", "सिक्लेस"],
    "11% KBL Debenture 2089": ["११% केबीएल डिबेन्चर २०८९", "केबीएल"],
    "Eastern Hydropower Limited": ["ईस्टर्न जलविद्युत लिमिटेड", "ईस्टर्न"],
    "Shrijanshil Laghubitta Bittiya Sanstha Limited": ["श्रिजनशील लघुबित्त बित्तीय संस्था लिमिटेड", "श्रिजनशील"],
    "Peoples Hydropower Company Limited": ["पिपुल्स जलविद्युत कम्पनी लिमिटेड", "पिपुल्स जल"],
    "NIBL Growth Fund": ["एनआईबीएल ग्रोथ फन्ड", "एनआईबीएल ग्रोथ"],
    "Sanima Growth Fund": ["सनिमा ग्रोथ फन्ड", "सनिमा ग्रोथ"],
    "Unique Nepal Laghubitta Bittiya Sanstha Limited": ["युनिक नेपाल लघुबित्त बित्तीय संस्था लिमिटेड", "युनिक"],
    "Super Madi Hydropower Limited": ["सुपर मादी जलविद्युत लिमिटेड", "सुपर मादी"],
    "Asian Hydropower Limited": ["एशियन जलविद्युत लिमिटेड", "एशियन जल"],
    "Kalinchowk Darshan Limited": ["कालिञ्चोक दरshan लिमिटेड", "कालिञ्चोक"],
    "Everest Bank Limited Energy Bond": ["एभरेष्ट बैंक लिमिटेड एनर्जी बन्ड", "एभरेष्ट बन्ड"],
    "Sanima Middle Tamor Hydropower Limited": ["सनिमा मिडल तामोर जलविद्युत लिमिटेड", "सनिमा तामोर"],
    "Sagarmatha Jalabidhyut Company Limited": ["सगरमाथा जलविद्युत कम्पनी लिमिटेड", "सगरमाथा जल"],
    "Bhugol Energy Development Company Limited": ["भुगोल एनर्जी डेभलपमेन्ट कम्पनी लिमिटेड", "भुगोल"],
    "Ingwa Hydropower Limited": ["इङ्गवा जलविद्युत लिमिटेड", "इङ्गवा"],
    "IME Life Insurance Company Limited": ["आइएमई लाइफ इन्स्योरेन्स कम्पनी लिमिटेड", "आइएमई"],
    "Upper Syange Hydropower Limited": ["अपर स्याङ्जे जलविद्युत लिमिटेड", "अपर स्याङ्जे"],
    "11% Mahalaxmi Debenture 2089": ["११% महालक्ष्मी डिबेन्चर २०८९", "महालक्ष्मी डिबेन्चर"],
    "Reliable Nepal Life Insurance Limited": ["रिलायबल नेपाल लाइफ इन्स्योरेन्स लिमिटेड", "रिलायबल"],
    "Sun Nepal Life Insurance Company Limited": ["सन नेपाल लाइफ इन्स्योरेन्स कम्पनी लिमिटेड", "सन नेपाल"],
    "Mid Solu Hydropower Limited": ["मिड सोलु जलविद्युत लिमिटेड", "मिड सोलु"],
    "Mathillo Mailun Khola Jalvidhyut Limited": ["माथिल्लो मैलुङ खोला जलविद्युत लिमिटेड", "माथिल्लो मैलुङ"],
    "Muktinath Krishi Company Limited": ["मुक्तिनाथ कृषि कम्पनी लिमिटेड", "मुक्तिनाथ कृषि"],
    "Himalayan Reinsurance Limited": ["हिमालयन पुनर्बीमा लिमिटेड", "हिमालयन पुनर्बीमा"],
    "9% ICFC Finance Limited Debenture 2088": ["९% आईसीएफसी फाइनान्स लिमिटेड डिबेन्चर २०८८", "आईसीएफसी डिबेन्चर"],
    "NMB Hybrid Fund L- II": ["एनएमबी हाइब्रिड फन्ड एल-२", "एनएमबी हाइब्रिड"],
    "Everest Bank Limited Debenture 2091": ["एभरेष्ट बैंक लिमिटेड डिबेन्चर २०९१", "एभरेष्ट डिबेन्चर"],
    "Om Megashree Pharmaceuticals Limited": ["ओम मेघश्री फर्मास्युटिकल्स लिमिटेड", "ओम मेघश्री"],
    "Reliable Samriddhi Yojana": ["रिलायबल समृद्धि योजना", "रिलायबल योजना"],
    "Nifra Green Energy Debenture 6% - 2088/89": ["निफ्रा ग्रीन एनर्जी डिबेन्चर ६% - २०८८/८९", "निफ्रा डिबेन्चर"],
    "Trade Tower Limited": ["ट्रेड टावर लिमिटेड", "ट्रेड टावर"],
}

# Set to track processed article IDs to avoid duplicates
processed_ids = set()

# Function to detect language and match based on Nepali translations
def detect_and_match(content):
    try:
        lang = langdetect.detect(content)
        logger.info(f"Detected language: {lang}") # 2025-08-01 14:21:00 +0545 - INFO - Detected language: ne
        content = unicodedata.normalize('NFKD', content.lower().strip())
        best_match = None # If multiple matches were found then best match is stored
        for company_name, translations in nepali_translations.items():
            for translation in translations:
                translation_normalized = unicodedata.normalize('NFKD', translation.lower().strip())
                if re.search(r'\b' + re.escape(translation_normalized) + r'\b', content, re.IGNORECASE): # boundary match, try to matches exact word 
                    return company_name, 100  # Return the English company name as the match
                if translation_normalized in content:
                    return company_name, 100 # if direct match is found, match is true if न,बि,ल are found in this exact sequence
        return None, 0  # No match found
    except Exception as e:
        logger.error(f"Error in detect_and_match: {e}")
        return None, 0

"""
nepali_translations = {
    "Nabil Bank Limited": ["नबिल बैंक लिमिटेड", "नबिल"],
}
company_name = Nabil Bank Limited, translations = ["नबिल बैंक लिमिटेड", "नबिल"]
translation = At first loops for "नबिल बैंक लिमिटेड" and then "नबिल"
returns if match are found


"""
# Function to fetch news from ShareHub Nepal API
def fetch_sharehub_news(last_post_id=None, max_retries=3):
    try:
        base_url = "https://sharehubnepal.com/account/api/v1/khula-manch/post"
        params = {"MediaType": "News", "Size": 200}
        if last_post_id:
            params["LastPostId"] = last_post_id
        for attempt in range(max_retries):
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"ShareHub Attempt {attempt + 1} failed with status {response.status_code}, retrying...")
        logger.error(f"Failed to fetch ShareHub news after {max_retries} attempts")
        return {"data": []}
    except Exception as e:
        logger.error(f"Error fetching ShareHub news: {e}")
        return {"data": []}

# Function to classify a single news item
def classify_news_item(item):
    try:
        article_id = item.get('id', '')
        if article_id in processed_ids:
            return None  # Skip if already processed
        title = item.get('title', '')
        summary = item.get('summary', '')
        content = f"{title} {summary}"  # Combine title and summary for matching, exclude mediaUrl
        company_match, score = detect_and_match(content)
        if score == 0:  # No share symbol or name match found
            return None
        result = {
            "articleId": article_id,
            "publishedDate": item.get('publishedDate', ''),
            "title": title,
            "summary": summary,
            "mediaUrl": item.get('mediaUrl', ''),
            "matchedCompany": company_match,
            "matchScore": score,
            "source": "ShareHub"
        }
        processed_ids.add(article_id)  # Add to processed set after successful classification
        return result
    except Exception as e:
        logger.error(f"Error classifying news item {item.get('id', '')}: {e}")
        return None

# Function to save news to individual files
def save_news_item(news_item):
    company = news_item.get('matchedCompany', 'unknown')
    # Get the symbol based on the matched company name
    symbol = nepse_df.loc[nepse_df['Security Name'] == company, 'Symbol'].iloc[0] if company in nepse_df['Security Name'].values else 'unknown'
    # Define the directory path
    directory = "E:\\hey\\output\\news_data"
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    filename = os.path.join(directory, f"{symbol}_news.csv")
    df = pd.DataFrame([news_item])
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df.to_csv(filename, mode='w', index=False, encoding='utf-8-sig')
    logger.info(f"Saved news item to {filename}")

# Function to process and save news to CSV with batch processing
def process_news():
    all_news = []
    last_id_sharehub = None
    news_count = 0
    batch_size = 200
    target_news = 10000
    while news_count < target_news:
        # Fetch from ShareHub API
        data = fetch_sharehub_news(last_id_sharehub)
        if not data.get('data'):
            logger.warning("No more data available from ShareHub, attempting to fetch more...")
            time.sleep(5)
            data = fetch_sharehub_news(last_id_sharehub)
            if not data.get('data'):
                break
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(classify_news_item, item) for item in data['data']]
            for future in as_completed(futures):
                classified_item = future.result()
                if classified_item:
                    all_news.append(classified_item)
                    news_count += 1
                    if len(all_news) >= batch_size:
                        for item in all_news:
                            save_news_item(item)
                        all_news = []
        last_id_sharehub = data['data'][-1].get('id') if data['data'] else None
        logger.info(f"Fetched {news_count} unique news items so far from ShareHub...")
        if len(data['data']) < 200:
            break
    if all_news:
        for item in all_news:
            save_news_item(item)
    logger.info("News data processing completed")

# Schedule the news update every 6 hours
schedule.every(6).hours.do(process_news)

# Run the scheduler
if __name__ == "__main__":
    logger.info(f"Starting news processing at {datetime.now().strftime('%I:%M %p %z on %B %d, %Y')}")
    process_news()  # Initial run
    while True:
        schedule.run_pending()
        time.sleep(60)