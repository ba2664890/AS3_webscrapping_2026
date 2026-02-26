"""
Lance ce fichier depuis senwebstats/ :
  python diagnostic_ddg.py

Il va analyser la vraie structure HTML de DuckDuckGo
et trouver les bons sélecteurs CSS automatiquement.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

print("Requête vers DuckDuckGo...")
url = "https://html.duckduckgo.com/html/?q=seneweb+senegal&kl=sn-fr"
r = requests.get(url, headers=headers, timeout=15)
print(f"Status: {r.status_code} | Taille: {len(r.text)} caractères")

soup = BeautifulSoup(r.text, "html.parser")

# ── Test 1 : tous les liens HTTP ──────────────────────────────
print("\n" + "="*55)
print("TEST 1 — Tous les liens <a href=http...> dans la page")
print("="*55)
found_links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if href.startswith("http") and "duckduckgo" not in href:
        domain = urlparse(href).netloc.replace("www.", "")
        text = a.get_text(strip=True)[:50]
        found_links.append((href, domain, text))

print(f"Trouvé {len(found_links)} liens externes")
for href, domain, text in found_links[:15]:
    print(f"  {domain:<30} | {text}")

# ── Test 2 : structure des divs ───────────────────────────────
print("\n" + "="*55)
print("TEST 2 — Classes CSS des divs principaux")
print("="*55)
classes_found = {}
for div in soup.find_all("div", class_=True):
    for cls in div.get("class", []):
        classes_found[cls] = classes_found.get(cls, 0) + 1

# Afficher les classes les plus fréquentes
top_classes = sorted(classes_found.items(), key=lambda x: x[1], reverse=True)[:20]
for cls, count in top_classes:
    print(f"  .{cls:<30} {count}x")

# ── Test 3 : sélecteurs candidats ────────────────────────────
print("\n" + "="*55)
print("TEST 3 — Sélecteurs candidats pour les résultats")
print("="*55)
selectors = [
    ".result", ".web-result", ".result__body", ".results_links",
    "article", ".serp__results", ".result__title", "h2",
    "[data-testid]", ".results--main", "li.result"
]
for sel in selectors:
    elements = soup.select(sel)
    if elements:
        print(f"  '{sel}' → {len(elements)} éléments TROUVÉS ✓")
        # Montrer le premier
        first_text = elements[0].get_text(strip=True)[:80]
        print(f"    Exemple: {first_text}")
    else:
        print(f"  '{sel}' → 0 éléments")

# ── Test 4 : sauvegarder le HTML pour inspection ─────────────
with open("ddg_debug.html", "w", encoding="utf-8") as f:
    f.write(r.text)
print(f"\n  HTML sauvegardé dans ddg_debug.html ({len(r.text)} chars)")
print("  Ouvre ce fichier avec le Bloc-notes pour voir la structure")
print("\n" + "="*55)
