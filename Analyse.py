import os
import sys
import requests
import datetime
import json
from bs4 import BeautifulSoup
import time as time_module
from typing import Dict, List, Optional
import logging
import subprocess

# --- Configuration via variables d'environnement (facultatif) ---
GRQ_KEY = os.environ.get("GRQ_KEY")
GIT_REMOTE = os.environ.get("GIT_REMOTE", "origin")
GIT_AUTHOR_NAME = os.environ.get("GIT_AUTHOR_NAME")
GIT_AUTHOR_EMAIL = os.environ.get("GIT_AUTHOR_EMAIL")

REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "20"))
SLEEP_BETWEEN_REQUESTS = float(os.environ.get("SLEEP_BETWEEN_REQUESTS", "0.8"))

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class FootballMatchAnalyzer:
    def __init__(self):
        # Scraping headers
        self.scraping_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }

        # Liste des URLs de standings (conservées, mais NON utilisées pour scraping)
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

        # Equipes exemples (ajustez/complétez selon vos besoins)
        self.teams_data = {
            "Argentine (ARG.1)": [
                {"team": "Argentinos JRS", "results_url": "https://www.espn.com/football/team/results/_/id/458/argentinos-juniors"},
                {"team": "Newells Old Boys", "results_url": "https://www.espn.com/football/team/results/_/id/457/newells-old-boys"},
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
            "Russia (RUS.1)": [
                {"team": "FC Orenburg", "results_url": "https://www.espn.com/football/team/results/_/id/1080/fc-orenburg"},
                {"team": "Nizhny Novgorod", "results_url": "https://www.espn.com/football/team/results/_/id/2011/nizhny-novgorod"}
            ],
            "MLS (USA.1)": [
                {"team": "Atlanta United FC", "results_url": "https://www.espn.com/football/team/results/_/id/1608/atlanta-united"},
                {"team": "DC United", "results_url": "https://www.espn.com/football/team/results/_/id/1615/dc-united"}
            ]
        }

        # Output dir
        self.output_dir = "analyses"
        os.makedirs(self.output_dir, exist_ok=True)

    def _git_commit_and_push(self, file_paths: List[str], commit_message: str) -> bool:
        try:
            if GIT_AUTHOR_NAME:
                subprocess.run(["git", "config", "user.name", GIT_AUTHOR_NAME], check=True)
            if GIT_AUTHOR_EMAIL:
                subprocess.run(["git", "config", "user.email", GIT_AUTHOR_EMAIL], check=True)
            subprocess.run(["git", "add"] + file_paths, check=True)
            try:
                subprocess.run(["git", "commit", "-m", commit_message], check=True)
            except subprocess.CalledProcessError:
                logging.info("ℹ️ Aucun changement à committer.")
            subprocess.run(["git", "push", GIT_REMOTE, "HEAD"], check=True)
            logging.info("✅ Commit et push effectués.")
            return True
        except Exception as e:
            logging.warning(f"Erreur git: {e}")
            return False

    def fetch_team_results_page(self, url: str) -> Optional[str]:
        try:
            logging.info(f"Tentative de récupération de la page results: {url}")
            r = requests.get(url, headers=self.scraping_headers, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            time_module.sleep(SLEEP_BETWEEN_REQUESTS)
            return r.text
        except Exception as e:
            logging.warning(f"Erreur fetch {url}: {e}")
            return None

    def parse_espn_results(self, html: str) -> List[Dict]:
        """
        Parse un page 'team/results' ESPN et retourne la liste des matchs passés.
        Chaque match contient : date_utc, opponent, home_or_away, score_for, score_against, competition, venue, raw_summary
        """
        soup = BeautifulSoup(html, "html.parser")
        matches = []

        # ESPN uses sections with class 'Table' and 'ScoreCell' etc. Nous faisons une parsing robuste:
        # Chercher les blocs de résultats: rows de table ou éléments 'article' listés.
        # On va extraire les lignes contenant 'result' ou 'score' ou 'final'.
        # Méthode heuristique:
        for row in soup.find_all(["tr", "li", "div"], recursive=True):
            text = row.get_text(" ", strip=True)
            if not text:
                continue
            # Heuristique: contient une date et un score séparé par '-' ou '–' ou 'FT'
            if re.search(r"\bFT\b", text) or re.search(r"\d+\s*[-–]\s*\d+", text):
                # Try to extract opponent and score
                try:
                    # competition (small)
                    comp = None
                    comp_tag = row.find_previous(["h2", "h3", "span"])
                    if comp_tag:
                        comp = comp_tag.get_text(" ", strip=True)

                    # date - attempt to find time/date in ancestor nodes
                    date_text = None
                    date_tag = row.find_previous(string=re.compile(r"\w+\s+\d{1,2},\s*\d{4}|\d{1,2}\s+\w+\s+\d{4}"))
                    if date_tag:
                        date_text = date_tag.strip()
                    else:
                        # fallback: find any 'time' tag
                        ttag = row.find("time")
                        if ttag and ttag.has_attr("datetime"):
                            date_text = ttag["datetime"]

                    # score
                    mscore = re.search(r"(\d+)\s*[-–]\s*(\d+)", text)
                    if mscore:
                        score_for = int(mscore.group(1))
                        score_against = int(mscore.group(2))
                    else:
                        # if no score, skip
                        continue

                    # opponent: heuristique - text parts excluding score
                    txt = re.sub(r"\s*\d+\s*[-–]\s*\d+\s*", " |SCORE| ", text)
                    parts = [p.strip() for p in txt.split("|") if p.strip()]
                    opponent = None
                    home_or_away = None
                    if len(parts) >= 1:
                        # choose the part that is not SCORE and not date
                        for p in parts:
                            if "SCORE" in p:
                                continue
                            # ignore date-like
                            if re.search(r"\d{4}", p):
                                continue
                            # if contains vs or v. or VS, treat accordingly
                            if re.search(r"\b(vs?|v\.|vs)\b", p, re.I):
                                opponent = re.sub(r"\b(vs?|v\.|vs)\b", "", p, flags=re.I).strip()
                                # determine home/away by presence of 'at' or '@'
                                if re.search(r"@\s*| at ", p, re.I):
                                    home_or_away = "away"
                                else:
                                    home_or_away = "home"
                                break
                            # else heuristically pick a short name
                            if len(p) < 40 and not re.search(r"Final|FT|Live", p, re.I):
                                if not opponent:
                                    opponent = p

                    match = {
                        "date_text": date_text,
                        "opponent": opponent,
                        "home_or_away": home_or_away,
                        "score_for": score_for,
                        "score_against": score_against,
                        "competition": comp,
                        "raw_summary": text
                    }
                    matches.append(match)
                except Exception as e:
                    logging.debug(f"Erreur parsing row: {e}")
                    continue

        # Remove duplicates (by raw_summary)
        unique = []
        seen = set()
        for m in matches:
            key = (m.get("raw_summary"), m.get("date_text"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(m)
        return unique

    def compute_basic_stats(self, matches: List[Dict]) -> Dict:
        stats = {
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_diff": 0
        }
        for m in matches:
            stats["played"] += 1
            gf = m.get("score_for")
            ga = m.get("score_against")
            if gf is None or ga is None:
                continue
            stats["goals_for"] += gf
            stats["goals_against"] += ga
            if gf > ga:
                stats["wins"] += 1
            elif gf == ga:
                stats["draws"] += 1
            else:
                stats["losses"] += 1
        stats["goal_diff"] = stats["goals_for"] - stats["goals_against"]
        return stats

    def ask_groq(self, messages):
        if not GRQ_KEY:
            logging.info("🔒 GRQ_KEY non défini — saut de l'analyse IA.")
            return None
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GRQ_KEY}"}
        data = {
            "model": "openai/gpt-oss-120b",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1500
        }
        try:
            r = requests.post(url, headers=headers, json=data, timeout=30)
            if r.status_code != 200:
                logging.warning(f"IA erreur {r.status_code}: {r.text}")
                return None
            j = r.json()
            try:
                return j["choices"][0]["message"]["content"]
            except Exception:
                return None
        except Exception as e:
            logging.warning(f"Erreur IA: {e}")
            return None

    def analyze(self):
        """
        Parcours self.teams_data, récupère chaque page results, parse les matchs passés,
        calcule des stats basiques, lance IA si possible, puis écrit un JSON complet.
        """
        result = {
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "standings_urls": self.league_standings_urls,  # kept but not fetched
            "leagues": {}
        }

        for league_name, teams in self.teams_data.items():
            logging.info(f"Processing league: {league_name}")
            league_entry = {
                "league_name": league_name,
                "teams": []
            }
            for t in teams:
                team_name = t.get("team")
                results_url = t.get("results_url")
                team_entry = {
                    "team": team_name,
                    "results_url": results_url,
                    "results_page_fetched": False,
                    "results_page_fetch_error": None,
                    "past_matches": [],
                    "stats": {},
                    "ai_analysis_text": None
                }

                if not results_url:
                    team_entry["results_page_fetch_error"] = "missing_results_url"
                    league_entry["teams"].append(team_entry)
                    continue

                html = self.fetch_team_results_page(results_url)
                if not html:
                    team_entry["results_page_fetched"] = False
                    team_entry["results_page_fetch_error"] = "fetch_failed"
                    league_entry["teams"].append(team_entry)
                    continue

                team_entry["results_page_fetched"] = True
                try:
                    matches = self.parse_espn_results(html)
                    team_entry["past_matches"] = matches or []
                    team_entry["stats"] = self.compute_basic_stats(matches or [])
                    # IA analysis only if we have at least one match
                    if matches and len(matches) > 0:
                        # prepare prompt
                        brief = f"Fournis une analyse concise pour l'équipe {team_name} basée sur les {len(matches)} derniers matchs. Donne points forts, points faibles, forme récente en 3-5 lignes."
                        messages = [
                            {"role": "system", "content": "You are a helpful football analyst."},
                            {"role": "user", "content": brief + "\n\nMatches:\n" + json.dumps(matches, ensure_ascii=False)}
                        ]
                        ai_resp = self.ask_groq(messages)
                        team_entry["ai_analysis_text"] = ai_resp
                    else:
                        team_entry["ai_analysis_text"] = None
                except Exception as e:
                    team_entry["results_page_fetch_error"] = f"parse_error: {e}"
                league_entry["teams"].append(team_entry)

            result["leagues"][league_name] = league_entry

        # Ensure all keys exist at root
        if "metadata" not in result:
            result["metadata"] = {}
        result["metadata"].update({
            "note": "standings not fetched; standings_urls preserved under standings_urls key."
        })

        # Write JSON file (timestamped)
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        outfile = os.path.join(self.output_dir, f"analysis_{timestamp}.json")
        try:
            with open(outfile, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logging.info(f"✅ Analyse écrite dans {outfile}")
        except Exception as e:
            logging.error(f"Erreur écriture JSON: {e}")
            raise

        # Optionally git commit & push
        try:
            self._git_commit_and_push([outfile], f"Auto: analysis {timestamp}")
        except Exception:
            pass

        return result

if __name__ == "__main__":
    analyzer = FootballMatchAnalyzer()
    res = analyzer.analyze()
    print("Done. JSON generated keys:", list(res.keys()))