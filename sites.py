"""
Configuration des sites cibles sénégalais par catégorie.
"""

SITES = {
    "presse": [
        {"name": "Seneweb", "url": "https://www.seneweb.com", "domain": "seneweb.com"},
        {"name": "Dakaractu", "url": "https://www.dakaractu.com", "domain": "dakaractu.com"},
        {"name": "Senenews", "url": "https://www.senenews.com", "domain": "senenews.com"},
        {"name": "Rewmi", "url": "https://www.rewmi.com", "domain": "rewmi.com"},
        {"name": "Leral", "url": "https://www.leral.net", "domain": "leral.net"},
        {"name": "Pressafrik", "url": "https://www.pressafrik.com", "domain": "pressafrik.com"},
        {"name": "Actusen", "url": "https://actusen.sn", "domain": "actusen.sn"},
        {"name": "Senego", "url": "https://senego.com", "domain": "senego.com"},
        {"name": "Sud Quotidien", "url": "https://www.sudquotidien.sn", "domain": "sudquotidien.sn"},
        {"name": "L'Observateur", "url": "https://www.lobservateur.sn", "domain": "lobservateur.sn"},
        {"name": "Xibaaru", "url": "https://xibaaru.com", "domain": "xibaaru.com"},
        {"name": "Dakarmatin", "url": "https://www.dakarmatin.com", "domain": "dakarmatin.com"},
    ],
    "ecommerce": [
        {"name": "Jumia Sénégal", "url": "https://www.jumia.sn", "domain": "jumia.sn"},
        {"name": "Expat Dakar", "url": "https://www.expat-dakar.com", "domain": "expat-dakar.com"},
        {"name": "CoinAfrique", "url": "https://sn.coinafrique.com", "domain": "sn.coinafrique.com"},
        {"name": "Afrikrea", "url": "https://www.afrikrea.com", "domain": "afrikrea.com"},
        {"name": "Dakar Deal", "url": "https://www.dakardeal.com", "domain": "dakardeal.com"},
    ],
    "telephonie": [
        {"name": "Orange Sénégal", "url": "https://www.orange.sn", "domain": "orange.sn"},
        {"name": "Free Sénégal", "url": "https://www.free.sn", "domain": "free.sn"},
        {"name": "Expresso", "url": "https://www.expressotelecom.sn", "domain": "expressotelecom.sn"},
        {"name": "Sonatel", "url": "https://www.sonatel.com", "domain": "sonatel.com"},
    ],
    "banque_finance": [
        {"name": "CBAO", "url": "https://www.cbao.sn", "domain": "cbao.sn"},
        {"name": "Ecobank Sénégal", "url": "https://ecobank.com/sn", "domain": "ecobank.com"},
        {"name": "Wave", "url": "https://www.wave.com/fr/sen", "domain": "wave.com"},
        {"name": "Orange Money", "url": "https://www.orangemoney.sn", "domain": "orangemoney.sn"},
    ],
    "emploi": [
        {"name": "Senjob", "url": "https://www.senjob.com", "domain": "senjob.com"},
        {"name": "Emploi Sénégal", "url": "https://www.emploi.sn", "domain": "emploi.sn"},
        {"name": "Rekrute Afrique", "url": "https://www.rekrute.com", "domain": "rekrute.com"},
    ],
}

# Tous les sites à plat
ALL_SITES = []
for category, sites in SITES.items():
    for site in sites:
        ALL_SITES.append({**site, "category": category})

# User-Agents rotatifs pour éviter le blocage
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
]

# Délais entre requêtes (secondes) — respecter les serveurs
SCRAPE_DELAY_MIN = 2
SCRAPE_DELAY_MAX = 5

# Google PageSpeed API (gratuite, 25 000 requêtes/jour)
PAGESPEED_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
PAGESPEED_API_KEY = "AIzaSyCEj9OsTdXWAd9FzPaeVoBpOYpw-SKvt4Y"  # Optionnel mais recommandé pour augmenter les quotas

# CommonCrawl — index des backlinks gratuit
COMMONCRAWL_INDEX_URL = "https://index.commoncrawl.org/CC-MAIN-2024-30-index"
COMMONCRAWL_API_URL = "https://index.commoncrawl.org/CC-MAIN-2024-30-index?output=json&url="
