# 📊 SenWebStats 🇸🇳
## Statistiques & Performances des Sites Web Sénégalais

> L'équivalent sénégalais de Semrush/Ahrefs — 100% sources gratuites.

---

## 🎯 Objectif

Analyser et comparer les performances web des sites sénégalais (presse, e-commerce, téléphonie, banque, emploi) en collectant :

- **Métadonnées HTML** : title, description, structure, liens
- **Performance** : Google PageSpeed (Core Web Vitals)
- **Backlinks** : CommonCrawl Index (gratuit)
- **Estimation de trafic** : Modèle CTR × Volume de recherche

---

## 🚀 Installation

```bash
# 1. Cloner / créer le projet
cd senwebstats

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Initialiser la base de données
python main.py init

# 4. Lancer la collecte
python main.py crawl          # Métadonnées HTML
python main.py perf           # Performance PageSpeed
python main.py backlinks      # Backlinks CommonCrawl

# 5. Lancer l'app Streamlit
streamlit run app/streamlit_app.py
```

---

## 📁 Structure du Projet

```
senwebstats/
├── main.py                          # Point d'entrée principal
├── requirements.txt
├── config/
│   └── sites.py                     # Liste des sites cibles
├── database/
│   └── schema.py                    # Schéma SQLite + fonctions DB
├── data_collection/
│   ├── scrapers/
│   │   └── metadata_scraper.py      # Scraper HTML principal
│   └── apis/
│       ├── pagespeed_collector.py   # Google PageSpeed API
│       └── backlinks_collector.py   # CommonCrawl backlinks
├── processing/                      # À venir : modèle CTR
├── app/
│   └── streamlit_app.py             # Dashboard Streamlit
└── data/
    └── senwebstats.db               # Base SQLite (générée)
```

---

## 🔧 Commandes Disponibles

| Commande | Description |
|----------|-------------|
| `python main.py init` | Initialiser DB + insérer les sites |
| `python main.py crawl` | Crawler tous les sites |
| `python main.py crawl --cat presse` | Crawler une catégorie |
| `python main.py perf` | Collecter les scores PageSpeed |
| `python main.py backlinks` | Collecter les backlinks |
| `python main.py full` | Tout collecter en une fois |
| `python main.py report` | Rapport rapide en terminal |
| `streamlit run app/streamlit_app.py` | Lancer le dashboard |

---

## 📊 Métriques Collectées

### Métadonnées HTML
- Title, meta description, meta keywords
- Balises Open Graph (titre, description, image)
- Canonical URL, robots meta
- H1, H2 count
- Liens internes / externes
- Images (avec/sans alt)
- Nombre de mots
- SSL, Sitemap, Robots.txt

### Performance (PageSpeed API)
- Score Performance, SEO, Accessibilité, Bonnes pratiques
- LCP (Largest Contentful Paint)
- FCP (First Contentful Paint)
- TTFB (Time To First Byte)
- CLS (Cumulative Layout Shift)
- TTI (Time To Interactive)

### Backlinks (CommonCrawl)
- Total pages indexées
- Domaines référents
- Top domaines référents
- Évolution vs collecte précédente

---

## 🗂️ Sites Suivis

| Catégorie | Sites |
|-----------|-------|
| 📰 Presse | Seneweb, Dakaractu, Senenews, Rewmi, Leral, Senego... |
| 🛒 E-commerce | Jumia, Expat Dakar, CoinAfrique, Afrikrea... |
| 📱 Téléphonie | Orange SN, Free SN, Expresso, Sonatel |
| 🏦 Banque/Finance | CBAO, Ecobank, Wave, Orange Money |
| 💼 Emploi | Senjob, Emploi.sn, Rekrute |

---

## 🗺️ Roadmap

- [x] Phase 1 : Scraper métadonnées HTML
- [x] Phase 1 : Performance PageSpeed
- [x] Phase 1 : Backlinks CommonCrawl
- [x] Phase 1 : Dashboard Streamlit basique
- [ ] Phase 2 : Modèle CTR × Volume (estimation trafic)
- [ ] Phase 2 : Scraping SERP Google (positions mots-clés)
- [ ] Phase 2 : Analyse de tendances temporelles
- [ ] Phase 3 : Scheduler automatique (collecte quotidienne)
- [ ] Phase 3 : Alertes sur changements significatifs
- [ ] Phase 4 : API FastAPI publique
- [ ] Phase 4 : Export CSV/Excel des données

---

## ⚠️ Bonnes Pratiques

- Délais entre requêtes : 2-5 secondes
- Rotation des User-Agents
- Respect des fichiers robots.txt
- API PageSpeed : gratuite jusqu'à 25 000 req/jour
- CommonCrawl : utilisation de l'API index (pas de téléchargement massif)

---

## 👨‍💻 Prochaines Étapes

Pour estimer le trafic comme Semrush, il faudra :
1. Collecter les mots-clés pour lesquels chaque site se positionne (scraping SERP)
2. Récupérer les volumes de recherche mensuels (Google Keyword Planner ou scraping)
3. Appliquer le modèle CTR par position : `trafic = volume × CTR[position]`
4. Agréger par site pour obtenir le trafic mensuel estimé
python app/dashboard.py