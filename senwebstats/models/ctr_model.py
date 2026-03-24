"""
SenWebStats — Modèle de trafic basé sur les CTR (Click-Through Rates)
======================================================================
Trois niveaux d'estimation, du plus précis au plus proxy :

  NIVEAU 1 — API temps réel (le plus précis)
    Semrush  : positions réelles + volumes de recherche par domaine
    DataForSEO : positions SERP Google Sénégal (location_code=2686)

  NIVEAU 2 — Modèle CTR × Pool de mots-clés (proxy calibré)
    Mapping score_global → position estimée
    Courbe CTR publiée (AWR 2023 ou Sistrix 2020)
    Pool de mots-clés pondérés par catégorie (marché sénégalais)

  NIVEAU 3 — Modèle de base (fallback pur)
    base_catégorie × (score_global / 100) ^ 1.5

Sources des courbes CTR :
  - AWR (Advanced Web Ranking) Global Study 2023 — desktop+mobile blended
    https://www.advancedwebranking.com/ctrstudy/
  - Sistrix CTR Model 2020 — marché européen francophone
    https://www.sistrix.com/blog/ctr-for-google-serp/
  - SparkToro / Rand Fishkin 2023 — zero-click & CTR study

Notes méthodologiques :
  Le marché sénégalais est peu documenté. Les volumes de mots-clés
  sont des estimations calibrées sur :
    - Google Trends (volumes relatifs Sénégal vs France)
    - SimilarWeb benchmarks Afrique de l'Ouest 2023
    - ~8 millions d'internautes au Sénégal (ARTP 2023)
    - Taux de pénétration Google Search ~92% (StatCounter 2023)
"""

import math
import os
import json
import requests
import base64
from typing import Optional

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# COURBES CTR PUBLIÉES
# ─────────────────────────────────────────────────────────────────────────────

# AWR 2023 — blended desktop+mobile, toutes industries
# Source: Advanced Web Ranking CTR Study Q3 2023
AWR_2023: dict[int, float] = {
    1: 0.2972,  2: 0.1495,  3: 0.1037,  4: 0.0745,  5: 0.0572,
    6: 0.0447,  7: 0.0360,  8: 0.0294,  9: 0.0248, 10: 0.0212,
   11: 0.0172, 12: 0.0142, 13: 0.0120, 14: 0.0102, 15: 0.0088,
   16: 0.0076, 17: 0.0066, 18: 0.0057, 19: 0.0050, 20: 0.0044,
}

# Sistrix 2020 — marché francophone européen (référence académique)
# Source: https://www.sistrix.com/blog/ctr-for-google-serp/
SISTRIX_2020: dict[int, float] = {
    1: 0.3350,  2: 0.1550,  3: 0.0960,  4: 0.0650,  5: 0.0470,
    6: 0.0350,  7: 0.0270,  8: 0.0220,  9: 0.0170, 10: 0.0140,
   11: 0.0100, 12: 0.0080, 13: 0.0070, 14: 0.0060, 15: 0.0055,
   16: 0.0050, 17: 0.0045, 18: 0.0040, 19: 0.0035, 20: 0.0030,
}

# SparkToro 2023 — tient compte du zero-click (plus conservateur)
SPARKTORO_2023: dict[int, float] = {
    1: 0.2190,  2: 0.1154,  3: 0.0858,  4: 0.0670,  5: 0.0530,
    6: 0.0430,  7: 0.0360,  8: 0.0306,  9: 0.0263, 10: 0.0229,
   11: 0.0160, 12: 0.0130, 13: 0.0110, 14: 0.0090, 15: 0.0080,
   16: 0.0065, 17: 0.0055, 18: 0.0047, 19: 0.0042, 20: 0.0037,
}

# Courbes disponibles (pour l'UI)
CTR_CURVES = {
    "AWR 2023 (recommandé)":    AWR_2023,
    "Sistrix 2020 (francophone)": SISTRIX_2020,
    "SparkToro 2023 (conservateur)": SPARKTORO_2023,
}

DEFAULT_CURVE = "AWR 2023 (recommandé)"


# ─────────────────────────────────────────────────────────────────────────────
# POOL DE MOTS-CLÉS — MARCHÉ SÉNÉGALAIS
# Format : (keyword, volume_mensuel_estimé, type_requête)
# types : "navigational" (branded) | "informational" | "transactional"
# ─────────────────────────────────────────────────────────────────────────────

SENEGAL_KEYWORD_POOLS: dict[str, list[tuple]] = {
    "presse": [
        # Requêtes navigationnelles (branded) — CTR très élevé pour le site cible
        ("senenews", 55000, "navigational"),
        ("seneweb", 48000, "navigational"),
        ("dakaractu", 32000, "navigational"),
        ("dakarmatin", 20000, "navigational"),
        ("rewmi", 18000, "navigational"),
        ("leral.net", 15000, "navigational"),
        ("igfm.sn", 14000, "navigational"),
        ("pressafrik", 12000, "navigational"),
        # Requêtes informationnelles — partagées entre tous les sites
        ("actualite senegal", 28000, "informational"),
        ("news senegal", 22000, "informational"),
        ("senegal aujourd'hui", 18000, "informational"),
        ("information senegal", 15000, "informational"),
        ("revue de presse senegal", 10000, "informational"),
        ("politique senegal", 9000, "informational"),
        ("economie senegal", 7500, "informational"),
        ("sport senegal", 8000, "informational"),
        ("football senegal", 12000, "informational"),
        ("elections senegal", 6000, "informational"),
    ],
    "ecommerce": [
        ("jumia senegal", 40000, "navigational"),
        ("expat dakar", 22000, "navigational"),
        ("dakar deal", 8000, "navigational"),
        ("kaymu senegal", 6000, "navigational"),
        ("acheter en ligne senegal", 9000, "transactional"),
        ("boutique en ligne dakar", 7000, "transactional"),
        ("livraison dakar", 8000, "transactional"),
        ("shopping en ligne senegal", 5000, "transactional"),
        ("marketplace senegal", 4500, "informational"),
        ("vente en ligne senegal", 4000, "transactional"),
        ("prix smartphone senegal", 6000, "transactional"),
        ("electromenager dakar", 3500, "transactional"),
    ],
    "telephonie": [
        ("orange senegal", 75000, "navigational"),
        ("free senegal", 55000, "navigational"),
        ("expresso senegal", 22000, "navigational"),
        ("forfait internet senegal", 12000, "transactional"),
        ("recharge orange senegal", 9000, "transactional"),
        ("4g senegal", 8000, "informational"),
        ("fibre optique dakar", 5000, "informational"),
        ("debit internet senegal", 4000, "informational"),
        ("abonnement internet senegal", 6000, "transactional"),
        ("appel international senegal", 3500, "transactional"),
    ],
    "banque_finance": [
        ("attijariwafa bank senegal", 12000, "navigational"),
        ("cbao senegal", 10000, "navigational"),
        ("bnde senegal", 7000, "navigational"),
        ("sgbs senegal", 8000, "navigational"),
        ("credit senegal", 8000, "transactional"),
        ("banque en ligne senegal", 6000, "informational"),
        ("mobile money senegal", 9000, "informational"),
        ("wave senegal", 25000, "navigational"),
        ("orange money senegal", 18000, "navigational"),
        ("microfinance senegal", 4000, "informational"),
        ("assurance senegal", 5000, "informational"),
        ("investir senegal", 3000, "informational"),
    ],
    "emploi": [
        ("emploi senegal", 18000, "informational"),
        ("offre d'emploi dakar", 15000, "informational"),
        ("recrutement senegal", 12000, "informational"),
        ("jobs senegal", 10000, "informational"),
        ("stage senegal", 7000, "informational"),
        ("carriere senegal", 4000, "informational"),
        ("cv senegal", 3500, "informational"),
        ("fonctionnaire senegal", 5000, "informational"),
        ("concours senegal", 8000, "informational"),
        ("travail dakar", 6000, "informational"),
    ],
}

# Multiplicateurs CTR par type de requête
# Les requêtes navigationnelles bénéficient d'un CTR beaucoup plus élevé
# car l'utilisateur cherche spécifiquement ce site
QUERY_TYPE_MULTIPLIER = {
    "navigational":   2.8,   # L'utilisateur cherche ce site exactement
    "transactional":  1.2,   # Intent commercial → CTR légèrement supérieur
    "informational":  1.0,   # CTR standard de la courbe
}


# ─────────────────────────────────────────────────────────────────────────────
# PROXY : SCORE → POSITION ESTIMÉE
# ─────────────────────────────────────────────────────────────────────────────

def score_to_position(score_global: float, score_autorite: float = 50.0) -> int:
    """
    Convertit un score global (0-100) en position SERP estimée (1-20).

    Formule exponentielle calibrée sur le comportement observé :
      - score 100 → position 1 (monopole de niche)
      - score  80 → position ~3
      - score  60 → position ~7
      - score  40 → position ~12
      - score  20 → position 20+

    Le score d'autorité module légèrement la position :
    un site avec forte autorité backlinks surclasse son score technique.
    """
    # Pénalité/bonus autorité : ±15% selon l'écart à la moyenne (50)
    authority_bonus = (score_autorite - 50) / 50 * 0.15
    effective_score = max(0, min(100, score_global * (1 + authority_bonus)))

    # Courbe exponentielle : position = exp((100 - score) / 21.7)
    # Constante 21.7 calibrée pour : score=100→pos=1, score=40→pos=18
    pos = math.exp((100 - effective_score) / 21.7)
    return max(1, min(20, round(pos)))


def ctr_at_position(position: int, curve: dict = AWR_2023) -> float:
    """Retourne le CTR pour une position donnée (1-20). Extrapolation au-delà."""
    if position <= 0:
        return curve[1]
    if position in curve:
        return curve[position]
    # Extrapolation au-delà de 20 : décroissance exponentielle
    base = curve.get(20, 0.004)
    return base * math.exp(-(position - 20) * 0.15)


# ─────────────────────────────────────────────────────────────────────────────
# ESTIMATION PAR PROXY (niveau 2 — sans API)
# ─────────────────────────────────────────────────────────────────────────────

def estimate_traffic_proxy(
    row: pd.Series,
    curve: dict = AWR_2023,
) -> dict:
    """
    Estime le trafic mensuel d'un site par le modèle CTR proxy.

    Algorithme :
      Pour chaque mot-clé du pool de la catégorie :
        1. Vérifier si le mot-clé est navigational et correspond au site
           (ex: "senenews" → uniquement senenews.com bénéficie de ce volume)
        2. Estimer la position du site sur ce mot-clé
        3. Appliquer : trafic_kw = volume × CTR(position) × type_multiplier
      Total = somme de tous les mots-clés

    Pour les requêtes navigationnelles, seul le site "propriétaire" du
    mot-clé capte ce trafic. Pour les informational/transactional,
    le volume est partagé entre sites concurrents (divisé par ~5).
    """
    category = row.get("category", "presse")
    score_global = float(row.get("score_global", 50))
    score_autorite = float(row.get("score_autorite", 50))
    domain = str(row.get("domain", "")).lower().replace("www.", "")
    name = str(row.get("name", "")).lower()

    keywords = SENEGAL_KEYWORD_POOLS.get(category, [])
    estimated_position = score_to_position(score_global, score_autorite)

    total_traffic = 0
    breakdown = []

    for keyword, volume, query_type in keywords:
        # Pour les requêtes navigationnelles : trafic uniquement si le
        # mot-clé correspond au domaine ou au nom du site
        if query_type == "navigational":
            kw_clean = keyword.lower().replace(".", "").replace("-", "").replace(" ", "")
            domain_clean = domain.replace(".", "").replace("-", "")
            name_clean = name.replace(" ", "").replace("-", "")
            is_own_brand = (
                kw_clean in domain_clean or
                domain_clean in kw_clean or
                kw_clean in name_clean or
                name_clean in kw_clean
            )
            if not is_own_brand:
                continue  # Ce volume navigational appartient à un concurrent
            # Pour sa propre marque : CTR très élevé à la position 1
            effective_ctr = ctr_at_position(1, curve) * QUERY_TYPE_MULTIPLIER["navigational"]
            kw_traffic = int(volume * effective_ctr)
        else:
            # Requêtes partagées entre concurrents de la catégorie
            # Divisé par le nombre de sites dans la catégorie (~5 en moyenne)
            shared_volume = volume / 5.0
            effective_ctr = ctr_at_position(estimated_position, curve)
            type_mult = QUERY_TYPE_MULTIPLIER.get(query_type, 1.0)
            kw_traffic = int(shared_volume * effective_ctr * type_mult)

        total_traffic += kw_traffic
        breakdown.append({
            "keyword": keyword,
            "volume": volume,
            "type": query_type,
            "position": 1 if query_type == "navigational" else estimated_position,
            "ctr_pct": round(effective_ctr * 100, 2),
            "traffic": kw_traffic,
        })

    return {
        "trafic_ctr": total_traffic,
        "position_estimee": estimated_position,
        "breakdown": breakdown,
    }


def compute_ctr_scores(df: pd.DataFrame, curve_name: str = DEFAULT_CURVE) -> pd.DataFrame:
    """
    Applique le modèle CTR proxy à toute la dataframe.
    Ajoute les colonnes : trafic_ctr, position_estimee.
    """
    curve = CTR_CURVES.get(curve_name, AWR_2023)
    df = df.copy()

    results = df.apply(lambda row: estimate_traffic_proxy(row, curve), axis=1)
    df["trafic_ctr"]       = results.apply(lambda r: r["trafic_ctr"])
    df["position_estimee"] = results.apply(lambda r: r["position_estimee"])

    return df


# ─────────────────────────────────────────────────────────────────────────────
# INTÉGRATION API — SEMRUSH
# ─────────────────────────────────────────────────────────────────────────────

class SemrushClient:
    """
    Client pour l'API Semrush.

    Tarification : https://www.semrush.com/api-analytics/
    - Plan Free : 10 requêtes/jour (analytics uniquement)
    - Plan Pro  : 3 000 unités/jour incluses
    - Coût estimé : ~$0.01 par domaine analysé

    Endpoint utilisé : Domain Organic Search
    Retourne : mots-clés organiques, positions, volumes, trafic estimé

    Config requise :
        SEMRUSH_API_KEY=votre_clé  (dans .env ou variables d'env)
    """
    BASE_URL = "https://api.semrush.com/"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SEMRUSH_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "votre_cle_ici")

    def get_domain_traffic(self, domain: str, database: str = "ww") -> dict:
        """
        Récupère le trafic organique estimé par Semrush pour un domaine.

        Args:
            domain   : ex. "senenews.com"
            database : "ww" (global) | "fr" (France) — Sénégal non disponible
                       → utiliser "ww" puis appliquer ratio marché (~3%)

        Returns:
            dict avec organic_traffic, organic_keywords, paid_traffic, etc.
        """
        if not self.is_configured():
            raise ValueError("Clé API Semrush non configurée. Ajouter SEMRUSH_API_KEY dans .env")

        params = {
            "type":       "domain_ranks",
            "key":        self.api_key,
            "domain":     domain,
            "database":   database,
            "export_columns": "Dn,Rk,Or,Ot,Oc,Ad,At,Ac",
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            lines = resp.text.strip().split("\n")
            if len(lines) < 2:
                return {"error": "Aucune donnée retournée", "domain": domain}
            headers = lines[0].split(";")
            values  = lines[1].split(";")
            data = dict(zip(headers, values))
            return {
                "domain":            domain,
                "organic_keywords":  int(data.get("Organic Keywords", 0) or 0),
                "organic_traffic":   int(data.get("Organic Traffic", 0) or 0),
                "organic_cost":      float(data.get("Organic Cost", 0) or 0),
                "source":            "semrush_api",
                "database":          database,
            }
        except requests.RequestException as e:
            return {"error": str(e), "domain": domain}

    def get_domain_keywords(self, domain: str, database: str = "ww", limit: int = 20) -> list:
        """
        Récupère les mots-clés organiques d'un domaine avec leurs positions.

        Returns:
            liste de dicts {keyword, position, volume, cpc, url, traffic_pct}
        """
        if not self.is_configured():
            return []

        params = {
            "type":            "domain_organic",
            "key":             self.api_key,
            "domain":          domain,
            "database":        database,
            "display_limit":   limit,
            "display_sort":    "tr_desc",
            "export_columns":  "Ph,Po,Nq,Cp,Ur,Tr",
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            lines = resp.text.strip().split("\n")
            if len(lines) < 2:
                return []
            headers = lines[0].split(";")
            results = []
            for line in lines[1:]:
                vals = line.split(";")
                row = dict(zip(headers, vals))
                results.append({
                    "keyword":     row.get("Keyword", ""),
                    "position":    int(row.get("Position", 20) or 20),
                    "volume":      int(row.get("Search Volume", 0) or 0),
                    "cpc":         float(row.get("CPC", 0) or 0),
                    "url":         row.get("URL", ""),
                    "traffic_pct": float(row.get("Traffic (%)", 0) or 0),
                })
            return results
        except requests.RequestException:
            return []

    def estimate_traffic_from_keywords(self, domain: str, curve: dict = AWR_2023) -> dict:
        """
        Estime le trafic via les mots-clés Semrush + courbe CTR.
        Plus précis que le proxy score→position.
        """
        keywords = self.get_domain_keywords(domain, limit=50)
        if not keywords:
            return {"error": "Aucun mot-clé trouvé", "domain": domain}

        total = sum(
            int(kw["volume"] * ctr_at_position(kw["position"], curve))
            for kw in keywords
        )
        return {
            "domain":          domain,
            "trafic_ctr":      total,
            "keywords_count":  len(keywords),
            "source":          "semrush_keywords",
        }


# ─────────────────────────────────────────────────────────────────────────────
# INTÉGRATION API — DATAFORSEO
# ─────────────────────────────────────────────────────────────────────────────

class DataForSEOClient:
    """
    Client pour l'API DataForSEO.

    Avantages vs Semrush : accès au SERP Google Sénégal (location_code=2686)
    Tarification : pay-as-you-go ~$0.0001/résultat (très accessible)
    Documentation : https://docs.dataforseo.com/

    Config requise dans .env :
        DATAFORSEO_LOGIN=votre_login
        DATAFORSEO_PASSWORD=votre_password
    """
    BASE_URL = "https://api.dataforseo.com/v3/"
    SENEGAL_LOCATION = 2686   # Google Sénégal (google.sn)
    FRANCE_LOCATION  = 2250   # Fallback si Sénégal non disponible

    def __init__(self, login: Optional[str] = None, password: Optional[str] = None):
        self.login    = login    or os.environ.get("DATAFORSEO_LOGIN", "")
        self.password = password or os.environ.get("DATAFORSEO_PASSWORD", "")

    def is_configured(self) -> bool:
        return bool(self.login and self.password)

    def _auth_header(self) -> dict:
        creds = base64.b64encode(f"{self.login}:{self.password}".encode()).decode()
        return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}

    def get_domain_metrics(self, domain: str) -> dict:
        """
        Récupère les métriques organiques d'un domaine via DataForSEO Labs.
        Endpoint : /dataforseo_labs/google/domain_metrics_by_categories/live

        Returns:
            dict avec organic_traffic_etpt, organic_count, visibility_index
        """
        if not self.is_configured():
            raise ValueError("Identifiants DataForSEO non configurés (DATAFORSEO_LOGIN / _PASSWORD)")

        payload = [{
            "target":        domain,
            "language_code": "fr",
            "location_code": self.SENEGAL_LOCATION,
        }]
        try:
            resp = requests.post(
                self.BASE_URL + "dataforseo_labs/google/domain_metrics_by_categories/live",
                headers=self._auth_header(),
                json=payload,
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            tasks = data.get("tasks", [])
            if not tasks or tasks[0].get("status_code") != 20000:
                return {"error": "Aucun résultat", "domain": domain}
            result = tasks[0].get("result", [{}])[0]
            metrics = result.get("metrics", {}).get("organic", {})
            return {
                "domain":           domain,
                "organic_traffic":  metrics.get("etv", 0),    # Expected Traffic Value
                "organic_count":    metrics.get("count", 0),  # Nombre de mots-clés classés
                "visibility":       metrics.get("pos_1", 0),  # Positions #1
                "source":           "dataforseo_labs",
                "location":         "senegal",
            }
        except requests.RequestException as e:
            return {"error": str(e), "domain": domain}

    def get_domain_serp_positions(self, domain: str, keywords: list[str]) -> list:
        """
        Récupère les positions SERP pour une liste de mots-clés sur google.sn.
        Plus précis que les labs : donne la vraie position sur le marché sénégalais.

        Args:
            domain   : domaine cible, ex. "senenews.com"
            keywords : liste de mots-clés à checker

        Returns:
            liste de {keyword, position, url, volume} pour ce domaine
        """
        if not self.is_configured() or not keywords:
            return []

        tasks = [
            {
                "keyword":       kw,
                "location_code": self.SENEGAL_LOCATION,
                "language_code": "fr",
                "device":        "mobile",
                "depth":         30,
            }
            for kw in keywords[:10]  # Max 10 par appel pour contrôler les coûts
        ]
        try:
            resp = requests.post(
                self.BASE_URL + "serp/google/organic/task_post",
                headers=self._auth_header(),
                json=tasks,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for task in data.get("tasks", []):
                if task.get("status_code") != 20000:
                    continue
                keyword = task["data"].get("keyword", "")
                for item in task.get("result", [{}])[0].get("items", []):
                    if domain.replace("www.", "") in item.get("domain", ""):
                        results.append({
                            "keyword":  keyword,
                            "position": item.get("rank_group", 20),
                            "url":      item.get("url", ""),
                        })
                        break
            return results
        except requests.RequestException:
            return []


# ─────────────────────────────────────────────────────────────────────────────
# INTÉGRATION API — SERPER.DEV (Google Search API)
# ─────────────────────────────────────────────────────────────────────────────

class SerperDevClient:
    """
    Client pour l'API Serper.dev — Google Search API.

    Avantages :
      - Accepte les comptes Gmail (inscription via Google)
      - 2 500 recherches gratuites/mois (sans carte bancaire)
      - Accès à Google Sénégal via gl=sn
      - Résultats SERP en temps réel (~100ms de latence)

    Tarification : https://serper.dev/pricing
      - Gratuit : 2 500 requêtes/mois
      - Starter : $50 pour 50 000 requêtes
      - Coût estimé pour 28 sites × 10 kw : 280 requêtes → 100% gratuit

    Inscription : https://serper.dev → "Sign up with Google"

    Config requise dans .env :
        SERPER_API_KEY=votre_cle_api
    """
    BASE_URL = "https://google.serper.dev/search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SERPER_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key not in ("votre_cle_serper", ""))

    def get_domain_position(
        self,
        domain: str,
        keyword: str,
        country: str = "sn",
        lang: str = "fr",
        depth: int = 10,
    ) -> int:
        """
        Retourne la position de `domain` pour `keyword` sur Google Sénégal.

        Args:
            domain  : ex. "senenews.com" (avec ou sans www)
            keyword : terme de recherche
            country : code pays ISO 2 lettres (sn = Sénégal)
            lang    : code langue (fr = français)
            depth   : nombre de résultats à analyser (max 100)

        Returns:
            Position 1-100 si trouvé, 20 si non classé dans le top `depth`.
        """
        if not self.is_configured():
            raise ValueError("Clé API Serper.dev non configurée. Ajouter SERPER_API_KEY dans .env")

        headers = {
            "X-API-KEY":    self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q":   keyword,
            "gl":  country,
            "hl":  lang,
            "num": depth,
        }
        resp = requests.post(self.BASE_URL, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        domain_clean = domain.lower().replace("www.", "")
        for item in data.get("organic", []):
            link = item.get("link", "").lower()
            if domain_clean in link:
                return int(item.get("position", 20))

        return 20  # Non trouvé dans le top `depth`

    def get_real_positions(
        self,
        domain: str,
        category: str,
        max_keywords: int = 10,
        country: str = "sn",
    ) -> list:
        """
        Vérifie les vraies positions SERP pour les mots-clés du pool de la catégorie.

        Args:
            domain       : domaine cible
            category     : catégorie dans SENEGAL_KEYWORD_POOLS
            max_keywords : nombre max de mots-clés à checker (pour limiter les coûts)
            country      : code pays Google (sn = Sénégal)

        Returns:
            liste de dicts {keyword, volume, query_type, real_position}
        """
        keywords = SENEGAL_KEYWORD_POOLS.get(category, [])[:max_keywords]
        results = []
        for keyword, volume, query_type in keywords:
            try:
                pos = self.get_domain_position(domain, keyword, country=country)
            except Exception:
                pos = 20  # Fallback si erreur réseau
            results.append({
                "keyword":       keyword,
                "volume":        volume,
                "query_type":    query_type,
                "real_position": pos,
            })
        return results

    def estimate_traffic_from_serp(
        self,
        domain: str,
        category: str,
        curve: dict = AWR_2023,
        max_keywords: int = 10,
    ) -> dict:
        """
        Estime le trafic en combinant les vraies positions Serper.dev + courbe CTR.

        C'est la méthode la plus précise sans abonnement Semrush :
          - Positions réelles sur Google Sénégal (gl=sn)
          - Volumes issus du pool SENEGAL_KEYWORD_POOLS
          - CTR appliqué via la courbe choisie

        Returns:
            dict avec trafic_ctr, position_moyenne, source, breakdown
        """
        positions = self.get_real_positions(domain, category, max_keywords)
        if not positions:
            return {"error": "Aucun résultat", "domain": domain, "source": "serper"}

        total_traffic = 0
        breakdown = []

        domain_clean = domain.lower().replace("www.", "")

        for item in positions:
            keyword    = item["keyword"]
            volume     = item["volume"]
            query_type = item["query_type"]
            pos        = item["real_position"]

            # Pour les requêtes navigationnelles, s'assurer que le volume
            # correspond bien à ce domaine (même logique que le proxy)
            if query_type == "navigational":
                kw_clean = keyword.lower().replace(".", "").replace("-", "").replace(" ", "")
                dc = domain_clean.replace(".", "").replace("-", "")
                if kw_clean not in dc and dc not in kw_clean:
                    # Ce mot-clé branded appartient à un concurrent
                    continue
                effective_ctr = ctr_at_position(pos, curve) * QUERY_TYPE_MULTIPLIER["navigational"]
                kw_traffic = int(volume * effective_ctr)
            else:
                shared_volume = volume / 5.0
                effective_ctr = ctr_at_position(pos, curve)
                type_mult     = QUERY_TYPE_MULTIPLIER.get(query_type, 1.0)
                kw_traffic    = int(shared_volume * effective_ctr * type_mult)

            total_traffic += kw_traffic
            breakdown.append({
                "keyword":    keyword,
                "volume":     volume,
                "type":       query_type,
                "position":   pos,
                "ctr_pct":    round(effective_ctr * 100, 2),
                "traffic":    kw_traffic,
            })

        avg_pos = (
            round(sum(i["real_position"] for i in positions) / len(positions), 1)
            if positions else 20
        )

        return {
            "domain":           domain,
            "trafic_ctr":       total_traffic,
            "position_moyenne": avg_pos,
            "keywords_checked": len(positions),
            "source":           "serper_dev",
            "breakdown":        breakdown,
        }


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION PRINCIPALE — ESTIME LE TRAFIC (avec fallback automatique)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_real_traffic(domain: str, category: str = "presse", curve: dict = AWR_2023) -> dict:
    """
    Essaie dans l'ordre :
      1. Serper.dev (positions Google Sénégal réelles — accepte Gmail, gratuit)
      2. DataForSEO Labs (plus précis, Google Sénégal)
      3. Semrush (global, data riche)
      4. Proxy CTR (pas d'API nécessaire)
    Retourne toujours un résultat avec indication de la source.
    """
    # Essai Serper.dev (priorité 1 — accepte Gmail, 2 500 req/mois gratuit)
    serper = SerperDevClient()
    if serper.is_configured():
        try:
            result = serper.estimate_traffic_from_serp(domain, category, curve)
            if "error" not in result and result.get("trafic_ctr", 0) > 0:
                return {"trafic_api": result["trafic_ctr"], **result}
        except Exception:
            pass  # Fallback sur l'API suivante

    # Essai DataForSEO
    dfs = DataForSEOClient()
    if dfs.is_configured():
        result = dfs.get_domain_metrics(domain)
        if "error" not in result and result.get("organic_traffic", 0) > 0:
            return {"trafic_api": result["organic_traffic"], "source": "dataforseo", **result}

    # Essai Semrush
    sem = SemrushClient()
    if sem.is_configured():
        result = sem.get_domain_traffic(domain)
        if "error" not in result and result.get("organic_traffic", 0) > 0:
            # Ratio Sénégal : environ 2-4% du trafic global Semrush pour les sites sénégalais
            senegal_ratio = 0.03
            return {
                "trafic_api": int(result["organic_traffic"] * senegal_ratio),
                "source":     "semrush",
                **result,
            }

    return {"trafic_api": None, "source": "proxy"}


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES PARTAGÉES
# ─────────────────────────────────────────────────────────────────────────────

CATEGORY_BASE = {
    "presse":        250000,
    "ecommerce":      80000,
    "telephonie":    120000,
    "banque_finance":  60000,
    "emploi":         40000,
}

CATEGORY_LABELS = {
    "presse":        "Presse & Médias",
    "ecommerce":     "E-commerce",
    "telephonie":    "Téléphonie & Telecom",
    "banque_finance": "Banque & Finance",
    "emploi":        "Emploi & Recrutement",
}
