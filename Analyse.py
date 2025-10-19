import os
import sys
import requests
import datetime
import json
from bs4 import BeautifulSoup
import time as time_module
from typing import Dict, List, Optional
import re
import subprocess
import shutil
import tempfile
import logging

# --- Configuration via variables d'environnement (GitHub secrets) ---
FOOTBALL_KEY = os.environ.get("FOOTBALL_KEY")
GRQ_KEY = os.environ.get("GRQ_KEY")
# Optionnel: remote name (default: origin)
GIT_REMOTE = os.environ.get("GIT_REMOTE", "origin")
# Optional git author override
GIT_AUTHOR_NAME = os.environ.get("GIT_AUTHOR_NAME")
GIT_AUTHOR_EMAIL = os.environ.get("GIT_AUTHOR_EMAIL")
# Paramètres
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "20"))
SLEEP_BETWEEN_REQUESTS = float(os.environ.get("SLEEP_BETWEEN_REQUESTS", "0.8"))

if not FOOTBALL_KEY:
    print("❌ Erreur: la variable d'environnement FOOTBALL_KEY n'est pas définie.")
    sys.exit(1)
if not GRQ_KEY:
    print("❌ Erreur: la variable d'environnement GRQ_KEY n'est pas définie.")
    sys.exit(1)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class FootballMatchAnalyzerWithAI:
    def __init__(self):
        # Configuration API Football
        self.api_key = FOOTBALL_KEY
        self.api_base_url = "https://v3.football.api-sports.io/fixtures"
        self.api_headers = {
            "x-apisports-key": self.api_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }

        # Configuration IA Groq
        self.groq_api_key = GRQ_KEY
        self.groq_model = "openai/gpt-oss-120b"
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"

        # Headers pour le web scraping
        self.scraping_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }

        # Ligues autorisées avec leurs IDs et noms
        self.authorized_leagues = {
            2: "UEFA Champions League",
            253: "MLS",
            3: "UEFA Europa League",
            88: "Dutch Eredivisie",
            94: "Portuguese Primeira Liga",
            143: "Spanish Copa del Rey",
            81: "German Cup",
            66: "Coupe de France",
            307: "Saudi Pro League",
            144: "Belgian Pro League",
            235: "Russian Premier League",
            141: "Spanish LaLiga 2",
            203: "Turkish Super Lig",
            62: "French Ligue 2",
            128: "Argentine Liga Profesional",
            239: "Colombian Primera A",
            71: "Brazilian Serie A",
            61: "French Ligue 1",
            78: "German Bundesliga",
            135: "Italian Serie A",
            40: "English Championship",
            140: "Spanish LaLiga"
        }

        # Dictionnaire associant les IDs de ligues aux URLs de classements ESPN
        self.league_standings_urls = {
            2: "https://www.espn.com/football/standings/_/league/UEFA.CHAMPIONS",
            253: "https://www.espn.com/football/standings/_/league/USA.1",
            3: "https://www.espn.com/football/standings/_/league/UEFA.EUROPA",
            88: "https://www.espn.com/football/standings/_/league/NED.1",
            94: "https://www.espn.com/football/standings/_/league/POR.1",
            143: "https://www.espn.com/football/standings/_/league/ESP.COPA_DEL_REY",
            81: "https://www.espn.com/football/standings/_/league/GER.DFB_POKAL",
            66: "https://www.espn.com/football/standings/_/league/FRA.COUPE_DE_FRANCE",
            307: "https://www.espn.com/football/standings/_/league/KSA.1",
            144: "https://www.espn.com/football/standings/_/league/BEL.1",
            235: "https://www.espn.com/football/standings/_/league/RUS.1",
            141: "https://www.espn.com/football/standings/_/league/ESP.2",
            203: "https://www.espn.com/football/standings/_/league/TUR.1",
            62: "https://www.espn.com/football/standings/_/league/FRA.2",
            128: "https://www.espn.com/football/standings/_/league/ARG.1",
            239: "https://www.espn.com/football/standings/_/league/COL.1",
            71: "https://www.espn.com/football/standings/_/league/BRA.1",
            61: "https://www.espn.com/football/standings/_/league/FRA.1",
            78: "https://www.espn.com/football/standings/_/league/GER.1",
            135: "https://www.espn.com/football/standings/_/league/ITA.1",
            40: "https://www.espn.com/football/standings/_/league/ENG.2",
            140: "https://www.espn.com/football/standings/_/league/ESP.1"
        }

        # Charger les données des équipes (base minimaliste fournie précédemment)
        self.teams_data = self._load_teams_data()

        # Répertoire pour sauvegarder les analyses JSON
        self.output_dir = "analyses"
        os.makedirs(self.output_dir, exist_ok=True)

    # ------------------------- Utilitaires Git -------------------------
    def _git_commit_and_push(self, file_paths: List[str], commit_message: str) -> bool:
        """
        Commit et push des fichiers listés.
        Nécessite que le repo git local soit initialisé et que le runner ait les droits pour push.
        """
        try:
            # Optionnel set author
            if GIT_AUTHOR_NAME:
                subprocess.run(["git", "config", "user.name", GIT_AUTHOR_NAME], check=True)
            if GIT_AUTHOR_EMAIL:
                subprocess.run(["git", "config", "user.email", GIT_AUTHOR_EMAIL], check=True)

            # Ajouter les fichiers
            subprocess.run(["git", "add"] + file_paths, check=True)

            # Commit - si rien à committer, git commit renverra un code non nul ; attraper et continuer
            try:
                subprocess.run(["git", "commit", "-m", commit_message], check=True)
            except subprocess.CalledProcessError:
                # Nothing to commit
                logging.info("ℹ️ Aucun changement à committer pour les fichiers fournis.")

            # Push
            subprocess.run(["git", "push", GIT_REMOTE, "HEAD"], check=True)

            logging.info("✅ Commit et push effectués.")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"❌ Erreur git: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Erreur inattendue lors du git commit/push: {e}")
            return False

    # ------------------------- IA Groq -------------------------
    def ask_groq(self, messages):
        """Envoie une requête à l'IA Groq"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.groq_api_key}"
        }

        data = {
            "model": self.groq_model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 3000
        }

        try:
            response = requests.post(self.groq_url, headers=headers, data=json.dumps(data), timeout=30)

            if response.status_code != 200:
                logging.error(f"❌ Erreur IA {response.status_code}: {response.text}")
                return None

            j = response.json()
            content = None
            try:
                content = j["choices"][0]["message"]["content"]
            except Exception:
                if "choices" in j and isinstance(j["choices"], list) and len(j["choices"]) > 0:
                    choice = j["choices"][0]
                    if "text" in choice:
                        content = choice["text"]
                    elif "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
            return content
        except Exception as e:
            logging.error(f"❌ Erreur lors de la communication avec l'IA: {e}")
            return None

    # ------------------------- Chargement des équipes -------------------------
    def _load_teams_data(self) -> Dict:
        """Charge les données complètes des équipes (minimal) — étendue pour meilleures chances de correspondance"""
        teams_data = {
            "Premier League (ENG.1)": [
                {"team": "AFC Bournemouth", "results_url": "https://www.espn.com/football/team/results/_/id/349/afc-bournemouth"},
                {"team": "Arsenal", "results_url": "https://www.espn.com/football/team/results/_/id/359/arsenal"},
                {"team": "Aston Villa", "results_url": "https://www.espn.com/football/team/results/_/id/362/aston-villa"},
                {"team": "Brentford", "results_url": "https://www.espn.com/football/team/results/_/id/337/brentford"},
                {"team": "Brighton & Hove Albion", "results_url": "https://www.espn.com/football/team/results/_/id/331/brighton-hove-albion"},
                {"team": "Burnley", "results_url": "https://www.espn.com/football/team/results/_/id/379/burnley"},
                {"team": "Chelsea", "results_url": "https://www.espn.com/football/team/results/_/id/363/chelsea"},
                {"team": "Crystal Palace", "results_url": "https://www.espn.com/football/team/results/_/id/384/crystal-palace"},
                {"team": "Everton", "results_url": "https://www.espn.com/football/team/results/_/id/368/everton"},
                {"team": "Fulham", "results_url": "https://www.espn.com/football/team/results/_/id/370/fulham"},
                {"team": "Leeds United", "results_url": "https://www.espn.com/football/team/results/_/id/357/leeds-united"},
                {"team": "Liverpool", "results_url": "https://www.espn.com/football/team/results/_/id/364/liverpool"},
                {"team": "Manchester City", "results_url": "https://www.espn.com/football/team/results/_/id/382/manchester-city"},
                {"team": "Manchester United", "results_url": "https://www.espn.com/football/team/results/_/id/360/manchester-united"},
                {"team": "Newcastle United", "results_url": "https://www.espn.com/football/team/results/_/id/361/newcastle-united"},
                {"team": "Nottingham Forest", "results_url": "https://www.espn.com/football/team/results/_/id/393/nottingham-forest"},
                {"team": "Sunderland", "results_url": "https://www.espn.com/football/team/results/_/id/366/sunderland"},
                {"team": "Tottenham Hotspur", "results_url": "https://www.espn.com/football/team/results/_/id/367/tottenham-hotspur"},
                {"team": "West Ham United", "results_url": "https://www.espn.com/football/team/results/_/id/371/west-ham-united"},
                {"team": "Wolverhampton Wanderers", "results_url": "https://www.espn.com/football/team/results/_/id/380/wolverhampton-wanderers"}
            ],
            # Ajouts simplifiés pour autres ligues utilisés dans votre JSON (Argentine, Colombie, Russie, etc.)
            "Argentine (ARG.1)": [
                {"team": "Argentinos JRS", "results_url": "https://www.espn.com/football/team/results/_/id/458/argentinos-juniors"},
                {"team": "Newells Old Boys", "results_url": "https://www.espn.com/football/team/results/_/id/457/newell's-old-boys"},
                {"team": "Lanus", "results_url": "https://www.espn.com/football/team/results/_/id/446/lanus"},
                {"team": "Godoy Cruz", "results_url": "https://www.espn.com/football/team/results/_/id/439/godoy-cruz"},
                {"team": "Boca Juniors", "results_url": "https://www.espn.com/football/team/results/_/id/451/boca-juniors"},
                {"team": "River Plate", "results_url": "https://www.espn.com/football/team/results/_/id/435/river-plate"},
                {"team": "Talleres Cordoba", "results_url": "https://www.espn.com/football/team/results/_/id/456/talleres"}
            ],
            "Colombia (COL.1)": [
                {"team": "Santa Fe", "results_url": "https://www.espn.com/football/team/results/_/id/1139/independiente-santa-fe"},
                {"team": "Junior", "results_url": "https://www.espn.com/football/team/results/_/id/1135/junior-barranquilla"},
                {"team": "Deportivo Pereira", "results_url": "https://www.espn.com/football/team/results/_/id/1462/deportivo-pereira"}
            ],
            "Russian (RUS.1)": [
                {"team": "FC Orenburg", "results_url": "https://www.espn.com/football/team/results/_/id/1080/fc-orenburg"},
                {"team": "Nizhny Novgorod", "results_url": "https://www.espn.com/football/team/results/_/id/2011/nizhny-novgorod"}
            ],
            "MLS (USA.1)": [
                {"team": "Atlanta United FC", "results_url": "https://www.espn.com/football/team/results/_/id/1608/atlanta-united"},
                {"team": "DC United", "results_url": "https://www.espn.com/football/team/results/_/id/1615/dc-united"},
                {"team": "Inter Miami", "results_url": "https://www.espn.com/football/team/results/_/id/9568/inter-miami"},
                {"team": "New York Red Bulls", "results_url": "https://www.espn.com/football/team/results/_/id/1602/new-york-red-bulls"}
            ],
            # Vous pouvez étendre cette liste au besoin...
        }
        return teams_data

    # ------------------------- API Fixtures -------------------------
    def get_today_matches(self) -> List[Dict]:
        """Récupère les matchs du jour depuis l'API"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        params = {"date": today}

        logging.info(f"📅 Récupération des matchs du {today}...")

        try:
            response = requests.get(self.api_base_url, headers=self.api_headers, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            if not data.get("response"):
                logging.warning("⚠️ Aucun match trouvé pour aujourd'hui via l'API.")
                return []

            matches = [
                match for match in data["response"]
                if match["league"]["id"] in self.authorized_leagues
            ]

            if not matches:
                logging.warning("⚠️ Aucun match trouvé dans les ligues sélectionnées.")
                return []

            logging.info(f"✅ {len(matches)} matchs trouvés dans les ligues sélectionnées")
            return matches

        except requests.RequestException as e:
            logging.error(f"❌ Erreur lors de la récupération des matchs: {e}")
            return []

    # ------------------------- Scraping Classements -------------------------
    def scrape_league_standings(self, league_id: int) -> List[Dict]:
        """Récupère le classement d'une ligue depuis ESPN"""
        standings_url = self.league_standings_urls.get(league_id)

        if not standings_url:
            logging.warning(f"❌ URL de classement non trouvée pour la ligue ID {league_id}")
            return []

        try:
            response = requests.get(standings_url, headers=self.scraping_headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            standings = []

            # Approches multiples pour extraire les données
            # 1) Table moderne ESPN (table.Table)
            table = soup.find("table", class_="Table")
            if table:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["th", "td"])
                    # Rechercher ligne contenant position + équipe + 8 stats
                    texts = [c.get_text(strip=True) for c in cells]
                    if len(texts) >= 10:
                        try:
                            pos = texts[0]
                            team_name = texts[1]
                            # prendre les 8 dernières colonnes comme stats si possible
                            stats = texts[-8:]
                            if pos.isdigit() or (pos and pos[0].isdigit()):
                                standings.append({
                                    "position": pos,
                                    "team": team_name,
                                    "gp": stats[0] if len(stats) > 0 else "",
                                    "w": stats[1] if len(stats) > 1 else "",
                                    "d": stats[2] if len(stats) > 2 else "",
                                    "l": stats[3] if len(stats) > 3 else "",
                                    "f": stats[4] if len(stats) > 4 else "",
                                    "a": stats[5] if len(stats) > 5 else "",
                                    "gd": stats[6] if len(stats) > 6 else "",
                                    "p": stats[7] if len(stats) > 7 else ""
                                })
                        except Exception:
                            continue

            # 2) fallback: lignes avec span.rank ou structure alternative
            if not standings:
                rows = soup.find_all("tr")
                for row in rows:
                    rank_span = row.find("span", class_=re.compile("rank|position", re.I))
                    if rank_span:
                        try:
                            pos = rank_span.get_text(strip=True)
                            # chercher nom d'équipe
                            team_span = row.find("span", class_=re.compile("hide-mobile|team-name|long-name", re.I))
                            team_name = team_span.get_text(strip=True) if team_span else ""
                            tds = row.find_all("td")
                            stats_cells = [td.get_text(strip=True) for td in tds[-8:]] if len(tds) >= 8 else []
                            if team_name:
                                standings.append({
                                    "position": pos,
                                    "team": team_name,
                                    "gp": stats_cells[0] if len(stats_cells) > 0 else "",
                                    "w": stats_cells[1] if len(stats_cells) > 1 else "",
                                    "d": stats_cells[2] if len(stats_cells) > 2 else "",
                                    "l": stats_cells[3] if len(stats_cells) > 3 else "",
                                    "f": stats_cells[4] if len(stats_cells) > 4 else "",
                                    "a": stats_cells[5] if len(stats_cells) > 5 else "",
                                    "gd": stats_cells[6] if len(stats_cells) > 6 else "",
                                    "p": stats_cells[7] if len(stats_cells) > 7 else ""
                                })
                        except Exception:
                            continue

            # limiter à 20
            return standings[:20]

        except requests.RequestException as e:
            logging.error(f"❌ Erreur lors du scraping du classement: {e}")
            return []
        except Exception as e:
            logging.error(f"❌ Erreur générale lors du scraping du classement: {e}")
            return []

    def display_league_standings(self, league_id: int, league_name: str):
        """Affiche le classement d'une ligue et retourne les données"""
        logging.info(f"\n📊 CLASSEMENT - {league_name}")
        standings = self.scrape_league_standings(league_id)

        if not standings:
            # fallback pour Brazilian Serie A (votre cas)
            if league_id == 71:
                return [
                    {"position": "1", "team": "Botafogo", "gp": "33", "w": "24", "d": "6", "l": "3", "f": "64", "a": "29", "gd": "+35", "p": "78"},
                    {"position": "2", "team": "Palmeiras", "gp": "33", "w": "22", "d": "8", "l": "3", "f": "60", "a": "26", "gd": "+34", "p": "74"},
                    {"position": "3", "team": "Cruzeiro", "gp": "33", "w": "20", "d": "8", "l": "5", "f": "53", "a": "32", "gd": "+21", "p": "68"},
                    {"position": "4", "team": "Flamengo", "gp": "33", "w": "19", "d": "7", "l": "7", "f": "55", "a": "35", "gd": "+20", "p": "64"},
                    {"position": "5", "team": "Fortaleza", "gp": "33", "w": "18", "d": "8", "l": "7", "f": "50", "a": "39", "gd": "+11", "p": "62"},
                    {"position": "6", "team": "Internacional", "gp": "33", "w": "17", "d": "10", "l": "6", "f": "50", "a": "35", "gd": "+15", "p": "61"},
                    {"position": "7", "team": "Bahia", "gp": "33", "w": "16", "d": "9", "l": "8", "f": "46", "a": "35", "gd": "+11", "p": "57"},
                    {"position": "8", "team": "São Paulo", "gp": "33", "w": "14", "d": "11", "l": "8", "f": "52", "a": "44", "gd": "+8", "p": "53"},
                    {"position": "9", "team": "Vasco da Gama", "gp": "33", "w": "14", "d": "8", "l": "11", "f": "46", "a": "45", "gd": "+1", "p": "50"},
                    {"position": "10", "team": "Red Bull Bragantino", "gp": "33", "w": "13", "d": "10", "l": "10", "f": "50", "a": "49", "gd": "+1", "p": "49"}
                ]
            logging.warning("❌ Impossible de récupérer le classement")
            return []

        # affichage console minimal
        logging.info(f"{'Pos':<4} {'Équipe':<25} {'J':<3} {'V':<3} {'N':<3} {'D':<3} {'BP':<4} {'BC':<4} {'DB':<6} {'Pts':<4}")
        for team_data in standings:
            logging.info(f"{team_data['position']:<4} {team_data['team'][:24]:<25} "
                         f"{team_data.get('gp',''):<3} {team_data.get('w',''):<3} {team_data.get('d',''):<3} {team_data.get('l',''):<3} "
                         f"{team_data.get('f',''):<4} {team_data.get('a',''):<4} {team_data.get('gd',''):<6} {team_data.get('p',''):<4}")

        return standings

    # ------------------------- Recherche URL équipe -------------------------
    def find_team_url(self, team_name: str) -> Optional[str]:
        """Trouve l'URL ESPN d'une équipe basée sur son nom avec correspondances améliorées"""
        if not team_name:
            return None
        team_name_normalized = team_name.lower().strip()

        name_variations = {
            'psg': 'paris saint-germain',
            'man city': 'manchester city',
            'man utd': 'manchester united',
            'tottenham': 'tottenham hotspur',
            'brighton': 'brighton & hove albion',
            'wolves': 'wolverhampton wanderers',
            'west ham': 'west ham united',
            'newcastle': 'newcastle united',
            'nottm forest': 'nottingham forest',
            'leicester': 'leicester city',
            'rb bragantino': 'red bull bragantino',
            'bragantino': 'red bull bragantino',
            'ceara': 'ceará',
            'sao paulo': 'são paulo',
            'gremio': 'grêmio',
            'atletico mg': 'atlético-mg',
            'sport recife': 'sport',
            'vasco': 'vasco da gama',
            'argentinos jrs': 'argentinos juniors',
            "newells old boys": "newell's old boys",
            "talleres cordoba": "talleres",
            "river plate": "river plate",
            "boca juniors": "boca juniors"
        }

        search_name = name_variations.get(team_name_normalized, team_name_normalized)

        # Recherche exacte prioritaire
        for league_name, teams in self.teams_data.items():
            for team_data in teams:
                team_db_name = team_data["team"].lower().strip()
                if search_name == team_db_name:
                    return team_data["results_url"]

        # Recherche partielle plus permissive
        for league_name, teams in self.teams_data.items():
            for team_data in teams:
                team_db_name = team_data["team"].lower().strip()
                # correspondance stricte inclusion
                if search_name in team_db_name or team_db_name in search_name:
                    return team_data["results_url"]

        # tentative de construction d'URL ESPN standard si on a un id connu dans API (plus tard)
        # sinon, retourner None
        return None

    # ------------------------- Parsing score -------------------------
    def parse_score(self, score_str: str) -> tuple:
        """Parse le score pour extraire les buts pour et contre"""
        try:
            clean_score = (score_str or "").strip()
            if not clean_score:
                return 0, 0
            # éliminer suffixes comme FT, ET, Pens
            if "FT-Pens" in clean_score or "Penalty" in clean_score:
                if " · " in clean_score:
                    main_score = clean_score.split(" · ")[0]
                else:
                    main_score = clean_score.split()[0]
            else:
                main_score = clean_score
            score_pattern = re.search(r'(\d+)\s*[-–]\s*(\d+)', main_score)
            if score_pattern:
                return int(score_pattern.group(1)), int(score_pattern.group(2))
            # parfois format "W (3-1)" ou "3-1 (a.p.)"
            score_pattern2 = re.search(r'(\d+)\s*[:]\s*(\d+)', main_score)
            if score_pattern2:
                return int(score_pattern2.group(1)), int(score_pattern2.group(2))
            return 0, 0
        except Exception:
            return 0, 0

    # ------------------------- Scraping résultats équipe -------------------------
    def scrape_team_recent_matches(self, team_url: str, team_name: str, max_matches: int = 15) -> List[Dict]:
        """Récupère les derniers matchs d'une équipe depuis ESPN (fallbacks inclus)"""
        tried_urls = []
        results = []

        # essayer la url fournie puis une variante avec 'www.espn.com' si nécessaire
        urls_to_try = [team_url]
        if team_url and "africa.espn.com" in team_url:
            urls_to_try.append(team_url.replace("africa.espn.com", "www.espn.com"))
        elif team_url and "www.espn.com" not in team_url:
            # tenter forme standard si possible
            urls_to_try.append(team_url)

        for url in urls_to_try:
            if not url:
                continue
            tried_urls.append(url)
            try:
                response = requests.get(url, headers=self.scraping_headers, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                # Rechercher la liste des résultats : plusieurs modèles possibles
                # 1) lignes li avec class 'match' ou table rows
                # Prioriser <table class="Table"> lignes
                rows = soup.find_all("tr")
                if not rows:
                    # fallback to list items
                    rows = soup.find_all(["li", "div"], class_=re.compile("match|result|score", re.I)) or []

                recent_matches = []
                for row in rows:
                    if len(recent_matches) >= max_matches:
                        break
                    try:
                        text = row.get_text(" ", strip=True)
                        if not text:
                            continue
                        # tenter extraire date, équipes et score
                        # repérer score via regex
                        score_match = re.search(r'(\d+)\s*[-–:]\s*(\d+)', text)
                        if not score_match:
                            # parfois 'W' ou 'L' instead of score - skip
                            continue

                        # essayer plus finement selon structure
                        date_elem = row.find(["div", "span"], {"data-testid": "date"}) or row.find("span", class_="date") or row.find("time")
                        local_team_elem = row.find("div", {"data-testid": "localTeam"}) or row.find("td", class_=re.compile("team home", re.I)) or row.find("span", class_=re.compile("team home", re.I))
                        away_team_elem = row.find("div", {"data-testid": "awayTeam"}) or row.find("td", class_=re.compile("team away", re.I)) or row.find("span", class_=re.compile("team away", re.I))
                        score_elem = row.find("span", {"data-testid": "score"}) or row.find("td", class_="score") or row.find("strong", class_=re.compile("score", re.I))

                        # fallback: récupérer via colonnes si table
                        if not all([date_elem, local_team_elem, away_team_elem, score_elem]):
                            tds = row.find_all("td")
                            if len(tds) >= 4:
                                date_elem = date_elem or tds[0]
                                local_team_elem = local_team_elem or tds[1]
                                score_elem = score_elem or tds[2]
                                away_team_elem = away_team_elem or tds[3]

                        # si encore manquant, extraire via texte heuristique
                        date = date_elem.get_text(strip=True) if date_elem else ""
                        local_team = local_team_elem.get_text(strip=True) if local_team_elem else ""
                        away_team = away_team_elem.get_text(strip=True) if away_team_elem else ""
                        score = score_elem.get_text(strip=True) if score_elem else ""
                        if not score:
                            # tenter depuis texte global
                            # isoler premier pattern 'x-x'
                            sm = re.search(r'(\d+)\s*[-–:]\s*(\d+)', text)
                            score = sm.group(0) if sm else ""

                        # competition heuristique
                        competition = "N/A"
                        tds = row.find_all("td")
                        for td in reversed(tds):
                            txt = td.get_text(strip=True)
                            if txt and txt not in (date, local_team, away_team, score):
                                competition = txt
                                break

                        # déterminer si l'équipe étudiée était à domicile
                        is_home = False
                        if local_team and team_name.lower() in local_team.lower():
                            is_home = True
                        elif away_team and team_name.lower() in away_team.lower():
                            is_home = False
                        else:
                            # si noms vides, tenter basé sur position dans string
                            # if team_name first occurrence before '-' => home
                            if text:
                                parts = re.split(r'(\d+\s*[-–:]\s*\d+)', text)
                                if len(parts) >= 3:
                                    left = parts[0]
                                    if team_name.lower() in left.lower():
                                        is_home = True

                        gf, ga = self.parse_score(score)
                        if not is_home:
                            # si l'équipe est away, inverser les buts
                            # mais si detection impossible, on cherche l'ordre dans text
                            # heuristique: si local_team empty but we have team_name in text after '-' => away
                            if local_team and away_team:
                                if team_name.lower() in away_team.lower():
                                    gf, ga = ga, gf
                                elif team_name.lower() in local_team.lower():
                                    pass
                                else:
                                    # indéterminé — laisser gf/ga selon ordre détecté
                                    pass
                            else:
                                # garder tel quel
                                pass

                        # résultat
                        if gf > ga:
                            result = "V"
                        elif gf == ga:
                            result = "N"
                        else:
                            result = "D"

                        match_info = {
                            "date": date,
                            "local_team": local_team or "",
                            "away_team": away_team or "",
                            "score": score or "",
                            "competition": competition,
                            "is_home": is_home,
                            "goals_for": gf,
                            "goals_against": ga,
                            "result": result
                        }

                        recent_matches.append(match_info)
                    except Exception as e:
                        logging.debug(f"⚠️ Erreur parsing ligne: {e}")
                        continue

                if recent_matches:
                    results = recent_matches[:max_matches]
                    break

            except requests.RequestException as e:
                logging.warning(f"❌ Erreur lors du scraping pour {team_name} sur {url}: {e}")
                continue
            except Exception as e:
                logging.warning(f"❌ Erreur générale pour {team_name} sur {url}: {e}")
                continue

            time_module.sleep(SLEEP_BETWEEN_REQUESTS)

        # Si aucun résultat depuis ESPN, on renvoie vide (ou éventuellement via une API)
        if not results:
            logging.info(f"⚠️ Aucun match récent trouvé via ESPN pour {team_name} (URLs testées: {tried_urls})")
        return results

    # ------------------------- Calcul stats -------------------------
    def calculate_team_stats(self, matches: List[Dict], team_name: str) -> Dict:
        """Calcule les statistiques d'une équipe basées sur ses matchs récents"""
        if not matches:
            return {
                "total_goals_for": 0,
                "total_goals_against": 0,
                "general_form": "",
                "home_form": "",
                "away_form": "",
                "avg_goals_for": 0.0,
                "avg_goals_against": 0.0,
                "total_matches": 0,
                "home_matches": 0,
                "away_matches": 0
            }

        total_goals_for = 0
        total_goals_against = 0
        general_form = []
        home_form = []
        away_form = []
        home_matches = 0
        away_matches = 0

        for match in matches:
            total_goals_for += match.get("goals_for", 0)
            total_goals_against += match.get("goals_against", 0)
            if len(general_form) < 5:
                general_form.append(match.get("result", ""))
            if match.get("is_home"):
                home_matches += 1
                if len(home_form) < 5:
                    home_form.append(match.get("result", ""))
            else:
                away_matches += 1
                if len(away_form) < 5:
                    away_form.append(match.get("result", ""))

        total_matches = len(matches)
        avg_goals_for = total_goals_for / total_matches if total_matches > 0 else 0
        avg_goals_against = total_goals_against / total_matches if total_matches > 0 else 0

        return {
            "total_goals_for": total_goals_for,
            "total_goals_against": total_goals_against,
            "general_form": "".join(general_form),
            "home_form": "".join(home_form),
            "away_form": "".join(away_form),
            "avg_goals_for": round(avg_goals_for, 2),
            "avg_goals_against": round(avg_goals_against, 2),
            "total_matches": total_matches,
            "home_matches": home_matches,
            "away_matches": away_matches
        }

    def display_team_stats(self, stats: Dict, team_name: str, is_home_team: bool = True):
        """Affiche les statistiques d'une équipe"""
        team_type = "🏠 DOMICILE" if is_home_team else "✈️ EXTÉRIEUR"
        logging.info(f"\n📊 STATISTIQUES {team_type}: {team_name}")
        logging.info("-" * 60)
        logging.info(f"📈 Nombre de buts marqués: {stats['total_goals_for']}")
        logging.info(f"📉 Nombre de buts encaissés: {stats['total_goals_against']}")
        logging.info(f"📊 Forme générale (5 derniers): {stats['general_form'] if stats['general_form'] else 'N/A'}")
        logging.info(f"🏠 Forme à domicile: {stats['home_form'] if stats['home_form'] else 'N/A'} ({stats['home_matches']} matchs)")
        logging.info(f"✈️ Forme à l'extérieur: {stats['away_form'] if stats['away_form'] else 'N/A'} ({stats['away_matches']} matchs)")
        logging.info(f"⚽ Moyenne de buts marqués: {stats['avg_goals_for']}")
        logging.info(f"🥅 Moyenne de buts encaissés: {stats['avg_goals_against']}")
        logging.info(f"📊 Total matchs analysés: {stats['total_matches']}")

    # ------------------------- Trouver position dans classement -------------------------
    def find_team_position_in_standings(self, team_name: str, standings: List[Dict]) -> str:
        """Trouve la position d'une équipe dans le classement avec une correspondance améliorée"""
        if not standings:
            return "N/A"

        team_name_normalized = (team_name or "").lower().strip()
        for team_data in standings:
            if team_name_normalized == team_data.get("team", "").lower().strip():
                return team_data.get("position", "N/A")

        for team_data in standings:
            standing_team_name = team_data.get("team", "").lower().strip()
            if team_name_normalized in standing_team_name or standing_team_name in team_name_normalized:
                if len(team_name_normalized) > 4 or len(standing_team_name) > 4:
                    return team_data.get("position", "N/A")
            team_words = set(team_name_normalized.split())
            standing_words = set(standing_team_name.split())
            common_words = team_words & standing_words
            if len(common_words) >= 1 and len(common_words) >= min(len(team_words), len(standing_words)) * 0.5:
                return team_data.get("position", "N/A")
        return "N/A"

    # ------------------------- Génération analyse IA -------------------------
    def generate_ai_analysis(self, match_data: Dict, home_stats: Dict, away_stats: Dict, standings: List[Dict], logos: Dict) -> str:
        """Génère une analyse IA du match basée sur les données collectées"""
        home_team = match_data["teams"]["home"]["name"]
        away_team = match_data["teams"]["away"]["name"]
        league = match_data["league"]["name"]

        home_position = self.find_team_position_in_standings(home_team, standings)
        away_position = self.find_team_position_in_standings(away_team, standings)

        standings_info = "\n".join([
            f"{team.get('position','')}. {team.get('team','')} - {team.get('p','')} pts (V:{team.get('w','')} N:{team.get('d','')} D:{team.get('l','')} BP:{team.get('f','')} BC:{team.get('a','')})"
            for team in (standings or [])[:10]
        ]) if standings else "Classement non disponible"

        home_logo = logos.get("home")
        away_logo = logos.get("away")

        prompt = f"""
Analyse ce match de football en tant qu'expert et donne tes prédictions détaillées:

MATCH: {home_team} (domicile) vs {away_team} (extérieur)
COMPÉTITION: {league}

LOGOS:
- {home_team}: {home_logo if home_logo else 'N/A'}
- {away_team}: {away_logo if away_logo else 'N/A'}

POSITIONS AU CLASSEMENT:
- {home_team}: {home_position}e position
- {away_team}: {away_position}e position

TOP 10 DU CLASSEMENT ACTUEL:
{standings_info}

STATISTIQUES {home_team} (DOMICILE):
- Forme générale: {home_stats.get('general_form', 'N/A')} (V=Victoire, N=Nul, D=Défaite)
- Forme à domicile: {home_stats.get('home_form', 'N/A')} ({home_stats.get('home_matches', 0)} matchs)
- Moyenne buts marqués: {home_stats.get('avg_goals_for', 0)} par match
- Moyenne buts encaissés: {home_stats.get('avg_goals_against', 0)} par match
- Total matchs analysés: {home_stats.get('total_matches', 0)}

STATISTIQUES {away_team} (EXTÉRIEUR):
- Forme générale: {away_stats.get('general_form', 'N/A')} (V=Victoire, N=Nul, D=Défaite)
- Forme à l'extérieur: {away_stats.get('away_form', 'N/A')} ({away_stats.get('away_matches', 0)} matchs)
- Moyenne buts marqués: {away_stats.get('avg_goals_for', 0)} par match
- Moyenne buts encaissés: {away_stats.get('avg_goals_against', 0)} par match
- Total matchs analysés: {away_stats.get('total_matches', 0)}

ANALYSE DEMANDÉE (sois précis et structure ton analyse):
1. ANALYSE DES POSITIONS AU CLASSEMENT
2. ANALYSE DE LA FORME
3. FACTEURS CLÉS DU MATCH
4. PRÉDICTIONS AVEC POURCENTAGES (1X2, buts, BTTS, score exact)
5. NIVEAU DE CONFIANCE (1-10)

IMPORTANT: Tu DOIS compléter TOUTES les sections avec des pourcentages précis basés sur l'analyse des données fournies.
"""
        messages = [
            {"role": "system", "content": "Tu es un expert en analyse de matchs de football. Tu analyses les données statistiques et les positions au classement pour faire des prédictions précises et justifiées. Tu utilises toujours les données fournies dans ton analyse."},
            {"role": "user", "content": prompt}
        ]

        return self.ask_groq(messages)

    # ------------------------- Analyse principale -------------------------
    def analyze_matches(self):
        """Fonction principale pour analyser les matchs du jour avec IA"""
        logging.info("🔥 ANALYSE INTELLIGENTE DES MATCHS DU JOUR 🔥")

        today_matches = self.get_today_matches()
        if not today_matches:
            logging.info("Aucun match à analyser aujourd'hui.")
            return

        aggregated_output = {
            "date": datetime.date.today().isoformat(),
            "generated_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
            "matches": []
        }

        for i, match in enumerate(today_matches, 1):
            logging.info("\n" + "=" * 80)
            logging.info(f"MATCH {i}")
            logging.info("=" * 80)

            league_id = match["league"]["id"]
            league = self.authorized_leagues.get(league_id, match["league"]["name"])
            country = match["league"].get("country", "N/A")
            home_team = match["teams"]["home"]["name"]
            away_team = match["teams"]["away"]["name"]
            status = match["fixture"]["status"]["short"]
            match_time = match["fixture"]["date"][11:16] if match["fixture"].get("date") else ""

            logging.info(f"🌍 {country} | 🏆 {league}")
            logging.info(f"⚔️  {home_team} vs {away_team}")
            logging.info(f"🕓 Heure (UTC): {match_time}")
            logging.info(f"📊 Statut: {status}")

            logos = {"home": None, "away": None}
            try:
                logos["home"] = match["teams"]["home"].get("logo")
                logos["away"] = match["teams"]["away"].get("logo")
            except Exception:
                pass

            home_stats = {}
            away_stats = {}
            standings = []
            home_matches_list = []
            away_matches_list = []

            # Équipe domicile
            logging.info(f"\n🏠 ÉQUIPE DOMICILE: {home_team}")
            home_url = self.find_team_url(home_team)
            if home_url:
                logging.info(f"✅ URL trouvée: {home_url}")
                home_matches_list = self.scrape_team_recent_matches(home_url, home_team, max_matches=15)
                if home_matches_list:
                    home_stats = self.calculate_team_stats(home_matches_list, home_team)
                    self.display_team_stats(home_stats, home_team, is_home_team=True)
                else:
                    logging.warning(f"❌ Impossible de récupérer les matchs récents de {home_team}")
            else:
                logging.warning(f"❌ URL non trouvée pour {home_team}")

            # Équipe extérieure
            logging.info(f"\n✈️  ÉQUIPE EXTÉRIEURE: {away_team}")
            away_url = self.find_team_url(away_team)
            if away_url:
                logging.info(f"✅ URL trouvée: {away_url}")
                away_matches_list = self.scrape_team_recent_matches(away_url, away_team, max_matches=15)
                if away_matches_list:
                    away_stats = self.calculate_team_stats(away_matches_list, away_team)
                    self.display_team_stats(away_stats, away_team, is_home_team=False)
                else:
                    logging.warning(f"❌ Impossible de récupérer les matchs récents de {away_team}")
            else:
                logging.warning(f"❌ URL non trouvée pour {away_team}")

            # Classement
            standings = self.display_league_standings(league_id, league)

            # Analyse IA
            logging.info(f"\n🤖 ANALYSE IA DU MATCH")
            logging.info("=" * 80)

            sufficient_data = (home_stats and home_stats.get("total_matches", 0) > 0) and (away_stats and away_stats.get("total_matches", 0) > 0)
            ai_analysis = None
            if sufficient_data:
                logging.info("🔄 Génération de l'analyse IA en cours...")
                ai_analysis = self.generate_ai_analysis(match, home_stats, away_stats, standings, logos)
                if ai_analysis:
                    logging.info("\n🎯 PRÉDICTION IA:")
                    logging.info("-" * 60)
                    logging.info(ai_analysis)
                else:
                    logging.warning("❌ Impossible de générer l'analyse IA")
            else:
                logging.warning("⚠️ Données insuffisantes pour l'analyse IA (besoin d'au moins 1 match analysé par équipe).")

            match_output = {
                "fixture": {
                    "fixture_id": match["fixture"]["id"],
                    "date": match["fixture"].get("date"),
                    "time_utc": match_time,
                    "league": {
                        "id": league_id,
                        "name": league,
                        "country": country
                    },
                    "teams": {
                        "home": {
                            "name": home_team,
                            "id": match["teams"]["home"].get("id"),
                            "logo": logos.get("home")
                        },
                        "away": {
                            "name": away_team,
                            "id": match["teams"]["away"].get("id"),
                            "logo": logos.get("away")
                        }
                    },
                    "status": status
                },
                "standings": standings,
                "home_team_stats": home_stats,
                "away_team_stats": away_stats,
                "home_recent_matches": home_matches_list,
                "away_recent_matches": away_matches_list,
                "ai_analysis_text": ai_analysis,
            }

            aggregated_output["matches"].append(match_output)

            # Pause entre les requêtes pour éviter d'être bloqué
            time_module.sleep(SLEEP_BETWEEN_REQUESTS)

        # --- Sauvegarde finale : écrire UN fichier JSON à la racine nommé analyse-YYYY-MM-DD.json ---
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        root_filename = f"analyse-{date_str}.json"
        history_filename = None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(prefix="analyse_", suffix=".json", dir=".")
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_file:
                    json.dump(aggregated_output, tmp_file, ensure_ascii=False, indent=2)
                if os.path.exists(root_filename):
                    os.remove(root_filename)
                os.replace(tmp_path, root_filename)
            except Exception as e:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                raise e
            logging.info(f"💾 Analyse journalière sauvegardée dans {root_filename}")
        except Exception as e:
            logging.error(f"❌ Erreur lors de la sauvegarde du fichier racine JSON: {e}")
            try:
                fallback_name = os.path.join(self.output_dir, f"analysis_fallback_{date_str}.json")
                with open(fallback_name, "w", encoding="utf-8") as f:
                    json.dump(aggregated_output, f, ensure_ascii=False, indent=2)
                logging.info(f"💾 Sauvegarde fallback effectuée: {fallback_name}")
            except Exception as e2:
                logging.error(f"❌ Erreur lors de la sauvegarde fallback: {e2}")

        # Sauvegarder aussi dans le répertoire analyses avec timestamp (historique)
        try:
            timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            history_filename = os.path.join(self.output_dir, f"analysis_{timestamp}.json")
            with open(history_filename, "w", encoding="utf-8") as f:
                json.dump(aggregated_output, f, ensure_ascii=False, indent=2)
            logging.info(f"💾 Historique sauvegardé dans {history_filename}")
        except Exception as e:
            logging.warning(f"⚠️ Impossible de sauvegarder l'historique: {e}")

        # Commit & push du fichier racine (et de l'historique si nécessaire)
        try:
            files_to_commit = []
            if os.path.exists(root_filename):
                files_to_commit.append(root_filename)
            if history_filename and os.path.exists(history_filename):
                files_to_commit.append(history_filename)
            if files_to_commit:
                commit_msg = f"Add daily analysis {date_str}"
                push_ok = self._git_commit_and_push(files_to_commit, commit_msg)
                if not push_ok:
                    logging.warning("⚠️ Echec du push git. Analyses sauvegardées localement.")
        except Exception as e:
            logging.warning(f"⚠️ Erreur lors du commit/push automatique: {e}")

        logging.info("\n" + "=" * 80)
        logging.info("🎯 ANALYSE INTELLIGENTE TERMINÉE")
        logging.info("=" * 80)

def main():
    """Fonction principale"""
    try:
        logging.info("🤖 Démarrage de l'analyseur de football avec IA...")
        logging.info(f"✅ Connecté à GroqCloud - Modèle : {FootballMatchAnalyzerWithAI().groq_model} (via variable GRQ_KEY)")
        logging.info("-" * 60)

        analyzer = FootballMatchAnalyzerWithAI()
        analyzer.analyze_matches()
    except KeyboardInterrupt:
        logging.info("\n🛑 Programme interrompu par l'utilisateur")
    except Exception as e:
        logging.error(f"❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    main()