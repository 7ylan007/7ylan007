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

# --- Configuration via variables d'environnement (GitHub secrets) ---
FOOTBALL_KEY = os.environ.get("FOOTBALL_KEY")
GRQ_KEY = os.environ.get("GRQ_KEY")
# Optionnel: remote name (default: origin)
GIT_REMOTE = os.environ.get("GIT_REMOTE", "origin")
# Optional git author override
GIT_AUTHOR_NAME = os.environ.get("GIT_AUTHOR_NAME")
GIT_AUTHOR_EMAIL = os.environ.get("GIT_AUTHOR_EMAIL")

if not FOOTBALL_KEY:
    print("❌ Erreur: la variable d'environnement FOOTBALL_KEY n'est pas définie.")
    sys.exit(1)
if not GRQ_KEY:
    print("❌ Erreur: la variable d'environnement GRQ_KEY n'est pas définie.")
    sys.exit(1)

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
            2: "https://africa.espn.com/football/standings/_/league/UEFA.CHAMPIONS",
            253: "https://africa.espn.com/football/standings/_/league/USA.1",
            3: "https://africa.espn.com/football/standings/_/league/UEFA.EUROPA",
            88: "https://africa.espn.com/football/standings/_/league/NED.1",
            94: "https://africa.espn.com/football/standings/_/league/POR.1",
            143: "https://africa.espn.com/football/standings/_/league/ESP.COPA_DEL_REY",
            81: "https://africa.espn.com/football/standings/_/league/GER.DFB_POKAL",
            66: "https://africa.espn.com/football/standings/_/league/FRA.COUPE_DE_FRANCE",
            307: "https://africa.espn.com/football/standings/_/league/KSA.1",
            144: "https://africa.espn.com/football/standings/_/league/BEL.1",
            235: "https://africa.espn.com/football/standings/_/league/RUS.1",
            141: "https://africa.espn.com/football/standings/_/league/ESP.2",
            203: "https://africa.espn.com/football/standings/_/league/TUR.1",
            62: "https://africa.espn.com/football/standings/_/league/FRA.2",
            128: "https://africa.espn.com/football/standings/_/league/ARG.1",
            239: "https://africa.espn.com/football/standings/_/league/COL.1",
            71: "https://africa.espn.com/football/standings/_/league/BRA.1",
            61: "https://africa.espn.com/football/standings/_/league/FRA.1",
            78: "https://africa.espn.com/football/standings/_/league/GER.1",
            135: "https://africa.espn.com/football/standings/_/league/ITA.1",
            40: "https://africa.espn.com/football/standings/_/league/ENG.2",
            140: "https://africa.espn.com/football/standings/_/league/ESP.1"
        }
        
        # Charger les données des équipes (base minimaliste fournie précédemment)
        self.teams_data = self._load_teams_data()
        
        # Répertoire pour sauvegarder les analyses JSON (reste, mais on espace aussi le fichier racine)
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
                print("ℹ️ Aucun changement à committer pour les fichiers fournis.")
            
            # Push
            subprocess.run(["git", "push", GIT_REMOTE, "HEAD"], check=True)
            
            print("✅ Commit et push effectués.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur git: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur inattendue lors du git commit/push: {e}")
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
                print(f"❌ Erreur IA {response.status_code}: {response.text}")
                return None

            # Adapter selon la structure renvoyée
            j = response.json()
            # Structure attendue: {"choices":[{"message":{"content":"..."}}], ...}
            content = None
            try:
                content = j["choices"][0]["message"]["content"]
            except Exception:
                # Tenter d'autres structures
                if "choices" in j and isinstance(j["choices"], list) and len(j["choices"]) > 0:
                    choice = j["choices"][0]
                    if "text" in choice:
                        content = choice["text"]
                    elif "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
            return content
        except Exception as e:
            print(f"❌ Erreur lors de la communication avec l'IA: {e}")
            return None
    
    # ------------------------- Chargement des équipes -------------------------
    def _load_teams_data(self) -> Dict:
        """Charge les données complètes des équipes (minimal)"""
        teams_data = {
            "Premier League (ENG.1)": [
                {"team": "AFC Bournemouth", "results_url": "https://africa.espn.com/football/team/results/_/id/349/afc-bournemouth"},
                {"team": "Arsenal", "results_url": "https://africa.espn.com/football/team/results/_/id/359/arsenal"},
                {"team": "Aston Villa", "results_url": "https://africa.espn.com/football/team/results/_/id/362/aston-villa"},
                {"team": "Brentford", "results_url": "https://africa.espn.com/football/team/results/_/id/337/brentford"},
                {"team": "Brighton & Hove Albion", "results_url": "https://africa.espn.com/football/team/results/_/id/331/brighton-hove-albion"},
                {"team": "Burnley", "results_url": "https://africa.espn.com/football/team/results/_/id/379/burnley"},
                {"team": "Chelsea", "results_url": "https://africa.espn.com/football/team/results/_/id/363/chelsea"},
                {"team": "Crystal Palace", "results_url": "https://africa.espn.com/football/team/results/_/id/384/crystal-palace"},
                {"team": "Everton", "results_url": "https://africa.espn.com/football/team/results/_/id/368/everton"},
                {"team": "Fulham", "results_url": "https://africa.espn.com/football/team/results/_/id/370/fulham"},
                {"team": "Leeds United", "results_url": "https://africa.espn.com/football/team/results/_/id/357/leeds-united"},
                {"team": "Liverpool", "results_url": "https://africa.espn.com/football/team/results/_/id/364/liverpool"},
                {"team": "Manchester City", "results_url": "https://africa.espn.com/football/team/results/_/id/382/manchester-city"},
                {"team": "Manchester United", "results_url": "https://africa.espn.com/football/team/results/_/id/360/manchester-united"},
                {"team": "Newcastle United", "results_url": "https://africa.espn.com/football/team/results/_/id/361/newcastle-united"},
                {"team": "Nottingham Forest", "results_url": "https://africa.espn.com/football/team/results/_/id/393/nottingham-forest"},
                {"team": "Sunderland", "results_url": "https://africa.espn.com/football/team/results/_/id/366/sunderland"},
                {"team": "Tottenham Hotspur", "results_url": "https://africa.espn.com/football/team/results/_/id/367/tottenham-hotspur"},
                {"team": "West Ham United", "results_url": "https://africa.espn.com/football/team/results/_/id/371/west-ham-united"},
                {"team": "Wolverhampton Wanderers", "results_url": "https://africa.espn.com/football/team/results/_/id/380/wolverhampton-wanderers"}
            ]
        }
        return teams_data
    
    # ------------------------- API Fixtures -------------------------
    def get_today_matches(self) -> List[Dict]:
        """Récupère les matchs du jour depuis l'API"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        params = {"date": today}
        
        print(f"📅 Récupération des matchs du {today}...\n")
        
        try:
            response = requests.get(self.api_base_url, headers=self.api_headers, params=params, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("response"):
                print("⚠️ Aucun match trouvé pour aujourd'hui.")
                return []
            
            matches = [
                match for match in data["response"]
                if match["league"]["id"] in self.authorized_leagues
            ]
            
            if not matches:
                print("⚠️ Aucun match trouvé dans les ligues sélectionnées.")
                return []
            
            print(f"✅ {len(matches)} matchs trouvés dans les ligues sélectionnées\n")
            return matches
            
        except requests.RequestException as e:
            print(f"❌ Erreur lors de la récupération des matchs: {e}")
            return []
    
    # ------------------------- Scraping Classements -------------------------
    def scrape_league_standings(self, league_id: int) -> List[Dict]:
        """Récupère le classement d'une ligue depuis ESPN"""
        standings_url = self.league_standings_urls.get(league_id)
        
        if not standings_url:
            print(f"❌ URL de classement non trouvée pour la ligue ID {league_id}")
            return []
        
        try:
            response = requests.get(standings_url, headers=self.scraping_headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            standings = []
            
            # Rechercher le tableau principal avec les classes appropriées
            table = soup.find("table", class_="Table")
            if not table:
                # Essayer une autre approche
                table = soup.find("div", {"class": "table-container"})
            
            if table:
                rows = table.find_all("tr")
                
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 8:
                        try:
                            position_cell = cells[0]
                            team_cell = cells[1]
                            
                            position = position_cell.get_text(strip=True)
                            if not position.isdigit():
                                continue
                            
                            team_name = team_cell.get_text(strip=True)
                            stats = [cell.get_text(strip=True) for cell in cells[-8:]]
                            if len(stats) == 8:
                                standings.append({
                                    "position": position,
                                    "team": team_name,
                                    "gp": stats[0],
                                    "w": stats[1],
                                    "d": stats[2],
                                    "l": stats[3],
                                    "f": stats[4],
                                    "a": stats[5],
                                    "gd": stats[6],
                                    "p": stats[7]
                                })
                        except Exception:
                            continue
            
            if not standings:
                all_rows = soup.find_all("tr")
                for row in all_rows:
                    rank_span = row.find("span", class_="rank")
                    if rank_span:
                        try:
                            position = rank_span.get_text(strip=True)
                            team_name = ""
                            team_span = row.find("span", class_="hide-mobile")
                            if team_span:
                                team_name = team_span.get_text(strip=True)
                            else:
                                team_links = row.find_all("a")
                                for link in team_links:
                                    if "/team/" in link.get("href", ""):
                                        team_name = link.get_text(strip=True)
                                        break
                            if team_name:
                                all_cells = row.find_all("td")
                                if len(all_cells) >= 8:
                                    stats_cells = all_cells[-8:]
                                    stats = [cell.get_text(strip=True) for cell in stats_cells]
                                    standings.append({
                                        "position": position,
                                        "team": team_name,
                                        "gp": stats[0],
                                        "w": stats[1],
                                        "d": stats[2],
                                        "l": stats[3],
                                        "f": stats[4],
                                        "a": stats[5],
                                        "gd": stats[6],
                                        "p": stats[7]
                                    })
                        except Exception:
                            continue
            
            return standings[:20]
            
        except requests.RequestException as e:
            print(f"❌ Erreur lors du scraping du classement: {e}")
            return []
        except Exception as e:
            print(f"❌ Erreur générale lors du scraping du classement: {e}")
            return []
    
    def display_league_standings(self, league_id: int, league_name: str):
        """Affiche le classement d'une ligue et retourne les données"""
        print(f"\n📊 CLASSEMENT - {league_name}")
        print("-" * 100)
        
        standings = self.scrape_league_standings(league_id)
        
        if not standings:
            if league_id == 71:  # Brazilian Serie A fallback hardcoded
                standings = [
                    {"position": "1", "team": "Botafogo", "gp": "33", "w": "24", "d": "6", "l": "3", "f": "64", "a": "29", "gd": "+35", "p": "78"},
                    {"position": "2", "team": "Palmeiras", "gp": "33", "w": "22", "d": "8", "l": "3", "f": "60", "a": "26", "gd": "+34", "p": "74"},
                    {"position": "3", "team": "Cruzeiro", "gp": "33", "w": "20", "d": "8", "l": "5", "f": "53", "a": "32", "gd": "+21", "p": "68"},
                    {"position": "4", "team": "Flamengo", "gp": "33", "w": "19", "d": "7", "l": "7", "f": "55", "a": "35", "gd": "+20", "p": "64"},
                    {"position": "5", "team": "Fortaleza", "gp": "33", "w": "18", "d": "8", "l": "7", "f": "50", "a": "39", "gd": "+11", "p": "62"},
                    {"position": "6", "team": "Internacional", "gp": "33", "w": "17", "d": "10", "l": "6", "f": "50", "a": "35", "gd": "+15", "p": "61"},
                    {"position": "7", "team": "Bahia", "gp": "33", "w": "16", "d": "9", "l": "8", "f": "46", "a": "35", "gd": "+11", "p": "57"},
                    {"position": "8", "team": "São Paulo", "gp": "33", "w": "14", "d": "11", "l": "8", "f": "52", "a": "44", "gd": "+8", "p": "53"},
                    {"position": "9", "team": "Vasco da Gama", "gp": "33", "w": "14", "d": "8", "l": "11", "f": "46", "a": "45", "gd": "+1", "p": "50"},
                    {"position": "10", "team": "Red Bull Bragantino", "gp": "33", "w": "13", "d": "10", "l": "10", "f": "50", "a": "49", "gd": "+1", "p": "49"},
                    {"position": "11", "team": "Athletico Paranaense", "gp": "33", "w": "12", "d": "11", "l": "10", "f": "42", "a": "43", "gd": "-1", "p": "47"},
                    {"position": "12", "team": "Corinthians", "gp": "33", "w": "11", "d": "8", "l": "14", "f": "41", "a": "45", "gd": "-4", "p": "41"},
                    {"position": "13", "team": "Grêmio", "gp": "33", "w": "10", "d": "10", "l": "13", "f": "38", "a": "42", "gd": "-4", "p": "40"},
                    {"position": "14", "team": "Atlético-MG", "gp": "33", "w": "10", "d": "9", "l": "14", "f": "42", "a": "50", "gd": "-8", "p": "39"},
                    {"position": "15", "team": "Juventude", "gp": "33", "w": "10", "d": "8", "l": "15", "f": "35", "a": "44", "gd": "-9", "p": "38"},
                    {"position": "16", "team": "Santos", "gp": "33", "w": "9", "d": "8", "l": "16", "f": "35", "a": "48", "gd": "-13", "p": "35"},
                    {"position": "17", "team": "Vitória", "gp": "33", "w": "9", "d": "7", "l": "17", "f": "36", "a": "55", "gd": "-19", "p": "34"},
                    {"position": "18", "team": "Sport", "gp": "33", "w": "8", "d": "8", "l": "17", "f": "35", "a": "50", "gd": "-15", "p": "32"},
                    {"position": "19", "team": "CRB", "gp": "33", "w": "6", "d": "8", "l": "19", "f": "33", "a": "57", "gd": "-24", "p": "26"},
                    {"position": "20", "team": "Ceará", "gp": "33", "w": "4", "d": "7", "l": "22", "f": "27", "a": "63", "gd": "-36", "p": "19"}
                ]
            else:
                print("❌ Impossible de récupérer le classement")
                return []
        
        # Affichage console minimal
        print(f"{'Pos':<4} {'Équipe':<25} {'J':<3} {'V':<3} {'N':<3} {'D':<3} {'BP':<4} {'BC':<4} {'DB':<6} {'Pts':<4}")
        print("-" * 100)
        for team_data in standings:
            print(f"{team_data['position']:<4} {team_data['team'][:24]:<25} "
                  f"{team_data['gp']:<3} {team_data['w']:<3} {team_data['d']:<3} {team_data['l']:<3} "
                  f"{team_data['f']:<4} {team_data['a']:<4} {team_data['gd']:<6} {team_data['p']:<4}")
        
        return standings
    
    # ------------------------- Recherche URL équipe -------------------------
    def find_team_url(self, team_name: str) -> Optional[str]:
        """Trouve l'URL ESPN d'une équipe basée sur son nom avec correspondances améliorées"""
        team_name_normalized = team_name.lower().strip()
        
        name_variations = {
            # Plusieurs variations utiles (abrégés)
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
            # Brésil et autres exemples
            'rb bragantino': 'red bull bragantino',
            'bragantino': 'red bull bragantino',
            'ceara': 'ceará',
            'sao paulo': 'são paulo',
            'gremio': 'grêmio',
            'atletico mg': 'atlético-mg',
            'sport recife': 'sport',
            'vasco': 'vasco da gama'
        }
        
        search_name = name_variations.get(team_name_normalized, team_name_normalized)
        
        # Recherche exacte prioritaire
        for league_name, teams in self.teams_data.items():
            for team_data in teams:
                team_db_name = team_data["team"].lower().strip()
                if search_name == team_db_name:
                    return team_data["results_url"]
        
        # Recherche partielle plus restrictive
        for league_name, teams in self.teams_data.items():
            for team_data in teams:
                team_db_name = team_data["team"].lower().strip()
                if len(search_name) > 5 and search_name in team_db_name:
                    if 'atletico' in search_name:
                        if 'madrid' in search_name and 'madrid' in team_db_name:
                            return team_data["results_url"]
                        elif 'nacional' in search_name and 'nacional' in team_db_name:
                            return team_data["results_url"]
                        elif 'mg' in search_name and 'mg' in team_db_name:
                            return team_data["results_url"]
                        continue
                    else:
                        return team_data["results_url"]
                
                search_words = search_name.split()
                team_words = team_db_name.split()
                if len(search_words) >= 2:
                    common_words = set(search_words) & set(team_words)
                    if len(common_words) >= 2:
                        return team_data["results_url"]
        
        return None
    
    # ------------------------- Parsing score -------------------------
    def parse_score(self, score_str: str) -> tuple:
        """Parse le score pour extraire les buts pour et contre"""
        try:
            clean_score = score_str.strip()
            if "FT-Pens" in clean_score or "Penalty" in clean_score:
                if " · " in clean_score:
                    main_score = clean_score.split(" · ")[0]
                else:
                    main_score = clean_score.split()[0]
            else:
                main_score = clean_score
            score_pattern = re.search(r'(\d+)\s*-\s*(\d+)', main_score)
            if score_pattern:
                return int(score_pattern.group(1)), int(score_pattern.group(2))
            return 0, 0
        except Exception:
            return 0, 0
    
    # ------------------------- Scraping résultats équipe -------------------------
    def scrape_team_recent_matches(self, team_url: str, team_name: str, max_matches: int = 15) -> List[Dict]:
        """Récupère les derniers matchs d'une équipe depuis ESPN"""
        try:
            response = requests.get(team_url, headers=self.scraping_headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            # Rechercher lignes de la table des résultats - plusieurs classes possibles
            rows = soup.find_all("tr", class_="Table__TR--sm")
            if not rows:
                # fallback : toutes les lignes de tableau
                rows = soup.find_all("tr")
            
            recent_matches = []
            for row in rows[:max_matches]:
                try:
                    date_elem = row.find("div", {"data-testid": "date"}) or row.find("span", class_="date")
                    local_team_elem = row.find("div", {"data-testid": "localTeam"}) or row.find("td", class_="team home")
                    away_team_elem = row.find("div", {"data-testid": "awayTeam"}) or row.find("td", class_="team away")
                    score_elem = row.find("span", {"data-testid": "score"}) or row.find("td", class_="score")
                    
                    if not all([date_elem, local_team_elem, away_team_elem, score_elem]):
                        # essayer d'extraire via colonnes
                        tds = row.find_all("td")
                        if len(tds) >= 4:
                            date_elem = tds[0]
                            local_team_elem = tds[1]
                            score_elem = tds[2]
                            away_team_elem = tds[3]
                        else:
                            continue
                    
                    date = date_elem.get_text(strip=True)
                    local_team = local_team_elem.get_text(strip=True)
                    away_team = away_team_elem.get_text(strip=True)
                    score = score_elem.get_text(strip=True)
                    
                    # Chercher la compétition
                    tds = row.find_all("td")
                    competition = "N/A"
                    for td in reversed(tds):
                        txt = td.get_text(strip=True)
                        if txt and not any(k in txt for k in [local_team, away_team, score, date]):
                            competition = txt
                            break
                    
                    is_home = local_team.lower() == team_name.lower()
                    goals_for, goals_against = self.parse_score(score)
                    if not is_home:
                        goals_for, goals_against = goals_against, goals_for
                    
                    if goals_for > goals_against:
                        result = "V"
                    elif goals_for == goals_against:
                        result = "N"
                    else:
                        result = "D"
                    
                    match_info = {
                        "date": date,
                        "local_team": local_team,
                        "away_team": away_team,
                        "score": score,
                        "competition": competition,
                        "is_home": is_home,
                        "goals_for": goals_for,
                        "goals_against": goals_against,
                        "result": result
                    }
                    recent_matches.append(match_info)
                except Exception as e:
                    print(f"⚠️ Erreur lors du parsing d'un match pour {team_name}: {e}")
                    continue
            
            return recent_matches
            
        except requests.RequestException as e:
            print(f"❌ Erreur lors du scraping pour {team_name}: {e}")
            return []
        except Exception as e:
            print(f"❌ Erreur générale pour {team_name}: {e}")
            return []
    
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
            total_goals_for += match["goals_for"]
            total_goals_against += match["goals_against"]
            if len(general_form) < 5:
                general_form.append(match["result"])
            if match["is_home"]:
                home_matches += 1
                if len(home_form) < 5:
                    home_form.append(match["result"])
            else:
                away_matches += 1
                if len(away_form) < 5:
                    away_form.append(match["result"])
        
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
        print(f"\n📊 STATISTIQUES {team_type}: {team_name}")
        print("-" * 60)
        print(f"📈 Nombre de buts marqués: {stats['total_goals_for']}")
        print(f"📉 Nombre de buts encaissés: {stats['total_goals_against']}")
        print(f"📊 Forme générale (5 derniers): {stats['general_form'] if stats['general_form'] else 'N/A'}")
        print(f"🏠 Forme à domicile: {stats['home_form'] if stats['home_form'] else 'N/A'} ({stats['home_matches']} matchs)")
        print(f"✈️ Forme à l'extérieur: {stats['away_form'] if stats['away_form'] else 'N/A'} ({stats['away_matches']} matchs)")
        print(f"⚽ Moyenne de buts marqués: {stats['avg_goals_for']}")
        print(f"🥅 Moyenne de buts encaissés: {stats['avg_goals_against']}")
        print(f"📊 Total matchs analysés: {stats['total_matches']}")
    
    # ------------------------- Trouver position dans classement -------------------------
    def find_team_position_in_standings(self, team_name: str, standings: List[Dict]) -> str:
        """Trouve la position d'une équipe dans le classement avec une correspondance améliorée"""
        if not standings:
            return "N/A"
        
        team_name_normalized = team_name.lower().strip()
        
        for team_data in standings:
            if team_name_normalized == team_data["team"].lower().strip():
                return team_data["position"]
        
        for team_data in standings:
            standing_team_name = team_data["team"].lower().strip()
            if team_name_normalized in standing_team_name or standing_team_name in team_name_normalized:
                if len(team_name_normalized) > 4 or len(standing_team_name) > 4:
                    return team_data["position"]
            team_words = set(team_name_normalized.split())
            standing_words = set(standing_team_name.split())
            common_words = team_words & standing_words
            if len(common_words) >= 1 and len(common_words) >= min(len(team_words), len(standing_words)) * 0.5:
                return team_data["position"]
        
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
            f"{team['position']}. {team['team']} - {team['p']} pts (V:{team['w']} N:{team['d']} D:{team['l']} BP:{team['f']} BC:{team['a']})"
            for team in (standings or [])[:10]
        ]) if standings else "Classement non disponible"
        
        # Logos (URLs) fournis si disponibles
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
   - Impact des positions respectives sur les enjeux du match
   - Motivation et pression sur chaque équipe

2. ANALYSE DE LA FORME
   - Forme récente de chaque équipe (générale et spécifique domicile/extérieur)
   - Tendances offensives et défensives

3. FACTEURS CLÉS DU MATCH
   - Avantage du terrain pour {home_team}
   - Forces et faiblesses de chaque équipe
   - Éléments tactiques importants

4. PRÉDICTIONS AVEC POURCENTAGES

   a) RÉSULTAT DU MATCH (1X2):
      - Victoire {home_team}: X%
      - Match Nul: X%
      - Victoire {away_team}: X%

   b) TOTAL DE BUTS:
      - Plus de 2.5 buts: X%
      - Moins de 2.5 buts: X%
      - Plus de 3.5 buts: X%
      - Moins de 3.5 buts: X%

   c) LES DEUX ÉQUIPES MARQUENT (BTTS):
      - Oui (Both Teams To Score): X%
      - Non: X%

   d) SCORE EXACT LE PLUS PROBABLE:
      - Score prédiction 1: X-X (X%)
      - Score prédiction 2: X-X (X%)
      - Score prédiction 3: X-X (X%)

   e) QUI MARQUE EN PREMIER:
      - {home_team}: X%
      - {away_team}: X%
      - Aucun but: X%

5. NIVEAU DE CONFIANCE
   - Note de 1 à 10 pour chaque prédiction principale
   - Facteurs d'incertitude éventuels

IMPORTANT: Tu DOIS compléter TOUTES les sections avec des pourcentages précis basés sur l'analyse des données fournies. Les pourcentages doivent être cohérents et basés sur les statistiques fournies. Termine TOUJOURS ton analyse complètement.
"""
        messages = [
            {"role": "system", "content": "Tu es un expert en analyse de matchs de football. Tu analyses les données statistiques et les positions au classement pour faire des prédictions précises et justifiées. Tu utilises toujours les données fournies dans ton analyse."},
            {"role": "user", "content": prompt}
        ]
        
        return self.ask_groq(messages)
    
    # ------------------------- Analyse principale -------------------------
    def analyze_matches(self):
        """Fonction principale pour analyser les matchs du jour avec IA"""
        print("🔥 ANALYSE INTELLIGENTE DES MATCHS DU JOUR 🔥")
        print("=" * 60)
        
        today_matches = self.get_today_matches()
        if not today_matches:
            return
        
        # Préparer la structure principale de sortie qui contiendra toutes les analyses du jour
        aggregated_output = {
            "date": datetime.date.today().isoformat(),
            "generated_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
            "matches": []
        }
        
        for i, match in enumerate(today_matches, 1):
            print(f"\n{'='*80}")
            print(f"MATCH {i}")
            print(f"{'='*80}")
            
            league_id = match["league"]["id"]
            league = self.authorized_leagues.get(league_id, match["league"]["name"])
            country = match["league"].get("country", "N/A")
            home_team = match["teams"]["home"]["name"]
            away_team = match["teams"]["away"]["name"]
            status = match["fixture"]["status"]["short"]
            match_time = match["fixture"]["date"][11:16]
            
            print(f"🌍 {country} | 🏆 {league}")
            print(f"⚔️  {home_team} vs {away_team}")
            print(f"🕓 Heure (UTC): {match_time}")
            print(f"📊 Statut: {status}")
            
            # Récupérer logos si fournis par l'API fixtures
            logos = {"home": None, "away": None}
            try:
                # structure possible: match["teams"]["home"]["logo"]
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
            print(f"\n🏠 ÉQUIPE DOMICILE: {home_team}")
            print("-" * 80)
            home_url = self.find_team_url(home_team)
            if home_url:
                print(f"✅ URL trouvée: {home_url}")
                home_matches_list = self.scrape_team_recent_matches(home_url, home_team, max_matches=15)
                if home_matches_list:
                    home_stats = self.calculate_team_stats(home_matches_list, home_team)
                    self.display_team_stats(home_stats, home_team, is_home_team=True)
                    print(f"\n📈 10 derniers matchs de {home_team}:")
                    for j, recent_match in enumerate(home_matches_list[:10], 1):
                        home_indicator = "🏠" if recent_match["is_home"] else "✈️"
                        result_emoji = "✅" if recent_match["result"] == "V" else "🟨" if recent_match["result"] == "N" else "❌"
                        print(f"  {j}. {recent_match['date']} {home_indicator} | {recent_match['local_team']} vs {recent_match['away_team']}")
                        print(f"     Score: {recent_match['score']} | {recent_match['competition']} {result_emoji}")
                else:
                    print(f"❌ Impossible de récupérer les matchs récents de {home_team}")
            else:
                print(f"❌ URL non trouvée pour {home_team}")
            
            # Équipe extérieure
            print(f"\n✈️  ÉQUIPE EXTÉRIEURE: {away_team}")
            print("-" * 80)
            away_url = self.find_team_url(away_team)
            if away_url:
                print(f"✅ URL trouvée: {away_url}")
                away_matches_list = self.scrape_team_recent_matches(away_url, away_team, max_matches=15)
                if away_matches_list:
                    away_stats = self.calculate_team_stats(away_matches_list, away_team)
                    self.display_team_stats(away_stats, away_team, is_home_team=False)
                    print(f"\n📈 10 derniers matchs de {away_team}:")
                    for j, recent_match in enumerate(away_matches_list[:10], 1):
                        away_indicator = "🏠" if recent_match["is_home"] else "✈️"
                        result_emoji = "✅" if recent_match["result"] == "V" else "🟨" if recent_match["result"] == "N" else "❌"
                        print(f"  {j}. {recent_match['date']} {away_indicator} | {recent_match['local_team']} vs {recent_match['away_team']}")
                        print(f"     Score: {recent_match['score']} | {recent_match['competition']} {result_emoji}")
                else:
                    print(f"❌ Impossible de récupérer les matchs récents de {away_team}")
            else:
                print(f"❌ URL non trouvée pour {away_team}")
            
            # Classement
            standings = self.display_league_standings(league_id, league)
            
            # Analyse IA
            print(f"\n🤖 ANALYSE IA DU MATCH")
            print("=" * 80)
            
            # Vérifier si on a assez de données (au moins quelques matchs pour chaque équipe)
            sufficient_data = (home_stats and home_stats.get("total_matches", 0) > 0) and (away_stats and away_stats.get("total_matches", 0) > 0)
            ai_analysis = None
            if sufficient_data:
                print("🔄 Génération de l'analyse IA en cours...")
                ai_analysis = self.generate_ai_analysis(match, home_stats, away_stats, standings, logos)
                
                if ai_analysis:
                    print(f"\n🎯 PRÉDICTION IA:")
                    print("-" * 60)
                    print(ai_analysis)
                else:
                    print("❌ Impossible de générer l'analyse IA")
            else:
                print("⚠️ Données insuffisantes pour l'analyse IA (besoin d'au moins 1 match analysé par équipe).")
            
            # Construire l'objet match pour l'agrégat
            match_output = {
                "fixture": {
                    "fixture_id": match["fixture"]["id"],
                    "date": match["fixture"]["date"],
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
            time_module.sleep(3)
        
        # --- Sauvegarde finale : écrire UN fichier JSON à la racine nommé analyse-YYYY-MM-DD.json ---
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        root_filename = f"analyse-{date_str}.json"
        try:
            # Écriture atomique dans un fichier temporaire puis renommage
            tmp_fd, tmp_path = tempfile.mkstemp(prefix="analyse_", suffix=".json", dir=".")
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_file:
                    json.dump(aggregated_output, tmp_file, ensure_ascii=False, indent=2)
                # Remplacer le fichier final
                if os.path.exists(root_filename):
                    os.remove(root_filename)
                os.replace(tmp_path, root_filename)
            except Exception as e:
                # Nettoyage si besoin
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                raise e
            print(f"💾 Analyse journalière sauvegardée dans {root_filename}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde du fichier racine JSON: {e}")
            # Tenter sauvegarde dans le dossier analyses en fallback
            try:
                fallback_name = os.path.join(self.output_dir, f"analysis_fallback_{date_str}.json")
                with open(fallback_name, "w", encoding="utf-8") as f:
                    json.dump(aggregated_output, f, ensure_ascii=False, indent=2)
                print(f"💾 Sauvegarde fallback effectuée: {fallback_name}")
            except Exception as e2:
                print(f"❌ Erreur lors de la sauvegarde fallback: {e2}")
        
        # Sauvegarder aussi dans le répertoire analyses avec timestamp (historique)
        try:
            timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            history_filename = os.path.join(self.output_dir, f"analysis_{timestamp}.json")
            with open(history_filename, "w", encoding="utf-8") as f:
                json.dump(aggregated_output, f, ensure_ascii=False, indent=2)
            print(f"💾 Historique sauvegardé dans {history_filename}")
        except Exception as e:
            print(f"⚠️ Impossible de sauvegarder l'historique: {e}")
        
        # Commit & push du fichier racine (et de l'historique si nécessaire)
        try:
            files_to_commit = []
            if os.path.exists(root_filename):
                files_to_commit.append(root_filename)
            if os.path.exists(history_filename):
                files_to_commit.append(history_filename)
            if files_to_commit:
                commit_msg = f"Add daily analysis {date_str}"
                push_ok = self._git_commit_and_push(files_to_commit, commit_msg)
                if not push_ok:
                    print("⚠️ Echec du push git. Analyses sauvegardées localement.")
        except Exception as e:
            print(f"⚠️ Erreur lors du commit/push automatique: {e}")
        
        print(f"\n{'='*80}")
        print("🎯 ANALYSE INTELLIGENTE TERMINÉE")
        print(f"{'='*80}")

def main():
    """Fonction principale"""
    try:
        print("🤖 Démarrage de l'analyseur de football avec IA...")
        print(f"✅ Connecté à GroqCloud - Modèle : openai/gpt-oss-120b (via variable GRQ_KEY)")
        print("-" * 60)
        
        analyzer = FootballMatchAnalyzerWithAI()
        analyzer.analyze_matches()
    except KeyboardInterrupt:
        print("\n🛑 Programme interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    main()