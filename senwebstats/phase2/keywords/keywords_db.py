
KEYWORDS = {
    "presse": [
        {"keyword": "seneweb",               "volume_est": 90000, "intent": "nav",    "lang": "fr"},
        {"keyword": "dakaractu",             "volume_est": 60000, "intent": "nav",    "lang": "fr"},
        {"keyword": "senenews",              "volume_est": 40000, "intent": "nav",    "lang": "fr"},
        {"keyword": "senego",                "volume_est": 35000, "intent": "nav",    "lang": "fr"},
        {"keyword": "leral net",             "volume_est": 25000, "intent": "nav",    "lang": "fr"},
        {"keyword": "rewmi",                 "volume_est": 20000, "intent": "nav",    "lang": "fr"},
        {"keyword": "actualite senegal",     "volume_est": 45000, "intent": "info",   "lang": "fr"},
        {"keyword": "news senegal",          "volume_est": 25000, "intent": "info",   "lang": "fr"},
        {"keyword": "ousmane sonko",         "volume_est": 70000, "intent": "info",   "lang": "fr"},
        {"keyword": "bassirou diomaye faye", "volume_est": 55000, "intent": "info",   "lang": "fr"},
        {"keyword": "sadio mane",            "volume_est": 40000, "intent": "info",   "lang": "fr"},
        {"keyword": "can 2025 senegal",      "volume_est": 30000, "intent": "info",   "lang": "fr"},
        {"keyword": "lion de la teranga",    "volume_est": 25000, "intent": "info",   "lang": "fr"},
        {"keyword": "journal senegal",       "volume_est": 20000, "intent": "info",   "lang": "fr"},
        {"keyword": "politique senegal",     "volume_est": 20000, "intent": "info",   "lang": "fr"},
        {"keyword": "elections senegal",     "volume_est": 18000, "intent": "info",   "lang": "fr"},
        {"keyword": "ligue 1 senegal",       "volume_est": 15000, "intent": "info",   "lang": "fr"},
        {"keyword": "senegal today",         "volume_est": 12000, "intent": "info",   "lang": "fr"},
        {"keyword": "xibaaru",               "volume_est": 12000, "intent": "nav",    "lang": "fr"},
        {"keyword": "dakarmatin",            "volume_est": 10000, "intent": "nav",    "lang": "fr"},
    ],
    "ecommerce": [
        {"keyword": "jumia senegal",           "volume_est": 35000, "intent": "nav",    "lang": "fr"},
        {"keyword": "expat dakar",             "volume_est": 25000, "intent": "nav",    "lang": "fr"},
        {"keyword": "appartement louer dakar", "volume_est": 22000, "intent": "transac","lang": "fr"},
        {"keyword": "voiture occasion dakar",  "volume_est": 20000, "intent": "transac","lang": "fr"},
        {"keyword": "iphone senegal",          "volume_est": 15000, "intent": "transac","lang": "fr"},
        {"keyword": "acheter en ligne senegal","volume_est": 15000, "intent": "transac","lang": "fr"},
        {"keyword": "smartphone senegal prix", "volume_est": 18000, "intent": "transac","lang": "fr"},
        {"keyword": "location maison dakar",   "volume_est": 18000, "intent": "transac","lang": "fr"},
        {"keyword": "coinafrique senegal",     "volume_est": 12000, "intent": "nav",    "lang": "fr"},
        {"keyword": "terrain vendre dakar",    "volume_est": 12000, "intent": "transac","lang": "fr"},
    ],
    "telephonie": [
        {"keyword": "orange senegal",          "volume_est": 40000, "intent": "nav",    "lang": "fr"},
        {"keyword": "wave senegal",            "volume_est": 35000, "intent": "nav",    "lang": "fr"},
        {"keyword": "free senegal",            "volume_est": 25000, "intent": "nav",    "lang": "fr"},
        {"keyword": "orange money senegal",    "volume_est": 25000, "intent": "nav",    "lang": "fr"},
        {"keyword": "recharge orange senegal", "volume_est": 20000, "intent": "transac","lang": "fr"},
        {"keyword": "forfait internet senegal","volume_est": 15000, "intent": "transac","lang": "fr"},
        {"keyword": "sonatel",                 "volume_est": 15000, "intent": "nav",    "lang": "fr"},
        {"keyword": "5g senegal",              "volume_est": 10000, "intent": "info",   "lang": "fr"},
    ],
    "banque_finance": [
        {"keyword": "transfert argent senegal","volume_est": 20000, "intent": "transac","lang": "fr"},
        {"keyword": "taux change fcfa euro",   "volume_est": 15000, "intent": "info",   "lang": "fr"},
        {"keyword": "bitcoin senegal",         "volume_est": 12000, "intent": "info",   "lang": "fr"},
        {"keyword": "banque senegal",          "volume_est": 12000, "intent": "info",   "lang": "fr"},
        {"keyword": "western union dakar",     "volume_est":  8000, "intent": "transac","lang": "fr"},
        {"keyword": "cbao senegal",            "volume_est":  8000, "intent": "nav",    "lang": "fr"},
    ],
    "emploi": [
        {"keyword": "emploi senegal",          "volume_est": 25000, "intent": "info",   "lang": "fr"},
        {"keyword": "offre emploi dakar",      "volume_est": 20000, "intent": "info",   "lang": "fr"},
        {"keyword": "concours senegal 2025",   "volume_est": 20000, "intent": "info",   "lang": "fr"},
        {"keyword": "recrutement senegal",     "volume_est": 15000, "intent": "info",   "lang": "fr"},
        {"keyword": "senjob",                  "volume_est": 10000, "intent": "nav",    "lang": "fr"},
        {"keyword": "bourse etude senegal",    "volume_est": 10000, "intent": "info",   "lang": "fr"},
    ],
}

ALL_KEYWORDS = []
for cat, kws in KEYWORDS.items():
    for kw in kws:
        ALL_KEYWORDS.append({**kw, "category": cat})
ALL_KEYWORDS.sort(key=lambda x: x["volume_est"], reverse=True)
TOTAL_KEYWORDS = len(ALL_KEYWORDS)
TOTAL_VOLUME   = sum(k["volume_est"] for k in ALL_KEYWORDS)
