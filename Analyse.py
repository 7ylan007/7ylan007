import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import subprocess
import math
import itertools
import os
import re
import numpy as np

# 🔑 Récupération des clés depuis GitHub Secrets (variables d'environnement)
API_KEY = os.getenv("API_FOOTBALL_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
groq_keys = [
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_API_KEY1")
]

# En-têtes API Football
api_headers = {
    'x-apisports-key': API_KEY
}

# Paramètres API Odds
REGION = "eu"
MARKETS = "h2h,totals"

# Alternateur pour Groq
groq_key_index = 0

team_name_mapping = {
    "Bournemouth": "AFC Bournemouth",
    "Rep. Of Ireland": "Republic Of Ireland",
    "Sport Recife": "Sport",
    "RB Bragantino": "Red Bull Bragantino",
    "Fortaleza EC": "Fortaleza",
    "Gremio":"Grêmio",
    "Vitoria": "Vitória",
    "Vasco DA Gama": "Vasco da Gama",
    "Sao Paulo": "São Paulo",
    "Atletico-MG": "Atlético-MG",
    "Paris Saint Germain": "Paris Saint-Germain",
    "Atletico Madrid": "Atlético Madrid",
    "San Diego": "San Diego FC",
    "Austin": "Austin FC",
    "Seattle Sounders": "Seattle Sounders FC",
    "Los Angeles FC": "LAFC",
    "Santa Fe": "Independiente Santa Fe",
    "Qingdao Youth Island": "Qingdao Hainiu",
    "Atletico Nacional": "Atlético Nacional",
    "Henan Jianye": "Henan Songshan Longmen",
    "SHANGHAI SIPG": "Shanghai Port",
    "Al-Hilal Saudi FC": "Al Hilal",
    "Inter Miami": "Inter Miami CF",
    "Portuguesa FC": "Portuguesa",
    "2 de Mayo": "2 de Mayo",
    "America de Cali": "América de Cali",
    "Carabobo FC": "Carabobo",
    "Rapid": "Rapid Bucuresti",
    "Operario-PR": "Operario PR",
    "Arges Pitesti": "Fc Arges",
    "Libertad Asuncion": "Libertad",
    "General Caballero": "General Caballero JLM",
    "Real Esppor Club": "Deportivo La Guaira",
    "UCV": "Universidad Central",
    "Cuiaba": "Cuiabá",
    "remo": "Remo",
}

classement_ligue_mapping = {
    "Colombia": {
        "Primera A": {
            "url": "https://www.espn.com/soccer/standings/_/league/col.1",
            "odds_id": "none",
            "data_json": "Colombia_Primera_A.json"
        }
    },
    "France": {
        "Ligue 1": {
            "url": "https://www.espn.com/soccer/standings/_/league/fra.1",
            "odds_id": "soccer_france_ligue_one",
            "data_json": "France_Ligue_1.json"
        }
    },
    "Belgium": {
        "Jupiler Pro League": {
            "url": "https://www.espn.com/soccer/standings/_/league/bel.1",
            "odds_id": "soccer_belgium_first_div",
            "data_json": "Belgium_Jupiler_Pro_League.json"
        }
    },
    "England": {
        "Premier League": {
            "url": "https://www.espn.com/soccer/standings/_/league/eng.1",
            "odds_id": "soccer_epl",
            "data_json": "p_league.json"
        },
        "National League": {
            "url": "https://www.espn.com/soccer/standings/_/league/eng.5",
            "odds_id": "none",
            "data_json": "England_National_League.json"
        }
    },
    "Netherlands": {
        "Eredivisie": {
            "url": "https://www.espn.com/soccer/standings/_/league/ned.1",
            "odds_id": "soccer_netherlands_eredivisie",
            "data_json": "Netherlands_Eredivisie.json"
        }
    },
    "Portugal": {
        "Primeira Liga": {
            "url": "https://www.espn.com/soccer/standings/_/league/por.1",
            "odds_id": "soccer_portugal_primeira_liga",
            "data_json": "Portugal_Primeira_Liga.json"
        }
    },
    "Spain": {
        "La Liga": {
            "url": "https://www.espn.com/soccer/standings/_/league/esp.1",
            "odds_id": "soccer_spain_la_liga",
            "data_json": "laliga.json"
        }
    },
    "Germany": {
        "Bundesliga": {
            "url": "https://www.espn.com/soccer/standings/_/league/ger.1",
            "odds_id": "soccer_germany_bundesliga",
            "data_json": "bundesliga.json"
        }
    },
    "Austria": {
        "Bundesliga": {
            "url": "https://www.espn.com/soccer/standings/_/league/aut.1",
            "odds_id": "soccer_austria_bundesliga",
            "data_json": "Austria_Bundesliga.json"
        }
    },
    "Italy": {
        "Serie A": {
            "url": "https://www.espn.com/soccer/standings/_/league/ita.1",
            "odds_id": "soccer_italy_serie_a",
            "data_json": "Italy_Serie_A.json"
        }
    },
    "Brazil": {
        "Serie A": {
            "url": "https://www.espn.com/soccer/standings/_/league/bra.1",
            "odds_id": "soccer_brazil_campeonato",
            "data_json": "Brazil_Serie_A.json"
        },
        "Serie B": {
            "url": "https://www.espn.com/soccer/standings/_/league/bra.2",
            "odds_id": "soccer_brazil_serie_b",
            "data_json": "Brazil_Serie_B.json"
        }
    },
    "Turkey": {
        "Süper Lig": {
            "url": "https://www.espn.com/soccer/standings/_/league/tur.1",
            "odds_id": "soccer_turkey_super_league",
            "data_json": "Turkey_Super_Lig.json"
        }
    },
    "Mexico": {
        "Liga MX": {
            "url": "https://www.espn.com/soccer/standings/_/league/mex.1",
            "odds_id": "soccer_mexico_ligamx",
            "data_json": "Mexico_Liga_MX.json"
        }
    },
    "USA": {
        "Major League Soccer": {
            "url": "https://www.espn.com/soccer/standings/_/league/usa.1",
            "odds_id": "soccer_usa_mls",
            "data_json": "USA_Major_League_Soccer.json"
        }
    },
    "Japan": {
        "J1 League": {
            "url": "https://www.espn.com/soccer/standings/_/league/jpn.1",
            "odds_id": "soccer_japan_j_league",
            "data_json": "Japan_J1_League.json"
        }
    },
    "Saudi-Arabia": {
        "Pro League": {
            "url": "https://www.espn.com/soccer/standings/_/league/ksa.1",
            "odds_id": "none",
            "data_json": "Saudi_Arabia_Pro_League.json"
        }
    },
    "Switzerland": {
        "Super League": {
            "url": "https://www.espn.com/soccer/standings/_/league/sui.1",
            "odds_id": "soccer_switzerland_superleague",
            "data_json": "Switzerland_Super_League.json"
        }
    },
    "China": {
        "Super League": {
            "url": "https://www.espn.com/soccer/standings/_/league/chn.1",
            "odds_id": "soccer_china_superleague",
            "data_json": "China_Super_League.json"
        }
    },
    "Russia": {
        "Premier League": {
            "url": "https://www.espn.com/soccer/standings/_/league/rus.1",
            "odds_id": "none",
            "data_json": "Russia_Premier_League.json"
        }
    },
    "Greece": {
        "Super League 1": {
            "url": "https://www.espn.com/soccer/standings/_/league/gre.1",
            "odds_id": "soccer_greece_super_league",
            "data_json": "Greece_Super_League_1.json"
        }
    },
    "Chile": {
        "Primera División": {
            "url": "https://www.espn.com/soccer/standings/_/league/chi.1",
            "odds_id": "soccer_chile_campeonato",
            "data_json": "Chile_Primera_Division.json"
        }
    },
    "Peru": {
        "Primera División": {
            "url": "https://www.espn.com/soccer/standings/_/league/per.1",
            "odds_id": "none",
            "data_json": "Peru_Primera_Division.json"
        }
    },
    "Sweden": {
        "Allsvenskan": {
            "url": "https://www.espn.com/soccer/standings/_/league/swe.1",
            "odds_id": "soccer_sweden_allsvenskan",
            "data_json": "Sweden_Allsvenskan.json"
        }
    },
    "Argentina": {
        "Primera Nacional": {
            "url": "https://www.espn.com/soccer/standings/_/league/arg.2",
            "odds_id": "soccer_argentina_primera_division",
            "data_json": "Argentina_Primera_Nacional.json"
        }
    },
    "Paraguay": {
        "Division Profesional": {
            "url": "https://www.espn.com/soccer/standings/_/league/par.1",
            "odds_id": "none",
            "data_json": "Paraguay_Division_Profesional.json"
        }
    },
    "Venezuela": {
        "Primera División": {
            "url": "https://www.espn.com/soccer/standings/_/league/ven.1",
            "odds_id": "none",
            "data_json": "Venezuela_Primera_Division.json"
        }
    },
    "Romania": {
        "Liga I": {
            "url": "https://www.espn.com/soccer/standings/_/league/rou.1",
            "odds_id": "none",
            "data_json": "Romania_Liga_I.json"
        }
    }
}

teams_urls = {
    # Bloc Europe du dernier JSON
    "Wales": {"results": "https://www.espn.com/soccer/team/results/_/id/578/wales"},
    "Turkey": {"results": "https://www.espn.com/soccer/team/results/_/id/465/turkey"},
    "Ukraine": {"results": "https://www.espn.com/soccer/team/results/_/id/457/ukraine"},
    "Sweden": {"results": "https://www.espn.com/soccer/team/results/_/id/466/sweden"},
    "Switzerland": {"results": "https://www.espn.com/soccer/team/results/_/id/475/switzerland"},
    "Slovenia": {"results": "https://www.espn.com/soccer/team/results/_/id/472/slovenia"},
    "Slovakia": {"results": "https://www.espn.com/soccer/team/results/_/id/468/slovakia"},
    "Scotland": {"results": "https://www.espn.com/soccer/team/results/_/id/580/scotland"},
    "Serbia": {"results": "https://www.espn.com/soccer/team/results/_/id/6757/serbia"},
    "Romania": {"results": "https://www.espn.com/soccer/team/results/_/id/473/romania"},
    "Norway": {"results": "https://www.espn.com/soccer/team/results/_/id/464/norway"},
    "Poland": {"results": "https://www.espn.com/soccer/team/results/_/id/471/poland"},
    "Northern Ireland": {"results": "https://www.espn.com/soccer/team/results/_/id/586/northern-ireland"},
    "Netherlands": {"results": "https://www.espn.com/soccer/team/results/_/id/449/netherlands"},
    "North Macedonia": {"results": "https://www.espn.com/soccer/team/results/_/id/463/north-macedonia"},
    "Montenegro": {"results": "https://www.espn.com/soccer/team/results/_/id/6775/montenegro"},
    "Moldova": {"results": "https://www.espn.com/soccer/team/results/_/id/483/moldova"},
    "Latvia": {"results": "https://www.espn.com/soccer/team/results/_/id/456/latvia"},
    "Kazakhstan": {"results": "https://www.espn.com/soccer/team/results/_/id/2619/kazakhstan"},
    "Kosovo": {"results": "https://www.espn.com/soccer/team/results/_/id/18272/kosovo"},
    "Italy": {"results": "https://www.espn.com/soccer/team/results/_/id/162/italy"},
    "Israel": {"results": "https://www.espn.com/soccer/team/results/_/id/461/israel"},
    "Malta": {"results": "https://www.espn.com/soccer/team/results/_/id/453/malta"},
    "Luxembourg": {"results": "https://www.espn.com/soccer/team/results/_/id/582/luxembourg"},
    "Lithuania": {"results": "https://www.espn.com/soccer/team/results/_/id/460/lithuania"},
    "Iceland": {"results": "https://www.espn.com/soccer/team/results/_/id/470/iceland"},
    "Hungary": {"results": "https://www.espn.com/soccer/team/results/_/id/480/hungary"},
    "Greece": {"results": "https://www.espn.com/soccer/team/results/_/id/455/greece"},
    "Gibraltar": {"results": "https://www.espn.com/soccer/team/results/_/id/16721/gibraltar"},
    "Finland": {"results": "https://www.espn.com/soccer/team/results/_/id/458/finland"},
    "Faroe Islands": {"results": "https://www.espn.com/soccer/team/results/_/id/447/faroe-islands"},
    "Estonia": {"results": "https://www.espn.com/soccer/team/results/_/id/444/estonia"},
    "England": {"results": "https://www.espn.com/soccer/team/results/_/id/448/england"},
    "Denmark": {"results": "https://www.espn.com/soccer/team/results/_/id/479/denmark"},
    "Czechia": {"results": "https://www.espn.com/soccer/team/results/_/id/450/czechia"},
    "Cyprus": {"results": "https://www.espn.com/soccer/team/results/_/id/445/cyprus"},
    "Croatia": {"results": "https://www.espn.com/soccer/team/results/_/id/477/croatia"},
    "Bulgaria": {"results": "https://www.espn.com/soccer/team/results/_/id/462/bulgaria"},
    "Bosnia and Herzegovina": {"results": "https://www.espn.com/soccer/team/results/_/id/452/bosnia-and-herzegovina"},
    "Belgium": {"results": "https://www.espn.com/soccer/team/results/_/id/459/belgium"},
    "Belarus": {"results": "https://www.espn.com/soccer/team/results/_/id/583/belarus"},
    "Austria": {"results": "https://www.espn.com/soccer/team/results/_/id/474/austria"},
    "Azerbaijan": {"results": "https://www.espn.com/soccer/team/results/_/id/581/azerbaijan"},
    "Armenia": {"results": "https://www.espn.com/soccer/team/results/_/id/579/armenia"},
    "Andorra": {"results": "https://www.espn.com/soccer/team/results/_/id/587/andorra"},
    "Albania": {"results": "https://www.espn.com/soccer/team/results/_/id/585/albania"},
    # Bloc Afrique, Asie, Caraïbes, etc. (et quelques doublons pour sécurité)
    "Angola": {"results": "https://www.espn.com/soccer/team/results/_/id/653/angola"},
    "Botswana": {"results": "https://www.espn.com/soccer/team/results/_/id/4245/botswana"},
    "Comoros": {"results": "https://www.espn.com/soccer/team/results/_/id/8601/comoros"},
    "Eswatini": {"results": "https://www.espn.com/soccer/team/results/_/id/6686/eswatini"},
    "Lesotho": {"results": "https://www.espn.com/soccer/team/results/_/id/6640/lesotho"},
    "Madagascar": {"results": "https://www.espn.com/soccer/team/results/_/id/5533/madagascar"},
    "Malawi": {"results": "https://www.espn.com/soccer/team/results/_/id/4325/malawi"},
    "Mauritius": {"results": "https://www.espn.com/soccer/team/results/_/id/5534/mauritius"},
    "Mozambique": {"results": "https://www.espn.com/soccer/team/results/_/id/8939/mozambique"},
    "Namibia": {"results": "https://www.espn.com/soccer/team/results/_/id/6725/namibia"},
    "South Africa": {"results": "https://www.espn.com/soccer/team/results/_/id/467/south-africa"},
    "Tanzania": {"results": "https://www.espn.com/soccer/team/results/_/id/5778/tanzania"},
    "Zimbabwe": {"results": "https://www.espn.com/soccer/team/results/_/id/4214/zimbabwe"},
    "Afghanistan": {"results": "https://www.espn.com/soccer/team/results/_/id/5780/afghanistan"},
    "Algeria": {"results": "https://www.espn.com/soccer/team/results/_/id/624/algeria"},
    "Anguilla": {"results": "https://www.espn.com/soccer/team/results/_/id/8942/anguilla"},
    "Aruba": {"results": "https://www.espn.com/soccer/team/results/_/id/2642/aruba"},
    "Barbados": {"results": "https://www.espn.com/soccer/team/results/_/id/2637/barbados"},
    "Benin": {"results": "https://www.espn.com/soccer/team/results/_/id/2844/benin"},
    "Bonaire": {"results": "https://www.espn.com/soccer/team/results/_/id/19314/bonaire"},
    "British Virgin Islands": {"results": "https://www.espn.com/soccer/team/results/_/id/2644/british-virgin-islands"},
    "Brunei Darussalam": {"results": "https://www.espn.com/soccer/team/results/_/id/10525/brunei-darussalam"},
    "Burkina Faso": {"results": "https://www.espn.com/soccer/team/results/_/id/2845/burkina-faso"},
    "Burundi": {"results": "https://www.espn.com/soccer/team/results/_/id/5779/burundi"},
    "Cambodia": {"results": "https://www.espn.com/soccer/team/results/_/id/5518/cambodia"},
    "Cameroon": {"results": "https://www.espn.com/soccer/team/results/_/id/656/cameroon"},
    "Canada": {"results": "https://www.espn.com/soccer/team/results/_/id/206/canada"},
    "Cape Verde Islands": {"results": "https://www.espn.com/soccer/team/results/_/id/2597/cape-verde-islands"},
    "Central African Republic": {"results": "https://www.espn.com/soccer/team/results/_/id/10528/central-african-republic"},
    "Chad": {"results": "https://www.espn.com/soccer/team/results/_/id/8941/chad"},
    "Chile": {"results": "https://www.espn.com/soccer/team/results/_/id/207/chile"},
    "Congo DR": {"results": "https://www.espn.com/soccer/team/results/_/id/2850/congo-dr"},
    "Costa Rica": {"results": "https://www.espn.com/soccer/team/results/_/id/214/costa-rica"},
    "Curacao": {"results": "https://www.espn.com/soccer/team/results/_/id/11678/curacao"},
    "Dominica": {"results": "https://www.espn.com/soccer/team/results/_/id/13582/dominica"},
    "Dominican Republic": {"results": "https://www.espn.com/soccer/team/results/_/id/2649/dominican-republic"},
    "El Salvador": {"results": "https://www.espn.com/soccer/team/results/_/id/2650/el-salvador"},
    "Equatorial Guinea": {"results": "https://www.espn.com/soccer/team/results/_/id/8938/equatorial-guinea"},
    "Gabon": {"results": "https://www.espn.com/soccer/team/results/_/id/4231/gabon"},
    "Gambia": {"results": "https://www.espn.com/soccer/team/results/_/id/7368/gambia"},
    "Georgia": {"results": "https://www.espn.com/soccer/team/results/_/id/584/georgia"},
    "Ghana": {"results": "https://www.espn.com/soccer/team/results/_/id/4469/ghana"},
    "Guatemala": {"results": "https://www.espn.com/soccer/team/results/_/id/2652/guatemala"},
    "Guinea-Bissau": {"results": "https://www.espn.com/soccer/team/results/_/id/8602/guinea-bissau"},
    "Haiti": {"results": "https://www.espn.com/soccer/team/results/_/id/2654/haiti"},
    "Honduras": {"results": "https://www.espn.com/soccer/team/results/_/id/215/honduras"},
    "Hong Kong": {"results": "https://www.espn.com/soccer/team/results/_/id/1928/hong-kong"},
    "India": {"results": "https://www.espn.com/soccer/team/results/_/id/4385/india"},
    "Iran": {"results": "https://www.espn.com/soccer/team/results/_/id/469/iran"},
    "Ivory Coast": {"results": "https://www.espn.com/soccer/team/results/_/id/4789/ivory-coast"},
    "Jamaica": {"results": "https://www.espn.com/soccer/team/results/_/id/1038/jamaica"},
    "Japan": {"results": "https://www.espn.com/soccer/team/results/_/id/627/japan"},
    "Jordan": {"results": "https://www.espn.com/soccer/team/results/_/id/2917/jordan"},
    "Kenya": {"results": "https://www.espn.com/soccer/team/results/_/id/2848/kenya"},
    "Laos": {"results": "https://www.espn.com/soccer/team/results/_/id/7348/laos"},
    "Lebanon": {"results": "https://www.espn.com/soccer/team/results/_/id/4388/lebanon"},
    "Liberia": {"results": "https://www.espn.com/soccer/team/results/_/id/4205/liberia"},
    "Liechtenstein": {"results": "https://www.espn.com/soccer/team/results/_/id/589/liechtenstein"},
    "Lithuania": {"results": "https://www.espn.com/soccer/team/results/_/id/460/lithuania"},
    "Luxembourg": {"results": "https://www.espn.com/soccer/team/results/_/id/582/luxembourg"},
    "Macau": {"results": "https://www.espn.com/soccer/team/results/_/id/6722/macau"},
    "Malaysia": {"results": "https://www.espn.com/soccer/team/results/_/id/2405/malaysia"},
    "Maldives": {"results": "https://www.espn.com/soccer/team/results/_/id/4390/maldives"},
    "Mali": {"results": "https://www.espn.com/soccer/team/results/_/id/2849/mali"},
    "Malta": {"results": "https://www.espn.com/soccer/team/results/_/id/453/malta"},
    "Mauritania": {"results": "https://www.espn.com/soccer/team/results/_/id/8940/mauritania"},
    "Mexico": {"results": "https://www.espn.com/soccer/team/results/_/id/203/mexico"},
    "Moldova": {"results": "https://www.espn.com/soccer/team/results/_/id/483/moldova"},
    "Montenegro": {"results": "https://www.espn.com/soccer/team/results/_/id/6775/montenegro"},
    "Morocco": {"results": "https://www.espn.com/soccer/team/results/_/id/2869/morocco"},
    "Mozambique": {"results": "https://www.espn.com/soccer/team/results/_/id/8939/mozambique"},
    "Nepal": {"results": "https://www.espn.com/soccer/team/results/_/id/5785/nepal"},
    "New Zealand": {"results": "https://www.espn.com/soccer/team/results/_/id/2666/new-zealand"},
    "Nicaragua": {"results": "https://www.espn.com/soccer/team/results/_/id/2658/nicaragua"},
    "Niger": {"results": "https://www.espn.com/soccer/team/results/_/id/8937/niger"},
    "Nigeria": {"results": "https://www.espn.com/soccer/team/results/_/id/657/nigeria"},
    "North Korea": {"results": "https://www.espn.com/soccer/team/results/_/id/4860/north-korea"},
    "Northern Ireland": {"results": "https://www.espn.com/soccer/team/results/_/id/586/northern-ireland"},
    "Norway": {"results": "https://www.espn.com/soccer/team/results/_/id/464/norway"},
    "Oman": {"results": "https://www.espn.com/soccer/team/results/_/id/2841/oman"},
    "Poland": {"results": "https://www.espn.com/soccer/team/results/_/id/471/poland"},
    "Panama": {"results": "https://www.espn.com/soccer/team/results/_/id/2659/panama"},
    "Puerto Rico": {"results": "https://www.espn.com/soccer/team/results/_/id/11766/puerto-rico"},
    "Republic Of Ireland": {"results": "https://www.espn.com/soccer/team/results/_/id/476/republic-of-ireland"},
    "Russia": {"results": "https://www.espn.com/soccer/team/results/_/id/454/russia"},
    "Rwanda": {"results": "https://www.espn.com/soccer/team/results/_/id/2851/rwanda"},
    "Saudi Arabia": {"results": "https://www.espn.com/soccer/team/results/_/id/655/saudi-arabia"},
    "Scotland": {"results": "https://www.espn.com/soccer/team/results/_/id/580/scotland"},
    "Senegal": {"results": "https://www.espn.com/soccer/team/results/_/id/654/senegal"},
    "Singapore": {"results": "https://www.espn.com/soccer/team/results/_/id/4384/singapore"},
    "Slovakia": {"results": "https://www.espn.com/soccer/team/results/_/id/468/slovakia"},
    "Slovenia": {"results": "https://www.espn.com/soccer/team/results/_/id/472/slovenia"},
    "South Africa": {"results": "https://www.espn.com/soccer/team/results/_/id/467/south-africa"},
    "South Korea": {"results": "https://www.espn.com/soccer/team/results/_/id/451/south-korea"},
    "Sri Lanka": {"results": "https://www.espn.com/soccer/team/results/_/id/5782/sri-lanka"},
    "St Kitts and Nevis": {"results": "https://www.espn.com/soccer/team/results/_/id/2662/st-kitts-and-nevis"},
    "St Martin": {"results": "https://www.espn.com/soccer/team/results/_/id/10596/st-martin"},
    "St Vincent and the Grenadines": {"results": "https://www.espn.com/soccer/team/results/_/id/13584/st-vincent-and-the-grenadines"},
    "Sudan": {"results": "https://www.espn.com/soccer/team/results/_/id/4319/sudan"},
    "Sweden": {"results": "https://www.espn.com/soccer/team/results/_/id/466/sweden"},
    "Switzerland": {"results": "https://www.espn.com/soccer/team/results/_/id/475/switzerland"},
    "Tajikistan": {"results": "https://www.espn.com/soccer/team/results/_/id/6723/tajikistan"},
    "Tanzania": {"results": "https://www.espn.com/soccer/team/results/_/id/5778/tanzania"},
    "Thailand": {"results": "https://www.espn.com/soccer/team/results/_/id/4396/thailand"},
    "Timor-Leste": {"results": "https://www.espn.com/soccer/team/results/_/id/8664/timor-leste"},
    "Trinidad and Tobago": {"results": "https://www.espn.com/soccer/team/results/_/id/2627/trinidad-and-tobago"},
    "Tunisia": {"results": "https://www.espn.com/soccer/team/results/_/id/659/tunisia"},
    "Turkey": {"results": "https://www.espn.com/soccer/team/results/_/id/465/turkey"},
    "Uganda": {"results": "https://www.espn.com/soccer/team/results/_/id/4211/uganda"},
    "Ukraine": {"results": "https://www.espn.com/soccer/team/results/_/id/457/ukraine"},
    "United States": {"results": "https://www.espn.com/soccer/team/results/_/id/660/united-states"},
    "Venezuela": {"results": "https://www.espn.com/soccer/team/results/_/id/213/venezuela"},
    "Vietnam": {"results": "https://www.espn.com/soccer/team/results/_/id/7349/vietnam"},
    "Wales": {"results": "https://www.espn.com/soccer/team/results/_/id/578/wales"},
    "Zambia": {"results": "https://www.espn.com/soccer/team/results/_/id/4277/zambia"},
    "Zanzibar": {"results": "https://www.espn.com/soccer/team/results/_/id/5815/zanzibar"},
    "Zimbabwe": {"results": "https://www.espn.com/soccer/team/results/_/id/4214/zimbabwe"},
    "Atlético-MG": {
    "results": "https://www.espn.com/soccer/team/results/_/id/7632/atletico-mg"
  },
  "Bahia": {
    "results": "https://www.espn.com/soccer/team/results/_/id/9967/bahia"
  },
  "Botafogo": {
    "results": "https://www.espn.com/soccer/team/results/_/id/6086/botafogo"
  },
  "Ceará": {
    "results": "https://www.espn.com/soccer/team/results/_/id/9969/ceara"
  },
  "Corinthians": {
    "results": "https://www.espn.com/soccer/team/results/_/id/874/corinthians"
  },
  "Cruzeiro": {
    "results": "https://www.espn.com/soccer/team/results/_/id/2022/cruzeiro"
  },
  "Flamengo": {
    "results": "https://www.espn.com/soccer/team/results/_/id/819/flamengo"
  },
  "Fluminense": {
    "results": "https://www.espn.com/soccer/team/results/_/id/3445/fluminense"
  },
  "Fortaleza": {
    "results": "https://www.espn.com/soccer/team/results/_/id/6272/fortaleza"
  },
  "Grêmio": {
    "results": "https://www.espn.com/soccer/team/results/_/id/6273/gremio"
  },
  "Internacional": {
    "results": "https://www.espn.com/soccer/team/results/_/id/1936/internacional"
  },
  "Juventude": {
    "results": "https://www.espn.com/soccer/team/results/_/id/6270/juventude"
  },
  "Mirassol": {
    "results": "https://www.espn.com/soccer/team/results/_/id/9169/mirassol"
  },
  "Palmeiras": {
    "results": "https://www.espn.com/soccer/team/results/_/id/2029/palmeiras"
  },
  "Red Bull Bragantino": {
    "results": "https://www.espn.com/soccer/team/results/_/id/6079/red-bull-bragantino"
  },
  "Santos": {
    "results": "https://www.espn.com/soccer/team/results/_/id/2674/santos"
  },
  "São Paulo": {
    "results": "https://www.espn.com/soccer/team/results/_/id/2026/sao-paulo"
  },
  "Vasco da Gama": {
    "results": "https://www.espn.com/soccer/team/results/_/id/3454/vasco-da-gama"
  },
  "Vitória": {
    "results": "https://www.espn.com/soccer/team/results/_/id/3457/vitoria"
  },
  "Sport": {
    "results": "https://www.espn.com/soccer/team/results/_/id/7635/sport"
  },
  "AFC Bournemouth": {
        "results": "https://www.espn.com/football/team/results/_/id/349/afc-bournemouth"
    },
    "Arsenal": {
        "results": "https://www.espn.com/football/team/results/_/id/359/arsenal"
    },
    "Aston Villa": {
        "results": "https://www.espn.com/football/team/results/_/id/362/aston-villa"
    },
    "Brentford": {
        "results": "https://www.espn.com/football/team/results/_/id/337/brentford"
    },
    "Brighton & Hove Albion": {
        "results": "https://www.espn.com/football/team/results/_/id/331/brighton-hove-albion"
    },
    "Chelsea": {
        "results": "https://www.espn.com/football/team/results/_/id/363/chelsea"
    },
    "Crystal Palace": {
        "results": "https://www.espn.com/football/team/results/_/id/384/crystal-palace"
    },
    "Everton": {
        "results": "https://www.espn.com/football/team/results/_/id/368/everton"
    },
    "Fulham": {
        "results": "https://www.espn.com/football/team/results/_/id/370/fulham"
    },
    "Ipswich Town": {
        "results": "https://www.espn.com/football/team/results/_/id/373/ipswich-town"
    },
    "Leicester City": {
        "results": "https://www.espn.com/football/team/results/_/id/375/leicester-city"
    },
    "Liverpool": {
        "results": "https://www.espn.com/football/team/results/_/id/364/liverpool"
    },
    "Manchester City": {
        "results": "https://www.espn.com/football/team/results/_/id/382/manchester-city"
    },
    "Manchester United": {
        "results": "https://www.espn.com/football/team/results/_/id/360/manchester-united"
    },
    "Newcastle United": {
        "results": "https://www.espn.com/football/team/results/_/id/361/newcastle-united"
    },
    "Nottingham Forest": {
        "results": "https://www.espn.com/football/team/results/_/id/393/nottingham-forest"
    },
    "Southampton": {
        "results": "https://www.espn.com/football/team/results/_/id/376/southampton"
    },
    "Tottenham Hotspur": {
        "results": "https://www.espn.com/football/team/results/_/id/367/tottenham-hotspur"
    },
    "West Ham United": {
        "results": "https://www.espn.com/football/team/results/_/id/371/west-ham-united"
    },
    "Wolverhampton Wanderers": {
        "results": "https://www.espn.com/football/team/results/_/id/380/wolverhampton-wanderers"
    },
    "Alavés": {
        "results": "https://www.espn.com/football/team/results/_/id/96/alaves"
    },
    "Athletic Club": {
        "results": "https://www.espn.com/football/team/results/_/id/93/athletic-club"
    },
    "Atlético Madrid": {
        "results": "https://www.espn.com/football/team/results/_/id/1068/atletico-madrid"
    },
    "Barcelona": {
        "results": "https://www.espn.com/football/team/results/_/id/83/barcelona"
    },
    "Celta Vigo": {
        "results": "https://www.espn.com/football/team/results/_/id/85/celta-vigo"
    },
    "Espanyol": {
        "results": "https://www.espn.com/football/team/results/_/id/88/espanyol"
    },
    "Getafe": {
        "results": "https://www.espn.com/football/team/results/_/id/2922/getafe"
    },
    "Girona": {
        "results": "https://www.espn.com/football/team/results/_/id/9812/girona"
    },
    "Las Palmas": {
        "results": "https://www.espn.com/football/team/results/_/id/98/las-palmas"
    },
    "Leganés": {
        "results": "https://www.espn.com/football/team/results/_/id/17534/leganes"
    },
    "Mallorca": {
        "results": "https://www.espn.com/football/team/results/_/id/84/mallorca"
    },
    "Osasuna": {
        "results": "https://www.espn.com/football/team/results/_/id/97/osasuna"
    },
    "Rayo Vallecano": {
        "results": "https://www.espn.com/football/team/results/_/id/101/rayo-vallecano"
    },
    "Real Betis": {
        "results": "https://www.espn.com/football/team/results/_/id/244/real-betis"
    },
    "Real Madrid": {
        "results": "https://www.espn.com/football/team/results/_/id/86/real-madrid"
    },
    "Real Sociedad": {
        "results": "https://www.espn.com/football/team/results/_/id/89/real-sociedad"
    },
    "Real Valladolid": {
        "results": "https://www.espn.com/football/team/results/_/id/95/real-valladolid"
    },
    "Sevilla": {
        "results": "https://www.espn.com/football/team/results/_/id/243/sevilla"
    },
    "Valencia": {
        "results": "https://www.espn.com/football/team/results/_/id/94/valencia"
    },
    "Villarreal": {
        "results": "https://www.espn.com/football/team/results/_/id/102/villarreal"
    },
    "AC Milan": {
        "results": "https://www.espn.com/football/team/results/_/id/103/ac-milan"
    },
    "AS Roma": {
        "results": "https://www.espn.com/football/team/results/_/id/104/as-roma"
    },
    "Atalanta": {
        "results": "https://www.espn.com/football/team/results/_/id/105/atalanta"
    },
    "Bologna": {
        "results": "https://www.espn.com/football/team/results/_/id/107/bologna"
    },
    "Cagliari": {
        "results": "https://www.espn.com/football/team/results/_/id/2925/cagliari"
    },
    "Como": {
        "results": "https://www.espn.com/football/team/results/_/id/2572/como"
    },
    "Cremonese": {
        "results": "https://www.espn.com/football/team/results/_/id/4050/cremonese"
    },
    "Fiorentina": {
        "results": "https://www.espn.com/football/team/results/_/id/109/fiorentina"
    },
    "Genoa": {
        "results": "https://www.espn.com/football/team/results/_/id/3263/genoa"
    },
    "Hellas Verona": {
        "results": "https://www.espn.com/football/team/results/_/id/119/hellas-verona"
    },
    "Internazionale": {
        "results": "https://www.espn.com/football/team/results/_/id/110/internazionale"
    },
    "Juventus": {
        "results": "https://www.espn.com/football/team/results/_/id/111/juventus"
    },
    "Lazio": {
        "results": "https://www.espn.com/football/team/results/_/id/112/lazio"
    },
    "Lecce": {
        "results": "https://www.espn.com/football/team/results/_/id/113/lecce"
    },
    "Napoli": {
        "results": "https://www.espn.com/football/team/results/_/id/114/napoli"
    },
    "Parma": {
        "results": "https://www.espn.com/football/team/results/_/id/115/parma"
    },
    "Pisa": {
        "results": "https://www.espn.com/football/team/results/_/id/3956/pisa"
    },
    "Sassuolo": {
        "results": "https://www.espn.com/football/team/results/_/id/3997/sassuolo"
    },
    "Torino": {
        "results": "https://www.espn.com/football/team/results/_/id/239/torino"
    },
    "Udinese": {
        "results": "https://www.espn.com/football/team/results/_/id/118/udinese"
    },
    "1. FC Heidenheim 1846": {
        "results": "https://www.espn.com/football/team/results/_/id/6418/1-fc-heidenheim-1846"
    },
    "1. FC Union Berlin": {
        "results": "https://www.espn.com/football/team/results/_/id/598/1-fc-union-berlin"
    },
    "Bayer Leverkusen": {
        "results": "https://www.espn.com/football/team/results/_/id/131/bayer-leverkusen"
    },
    "Bayern Munich": {
        "results": "https://www.espn.com/football/team/results/_/id/132/bayern-munich"
    },
    "Borussia Dortmund": {
        "results": "https://www.espn.com/football/team/results/_/id/124/borussia-dortmund"
    },
    "Borussia Mönchengladbach": {
        "results": "https://www.espn.com/football/team/results/_/id/268/borussia-monchengladbach"
    },
    "Eintracht Frankfurt": {
        "results": "https://www.espn.com/football/team/results/_/id/125/eintracht-frankfurt"
    },
    "FC Augsburg": {
        "results": "https://www.espn.com/football/team/results/_/id/3841/fc-augsburg"
    },
    "Holstein Kiel": {
        "results": "https://www.espn.com/football/team/results/_/id/7884/holstein-kiel"
    },
    "Mainz": {
        "results": "https://www.espn.com/football/team/results/_/id/2950/mainz"
    },
    "RB Leipzig": {
        "results": "https://www.espn.com/football/team/results/_/id/11420/rb-leipzig"
    },
    "SC Freiburg": {
        "results": "https://www.espn.com/football/team/results/_/id/126/sc-freiburg"
    },
    "St. Pauli": {
        "results": "https://www.espn.com/football/team/results/_/id/270/st-pauli"
    },
    "TSG Hoffenheim": {
        "results": "https://www.espn.com/football/team/results/_/id/7911/tsg-hoffenheim"
    },
    "VfB Stuttgart": {
        "results": "https://www.espn.com/football/team/results/_/id/134/vfb-stuttgart"
    },
    "VfL Bochum": {
        "results": "https://www.espn.com/football/team/results/_/id/121/vfl-bochum"
    },
    "VfL Wolfsburg": {
        "results": "https://www.espn.com/football/team/results/_/id/138/vfl-wolfsburg"
    },
    "Werder Bremen": {
        "results": "https://www.espn.com/football/team/results/_/id/137/werder-bremen"
    },
    "AJ Auxerre": {
        "results": "https://www.espn.com/football/team/results/_/id/172/aj-auxerre"
    },
    "AS Monaco": {
        "results": "https://www.espn.com/football/team/results/_/id/174/as-monaco"
    },
    "Angers": {
        "results": "https://www.espn.com/football/team/results/_/id/7868/angers"
    },
    "Brest": {
        "results": "https://www.espn.com/football/team/results/_/id/6997/brest"
    },
    "Le Havre AC": {
        "results": "https://www.espn.com/football/team/results/_/id/3236/le-havre-ac"
    },
    "Lens": {
        "results": "https://www.espn.com/football/team/results/_/id/175/lens"
    },
    "Lille": {
        "results": "https://www.espn.com/football/team/results/_/id/166/lille"
    },
    "Lyon": {
        "results": "https://www.espn.com/football/team/results/_/id/167/lyon"
    },
    "Marseille": {
        "results": "https://www.espn.com/football/team/results/_/id/176/marseille"
    },
    "Montpellier": {
        "results": "https://www.espn.com/football/team/results/_/id/274/montpellier"
    },
    "Nantes": {
        "results": "https://www.espn.com/football/team/results/_/id/165/nantes"
    },
    "Nice": {
        "results": "https://www.espn.com/football/team/results/_/id/2502/nice"
    },
    "Paris Saint-Germain": {
        "results": "https://www.espn.com/football/team/results/_/id/160/paris-saint-germain"
    },
    "Saint-Étienne": {
        "results": "https://www.espn.com/football/team/results/_/id/178/saint-etienne"
    },
    "Stade Rennais": {
        "results": "https://www.espn.com/football/team/results/_/id/169/stade-rennais"
    },
    "Stade de Reims": {
        "results": "https://www.espn.com/football/team/results/_/id/3243/stade-de-reims"
    },
    "Strasbourg": {
        "results": "https://www.espn.com/football/team/results/_/id/180/strasbourg"
    },
    "Toulouse": {
        "results": "https://www.espn.com/football/team/results/_/id/179/toulouse"
    },
    "Atlanta United FC": {
        "results": "https://www.espn.com/football/team/results/_/id/18418/atlanta-united-fc"
    },
    "Austin FC": {
        "results": "https://www.espn.com/football/team/results/_/id/20906/austin-fc"
    },
    "CF Montréal": {
        "results": "https://www.espn.com/football/team/results/_/id/9720/cf-montreal"
    },
    "Charlotte FC": {
        "results": "https://www.espn.com/football/team/results/_/id/21300/charlotte-fc"
    },
    "Chicago Fire FC": {
        "results": "https://www.espn.com/football/team/results/_/id/182/chicago-fire-fc"
    },
    "Colorado Rapids": {
        "results": "https://www.espn.com/football/team/results/_/id/184/colorado-rapids"
    },
    "Columbus Crew": {
        "results": "https://www.espn.com/football/team/results/_/id/183/columbus-crew"
    },
    "D.C. United": {
        "results": "https://www.espn.com/football/team/results/_/id/193/dc-united"
    },
    "FC Cincinnati": {
        "results": "https://www.espn.com/football/team/results/_/id/18267/fc-cincinnati"
    },
    "FC Dallas": {
        "results": "https://www.espn.com/football/team/results/_/id/185/fc-dallas"
    },
    "Houston Dynamo FC": {
        "results": "https://www.espn.com/football/team/results/_/id/6077/houston-dynamo-fc"
    },
    "Inter Miami CF": {
        "results": "https://www.espn.com/football/team/results/_/id/20232/inter-miami-cf"
    },
    "LA Galaxy": {
        "results": "https://www.espn.com/football/team/results/_/id/187/la-galaxy"
    },
    "LAFC": {
        "results": "https://www.espn.com/football/team/results/_/id/18966/lafc"
    },
    "Minnesota United FC": {
        "results": "https://www.espn.com/football/team/results/_/id/17362/minnesota-united-fc"
    },
    "Nashville SC": {
        "results": "https://www.espn.com/football/team/results/_/id/18986/nashville-sc"
    },
    "New England Revolution": {
        "results": "https://www.espn.com/football/team/results/_/id/189/new-england-revolution"
    },
    "New York City FC": {
        "results": "https://www.espn.com/football/team/results/_/id/17606/new-york-city-fc"
    },
    "New York Red Bulls": {
        "results": "https://www.espn.com/football/team/results/_/id/190/new-york-red-bulls"
    },
    "Orlando City SC": {
        "results": "https://www.espn.com/football/team/results/_/id/12011/orlando-city-sc"
    },
    "Philadelphia Union": {
        "results": "https://www.espn.com/football/team/results/_/id/10739/philadelphia-union"
    },
    "Portland Timbers": {
        "results": "https://www.espn.com/football/team/results/_/id/9723/portland-timbers"
    },
    "Real Salt Lake": {
        "results": "https://www.espn.com/football/team/results/_/id/4771/real-salt-lake"
    },
    "San Diego FC": {
        "results": "https://www.espn.com/football/team/results/_/id/22529/san-diego-fc"
    },
    "San Jose Earthquakes": {
        "results": "https://www.espn.com/football/team/results/_/id/191/san-jose-earthquakes"
    },
    "Seattle Sounders FC": {
        "results": "https://www.espn.com/football/team/results/_/id/9726/seattle-sounders-fc"
    },
    "Sporting Kansas City": {
        "results": "https://www.espn.com/football/team/results/_/id/186/sporting-kansas-city"
    },
    "St. Louis CITY SC": {
        "results": "https://www.espn.com/football/team/results/_/id/21812/st-louis-city-sc"
    },
    "Toronto FC": {
        "results": "https://www.espn.com/football/team/results/_/id/7318/toronto-fc"
    },
    "Vancouver Whitecaps": {
        "results": "https://www.espn.com/football/team/results/_/id/9727/vancouver-whitecaps"
    },
    "América": {
        "results": "https://www.espn.com/football/team/results/_/id/227/america"
    },
    "Atlas": {
        "results": "https://www.espn.com/football/team/results/_/id/216/atlas"
    },
    "Atlético de San Luis": {
        "results": "https://www.espn.com/football/team/results/_/id/15720/atletico-de-san-luis"
    },
    "Cruz Azul": {
        "results": "https://www.espn.com/football/team/results/_/id/218/cruz-azul"
    },
    "FC Juarez": {
        "results": "https://www.espn.com/football/team/results/_/id/17851/fc-juarez"
    },
    "Guadalajara": {
        "results": "https://www.espn.com/football/team/results/_/id/219/guadalajara"
    },
    "León": {
        "results": "https://www.espn.com/football/team/results/_/id/228/leon"
    },
    "Mazatlán FC": {
        "results": "https://www.espn.com/football/team/results/_/id/20702/mazatlan-fc"
    },
    "Monterrey": {
        "results": "https://www.espn.com/football/team/results/_/id/220/monterrey"
    },
    "Necaxa": {
        "results": "https://www.espn.com/football/team/results/_/id/229/necaxa"
    },
    "Pachuca": {
        "results": "https://www.espn.com/football/team/results/_/id/234/pachuca"
    },
    "Puebla": {
        "results": "https://www.espn.com/football/team/results/_/id/231/puebla"
    },
    "Pumas UNAM": {
        "results": "https://www.espn.com/football/team/results/_/id/233/pumas-unam"
    },
    "Querétaro": {
        "results": "https://www.espn.com/football/team/results/_/id/222/queretaro"
    },
    "Santos": {
        "results": "https://www.espn.com/football/team/results/_/id/225/santos"
    },
    "Tigres UANL": {
        "results": "https://www.espn.com/football/team/results/_/id/232/tigres-uanl"
    },
    "Tijuana": {
        "results": "https://www.espn.com/football/team/results/_/id/10125/tijuana"
    },
    "Toluca": {
        "results": "https://www.espn.com/football/team/results/_/id/223/toluca"
    },
    "AZ Alkmaar": {
        "results": "https://www.espn.com/football/team/results/_/id/140/az-alkmaar"
    },
    "Ajax Amsterdam": {
        "results": "https://www.espn.com/football/team/results/_/id/139/ajax-amsterdam"
    },
    "Almere City": {
        "results": "https://www.espn.com/football/team/results/_/id/5291/almere-city"
    },
    "FC Groningen": {
        "results": "https://www.espn.com/football/team/results/_/id/145/fc-groningen"
    },
    "FC Twente": {
        "results": "https://www.espn.com/football/team/results/_/id/152/fc-twente"
    },
    "FC Utrecht": {
        "results": "https://www.espn.com/football/team/results/_/id/153/fc-utrecht"
    },
    "Feyenoord Rotterdam": {
        "results": "https://www.espn.com/football/team/results/_/id/142/feyenoord-rotterdam"
    },
    "Fortuna Sittard": {
        "results": "https://www.espn.com/football/team/results/_/id/143/fortuna-sittard"
    },
    "Go Ahead Eagles": {
        "results": "https://www.espn.com/football/team/results/_/id/3706/go-ahead-eagles"
    },
    "Heerenveen": {
        "results": "https://www.espn.com/football/team/results/_/id/146/heerenveen"
    },
    "Heracles Almelo": {
        "results": "https://www.espn.com/football/team/results/_/id/3708/heracles-almelo"
    },
    "NAC Breda": {
        "results": "https://www.espn.com/football/team/results/_/id/141/nac-breda"
    },
    "NEC Nijmegen": {
        "results": "https://www.espn.com/football/team/results/_/id/147/nec-nijmegen"
    },
    "PEC Zwolle": {
        "results": "https://www.espn.com/football/team/results/_/id/2565/pec-zwolle"
    },
    "PSV Eindhoven": {
        "results": "https://www.espn.com/football/team/results/_/id/148/psv-eindhoven"
    },
    "RKC Waalwijk": {
        "results": "https://www.espn.com/football/team/results/_/id/155/rkc-waalwijk"
    },
    "Sparta Rotterdam": {
        "results": "https://www.espn.com/football/team/results/_/id/151/sparta-rotterdam"
    },
    "Willem II": {
        "results": "https://www.espn.com/football/team/results/_/id/156/willem-ii"
    },
    "AVS": {
        "results": "https://www.espn.com/football/team/results/_/id/22064/avs"
    },
    "Arouca": {
        "results": "https://www.espn.com/football/team/results/_/id/15784/arouca"
    },
    "Benfica": {
        "results": "https://www.espn.com/football/team/results/_/id/1929/benfica"
    },
    "Boavista": {
        "results": "https://www.espn.com/football/team/results/_/id/2256/boavista"
    },
    "Braga": {
        "results": "https://www.espn.com/football/team/results/_/id/2994/braga"
    },
    "C.D. Nacional": {
        "results": "https://www.espn.com/football/team/results/_/id/3472/cd-nacional"
    },
    "Casa Pia": {
        "results": "https://www.espn.com/football/team/results/_/id/21581/casa-pia"
    },
    "Estoril": {
        "results": "https://www.espn.com/football/team/results/_/id/12216/estoril"
    },
    "Estrela": {
        "results": "https://www.espn.com/football/team/results/_/id/21610/estrela"
    },
    "FC Famalicao": {
        "results": "https://www.espn.com/football/team/results/_/id/12698/fc-famalicao"
    },
    "FC Porto": {
        "results": "https://www.espn.com/football/team/results/_/id/437/fc-porto"
    },
    "Gil Vicente": {
        "results": "https://www.espn.com/football/team/results/_/id/3699/gil-vicente"
    },
    "Guimaraes": {
        "results": "https://www.espn.com/football/team/results/_/id/5309/guimaraes"
    },
    "Moreirense": {
        "results": "https://www.espn.com/football/team/results/_/id/3696/moreirense"
    },
    "Rio Ave": {
        "results": "https://www.espn.com/football/team/results/_/id/3822/rio-ave"
    },
    "SC Farense": {
        "results": "https://www.espn.com/football/team/results/_/id/20740/sc-farense"
    },
    "Santa Clara": {
        "results": "https://www.espn.com/football/team/results/_/id/12215/santa-clara"
    },
    "Sporting CP": {
        "results": "https://www.espn.com/football/team/results/_/id/2250/sporting-cp"
    },
    "Al Ahli": {
        "results": "https://www.espn.com/football/team/results/_/id/8346/al-ahli"
    },
    "Al Ettifaq": {
        "results": "https://www.espn.com/football/team/results/_/id/8363/al-ettifaq"
    },
    "Al Fateh": {
        "results": "https://www.espn.com/football/team/results/_/id/13033/al-fateh"
    },
    "Al Fayha": {
        "results": "https://www.espn.com/football/team/results/_/id/21827/al-fayha"
    },
    "Al Hilal": {
        "results": "https://www.espn.com/football/team/results/_/id/929/al-hilal"
    },
    "Al Ittihad": {
        "results": "https://www.espn.com/football/team/results/_/id/2276/al-ittihad"
    },
    "Al Khaleej": {
        "results": "https://www.espn.com/football/team/results/_/id/21829/al-khaleej"
    },
    "Al Kholood": {
        "results": "https://www.espn.com/football/team/results/_/id/22028/al-kholood"
    },
    "Al Nassr": {
        "results": "https://www.espn.com/football/team/results/_/id/817/al-nassr"
    },
    "Al Okhdood": {
        "results": "https://www.espn.com/football/team/results/_/id/21966/al-okhdood"
    },
    "Al Orobah": {
        "results": "https://www.espn.com/football/team/results/_/id/22029/al-orobah"
    },
    "Al Qadsiah": {
        "results": "https://www.espn.com/football/team/results/_/id/22022/al-qadsiah"
    },
    "Al Raed": {
        "results": "https://www.espn.com/football/team/results/_/id/21834/al-raed"
    },
    "Al Riyadh": {
        "results": "https://www.espn.com/football/team/results/_/id/21965/al-riyadh"
    },
    "Al Shabab": {
        "results": "https://www.espn.com/football/team/results/_/id/793/al-shabab"
    },
    "Al Taawoun": {
        "results": "https://www.espn.com/football/team/results/_/id/18459/al-taawoun"
    },
    "Al Wehda": {
        "results": "https://www.espn.com/football/team/results/_/id/21835/al-wehda"
    },
    "Damac": {
        "results": "https://www.espn.com/football/team/results/_/id/21828/damac"
    },
    "Beijing Guoan": {
        "results": "https://www.espn.com/football/team/results/_/id/2052/beijing-guoan"
    },
    "Changchun Yatai": {
        "results": "https://www.espn.com/football/team/results/_/id/8225/changchun-yatai"
    },
    "Chengdu Rongcheng": {
        "results": "https://www.espn.com/football/team/results/_/id/21355/chengdu-rongcheng"
    },
    "Dalian Yingbo": {
        "results": "https://www.espn.com/football/team/results/_/id/22537/dalian-yingbo"
    },
    "Henan Songshan Longmen": {
        "results": "https://www.espn.com/football/team/results/_/id/8240/henan-songshan-longmen"
    },
    "Meizhou Hakka": {
        "results": "https://www.espn.com/football/team/results/_/id/21507/meizhou-hakka"
    },
    "Qingdao Hainiu": {
        "results": "https://www.espn.com/football/team/results/_/id/21910/qingdao-hainiu"
    },
    "Qingdao West Coast": {
        "results": "https://www.espn.com/football/team/results/_/id/22198/qingdao-west-coast"
    },
    "Shandong Taishan": {
        "results": "https://www.espn.com/football/team/results/_/id/7521/shandong-taishan"
    },
    "Shanghai Port": {
        "results": "https://www.espn.com/football/team/results/_/id/15515/shanghai-port"
    },
    "Shanghai Shenhua": {
        "results": "https://www.espn.com/football/team/results/_/id/977/shanghai-shenhua"
    },
    "Shenzhen Xinpengcheng": {
        "results": "https://www.espn.com/football/team/results/_/id/22199/shenzhen-xinpengcheng"
    },
    "Tianjin Jinmen Tiger": {
        "results": "https://www.espn.com/football/team/results/_/id/8239/tianjin-jinmen-tiger"
    },
    "Wuhan Three Towns": {
        "results": "https://www.espn.com/football/team/results/_/id/21506/wuhan-three-towns"
    },
    "Yunnan Yukun": {
        "results": "https://www.espn.com/football/team/results/_/id/22536/yunnan-yukun"
    },
    "Zhejiang Professional FC": {
        "results": "https://www.espn.com/football/team/results/_/id/18203/zhejiang-professional-fc"
    },
    "Albirex Niigata": {
        "results": "https://www.espn.com/football/team/results/_/id/7113/albirex-niigata"
    },
    "Avispa Fukuoka": {
        "results": "https://www.espn.com/football/team/results/_/id/7107/avispa-fukuoka"
    },
    "Cerezo Osaka": {
        "results": "https://www.espn.com/football/team/results/_/id/7109/cerezo-osaka"
    },
    "FC Tokyo": {
        "results": "https://www.espn.com/football/team/results/_/id/3384/fc-tokyo"
    },
    "Fagiano Okayama": {
        "results": "https://www.espn.com/football/team/results/_/id/22522/fagiano-okayama"
    },
    "Gamba Osaka": {
        "results": "https://www.espn.com/football/team/results/_/id/7102/gamba-osaka"
    },
    "Kashima Antlers": {
        "results": "https://www.espn.com/football/team/results/_/id/7115/kashima-antlers"
    },
    "Kashiwa Reysol": {
        "results": "https://www.espn.com/football/team/results/_/id/7476/kashiwa-reysol"
    },
    "Kawasaki Frontale": {
        "results": "https://www.espn.com/football/team/results/_/id/7112/kawasaki-frontale"
    },
    "Kyoto Sanga": {
        "results": "https://www.espn.com/football/team/results/_/id/21361/kyoto-sanga"
    },
    "Machida Zelvia": {
        "results": "https://www.espn.com/football/team/results/_/id/22167/machida-zelvia"
    },
    "Nagoya Grampus": {
        "results": "https://www.espn.com/football/team/results/_/id/7108/nagoya-grampus"
    },
    "Sanfrecce Hiroshima": {
        "results": "https://www.espn.com/football/team/results/_/id/7114/sanfrecce-hiroshima"
    },
    "Shimizu S-Pulse": {
        "results": "https://www.espn.com/football/team/results/_/id/7104/shimizu-s-pulse"
    },
    "Shonan Bellmare": {
        "results": "https://www.espn.com/football/team/results/_/id/6902/shonan-bellmare"
    },
    "Tokyo Verdy 1969": {
        "results": "https://www.espn.com/football/team/results/_/id/3393/tokyo-verdy-1969"
    },
    "Urawa Red Diamonds": {
        "results": "https://www.espn.com/football/team/results/_/id/3385/urawa-red-diamonds"
    },
    "Vissel Kobe": {
        "results": "https://www.espn.com/football/team/results/_/id/7477/vissel-kobe"
    },
    "Yokohama F. Marinos": {
        "results": "https://www.espn.com/football/team/results/_/id/7116/yokohama-f-marinos"
    },
    "Yokohama FC": {
        "results": "https://www.espn.com/football/team/results/_/id/7145/yokohama-fc"
    },
    "Beitar Jerusalem": {
        "results": "https://www.espn.com/football/team/results/_/id/5218/beitar-jerusalem"
    },
    "Bnei Sakhnin": {
        "results": "https://www.espn.com/football/team/results/_/id/8329/bnei-sakhnin"
    },
    "Hapoel Be'er": {
        "results": "https://www.espn.com/football/team/results/_/id/13083/hapoel-beer"
    },
    "Hapoel Hadera": {
        "results": "https://www.espn.com/football/team/results/_/id/19255/hapoel-hadera"
    },
    "Hapoel Haifa": {
        "results": "https://www.espn.com/football/team/results/_/id/9577/hapoel-haifa"
    },
    "Hapoel Jerusalem": {
        "results": "https://www.espn.com/football/team/results/_/id/20970/hapoel-jerusalem"
    },
    "Hapoel Kiryat Shmona": {
        "results": "https://www.espn.com/football/team/results/_/id/8327/hapoel-kiryat-shmona"
    },
    "Ironi Tiberias": {
        "results": "https://www.espn.com/football/team/results/_/id/22311/ironi-tiberias"
    },
    "Maccabi Haifa": {
        "results": "https://www.espn.com/football/team/results/_/id/611/maccabi-haifa"
    },
    "Maccabi Netanya": {
        "results": "https://www.espn.com/football/team/results/_/id/5945/maccabi-netanya"
    },
    "Maccabi Petah-Tikva": {
        "results": "https://www.espn.com/football/team/results/_/id/2983/maccabi-petah-tikva"
    },
    "Maccabi Raina": {
        "results": "https://www.espn.com/football/team/results/_/id/21517/maccabi-raina"
    },
    "Maccabi Tel-Aviv": {
        "results": "https://www.espn.com/football/team/results/_/id/524/maccabi-tel-aviv"
    },
    "Moadon Sport Ashdod": {
        "results": "https://www.espn.com/football/team/results/_/id/5269/moadon-sport-ashdod"
    },
    "AEK Athens": {
        "results": "https://www.espn.com/football/team/results/_/id/887/aek-athens"
    },
    "Aris": {
        "results": "https://www.espn.com/football/team/results/_/id/11553/aris"
    },
    "Asteras Tripoli": {
        "results": "https://www.espn.com/football/team/results/_/id/8354/asteras-tripoli"
    },
    "Athens Kallithea": {
        "results": "https://www.espn.com/football/team/results/_/id/22325/athens-kallithea"
    },
    "Atromitos": {
        "results": "https://www.espn.com/football/team/results/_/id/6790/atromitos"
    },
    "Lamia": {
        "results": "https://www.espn.com/football/team/results/_/id/18814/lamia"
    },
    "Levadiakos": {
        "results": "https://www.espn.com/football/team/results/_/id/5276/levadiakos"
    },
    "OFI Crete": {
        "results": "https://www.espn.com/football/team/results/_/id/1010/ofi-crete"
    },
    "Olympiacos": {
        "results": "https://www.espn.com/football/team/results/_/id/435/olympiacos"
    },
    "PAOK Salonika": {
        "results": "https://www.espn.com/football/team/results/_/id/605/paok-salonika"
    },
    "Panathinaikos": {
        "results": "https://www.espn.com/football/team/results/_/id/443/panathinaikos"
    },
    "Panetolikos": {
        "results": "https://www.espn.com/football/team/results/_/id/11431/panetolikos"
    },
    "Panserraikos FC": {
        "results": "https://www.espn.com/football/team/results/_/id/21970/panserraikos-fc"
    },
    "Volos NFC": {
        "results": "https://www.espn.com/football/team/results/_/id/20043/volos-nfc"
    },
    "Anderlecht": {
        "results": "https://www.espn.com/football/team/results/_/id/441/anderlecht"
    },
    "Antwerp": {
        "results": "https://www.espn.com/football/team/results/_/id/17544/antwerp"
    },
    "Beerschot": {
        "results": "https://www.espn.com/football/team/results/_/id/991/beerschot"
    },
    "Cercle Brugge KSV": {
        "results": "https://www.espn.com/football/team/results/_/id/3610/cercle-brugge-ksv"
    },
    "Club Brugge": {
        "results": "https://www.espn.com/football/team/results/_/id/570/club-brugge"
    },
    "Dender": {
        "results": "https://www.espn.com/football/team/results/_/id/7878/dender"
    },
    "KAA Gent": {
        "results": "https://www.espn.com/football/team/results/_/id/3611/kaa-gent"
    },
    "KV Kortrijk": {
        "results": "https://www.espn.com/football/team/results/_/id/5786/kv-kortrijk"
    },
    "KV Mechelen": {
        "results": "https://www.espn.com/football/team/results/_/id/7879/kv-mechelen"
    },
    "KVC Westerlo": {
        "results": "https://www.espn.com/football/team/results/_/id/606/kvc-westerlo"
    },
    "Oud-Heverlee Leuven": {
        "results": "https://www.espn.com/football/team/results/_/id/5579/oud-heverlee-leuven"
    },
    "Racing Genk": {
        "results": "https://www.espn.com/football/team/results/_/id/938/racing-genk"
    },
    "Royal Charleroi SC": {
        "results": "https://www.espn.com/football/team/results/_/id/3616/royal-charleroi-sc"
    },
    "Sint-Truidense": {
        "results": "https://www.espn.com/football/team/results/_/id/936/sint-truidense"
    },
    "Standard Liege": {
        "results": "https://www.espn.com/football/team/results/_/id/559/standard-liege"
    },
    "Union St.-Gilloise": {
        "results": "https://www.espn.com/football/team/results/_/id/5807/union-st-gilloise"
    },
    "Akhmat Grozny": {
        "results": "https://www.espn.com/football/team/results/_/id/2991/akhmat-grozny"
    },
    "Akron Tolyatti": {
        "results": "https://www.espn.com/football/team/results/_/id/22271/akron-tolyatti"
    },
    "CSKA Moscow": {
        "results": "https://www.espn.com/football/team/results/_/id/1963/cska-moscow"
    },
    "Dinamo Moscow": {
        "results": "https://www.espn.com/football/team/results/_/id/596/dinamo-moscow"
    },
    "Dynamo Makhachkala": {
        "results": "https://www.espn.com/football/team/results/_/id/22300/dynamo-makhachkala"
    },
    "FC Khimki": {
        "results": "https://www.espn.com/football/team/results/_/id/7424/fc-khimki"
    },
    "Fakel Voronezh": {
        "results": "https://www.espn.com/football/team/results/_/id/21539/fakel-voronezh"
    },
    "Gazovik Orenburg": {
        "results": "https://www.espn.com/football/team/results/_/id/18285/gazovik-orenburg"
    },
    "Krasnodar": {
        "results": "https://www.espn.com/football/team/results/_/id/11336/krasnodar"
    },
    "Krylia Sovetov": {
        "results": "https://www.espn.com/football/team/results/_/id/3850/krylia-sovetov"
    },
    "Lokomotiv Moscow": {
        "results": "https://www.espn.com/football/team/results/_/id/442/lokomotiv-moscow"
    },
    "Nizhny Novgorod": {
        "results": "https://www.espn.com/football/team/results/_/id/13150/nizhny-novgorod"
    },
    "Rostov": {
        "results": "https://www.espn.com/football/team/results/_/id/3852/rostov"
    },
    "Rubin Kazan": {
        "results": "https://www.espn.com/football/team/results/_/id/3851/rubin-kazan"
    },
    "Spartak Moscow": {
        "results": "https://www.espn.com/football/team/results/_/id/1941/spartak-moscow"
    },
    "Zenit St Petersburg": {
        "results": "https://www.espn.com/football/team/results/_/id/2533/zenit-st-petersburg"
    },
    "FC Basel": {
        "results": "https://www.espn.com/football/team/results/_/id/989/fc-basel"
    },
    "FC Lugano": {
        "results": "https://www.espn.com/football/team/results/_/id/7672/fc-lugano"
    },
    "FC Luzern": {
        "results": "https://www.espn.com/football/team/results/_/id/7640/fc-luzern"
    },
    "FC Sion": {
        "results": "https://www.espn.com/football/team/results/_/id/3076/fc-sion"
    },
    "FC Zürich": {
        "results": "https://www.espn.com/football/team/results/_/id/3019/fc-zurich"
    },
    "Grasshoppers": {
        "results": "https://www.espn.com/football/team/results/_/id/492/grasshoppers"
    },
    "Lausanne Sports": {
        "results": "https://www.espn.com/football/team/results/_/id/11551/lausanne-sports"
    },
    "Servette": {
        "results": "https://www.espn.com/football/team/results/_/id/20032/servette"
    },
    "St. Gallen": {
        "results": "https://www.espn.com/football/team/results/_/id/557/st-gallen"
    },
    "Winterthur": {
        "results": "https://www.espn.com/football/team/results/_/id/20996/winterthur"
    },
    "Young Boys": {
        "results": "https://www.espn.com/football/team/results/_/id/2722/young-boys"
    },
    "Yverdon": {
        "results": "https://www.espn.com/football/team/results/_/id/21538/yverdon"
    },
    "Adana Demirspor": {
        "results": "https://www.espn.com/football/team/results/_/id/20765/adana-demirspor"
    },
    "Alanyaspor": {
        "results": "https://www.espn.com/football/team/results/_/id/9078/alanyaspor"
    },
    "Antalyaspor": {
        "results": "https://www.espn.com/football/team/results/_/id/3794/antalyaspor"
    },
    "Besiktas": {
        "results": "https://www.espn.com/football/team/results/_/id/1895/besiktas"
    },
    "Bodrum FK": {
        "results": "https://www.espn.com/football/team/results/_/id/22321/bodrum-fk"
    },
    "Caykur Rizespor": {
        "results": "https://www.espn.com/football/team/results/_/id/7656/caykur-rizespor"
    },
    "Eyupspor": {
        "results": "https://www.espn.com/football/team/results/_/id/20729/eyupspor"
    },
    "Fenerbahce": {
        "results": "https://www.espn.com/football/team/results/_/id/436/fenerbahce"
    },
    "Galatasaray": {
        "results": "https://www.espn.com/football/team/results/_/id/432/galatasaray"
    },
    "Gaziantep FK": {
        "results": "https://www.espn.com/football/team/results/_/id/20070/gaziantep-fk"
    },
    "Goztepe": {
        "results": "https://www.espn.com/football/team/results/_/id/789/goztepe"
    },
    "Hatayspor": {
        "results": "https://www.espn.com/football/team/results/_/id/20737/hatayspor"
    },
    "Istanbul Basaksehir": {
        "results": "https://www.espn.com/football/team/results/_/id/7914/istanbul-basaksehir"
    },
    "Kasimpasa": {
        "results": "https://www.espn.com/football/team/results/_/id/6870/kasimpasa"
    },
    "Kayserispor": {
        "results": "https://www.espn.com/football/team/results/_/id/3643/kayserispor"
    },
    "Konyaspor": {
        "results": "https://www.espn.com/football/team/results/_/id/7648/konyaspor"
    },
    "Samsunspor": {
        "results": "https://www.espn.com/football/team/results/_/id/11429/samsunspor"
    },
    "Sivasspor": {
        "results": "https://www.espn.com/football/team/results/_/id/3691/sivasspor"
    },
    "Trabzonspor": {
        "results": "https://www.espn.com/football/team/results/_/id/997/trabzonspor"
    },
    "Alianza FC": {
            "results": "https://www.espn.com/football/team/results/_/id/9761/alianza-fc"
        },
        "América de Cali": {
            "results": "https://www.espn.com/football/team/results/_/id/8109/america-de-cali"
        },
        "Atlético Junior": {
            "results": "https://www.espn.com/football/team/results/_/id/4815/atletico-junior"
        },
        "Atlético Nacional": {
            "results": "https://www.espn.com/football/team/results/_/id/5264/atletico-nacional"
        },
        "Boyacá Chicó": {
            "results": "https://www.espn.com/football/team/results/_/id/5480/boyaca-chico"
        },
        "Bucaramanga": {
            "results": "https://www.espn.com/football/team/results/_/id/6137/bucaramanga"
        },
        "Deportes Tolima": {
            "results": "https://www.espn.com/football/team/results/_/id/5489/deportes-tolima"
        },
        "Deportivo Cali": {
            "results": "https://www.espn.com/football/team/results/_/id/2672/deportivo-cali"
        },
        "Deportivo Pasto": {
            "results": "https://www.espn.com/football/team/results/_/id/5485/deportivo-pasto"
        },
        "Deportivo Pereira": {
            "results": "https://www.espn.com/football/team/results/_/id/5486/deportivo-pereira"
        },
        "Envigado": {
            "results": "https://www.espn.com/football/team/results/_/id/5481/envigado"
        },
        "Fortaleza CEIF": {
            "results": "https://www.espn.com/football/team/results/_/id/4928/fortaleza-ceif"
        },
        "Independiente Medellín": {
            "results": "https://www.espn.com/football/team/results/_/id/2690/independiente-medellin"
        },
        "Independiente Santa Fe": {
            "results": "https://www.espn.com/football/team/results/_/id/5488/independiente-santa-fe"
        },
        "La Equidad": {
            "results": "https://www.espn.com/football/team/results/_/id/7445/la-equidad"
        },
        "Llaneros": {
            "results": "https://www.espn.com/football/team/results/_/id/7915/llaneros"
        },
        "Millonarios": {
            "results": "https://www.espn.com/football/team/results/_/id/5484/millonarios"
        },
        "Once Caldas": {
            "results": "https://www.espn.com/football/team/results/_/id/2919/once-caldas"
        },
        "Unión Magdalena": {
            "results": "https://www.espn.com/football/team/results/_/id/17374/union-magdalena"
        },
        "Águilas Doradas": {
            "results": "https://www.espn.com/football/team/results/_/id/9762/aguilas-doradas"
        },
        "Amazonas": {
            "results": "https://africa.espn.com/football/team/results/_/id/21888/amazonas"
        },
        "America Mineiro": {
            "results": "https://africa.espn.com/football/team/results/_/id/6154/america-mineiro"
        },
        "Athletic": {
            "results": "https://africa.espn.com/football/team/results/_/id/20851/athletic"
        },
        "Athletico Paranaense": {
            "results": "https://africa.espn.com/football/team/results/_/id/3458/athletico-paranaense"
        },
        "Atletico Goianiense": {
            "results": "https://africa.espn.com/football/team/results/_/id/10357/atletico-goianiense"
        },
        "Avai": {
            "results": "https://africa.espn.com/football/team/results/_/id/9966/avai"
        },
        "Botafogo Sp": {
            "results": "https://africa.espn.com/football/team/results/_/id/10281/botafogo-sp"
        },
        "Crb": {
            "results": "https://africa.espn.com/football/team/results/_/id/9970/crb"
        },
        "Chapecoense": {
            "results": "https://africa.espn.com/football/team/results/_/id/9318/chapecoense"
        },
        "Coritiba": {
            "results": "https://africa.espn.com/football/team/results/_/id/3456/coritiba"
        },
        "Criciuma": {
            "results": "https://africa.espn.com/football/team/results/_/id/9971/criciuma"
        },
        "Cuiabá": {
            "results": "https://africa.espn.com/football/team/results/_/id/17313/cuiaba"
        },
        "Ferroviária": {
            "results": "https://africa.espn.com/football/team/results/_/id/18126/ferroviaria"
        },
        "Goiás": {
            "results": "https://africa.espn.com/football/team/results/_/id/3395/goias"
        },
        "Novorizontino": {
            "results": "https://africa.espn.com/football/team/results/_/id/18127/novorizontino"
        },
        "Operario PR": {
            "results": "https://africa.espn.com/football/team/results/_/id/18187/operario-pr"
        },
        "Paysandu": {
            "results": "https://africa.espn.com/football/team/results/_/id/15424/paysandu"
        },
        "Remo": {
            "results": "https://africa.espn.com/football/team/results/_/id/4936/remo"
        },
        "Vila Nova": {
            "results": "https://africa.espn.com/football/team/results/_/id/9973/vila-nova"
        },
        "Volta Redonda": {
            "results": "https://africa.espn.com/football/team/results/_/id/4806/volta-redonda"
        },
        "Audax Italiano": {
            "results": "https://africa.espn.com/football/team/results/_/id/4138/audax-italiano"
        },
        "Cobresal": {
            "results": "https://africa.espn.com/football/team/results/_/id/4133/cobresal"
        },
        "Colo Colo": {
            "results": "https://africa.espn.com/football/team/results/_/id/2688/colo-colo"
        },
        "Coquimbo Unido": {
            "results": "https://africa.espn.com/football/team/results/_/id/8186/coquimbo-unido"
        },
        "Deportes Iquique": {
            "results": "https://africa.espn.com/football/team/results/_/id/10142/deportes-iquique"
        },
        "Deportes Limache": {
            "results": "https://africa.espn.com/football/team/results/_/id/19195/deportes-limache"
        },
        "Everton Cd": {
            "results": "https://africa.espn.com/football/team/results/_/id/4129/everton-cd"
        },
        "Huachipato": {
            "results": "https://africa.espn.com/football/team/results/_/id/4134/huachipato"
        },
        "La Serena": {
            "results": "https://africa.espn.com/football/team/results/_/id/4137/la-serena"
        },
        "Ohiggins": {
            "results": "https://africa.espn.com/football/team/results/_/id/6072/ohiggins"
        },
        "Palestino": {
            "results": "https://africa.espn.com/football/team/results/_/id/4422/palestino"
        },
        "Universidad Catolica": {
            "results": "https://africa.espn.com/football/team/results/_/id/885/universidad-catolica"
        },
        "Universidad De Chile": {
            "results": "https://africa.espn.com/football/team/results/_/id/4139/universidad-de-chile"
        },
        "Union Espanola": {
            "results": "https://africa.espn.com/football/team/results/_/id/4132/union-espanola"
        },
        "Union La Calera": {
            "results": "https://africa.espn.com/football/team/results/_/id/10144/union-la-calera"
        },
        "Nublense": {
            "results": "https://africa.espn.com/football/team/results/_/id/7427/nublense"
        },
        "ADT": {
            "results": "https://africa.espn.com/football/team/results/_/id/21314/adt"
        },
        "Alianza Atletico": {
            "results": "https://africa.espn.com/football/team/results/_/id/5267/alianza-atletico"
        },
        "Alianza Lima": {
            "results": "https://africa.espn.com/football/team/results/_/id/2680/alianza-lima"
        },
        "Alianza Universidad": {
            "results": "https://africa.espn.com/football/team/results/_/id/19432/alianza-universidad"
        },
        "Atletico Grau": {
            "results": "https://africa.espn.com/football/team/results/_/id/20293/atletico-grau"
        },
        "Ayacucho Fc": {
            "results": "https://africa.espn.com/football/team/results/_/id/10116/ayacucho-fc"
        },
        "Cienciano Del Cusco": {
            "results": "https://africa.espn.com/football/team/results/_/id/3372/cienciano-del-cusco"
        },
        "Comerciantes Unidos": {
            "results": "https://africa.espn.com/football/team/results/_/id/18153/comerciantes-unidos"
        },
        "Cusco Fc": {
            "results": "https://africa.espn.com/football/team/results/_/id/11995/cusco-fc"
        },
        "Deportivo Binacional": {
            "results": "https://africa.espn.com/football/team/results/_/id/18985/deportivo-binacional"
        },
        "Deportivo Garcilaso": {
            "results": "https://africa.espn.com/football/team/results/_/id/21819/deportivo-garcilaso"
        },
        "Juan Pablo Ii": {
            "results": "https://africa.espn.com/football/team/results/_/id/22534/juan-pablo-ii"
        },
        "Los Chankas": {
            "results": "https://africa.espn.com/football/team/results/_/id/22168/los-chankas"
        },
        "Melgar": {
            "results": "https://africa.espn.com/football/team/results/_/id/7312/melgar"
        },
        "Sport Boys": {
            "results": "https://africa.espn.com/football/team/results/_/id/5570/sport-boys"
        },
        "Sport Huancayo": {
            "results": "https://africa.espn.com/football/team/results/_/id/10318/sport-huancayo"
        },
        "Sporting Cristal": {
            "results": "https://africa.espn.com/football/team/results/_/id/2673/sporting-cristal"
        },
        "Utc": {
            "results": "https://africa.espn.com/football/team/results/_/id/10122/utc"
        },
        "Universitario": {
            "results": "https://africa.espn.com/football/team/results/_/id/2685/universitario"
        },
        "Austria Vienna": {
            "results": "https://africa.espn.com/football/team/results/_/id/1382/austria-vienna"
        },
        "Fc Blau Weiß Linz": {
            "results": "https://africa.espn.com/football/team/results/_/id/21950/fc-blau-weiß-linz"
        },
        "Grazer Ak": {
            "results": "https://africa.espn.com/football/team/results/_/id/21846/grazer-ak"
        },
        "Lask Linz": {
            "results": "https://africa.espn.com/football/team/results/_/id/4411/lask-linz"
        },
        "Rb Salzburg": {
            "results": "https://africa.espn.com/football/team/results/_/id/2790/rb-salzburg"
        },
        "Rapid Vienna": {
            "results": "https://africa.espn.com/football/team/results/_/id/519/rapid-vienna"
        },
        "Sc Rheindorf Altach": {
            "results": "https://africa.espn.com/football/team/results/_/id/4405/sc-rheindorf-altach"
        },
        "Sk Sturm Graz": {
            "results": "https://africa.espn.com/football/team/results/_/id/3746/sk-sturm-graz"
        },
        "Sv Josko Ried": {
            "results": "https://africa.espn.com/football/team/results/_/id/3759/sv-josko-ried"
        },
        "Tsv Hartberg": {
            "results": "https://africa.espn.com/football/team/results/_/id/6907/tsv-hartberg"
        },
        "Wsg Swarovski Tirol": {
            "results": "https://africa.espn.com/football/team/results/_/id/18794/wsg-swarovski-tirol"
        },
        "Wolfsberger": {
            "results": "https://africa.espn.com/football/team/results/_/id/13294/wolfsberger"
        },
        "Aik": {
            "results": "https://africa.espn.com/football/team/results/_/id/994/aik"
        },
        "Bk Hacken": {
            "results": "https://africa.espn.com/football/team/results/_/id/7834/bk-hacken"
        },
        "Degerfors If": {
            "results": "https://africa.espn.com/football/team/results/_/id/20856/degerfors-if"
        },
        "Djurgarden": {
            "results": "https://africa.espn.com/football/team/results/_/id/2339/djurgarden"
        },
        "Gais": {
            "results": "https://africa.espn.com/football/team/results/_/id/8222/gais"
        },
        "Halmstads Bk": {
            "results": "https://africa.espn.com/football/team/results/_/id/3017/halmstads-bk"
        },
        "Hammarby If": {
            "results": "https://africa.espn.com/football/team/results/_/id/2495/hammarby-if"
        },
        "If Brommapojkarna": {
            "results": "https://africa.espn.com/football/team/results/_/id/8221/if-brommapojkarna"
        },
        "If Elfsborg": {
            "results": "https://africa.espn.com/football/team/results/_/id/529/if-elfsborg"
        },
        "Ifk Goteborg": {
            "results": "https://africa.espn.com/football/team/results/_/id/2556/ifk-goteborg"
        },
        "Ifk Norrkoping": {
            "results": "https://africa.espn.com/football/team/results/_/id/8544/ifk-norrkoping"
        },
        "Ifk Varnamo": {
            "results": "https://africa.espn.com/football/team/results/_/id/21382/ifk-varnamo"
        },
        "Ik Sirius": {
            "results": "https://africa.espn.com/football/team/results/_/id/8547/ik-sirius"
        },
        "Malmo Ff": {
            "results": "https://africa.espn.com/football/team/results/_/id/2720/malmo-ff"
        },
        "Mjallby Aif": {
            "results": "https://africa.espn.com/football/team/results/_/id/20301/mjallby-aif"
        },
        "Osters If": {
            "results": "https://africa.espn.com/football/team/results/_/id/2936/osters-if"
        },
        "Agropecuario": {
            "results": "https://africa.espn.com/football/team/results/_/id/13913/agropecuario"
        },
        "All Boys": {
            "results": "https://africa.espn.com/football/team/results/_/id/9786/all-boys"
        },
        "Almagro": {
            "results": "https://africa.espn.com/football/team/results/_/id/2/almagro"
        },
        "Almirante Brown": {
            "results": "https://africa.espn.com/football/team/results/_/id/9740/almirante-brown"
        },
        "Alvarado Mar Del Plata": {
            "results": "https://africa.espn.com/football/team/results/_/id/19143/alvarado-mar-del-plata"
        },
        "Arsenal Sarandi": {
            "results": "https://africa.espn.com/football/team/results/_/id/2635/arsenal-sarandi"
        },
        "Atlanta": {
            "results": "https://africa.espn.com/football/team/results/_/id/10146/atlanta"
        },
        "Central Norte": {
            "results": "https://africa.espn.com/football/team/results/_/id/11993/central-norte"
        },
        "Chacarita Juniors": {
            "results": "https://africa.espn.com/football/team/results/_/id/6/chacarita-juniors"
        },
        "Chaco For Ever": {
            "results": "https://africa.espn.com/football/team/results/_/id/11963/chaco-for-ever"
        },
        "Colegiales": {
            "results": "https://africa.espn.com/football/team/results/_/id/10149/colegiales"
        },
        "Colon Santa Fe": {
            "results": "https://africa.espn.com/football/team/results/_/id/7/colon-santa-fe"
        },
        "Defensores Unidos": {
            "results": "https://africa.espn.com/football/team/results/_/id/17697/defensores-unidos"
        },
        "Defensores De Belgrano": {
            "results": "https://africa.espn.com/football/team/results/_/id/10151/defensores-de-belgrano"
        },
        "Deportivo Madryn": {
            "results": "https://africa.espn.com/football/team/results/_/id/18260/deportivo-madryn"
        },
        "Deportivo Maipu": {
            "results": "https://africa.espn.com/football/team/results/_/id/11978/deportivo-maipu"
        },
        "Deportivo Moron": {
            "results": "https://africa.espn.com/football/team/results/_/id/10154/deportivo-moron"
        },
        "Estudiantes Buenos Aires": {
            "results": "https://africa.espn.com/football/team/results/_/id/17352/estudiantes-buenos-aires"
        },
        "Estudiantes De Rio Cuarto": {
            "results": "https://africa.espn.com/football/team/results/_/id/19685/estudiantes-de-rio-cuarto"
        },
        "Ferro Carril Oeste": {
            "results": "https://africa.espn.com/football/team/results/_/id/9743/ferro-carril-oeste"
        },
        "Gimnasia Mendoza": {
            "results": "https://africa.espn.com/football/team/results/_/id/11972/gimnasia-mendoza"
        },
        "Gimnasia Y Esgrima Jujuy": {
            "results": "https://africa.espn.com/football/team/results/_/id/5263/gimnasia-y-esgrima-jujuy"
        },
        "Gimnasia Y Tiro Salta": {
            "results": "https://africa.espn.com/football/team/results/_/id/10743/gimnasia-y-tiro-salta"
        },
        "Guemes": {
            "results": "https://africa.espn.com/football/team/results/_/id/18284/guemes"
        },
        "Los Andes": {
            "results": "https://africa.espn.com/football/team/results/_/id/13/los-andes"
        },
        "Mitre Santiago Del Estero": {
            "results": "https://africa.espn.com/football/team/results/_/id/11990/mitre-santiago-del-estero"
        },
        "Nueva Chicago": {
            "results": "https://africa.espn.com/football/team/results/_/id/236/nueva-chicago"
        },
        "Patronato": {
            "results": "https://africa.espn.com/football/team/results/_/id/10374/patronato"
        },
        "Quilmes": {
            "results": "https://africa.espn.com/football/team/results/_/id/2741/quilmes"
        },
        "Racing Cordoba": {
            "results": "https://africa.espn.com/football/team/results/_/id/19145/racing-cordoba"
        },
        "San Martin Tucuman": {
            "results": "https://africa.espn.com/football/team/results/_/id/17814/san-martin-tucuman"
        },
        "San Miguel": {
            "results": "https://africa.espn.com/football/team/results/_/id/10058/san-miguel"
        },
        "San Telmo": {
            "results": "https://africa.espn.com/football/team/results/_/id/10157/san-telmo"
        },
        "Talleres": {
            "results": "https://africa.espn.com/football/team/results/_/id/10161/talleres"
        },
        "Temperley": {
            "results": "https://africa.espn.com/football/team/results/_/id/10162/temperley"
        },
        "Tristan Suarez": {
            "results": "https://africa.espn.com/football/team/results/_/id/10163/tristan-suarez"
        },
        "2 de Mayo": {
            "results": "https://africa.espn.com/football/team/results/_/id/6097/2-de-mayo"
        },
        "Cerro Porteno": {
            "results": "https://africa.espn.com/football/team/results/_/id/2671/cerro-porteno"
        },
        "Club Atletico Tembetary": {
            "results": "https://africa.espn.com/football/team/results/_/id/22518/club-atletico-tembetary"
        },
        "Deportivo Recoleta": {
            "results": "https://africa.espn.com/football/team/results/_/id/22517/deportivo-recoleta"
        },
        "General Caballero JLM": {
            "results": "https://africa.espn.com/football/team/results/_/id/21316/general-caballero-jlm"
        },
        "Guarani": {
            "results": "https://africa.espn.com/football/team/results/_/id/7385/guarani"
        },
        "Libertad": {
            "results": "https://africa.espn.com/football/team/results/_/id/2670/libertad"
        },
        "Nacional": {
            "results": "https://africa.espn.com/football/team/results/_/id/5584/nacional"
        },
        "Olimpia": {
            "results": "https://africa.espn.com/football/team/results/_/id/2675/olimpia"
        },
        "Sportivo Ameliano": {
            "results": "https://africa.espn.com/football/team/results/_/id/21313/sportivo-ameliano"
        },
        "Sportivo Luqueño": {
            "results": "https://africa.espn.com/football/team/results/_/id/5583/sportivo-luqueno"
        },
        "Trinidense": {
            "results": "https://africa.espn.com/football/team/results/_/id/7466/trinidense"
        },
        "Academia Anzoategui": {
            "results": "https://africa.espn.com/football/team/results/_/id/13783/academia-anzoategui"
        },
        "Academia Puerto Cabello": {
            "results": "https://africa.espn.com/football/team/results/_/id/18995/academia-puerto-cabello"
        },
        "Carabobo": {
            "results": "https://africa.espn.com/football/team/results/_/id/6037/carabobo"
        },
        "Caracas FC": {
            "results": "https://africa.espn.com/football/team/results/_/id/4811/caracas-fc"
        },
        "Deportivo La Guaira": {
            "results": "https://africa.espn.com/football/team/results/_/id/17090/deportivo-la-guaira"
        },
        "Deportivo Rayo Zuliano": {
            "results": "https://africa.espn.com/football/team/results/_/id/21850/deportivo-rayo-zuliano"
        },
        "Deportivo Tachira": {
            "results": "https://africa.espn.com/football/team/results/_/id/4818/deportivo-tachira"
        },
        "Estudiantes de Merida": {
            "results": "https://africa.espn.com/football/team/results/_/id/6038/estudiantes-de-merida"
        },
        "Metropolitanos Fc": {
            "results": "https://africa.espn.com/football/team/results/_/id/13481/metropolitanos-fc"
        },
        "Monagas Sc": {
            "results": "https://africa.espn.com/football/team/results/_/id/6041/monagas-sc"
        },
        "Portuguesa": {
            "results": "https://africa.espn.com/football/team/results/_/id/6762/portuguesa"
        },
        "Universidad Central": {
            "results": "https://africa.espn.com/football/team/results/_/id/10094/universidad-central"
        },
        "Yaracuyanos": {
            "results": "https://africa.espn.com/football/team/results/_/id/10096/yaracuyanos"
        },
        "Zamora": {
            "results": "https://africa.espn.com/football/team/results/_/id/6763/zamora"
        },
        "Cfr Cluj Napoca": {
            "results": "https://africa.espn.com/football/team/results/_/id/5260/cfr-cluj-napoca"
        },
        "Csu Craiova": {
            "results": "https://africa.espn.com/football/team/results/_/id/8089/csu-craiova"
        },
        "Csikszereda": {
            "results": "https://africa.espn.com/football/team/results/_/id/21032/csikszereda"
        },
        "Dinamo Bucuresti": {
            "results": "https://africa.espn.com/football/team/results/_/id/2496/dinamo-bucuresti"
        },
        "Fc Arges": {
            "results": "https://africa.espn.com/football/team/results/_/id/20725/fc-arges"
        },
        "Fc Botosani": {
            "results": "https://africa.espn.com/football/team/results/_/id/9682/fc-botosani"
        },
        "Fc Farul Constanta": {
            "results": "https://africa.espn.com/football/team/results/_/id/6731/fc-farul-constanta"
        },
        "Fcsb": {
            "results": "https://africa.espn.com/football/team/results/_/id/484/fcsb"
        },
        "Hermannstadt": {
            "results": "https://africa.espn.com/football/team/results/_/id/19265/hermannstadt"
        },
        "Metaloglobus": {
            "results": "https://africa.espn.com/football/team/results/_/id/130880/metaloglobus"
        },
        "Otelul Galati": {
            "results": "https://africa.espn.com/football/team/results/_/id/2942/otelul-galati"
        },
        "Petrolul Ploiesti": {
            "results": "https://africa.espn.com/football/team/results/_/id/12603/petrolul-ploiesti"
        },
        "Rapid Bucuresti": {
            "results": "https://africa.espn.com/football/team/results/_/id/545/rapid-bucuresti"
        },
        "Uta Arad": {
            "results": "https://africa.espn.com/football/team/results/_/id/6912/uta-arad"
        },
        "Unirea Slobozia": {
            "results": "https://africa.espn.com/football/team/results/_/id/22314/unirea-slobozia"
        },
        "Universitatea Cluj": {
            "results": "https://africa.espn.com/football/team/results/_/id/8091/universitatea-cluj"
        },
        "Beitar Jerusalem": {
            "results": "https://africa.espn.com/football/team/results/_/id/5218/beitar-jerusalem"
        },
        "Bnei Sakhnin": {
            "results": "https://africa.espn.com/football/team/results/_/id/8329/bnei-sakhnin"
        },
        "Hapoel Beer": {
            "results": "https://africa.espn.com/football/team/results/_/id/13083/hapoel-beer"
        },
        "Hapoel Hadera": {
            "results": "https://africa.espn.com/football/team/results/_/id/19255/hapoel-hadera"
        },
        "Hapoel Haifa": {
            "results": "https://africa.espn.com/football/team/results/_/id/9577/hapoel-haifa"
        },
        "Hapoel Jerusalem": {
            "results": "https://africa.espn.com/football/team/results/_/id/20970/hapoel-jerusalem"
        },
        "Hapoel Kiryat Shmona": {
            "results": "https://africa.espn.com/football/team/results/_/id/8327/hapoel-kiryat-shmona"
        },
        "Ironi Tiberias": {
            "results": "https://africa.espn.com/football/team/results/_/id/22311/ironi-tiberias"
        },
        "Maccabi Haifa": {
            "results": "https://africa.espn.com/football/team/results/_/id/611/maccabi-haifa"
        },
        "Maccabi Netanya": {
            "results": "https://africa.espn.com/football/team/results/_/id/5945/maccabi-netanya"
        },
        "Maccabi Petah Tikva": {
            "results": "https://africa.espn.com/football/team/results/_/id/2983/maccabi-petah-tikva"
        },
        "Maccabi Raina": {
            "results": "https://africa.espn.com/football/team/results/_/id/21517/maccabi-raina"
        },
        "Maccabi Tel Aviv": {
            "results": "https://africa.espn.com/football/team/results/_/id/524/maccabi-tel-aviv"
        },
        "Moadon Sport Ashdod": {
            "results": "https://africa.espn.com/football/team/results/_/id/5269/moadon-sport-ashdod"
        },
        "Afc Fylde": {
            "results": "https://africa.espn.com/football/team/results/_/id/13884/afc-fylde"
        },
        "Aldershot Town": {
            "results": "https://africa.espn.com/football/team/results/_/id/632/aldershot-town"
        },
        "Altrincham": {
            "results": "https://africa.espn.com/football/team/results/_/id/633/altrincham"
        },
        "Barnet": {
            "results": "https://africa.espn.com/football/team/results/_/id/280/barnet"
        },
        "Boston United": {
            "results": "https://africa.espn.com/football/team/results/_/id/3256/boston-united"
        },
        "Braintree Town": {
            "results": "https://africa.espn.com/football/team/results/_/id/3828/braintree-town"
        },
        "Dagenham Redbridge": {
            "results": "https://africa.espn.com/football/team/results/_/id/275/dagenham-redbridge"
        },
        "Eastleigh": {
            "results": "https://africa.espn.com/football/team/results/_/id/3897/eastleigh"
        },
        "Ebbsfleet United": {
            "results": "https://africa.espn.com/football/team/results/_/id/640/ebbsfleet-united"
        },
        "Fc Halifax Town": {
            "results": "https://africa.espn.com/football/team/results/_/id/312/fc-halifax-town"
        },
        "Forest Green Rovers": {
            "results": "https://africa.espn.com/football/team/results/_/id/282/forest-green-rovers"
        },
        "Gateshead": {
            "results": "https://africa.espn.com/football/team/results/_/id/3138/gateshead"
        },
        "Hartlepool United": {
            "results": "https://africa.espn.com/football/team/results/_/id/323/hartlepool-united"
        },
        "Maidenhead United": {
            "results": "https://africa.espn.com/football/team/results/_/id/7156/maidenhead-united"
        },
        "Oldham Athletic": {
            "results": "https://africa.espn.com/football/team/results/_/id/332/oldham-athletic"
        },
        "Rochdale": {
            "results": "https://africa.espn.com/football/team/results/_/id/303/rochdale"
        },
        "Solihull Moors": {
            "results": "https://africa.espn.com/football/team/results/_/id/13061/solihull-moors"
        },
        "Southend United": {
            "results": "https://africa.espn.com/football/team/results/_/id/310/southend-united"
        },
        "Sutton United": {
            "results": "https://africa.espn.com/football/team/results/_/id/3231/sutton-united"
        },
        "Tamworth": {
            "results": "https://africa.espn.com/football/team/results/_/id/645/tamworth"
        },
        "Wealdstone": {
            "results": "https://africa.espn.com/football/team/results/_/id/3887/wealdstone"
        },
        "Woking": {
            "results": "https://africa.espn.com/football/team/results/_/id/290/woking"
        },
        "Yeovil Town": {
            "results": "https://africa.espn.com/football/team/results/_/id/284/yeovil-town"
        },
        "York City": {
            "results": "https://africa.espn.com/football/team/results/_/id/315/york-city"
        },
        "Aek Athens": {
            "results": "https://africa.espn.com/football/team/results/_/id/887/aek-athens"
        },
        "Aris": {
            "results": "https://africa.espn.com/football/team/results/_/id/11553/aris"
        },
        "Asteras Tripoli": {
            "results": "https://africa.espn.com/football/team/results/_/id/8354/asteras-tripoli"
        },
        "Athens Kallithea": {
            "results": "https://africa.espn.com/football/team/results/_/id/22325/athens-kallithea"
        },
        "Atromitos": {
            "results": "https://africa.espn.com/football/team/results/_/id/6790/atromitos"
        },
        "Lamia": {
            "results": "https://africa.espn.com/football/team/results/_/id/18814/lamia"
        },
        "Levadiakos": {
            "results": "https://africa.espn.com/football/team/results/_/id/5276/levadiakos"
        },
        "Ofi Crete": {
            "results": "https://africa.espn.com/football/team/results/_/id/1010/ofi-crete"
        },
        "Olympiacos": {
            "results": "https://africa.espn.com/football/team/results/_/id/435/olympiacos"
        },
        "Paok Salonika": {
            "results": "https://africa.espn.com/football/team/results/_/id/605/paok-salonika"
        },
        "Panathinaikos": {
            "results": "https://africa.espn.com/football/team/results/_/id/443/panathinaikos"
        },
        "Panetolikos": {
            "results": "https://africa.espn.com/football/team/results/_/id/11431/panetolikos"
        },
        "Panserraikos Fc": {
            "results": "https://africa.espn.com/football/team/results/_/id/21970/panserraikos-fc"
        },
        "Volos Nfc": {
            "results": "https://africa.espn.com/football/team/results/_/id/20043/volos-nfc"
        }
    # Ajoutez d'autres équipes si besoin
}
headers = {'User-Agent': 'Mozilla/5.0'}

PREDICTIONS = []
FAILED_TEAMS = set()
IGNORED_ZERO_FORM_TEAMS = []

def get_match_stats(game_id):
    """
    Récupère les statistiques détaillées d'un match ESPN via son game_id.
    Retourne un dict { "Possession": (home, away), ... }
    """
    url = f"https://africa.espn.com/football/match/_/gameId/{game_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/117.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        stats_section = soup.find("section", {"data-testid": "prism-LayoutCard"})
        stats_divs = stats_section.find_all("div", class_="LOSQp") if stats_section else []
        
        stats = {}
        for div in stats_divs:
            stat_name_tag = div.find("span", class_="OkRBU")
            if not stat_name_tag:
                continue
            stat_name = stat_name_tag.get_text(strip=True)
            values = div.find_all("span", class_="bLeWt")
            if len(values) >= 2:
                team1_value = values[0].get_text(strip=True)
                team2_value = values[1].get_text(strip=True)
                stats[stat_name] = (team1_value, team2_value)

        print(f"📊 Stats récupérées pour match {game_id}: {len(stats)} statistiques trouvées")
        return stats

    except Exception as e:
        print(f"❌ Erreur récupération stats match {game_id} : {e}")
        return {}

# 🧠 Fonction DeepSeek avec alternance automatique des clés et retry automatique (VERSION AMÉLIORÉE)
def call_deepseek_analysis(prompt, max_retries=5):
    global groq_key_index

    for attempt in range(1, max_retries + 1):
        key = groq_keys[groq_key_index % len(groq_keys)]
        groq_key_index += 1

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "openai/gpt-oss-120b",
            "messages": [
                {"role": "system", "content": "Tu es un expert en paris sportifs. Ton rôle est de faire une analyse complète du match en fonction des données fournies, puis de proposer UNE prédiction fiable parmi : victoire domicile, victoire extérieur, +2.5 buts, -2.5 buts, BTTS oui, BTTS non, double chance (1X ou X2). Tu dois aussi donner un pourcentage de confiance (0-100%) et les 2 scores les plus probables. ATTENTION : Ne jamais prédire 'match nul' - utilise plutôt 'double chance 1X' ou 'double chance X2'. Ta mission Faire la prédiction la plus probable et précise."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5
        }

        try:
            print(f"🧠 Tentative {attempt}/{max_retries} avec clé {(groq_key_index - 1) % len(groq_keys) + 1}...")
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"].strip()
            print(f"✅ Analyse IA réussie à la tentative {attempt}")
            return result
        except Exception as e:
            print(f"❌ Erreur DeepSeek (tentative {attempt}/{max_retries}) : {str(e)}")
            if attempt < max_retries:
                print("🔄 Nouvel essai dans 2 secondes...")
                import time
                time.sleep(2)  # Petite pause avant retry
            else:
                error_msg = f"❌ Échec définitif après {max_retries} tentatives. Dernière erreur : {str(e)}"
                print(error_msg)
                return error_msg

# 🎯 MODULE MONTE-CARLO : Probabilités vraies (autonome, sans IA ni cotes)
def ajuster_lambda_h2h(lambda_home, lambda_away, h2h_data):
    """
    Ajuste les moyennes de buts selon les confrontations directes passées.
    Si une équipe a marqué nettement plus souvent dans les H2H, on renforce son λ.
    """
    if not h2h_data:
        return lambda_home, lambda_away
    
    total_home = total_away = 0
    count = 0
    for m in h2h_data:
        score = m.get("score")
        if not score or "-" not in score:
            continue
        try:
            h, a = map(int, score.split("-"))
            total_home += h
            total_away += a
            count += 1
        except:
            continue

    if count == 0:
        return lambda_home, lambda_away

    avg_home = total_home / count
    avg_away = total_away / count

    # Ajustement doux (15%) pour éviter le sur-apprentissage
    poids = 0.15
    lambda_home = (1 - poids) * lambda_home + poids * avg_home
    lambda_away = (1 - poids) * lambda_away + poids * avg_away

    print(f"🆚 Ajustement H2H: λ_home {lambda_home:.2f} → {lambda_home:.2f}, λ_away {lambda_away:.2f} → {lambda_away:.2f}")
    return lambda_home, lambda_away

def simulation_match_montecarlo(stats_home, stats_away, h2h_data=None, n=20000):
    """
    Simulation Monte-Carlo avancée : combine modèle Poisson + calibrage international + H2H.
    Basée uniquement sur les statistiques (sans IA ni cotes).
    Retourne les probabilités 1X2, double chance, over/under, résultat+total.
    """
    print(f"🎲 Démarrage simulation Monte-Carlo avec {n} itérations...")
    
    # ⚽ Moyennes de buts internationales (pondérées FIFA/UEFA)
    base_home_avg = 1.52
    base_away_avg = 1.18
    
    # ⚙️ Calibrage selon les stats des équipes
    lambda_home = (stats_home["moyenne_marques"] + stats_away["moyenne_encaisses"]) / 2
    lambda_away = (stats_away["moyenne_marques"] + stats_home["moyenne_encaisses"]) / 2
    
    # Normalisation par la moyenne internationale
    lambda_home = (lambda_home + base_home_avg) / 2
    lambda_away = (lambda_away + base_away_avg) / 2

    print(f"🔢 λ initial: Home={lambda_home:.2f}, Away={lambda_away:.2f}")
    
    # 🆚 Ajustement selon les H2H si disponibles
    if h2h_data:
        lambda_home, lambda_away = ajuster_lambda_h2h(lambda_home, lambda_away, h2h_data)

    # 🧮 Simulations Monte-Carlo réelles
    buts_home = np.random.poisson(lambda_home, n)
    buts_away = np.random.poisson(lambda_away, n)
    totals = buts_home + buts_away

    # --- Comptages 1X2 ---
    v1 = np.sum(buts_home > buts_away)
    x = np.sum(buts_home == buts_away)
    v2 = np.sum(buts_home < buts_away)

    res_1x2 = {
        "V1": round(v1/n*100, 2),
        "X": round(x/n*100, 2),
        "V2": round(v2/n*100, 2)
    }

    # --- Double chance ---
    res_double = {
        "1X": round((v1+x)/n*100, 2),
        "12": round((v1+v2)/n*100, 2),
        "X2": round((x+v2)/n*100, 2)
    }

    # --- Over/Under pour différents seuils ---
    seuils = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    over_under = {}
    for s in seuils:
        over_under[f"plus_de_{s}"] = round(np.sum(totals > s)/n*100, 2)
        over_under[f"moins_de_{s}"] = round(np.sum(totals <= s)/n*100, 2)

    # --- BTTS (Both Teams To Score) ---
    btts_oui = np.sum((buts_home > 0) & (buts_away > 0))
    btts_non = n - btts_oui
    btts = {
        "oui": round(btts_oui/n*100, 2),
        "non": round(btts_non/n*100, 2)
    }

    # --- Probabilités conditionnelles Résultat + Total ---
    res_total_combo = {}
    for s in seuils:
        cond_v1 = np.sum((buts_home > buts_away) & (totals > s)) / n * 100
        cond_1x = np.sum(((buts_home >= buts_away) | (buts_home == buts_away)) & (totals > s)) / n * 100
        cond_v2 = np.sum((buts_home < buts_away) & (totals > s)) / n * 100
        res_total_combo[f"V1et+{s}"] = round(cond_v1, 2)
        res_total_combo[f"1Xet+{s}"] = round(cond_1x, 2)
        res_total_combo[f"V2et+{s}"] = round(cond_v2, 2)

    # --- Scores exacts les plus probables ---
    unique_scores, counts = np.unique(list(zip(buts_home, buts_away)), axis=0, return_counts=True)
    top_scores_idx = np.argsort(counts)[-10:][::-1] if len(counts) > 0 else np.array([], dtype=int)
    # (Remarque: la ligne ci‑dessous utilise une variante robuste)
    top_scores_idx = np.argsort(counts)[-10:][::-1] if len(counts) > 0 else np.array([], dtype=int)
    scores_probables = {}
    for idx in top_scores_idx:
        score = tuple(unique_scores[idx])
        prob = round(counts[idx]/n*100, 2)
        scores_probables[f"{score[0]}-{score[1]}"] = prob

    print(f"✅ Simulation terminée: {n} matchs simulés")
    print(f"🎯 Résultats: V1={res_1x2['V1']}%, X={res_1x2['X']}%, V2={res_1x2['V2']}%")
    print(f"⚽ Plus de 2.5 buts: {over_under['plus_de_2.5']}%")
    print(f"🥅 BTTS: {btts['oui']}%")

    return {
        "parametres_simulation": {
            "iterations": n,
            "lambda_home": round(lambda_home, 3),
            "lambda_away": round(lambda_away, 3),
            "ajustement_h2h": bool(h2h_data and len(h2h_data) > 0)
        },
        "1x2": res_1x2,
        "double_chance": res_double,
        "over_under": over_under,
        "btts": btts,
        "resultat_total": res_total_combo,
        "scores_probables": scores_probables,
        "buts_moyens_simules": {
            "home": round(np.mean(buts_home), 2),
            "away": round(np.mean(buts_away), 2),
            "total": round(np.mean(totals), 2)
        }
    }

# 🔮 Générateur de prompt détaillé (VERSION SANS MONTE-CARLO)
def generate_detailed_prompt(prediction_obj):
    home = prediction_obj["HomeTeam"]
    away = prediction_obj["AwayTeam"]
    stats_home = prediction_obj["stats_home"]
    stats_away = prediction_obj["stats_away"]
    odds = prediction_obj.get("odds", {})
    pos_home = prediction_obj.get("classement_home")
    pts_home = prediction_obj.get("points_classement_home")
    pos_away = prediction_obj.get("classement_away")
    pts_away = prediction_obj.get("points_classement_away")
    league = prediction_obj["league"]
    date = prediction_obj["date"]

    prompt = f"""
ANALYSE DE MATCH - {date}
{league}
{home} (DOMICILE) vs {away} (EXTÉRIEUR)

🏠 STATISTIQUES DE {home} (DOMICILE) :
- Classement : {pos_home}ᵉ avec {pts_home} points
- Moyenne buts marqués : {stats_home['moyenne_marques']:.2f}
- Moyenne buts encaissés : {stats_home['moyenne_encaisses']:.2f}
- Forme sur 6 matchs : {' '.join(stats_home['form_6'])} ({stats_home.get('total_points_6', 0)} points)
- Forme sur 10 matchs : {' '.join(stats_home['form_10'])} ({stats_home.get('total_points_10', 0)} points)
- Série domicile : {'-'.join(stats_home.get('serie_domicile', []))}
- Buts marqués domicile : {stats_home.get('buts_dom_marques', 0)}
- Buts encaissés domicile : {stats_home.get('buts_dom_encaisses', 0)}

✈️ STATISTIQUES DE {away} (EXTÉRIEUR) :
- Classement : {pos_away}ᵉ avec {pts_away} points
- Moyenne buts marqués : {stats_away['moyenne_marques']:.2f}
- Moyenne buts encaissés : {stats_away['moyenne_encaisses']:.2f}
- Forme sur 6 matchs : {' '.join(stats_away['form_6'])} ({stats_away.get('total_points_6', 0)} points)
- Forme sur 10 matchs : {' '.join(stats_away['form_10'])} ({stats_away.get('total_points_10', 0)} points)
- Série extérieur : {'-'.join(stats_away.get('serie_exterieur', []))}
- Buts marqués extérieur : {stats_away.get('buts_ext_marques', 0)}
- Buts encaissés extérieur : {stats_away.get('buts_ext_encaisses', 0)}

💰 COTES DISPONIBLES :
"""
    if odds and odds != {}:
        bookmaker = odds.get('bookmaker', 'N/A')
        prompt += f"Bookmaker : {bookmaker}\n"
        
        h2h = odds.get('h2h', {})
        if h2h:
            prompt += "- 1X2 : "
            for outcome, cote in h2h.items():
                prompt += f"{outcome} : {cote} | "
            prompt += "\n"
        
        totals = odds.get('totals', {})
        if totals:
            prompt += "- Total 2.5 : "
            for outcome, cote in totals.items():
                prompt += f"{outcome} : {cote} | "
            prompt += "\n"
    else:
        prompt += "Aucune cote disponible\n"

    # ✅ NOUVEAUTÉ 1 : Ajout des 10 derniers matchs complets avec nouvelle structure + STATS DÉTAILLÉES
    prompt += f"\n📅 10 DERNIERS MATCHS DE {home} (DOMICILE) AVEC STATISTIQUES DÉTAILLÉES :\n"
    last_matches_home = prediction_obj.get("last_matches_home", [])
    if last_matches_home:
        for i, match in enumerate(last_matches_home[:10], 1):
            if isinstance(match, dict) and all(key in match for key in ['date', 'home_team', 'away_team', 'score', 'competition', 'status']):
                date_match = match['date']
                team1 = match['home_team']
                team2 = match['away_team']
                competition = match['competition']
                score = match['score']
                status = match['status']
                game_id = match.get('game_id', 'N/A')
                url = match.get('url', 'N/A')
                
                prompt += f"  {i}. {date_match} | {team1} vs {team2} : {score} [{competition}] ({status}) [ID: {game_id}]\n"
                
                # ✅ NOUVEAU : Ajout des statistiques détaillées du match
                match_stats = match.get('stats', {})
                if match_stats:
                    prompt += f"     📊 Stats détaillées : "
                    for stat_name, (val1, val2) in match_stats.items():
                        prompt += f"{stat_name}: {val1}-{val2} | "
                    prompt += f"\n     🔗 URL: {url}\n"
                else:
                    prompt += f"     📊 Stats détaillées : Non disponibles\n"
    else:
        prompt += "  Aucun match détaillé disponible\n"

    prompt += f"\n📅 10 DERNIERS MATCHS DE {away} (EXTÉRIEUR) AVEC STATISTIQUES DÉTAILLÉES :\n"
    last_matches_away = prediction_obj.get("last_matches_away", [])
    if last_matches_away:
        for i, match in enumerate(last_matches_away[:10], 1):
            if isinstance(match, dict) and all(key in match for key in ['date', 'home_team', 'away_team', 'score', 'competition', 'status']):
                date_match = match['date']
                team1 = match['home_team']
                team2 = match['away_team']
                competition = match['competition']
                score = match['score']
                status = match['status']
                game_id = match.get('game_id', 'N/A')
                url = match.get('url', 'N/A')
                
                prompt += f"  {i}. {date_match} | {team1} vs {team2} : {score} [{competition}] ({status}) [ID: {game_id}]\n"
                
                # ✅ NOUVEAU : Ajout des statistiques détaillées du match
                match_stats = match.get('stats', {})
                if match_stats:
                    prompt += f"     📊 Stats détaillées : "
                    for stat_name, (val1, val2) in match_stats.items():
                        prompt += f"{stat_name}: {val1}-{val2} | "
                    prompt += f"\n     🔗 URL: {url}\n"
                else:
                    prompt += f"     📊 Stats détaillées : Non disponibles\n"
    else:
        prompt += "  Aucun match détaillé disponible\n"

    # ✅ NOUVEAUTÉ 2 : Ajout du classement complet de la ligue
    prompt += "\n🏆 CLASSEMENT COMPLET DE LA LIGUE :\n"
    classement_complet = prediction_obj.get("classement_complet", [])
    if classement_complet:
        for team_data in classement_complet[:20]:  # Limiter à 20 pour éviter un prompt trop long
            position = team_data.get('position', 'N/A')
            team_name = team_data.get('team', 'N/A')
            points = team_data.get('points', 'N/A')
            
            # Marquer les équipes du match en cours
            marker = ""
            if team_name == home:
                marker = " ← DOMICILE"
            elif team_name == away:
                marker = " ← EXTÉRIEUR"
            
            prompt += f"  {position}. {team_name} ({points} pts){marker}\n"
    else:
        prompt += "  Classement complet non disponible\n"

    # ✅ NOUVEAUTÉ 3 : Ajout des confrontations directes H2H avec STATISTIQUES DÉTAILLÉES
    confrontations_h2h = prediction_obj.get("confrontations_saison_derniere", [])
    if confrontations_h2h:
        prompt += f"\n🆚 CONFRONTATIONS DIRECTES (SAISON DERNIÈRE) AVEC STATISTIQUES DÉTAILLÉES :\n"
        for i, match in enumerate(confrontations_h2h, 1):
            date_h2h = match.get('date', 'N/A')
            team1_h2h = match.get('team1', 'N/A')
            team2_h2h = match.get('team2', 'N/A')
            score_h2h = match.get('score', 'N/A')
            competition_h2h = match.get('competition', 'N/A')
            source_h2h = match.get('source', 'N/A')
            game_id_h2h = match.get('gameId', 'N/A')
            
            prompt += f"  {i}. {date_h2h} | {team1_h2h} vs {team2_h2h} : {score_h2h} [{competition_h2h}] (Source: {source_h2h}) [ID: {game_id_h2h}]\n"
            
            # ✅ NOUVEAU : Ajout des statistiques détaillées H2H
            h2h_stats = match.get('stats', {})
            if h2h_stats:
                prompt += f"     📊 Stats H2H détaillées : "
                for stat_name, (val1, val2) in h2h_stats.items():
                    prompt += f"{stat_name}: {val1}-{val2} | "
                prompt += "\n"
            else:
                prompt += f"     📊 Stats H2H détaillées : Non disponibles\n"
    else:
        prompt += f"\n🆚 CONFRONTATIONS DIRECTES (SAISON DERNIÈRE) :\n  Aucune confrontation H2H disponible\n"

    prompt += f"""
MISSION :
1. Analyse comparative des deux équipes (forces/faiblesses)
2. Impact du facteur domicile/extérieur
3. Analyse des formes récentes et tendances à partir des matchs détaillés AVEC LEURS STATISTIQUES
4. Analyse du contexte du championnat grâce au classement complet
5. Prise en compte des confrontations directes récentes avec leurs statistiques détaillées
6. Évaluation des cotes (si disponibles)
7. ✨ NOUVEAU : Analyse approfondie des statistiques détaillées des matchs passés (possession, tirs, corners, etc.)
8. Prédiction finale claire : UNE SEULE recommandation parmi :
   - "Victoire domicile" ({home})
   - "Victoire extérieur" ({away})
   - "Plus de 2.5 buts"
   - "Moins de 2.5 buts"
   - "BTTS oui" (Both Teams To Score)
   - "BTTS non"
   - "Double chance 1X" (domicile ou nul)
   - "Double chance X2" (nul ou extérieur)

9. ✨ NOUVEAUTÉS OBLIGATOIRES :
   - POURCENTAGE DE CONFIANCE (0-100%) pour ta prédiction principale
   - LES 2 SCORES LES PLUS PROBABLES (ex: "1-0 ou 2-1")

⚠️ IMPORTANT : 
- Ne JAMAIS prédire "Match nul" - utilise "Double chance 1X" ou "Double chance X2" à la place.

Justifie ta prédiction avec toutes les données statistiques fournies, en tenant compte particulièrement des matchs récents détaillés avec leurs statistiques complètes, du contexte du classement, des confrontations directes avec leurs stats détaillées.

FORMAT DE RÉPONSE OBLIGATOIRE :
- PRÉDICTION PRINCIPALE : [ta prédiction]
- CONFIANCE : [X]%
- SCORES PROBABLES : [Score1] ou [Score2]
- JUSTIFICATION : [ton analyse détaillée]
"""
    return prompt

# ✅ FONCTION AMÉLIORÉE : Extraction des données de l'analyse IA (SUPPORT DES DEUX FORMATS)
def extract_confidence_percentage(analyse_ia):
    """
    Extrait le pourcentage de confiance de l'analyse IA
    Support des deux formats : 
    1. Format simple : CONFIANCE : XX%
    2. Format avec ** : **CONFIANCE** : XX %
    Retourne le pourcentage en tant que nombre entier ou None si non trouvé
    """
    if not analyse_ia or isinstance(analyse_ia, str) and analyse_ia.startswith("❌"):
        return None
    
    # Patterns pour le format avec ** (nouveau format)
    patterns_with_stars = [
        r'\*\*CONFIANCE\*\*\s*:\s*(\d+)\s*%',
        r'\*\*Confiance\*\*\s*:\s*(\d+)\s*%',
        r'\*\*confiance\*\*\s*:\s*(\d+)\s*%',
        r'\*\*CONFIANCE\*\*\s*:\s*(\d+)\s*\%',
    ]
    
    # Patterns pour le format simple (ancien format)
    patterns_simple = [
        r'CONFIANCE\s*:\s*(\d+)%',
        r'Confiance\s*:\s*(\d+)%',
        r'confiance\s*:\s*(\d+)%',
        r'CONFIANCE\s*:\s*(\d+)\s*%',
        r'(\d+)%\s*de\s*confiance',
        r'confiance\s*de\s*(\d+)%'
    ]
    
    # Essayer d'abord les patterns avec **
    for pattern in patterns_with_stars:
        match = re.search(pattern, analyse_ia, re.IGNORECASE)
        if match:
            try:
                percentage = int(match.group(1))
                if 0 <= percentage <= 100:
                    print(f"📊 Pourcentage de confiance extrait (format **) : {percentage}%")
                    return percentage
            except ValueError:
                continue
    
    # Puis essayer les patterns simples
    for pattern in patterns_simple:
        match = re.search(pattern, analyse_ia, re.IGNORECASE)
        if match:
            try:
                percentage = int(match.group(1))
                if 0 <= percentage <= 100:
                    print(f"📊 Pourcentage de confiance extrait (format simple) : {percentage}%")
                    return percentage
            except ValueError:
                continue
    
    print("⚠️ Pourcentage de confiance non trouvé dans l'analyse IA")
    return None

# ✅ NOUVELLES FONCTIONS D'EXTRACTION POUR LES AUTRES ÉLÉMENTS
def extract_prediction_principale(analyse_ia):
    """
    Extrait la prédiction principale de l'analyse IA
    Support des deux formats
    """
    if not analyse_ia or isinstance(analyse_ia, str) and analyse_ia.startswith("❌"):
        return None
    
    # Patterns pour le format avec **
    patterns_with_stars = [
        r'\*\*PRÉDICTION PRINCIPALE\*\*\s*:\s*([^\n\r]+)',
        r'\*\*Prédiction principale\*\*\s*:\s*([^\n\r]+)',
        r'\*\*PREDICTION PRINCIPALE\*\*\s*:\s*([^\n\r]+)',
    ]
    
    # Patterns pour le format simple
    patterns_simple = [
        r'PRÉDICTION PRINCIPALE\s*:\s*([^\n\r]+)',
        r'Prédiction principale\s*:\s*([^\n\r]+)',
        r'PREDICTION PRINCIPALE\s*:\s*([^\n\r]+)',
    ]
    
    # Essayer d'abord les patterns avec **
    for pattern in patterns_with_stars:
        match = re.search(pattern, analyse_ia, re.IGNORECASE)
        if match:
            prediction = match.group(1).strip()
            print(f"🎯 Prédiction principale extraite (format **) : {prediction}")
            return prediction
    
    # Puis essayer les patterns simples
    for pattern in patterns_simple:
        match = re.search(pattern, analyse_ia, re.IGNORECASE)
        if match:
            prediction = match.group(1).strip()
            print(f"🎯 Prédiction principale extraite (format simple) : {prediction}")
            return prediction
    
    print("⚠️ Prédiction principale non trouvée dans l'analyse IA")
    return None

def extract_corners_prevu(analyse_ia):
    """
    Extrait la prédiction de corners de l'analyse IA
    Support des deux formats
    """
    if not analyse_ia or isinstance(analyse_ia, str) and analyse_ia.startswith("❌"):
        return None
    
    # Patterns pour le format avec **
    patterns_with_stars = [
        r'\*\*CORNERS PRÉVUS\*\*\s*:\s*([^\n\r]+)',
        r'\*\*Corners prévus\*\*\s*:\s*([^\n\r]+)',
        r'\*\*CORNERS PREVUS\*\*\s*:\s*([^\n\r]+)',
    ]
    
    # Patterns pour le format simple
    patterns_simple = [
        r'CORNERS PRÉVUS\s*:\s*([^\n\r]+)',
        r'Corners prévus\s*:\s*([^\n\r]+)',
        r'CORNERS PREVUS\s*:\s*([^\n\r]+)',
    ]
    
    # Essayer d'abord les patterns avec **
    for pattern in patterns_with_stars:
        match = re.search(pattern, analyse_ia, re.IGNORECASE)
        if match:
            corners = match.group(1).strip()
            print(f"📐 Corners prévus extraits (format **) : {corners}")
            return corners
    
    # Puis essayer les patterns simples
    for pattern in patterns_simple:
        match = re.search(pattern, analyse_ia, re.IGNORECASE)
        if match:
            corners = match.group(1).strip()
            print(f"📐 Corners prévus extraits (format simple) : {corners}")
            return corners
    
    print("⚠️ Corners prévus non trouvés dans l'analyse IA")
    return None

def extract_tirs_cadres_prevu(analyse_ia):
    """
    Extrait la prédiction de tirs cadrés de l'analyse IA
    Support des deux formats
    """
    if not analyse_ia or isinstance(analyse_ia, str) and analyse_ia.startswith("❌"):
        return None
    
    # Patterns pour le format avec **
    patterns_with_stars = [
        r'\*\*TIRS CADRÉS PRÉVUS\*\*\s*:\s*([^\n\r]+)',
        r'\*\*Tirs cadrés prévus\*\*\s*:\s*([^\n\r]+)',
        r'\*\*TIRS CADRES PREVUS\*\*\s*:\s*([^\n\r]+)',
    ]
    
    # Patterns pour le format simple
    patterns_simple = [
        r'TIRS CADRÉS PRÉVUS\s*:\s*([^\n\r]+)',
        r'Tirs cadrés prévus\s*:\s*([^\n\r]+)',
        r'TIRS CADRES PREVUS\s*:\s*([^\n\r]+)',
    ]
    
    # Essayer d'abord les patterns avec **
    for pattern in patterns_with_stars:
        match = re.search(pattern, analyse_ia, re.IGNORECASE)
        if match:
            tirs = match.group(1).strip()
            print(f"🎯 Tirs cadrés prévus extraits (format **) : {tirs}")
            return tirs
    
    # Puis essayer les patterns simples
    for pattern in patterns_simple:
        match = re.search(pattern, analyse_ia, re.IGNORECASE)
        if match:
            tirs = match.group(1).strip()
            print(f"🎯 Tirs cadrés prévus extraits (format simple) : {tirs}")
            return tirs
    
    print("⚠️ Tirs cadrés prévus non trouvés dans l'analyse IA")
    return None

def extract_scores_probables(analyse_ia):
    """
    Extrait les scores probables de l'analyse IA
    Support des deux formats
    """
    if not analyse_ia or isinstance(analyse_ia, str) and analyse_ia.startswith("❌"):
        return None
    
    # Patterns pour le format avec **
    patterns_with_stars = [
        r'\*\*SCORES PROBABLES\*\*\s*:\s*([^\n\r]+)',
        r'\*\*Scores probables\*\*\s*:\s*([^\n\r]+)',
        r'\*\*SCORES PROBABLES\*\*\s*:\s*([^\n\r]+)',
    ]
    
    # Patterns pour le format simple
    patterns_simple = [
        r'SCORES PROBABLES\s*:\s*([^\n\r]+)',
        r'Scores probables\s*:\s*([^\n\r]+)',
        r'SCORES PROBABLES\s*:\s*([^\n\r]+)',
    ]
    
    # Essayer d'abord les patterns avec **
    for pattern in patterns_with_stars:
        match = re.search(pattern, analyse_ia, re.IGNORECASE)
        if match:
            scores = match.group(1).strip()
            print(f"⚽ Scores probables extraits (format **) : {scores}")
            return scores
    
    # Puis essayer les patterns simples
    for pattern in patterns_simple:
        match = re.search(pattern, analyse_ia, re.IGNORECASE)
        if match:
            scores = match.group(1).strip()
            print(f"⚽ Scores probables extraits (format simple) : {scores}")
            return scores
    
    print("⚠️ Scores probables non trouvés dans l'analyse IA")
    return None

def get_odds_for_match(sport_odds_id, home_team_api, away_team_api, home_team_espn, away_team_espn):
    if sport_odds_id == "none":
        print(f"⚠️ Pas d'odds_id disponible pour ce championnat")
        return None

    url = f"https://api.the-odds-api.com/v4/sports/{sport_odds_id}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGION,
        "markets": MARKETS,
        "oddsFormat": "decimal"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"❌ Erreur API Odds : {response.status_code}")
            return None

        matches = response.json()

        target_match = None
        for match in matches:
            home_odds = match['home_team']
            away_odds = match['away_team']

            if ((home_odds.lower() == home_team_api.lower() or away_odds.lower() == home_team_api.lower()) and 
                (home_odds.lower() == away_team_api.lower() or away_odds.lower() == away_team_api.lower())):
                target_match = match
                print(f"✅ Match trouvé avec noms API : {home_odds} vs {away_odds}")
                break

            if ((home_odds.lower() == home_team_espn.lower() or away_odds.lower() == home_team_espn.lower()) and 
                (home_odds.lower() == away_team_espn.lower() or away_odds.lower() == away_team_espn.lower())):
                target_match = match
                print(f"✅ Match trouvé avec noms ESPN : {home_odds} vs {away_odds}")
                break

        if not target_match:
            print(f"❌ Match non trouvé dans les cotes : {home_team_api} vs {away_team_api}")
            return None

        # ✅ Choix du bookmaker (priorité 1xBet, puis Betclic, sinon premier dispo)
        bookmaker = next((b for b in target_match['bookmakers'] if b['title'].lower() == "1xbet"), None)
        if not bookmaker:
            bookmaker = next((b for b in target_match['bookmakers'] if b['title'].lower() == "betclic"), None)
        if not bookmaker and target_match['bookmakers']:
            bookmaker = target_match['bookmakers'][0]

        if not bookmaker:
            print(f"⚠️ Aucun bookmaker disponible pour ce match")
            return None

        print(f"🏢 Bookmaker utilisé : {bookmaker['title']}")

        odds_data = {
            "bookmaker": bookmaker['title'],
            "h2h": {},
            "totals": {}
        }

        for market in bookmaker['markets']:
            if market['key'] == "h2h":
                print("🎯 Marché : 1X2")
                for outcome in market['outcomes']:
                    odds_data['h2h'][outcome['name']] = outcome['price']
                    print(f"    ➤ {outcome['name']} : Cote {outcome['price']}")
            elif market['key'] == "totals":
                print("🎯 Marché : Total 2.5 (Over/Under)")
                for outcome in market['outcomes']:
                    odds_data['totals'][outcome['name']] = outcome['price']
                    print(f"    ➤ {outcome['name']} : Cote {outcome['price']}")

        return odds_data

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des cotes : {e}")
        return None

# 🔧 Classe réutilisable de scraping de classement (VERSION AMÉLIORÉE)
class ClassementScraper:
    def __init__(self, url):
        self.url = url
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.teams_positions = {}
        self.full_standings = []  # Nouveau : stockage du classement complet

    def scrape_table(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Extraire les noms d'équipes
            team_divs = soup.select('.team-link .hide-mobile a')
            team_names = [tag.text.strip() for tag in team_divs]
            
            # 2. Extraire les points (8e cellule de chaque ligne dans le 2e tableau)
            stat_rows = soup.select('.Table__Scroller .Table__TBODY > tr')
            team_points = []
            
            for row in stat_rows:
                cells = row.find_all("td")
                if len(cells) >= 8:
                    try:
                        points = int(cells[7].text.strip())
                    except ValueError:
                        points = None
                    team_points.append(points)
            
            # 3. Combiner équipes + points et créer le dictionnaire de positions
            teams_data = list(zip(team_names, team_points))
            
            print(f"🏆 Classement extrait de {self.url}:")
            for i, (team, pts) in enumerate(teams_data, start=1):
                if team and pts is not None:
                    self.teams_positions[team.lower()] = (i, team, pts)
                    self.full_standings.append({
                        "position": i,
                        "team": team,
                        "points": pts
                    })
                    print(f"  {i}. {team}: {pts} points")

        except Exception as e:
            print(f"❌ Erreur scraping classement : {e}")

    def get_position(self, team_query):
        # Utiliser le mapping pour convertir le nom API vers le nom ESPN
        mapped_team_name = team_name_mapping.get(team_query, team_query)
        
        # Recherche exacte d'abord
        if mapped_team_name.lower() in self.teams_positions:
            return self.teams_positions[mapped_team_name.lower()]
        
        # Recherche partielle ensuite
        for key, (position, full_name, points) in self.teams_positions.items():
            if mapped_team_name.lower() in key or key in mapped_team_name.lower():
                return position, full_name, points
        return None, None, None

    def get_full_standings(self):
        """Retourne le classement complet"""
        return self.full_standings

# 🧠 Fonction utilitaire get_team_classement_position (modifiée pour retourner le classement complet)
def get_team_classement_position(country, league, team_name):
    league_info = classement_ligue_mapping.get(country, {}).get(league)
    if not league_info:
        print(f"⚠️ Informations de ligue introuvables pour {country} - {league}")
        return None, None, None, []
    
    url = league_info["url"]
    odds_id = league_info["odds_id"]
    
    print(f"🔍 Recherche classement pour {team_name} dans {country} - {league} (odds_id: {odds_id})")
    scraper = ClassementScraper(url)
    scraper.scrape_table()
    
    # Utiliser le mapping pour convertir le nom API vers le nom ESPN
    mapped_team_name = team_name_mapping.get(team_name, team_name)
    position, full_name, points = scraper.get_position(mapped_team_name)
    full_standings = scraper.get_full_standings()
    
    if position:
        print(f"✅ {full_name} trouvé à la position {position} avec {points} points")
    else:
        print(f"❌ {team_name} (mappé: {mapped_team_name}) non trouvé dans le classement")
    
    return position, full_name, points, full_standings

def get_espn_name(api_team_name):
    mapped = team_name_mapping.get(api_team_name, api_team_name)
    if mapped != api_team_name:
        print(f"🔄 Mapping appliqué: '{api_team_name}' → '{mapped}'")
    return mapped

def format_date_fr(date_str, time_str):
    try:
        dt = datetime.strptime(date_str + " " + time_str, "%Y-%m-%d %H:%M")
        mois_fr = [
            "", "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"
        ]
        mois = mois_fr[dt.month]
        return f"{dt.day} {mois} {dt.year} à {dt.strftime('%H:%M:%S')} UTC"
    except Exception as e:
        return f"{date_str} à {time_str}:00 UTC"

# 🆚 Fonction pour récupérer les confrontations directes de la saison passée avec STATISTIQUES DÉTAILLÉES - MODIFIÉE
def get_h2h_confrontations(home_team_espn, away_team_espn):
    """
    Récupère les confrontations directes de la saison passée depuis les fichiers JSON
    définis dans classement_ligue_mapping avec récupération des statistiques détaillées via gameId.
    Les JSON sont récupérés depuis le dépôt GitHub Raw :
    https://raw.githubusercontent.com/Jonnhy2255/Pronosoftbot/main/<data_json>
    """
    confrontations = []
    base_raw_url = "https://raw.githubusercontent.com/Jonnhy2255/Pronosoftbot/main/"

    # Parcourir tous les pays et ligues dans classement_ligue_mapping
    for country, leagues in classement_ligue_mapping.items():
        for league_name, league_info in leagues.items():
            data_json = league_info.get("data_json", "none")
            
            # Ignorer si pas de fichier JSON défini
            if data_json == "none" or not data_json:
                continue

            raw_url = base_raw_url + data_json
            try:
                print(f"🔍 Tentative de récupération H2H depuis {raw_url} ({league_name})")
                resp = requests.get(raw_url, timeout=15)
                if resp.status_code != 200:
                    print(f"⚠️ Échec téléchargement {data_json} : HTTP {resp.status_code}")
                    continue

                data = resp.json()
                
                matchs_trouvés = 0
                # Parcourir tous les matchs dans le fichier JSON
                for match in data:
                    team1 = match.get("team1", "")
                    team2 = match.get("team2", "")
                    
                    # Vérifier si les deux équipes correspondent (dans un sens ou l'autre)
                    if ((team1 == home_team_espn and team2 == away_team_espn) or 
                        (team1 == away_team_espn and team2 == home_team_espn)):
                        
                        match["source"] = league_name  # Ajouter la source du championnat
                        
                        # ✅ NOUVEAU : Récupérer les statistiques détaillées si gameId disponible
                        game_id = match.get("gameId", "N/A")
                        if game_id and game_id != "N/A":
                            try:
                                print(f"🔍 Récupération des stats H2H pour le match {game_id}...")
                                h2h_stats = get_match_stats(game_id)
                                match["stats"] = h2h_stats
                                if h2h_stats:
                                    print(f"📊 {len(h2h_stats)} statistiques H2H récupérées pour {team1} vs {team2}")
                            except Exception as e:
                                print(f"⚠️ Erreur récupération stats pour gameId {game_id} : {e}")
                                match["stats"] = {}
                        else:
                            match["stats"] = {}
                        
                        confrontations.append(match)
                        matchs_trouvés += 1
                
                if matchs_trouvés > 0:
                    print(f"🆚 {matchs_trouvés} confrontation(s) trouvée(s) dans {league_name}")
            except Exception as e:
                print(f"❌ Erreur lors de la récupération/lecture de {raw_url} ({league_name}) : {e}")
    
    print(f"🆚 Total : {len(confrontations)} confrontation(s) directe(s) trouvée(s) pour {home_team_espn} vs {away_team_espn}")
    return confrontations

def get_today_matches_filtered():
    today = datetime.now().strftime('%Y-%m-%d')
    url = "https://v3.football.api-sports.io/fixtures"
    params = {
        "date": today,
        "timezone": "Africa/Abidjan"
    }
    allowed_league_ids = [72, 265, 281, 218, 113, 129, 250, 252, 299, 283, 43, 239, 61, 144, 39, 88, 94, 140, 197, 203, 98, 383, 207, 169, 235, 262, 307, 71, 253, 78, 135]
    résultats = []
    try:
        response = requests.get(url, headers=api_headers, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"\n📅 Matchs du jour ({today}) :\n")
        for match in data.get("response", []):
            league_id = match['league']['id']
            league = match['league']['name']
            country = match['league']['country']
            home_api = match['teams']['home']['name']
            away_api = match['teams']['away']['name']
            logo_home = match['teams']['home']['logo']
            logo_away = match['teams']['away']['logo']
            time = match['fixture']['date'][11:16]
            date = match['fixture']['date'][:10]
            heure, minute = map(int, time.split(":"))
            if heure < 8:
                continue

            if league_id in allowed_league_ids:
                print(f"🏆 [{country}] {league} : {home_api} vs {away_api} à {time}")
                # Utiliser le mapping pour les noms ESPN
                home_espn = get_espn_name(home_api)
                away_espn = get_espn_name(away_api)
                
                if home_espn in teams_urls and away_espn in teams_urls:
                    print(f"\n🔎 Analyse automatique pour : {home_espn} & {away_espn}")
                    team1_stats = process_team(home_api, return_data=True)
                    team2_stats = process_team(away_api, return_data=True)
                    if team1_stats: team1_stats['nom'] = home_espn
                    if team2_stats: team2_stats['nom'] = away_espn
                    compare_teams_basic_stats(
                        team1_stats, team2_stats, home_api, away_api, date, time, league, country,
                        logo_home=logo_home, logo_away=logo_away, résultats=résultats
                    )
                else:
                    if home_espn in teams_urls:
                        process_team(home_api)
                    else:
                        FAILED_TEAMS.add(home_api)
                    if away_espn in teams_urls:
                        process_team(away_api)
                    else:
                        FAILED_TEAMS.add(away_api)
        
        # ✅ CORRECTION 1 : Récupérer le chemin retourné par sauvegarder_stats_brutes_json
        if résultats:
            chemin = sauvegarder_stats_brutes_json(résultats, today)  # ✅ Récupérer le chemin
            git_commit_and_push(chemin)  # ✅ Utiliser le bon chemin
        
        if FAILED_TEAMS:
            save_failed_teams_json(FAILED_TEAMS, today)
        if IGNORED_ZERO_FORM_TEAMS:
            save_ignored_teams_json(IGNORED_ZERO_FORM_TEAMS, today)
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des matchs : {e}")

def get_match_result_for_team(team_name, score, team1, team2):
    try:
        home_score, away_score = map(int, score.split(' - '))
    except Exception:
        return None
    
    # Utiliser le mapping pour comparer correctement
    mapped_team_name = team_name_mapping.get(team_name, team_name)
    mapped_team1 = team_name_mapping.get(team1, team1)
    mapped_team2 = team_name_mapping.get(team2, team2)
    
    if mapped_team_name == mapped_team1:
        return 'W' if home_score > away_score else 'D' if home_score == away_score else 'L'
    elif mapped_team_name == mapped_team2:
        return 'W' if away_score > home_score else 'D' if away_score == home_score else 'L'
    return None

def extract_goals(team_name, score, team1, team2):
    try:
        home_score, away_score = map(int, score.split(' - '))
    except Exception:
        return None, None, None
    
    # Utiliser le mapping pour comparer correctement
    mapped_team_name = team_name_mapping.get(team_name, team_name)
    mapped_team1 = team_name_mapping.get(team1, team1)
    mapped_team2 = team_name_mapping.get(team2, team2)
    
    if mapped_team_name == mapped_team1:
        return home_score, away_score, True
    elif mapped_team_name == mapped_team2:
        return away_score, home_score, False
    return None, None, None

def get_form_points(recent_form):
    points_map = {'W': 3, 'D': 1, 'L': 0}
    total = sum(points_map.get(r, 0) for r in recent_form)
    return total

def scrape_team_data(team_name, action):
    espn_team_name = get_espn_name(team_name)
    url = teams_urls.get(espn_team_name, {}).get(action)
    if not url:
        print(f"URL non trouvée pour {espn_team_name} et action {action}.")
        FAILED_TEAMS.add(team_name)
        return []
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        matches = soup.find_all('tr', class_='Table__TR')
        
        # ✅ NOUVELLE STRUCTURE - Objet au lieu de liste
        valid_results = []
        form_6 = []
        form_10 = []
        buts_dom_marques = 0
        buts_dom_encaisses = 0
        buts_ext_marques = 0
        buts_ext_encaisses = 0

        # 🏗️ Initialisation des séries domicile/extérieur
        serie_domicile = []
        serie_exterieur = []

        for match in matches:
            # Date
            date_tag = match.find('div', class_='matchTeams')
            date_text = date_tag.text.strip() if date_tag else "N/A"

            # Équipes
            teams = match.find_all('a', class_='AnchorLink Table__Team')
            team1 = teams[0].text.strip() if len(teams) > 0 else "N/A"
            team2 = teams[1].text.strip() if len(teams) > 1 else "N/A"

            # Compétition
            comp_tags = match.find_all('a', class_='AnchorLink')
            competition = comp_tags[1].text.strip() if len(comp_tags) > 1 else "N/A"

            # Score + Game ID (via l'URL du match)
            score_tag = match.find('a', href=lambda x: x and "gameId" in x)
            score = score_tag.text.strip() if score_tag else "N/A"
            game_id = "N/A"
            if score_tag and score_tag.get('href') and "gameId" in score_tag['href']:
                try:
                    game_id = score_tag['href'].split("gameId/")[1].split("/")[0]
                except:
                    game_id = "N/A"

            # Statut (FT, Postponed…) - essayer plusieurs sélecteurs
            status = "N/A"
            status_tag = match.find('span', {"data-testid": "result"})
            if not status_tag:
                # Fallback - chercher dans les derniers liens
                last_links = match.find_all('a', class_='AnchorLink')
                if last_links:
                    status = last_links[-1].text.strip()
            else:
                status = status_tag.text.strip()

            # Si toutes les infos clés sont présentes, créer l'objet match
            if all(val != "N/A" for val in [date_text, team1, team2, score]):
                match_obj = {
                    "game_id": game_id,
                    "date": date_text,
                    "home_team": team1,
                    "away_team": team2,
                    "score": score,
                    "status": status,
                    "competition": competition
                }

                # ✅ NOUVEAU : Enrichir avec les statistiques détaillées si game_id disponible
                if game_id != "N/A":
                    print(f"🔍 Récupération des stats détaillées pour le match {game_id}...")
                    match_stats = get_match_stats(game_id)
                    match_obj["stats"] = match_stats
                    match_obj["url"] = f"https://africa.espn.com/football/match/_/gameId/{game_id}"
                else:
                    match_obj["stats"] = {}
                    match_obj["url"] = "N/A"

                valid_results.append(match_obj)
                
                # Calculer les formes et stats avec la nouvelle structure
                result = get_match_result_for_team(espn_team_name, score, team1, team2)
                if result:
                    form_10.append(result)
                    if len(form_6) < 6:
                        form_6.append(result)

                    # 🔄 Ajout dans la bonne série - utiliser le mapping
                    mapped_team1 = team_name_mapping.get(team1, team1)
                    mapped_espn_name = team_name_mapping.get(espn_team_name, espn_team_name)
                    is_home = (mapped_team1 == mapped_espn_name)
                    if is_home:
                        serie_domicile.append(result)
                    else:
                        serie_exterieur.append(result)

                buts_m, buts_e, domicile = extract_goals(espn_team_name, score, team1, team2)
                if buts_m is not None and buts_e is not None:
                    if domicile:
                        buts_dom_marques += buts_m
                        buts_dom_encaisses += buts_e
                    else:
                        buts_ext_marques += buts_m
                        buts_ext_encaisses += buts_e
            
            if len(valid_results) >= 10:
                break
        
        nb_matchs = len(valid_results)
        if nb_matchs == 0:
            print("Aucun match trouvé.")
            FAILED_TEAMS.add(team_name)
            return []
        
        total_marques = buts_dom_marques + buts_ext_marques
        total_encaisses = buts_dom_encaisses + buts_ext_encaisses
        
        print(f"\n🗓️ {action.capitalize()} pour {espn_team_name} :")
        for match_obj in valid_results:
            print(f"ID: {match_obj['game_id']} | {match_obj['date']} | {match_obj['home_team']} vs {match_obj['away_team']} : {match_obj['score']} [{match_obj['competition']}] ({match_obj['status']})")
            # ✅ Afficher les stats si disponibles
            if match_obj.get('stats'):
                print(f"  📊 Stats: {len(match_obj['stats'])} statistiques récupérées")
                for stat_name, (val1, val2) in list(match_obj['stats'].items())[:3]:  # Afficher les 3 premières
                    print(f"    - {stat_name}: {val1} - {val2}")
                if len(match_obj['stats']) > 3:
                    print(f"    - ... et {len(match_obj['stats']) - 3} autres stats")
        
        total_points_6 = get_form_points(form_6)
        total_points_10 = get_form_points(form_10[:10])  # sécurité si <10
        
        print(f"\n📊 Forme courte (6 derniers matchs) : {' '.join(form_6)} (Total points : {total_points_6})")
        print(f"📊 Forme longue (10 derniers matchs) : {' '.join(form_10[:10])} (Total points : {total_points_10})")
        print(f"⚽ Buts marqués à domicile : {buts_dom_marques}")
        print(f"⚽ Buts encaissés à domicile : {buts_dom_encaisses}")
        print(f"⚽ Buts marqués à l'extérieur : {buts_ext_marques}")
        print(f"⚽ Buts encaissés à l'extérieur : {buts_ext_encaisses}")
        print(f"⚽ Total buts marqués : {total_marques}")
        print(f"🛡️ Total buts encaissés : {total_encaisses}")
        print(f"\n📈 Moyenne buts marqués par match : {total_marques / nb_matchs:.2f}")
        print(f"📉 Moyenne buts encaissés par match : {total_encaisses / nb_matchs:.2f}")

        # 💡 Affichage des séries
        print(f"🏠 Série domicile : {'-'.join(serie_domicile)}")
        print(f"✈️ Série extérieur : {'-'.join(serie_exterieur)}")

        return {
            "matches": valid_results,  # ✅ Maintenant c'est une liste d'objets avec nouvelle structure + STATS DÉTAILLÉES
            "moyenne_marques": total_marques / nb_matchs,
            "moyenne_encaisses": total_encaisses / nb_matchs,
            "form_6": form_6,
            "form_10": form_10[:10],
            "recent_form": form_6,  # compatibilité avec l'ancien code
            "serie_domicile": serie_domicile,
            "serie_exterieur": serie_exterieur,
            "buts_dom_marques": buts_dom_marques,
            "buts_dom_encaisses": buts_dom_encaisses,
            "buts_ext_marques": buts_ext_marques,
            "buts_ext_encaisses": buts_ext_encaisses,
            "total_marques": total_marques,
            "total_encaisses": total_encaisses,
            "total_points_6": total_points_6,
            "total_points_10": total_points_10,
            "total_points": total_points_6  # compatibilité avec l'ancien code
        }
    except Exception as e:
        print(f"Erreur scraping {espn_team_name} ({action}) : {e}")
        FAILED_TEAMS.add(team_name)
        return []

def compare_teams_basic_stats(
    t1, t2, name1, name2, match_date="N/A", match_time="N/A",
    league="N/A", country="N/A", logo_home=None, logo_away=None, résultats=None
):
    if not t1 or not t2:
        print("⚠️ Données insuffisantes pour la comparaison.")
        return

    # Vérifier si une équipe a une forme récente totalement vide (0 point)
    points1 = get_form_points(t1.get('form_6', []))
    points2 = get_form_points(t2.get('form_6', []))

    if points1 == 0:
        print(f"🚫 {name1} a une forme totalement vide (0 point), match ignoré.")
        IGNORED_ZERO_FORM_TEAMS.append(name1)
        return
    if points2 == 0:
        print(f"🚫 {name2} a une forme totalement vide (0 point), match ignoré.")
        IGNORED_ZERO_FORM_TEAMS.append(name2)
        return

    # 🏆 Récupération classement des équipes - utiliser le mapping (modifié pour récupérer le classement complet)
    pos_home, nom_classement_home, pts_home, full_standings_home = get_team_classement_position(country, league, name1)
    pos_away, nom_classement_away, pts_away, full_standings_away = get_team_classement_position(country, league, name2)

    if pos_home:
        print(f"📌 Classement de {nom_classement_home} : {pos_home}ᵉ avec {pts_home} points")
    if pos_away:
        print(f"📌 Classement de {nom_classement_away} : {pos_away}ᵉ avec {pts_away} points")

    # 💰 Récupération des cotes
    print(f"\n💰 Récupération des cotes...")
    home_espn = get_espn_name(name1)
    away_espn = get_espn_name(name2)
    
    league_info = classement_ligue_mapping.get(country, {}).get(league)
    odds_id = league_info.get("odds_id", "none") if league_info else "none"
    
    odds_data = get_odds_for_match(odds_id, name1, name2, home_espn, away_espn)

    # 🆚 Récupération des confrontations directes avec STATISTIQUES DÉTAILLÉES
    confrontations_h2h = get_h2h_confrontations(home_espn, away_espn)

    print(f"\n📅 Match prévu le {match_date} à {match_time}")
    print(f"🏆 Compétition : [{country}] {league}")
    print(f"⚔️ {name1} vs {name2}")
    
    print(f"\n🤝 Statistiques brutes :")
    print(f"{name1} ➤ Moy. buts marqués : {t1['moyenne_marques']:.2f} | Moy. encaissés : {t1['moyenne_encaisses']:.2f}")
    print(f"{name2} ➤ Moy. buts marqués : {t2['moyenne_marques']:.2f} | Moy. encaissés : {t2['moyenne_encaisses']:.2f}")

    print(f"\n📊 Forme courte (6) : {' '.join(t1['form_6'])} ({name1}) vs {' '.join(t2['form_6'])} ({name2})")
    print(f"📊 Forme longue (10) : {' '.join(t1['form_10'])} ({name1}) vs {' '.join(t2['form_10'])} ({name2})")

    print(f"🏠 Série domicile ({name1}) : {'-'.join(t1.get('serie_domicile', []))}")
    print(f"✈️ Série extérieur ({name2}) : {'-'.join(t2.get('serie_exterieur', []))}")

    # ✅ CRÉATION DE L'OBJET AVEC NOUVELLE STRUCTURE DES MATCHS + STATS DÉTAILLÉES
    prediction_obj = {
        "id": len(PREDICTIONS) + 1,
        "HomeTeam": name1,
        "AwayTeam": name2,
        "date": format_date_fr(match_date, match_time),
        "league": f"{country} - {league}",
        "type": "stats_brutes_avec_cotes_et_ia_avec_stats_detaillees_h2h_enrichi_tirs_confiance_scores_extraction_amelioree",
        "odds": odds_data,  # Cotes des bookmakers
        "stats_home": {
            "moyenne_marques": t1['moyenne_marques'],
            "moyenne_encaisses": t1['moyenne_encaisses'],
            "form_6": t1['form_6'],
            "form_10": t1['form_10'],
            "recent_form": t1['form_6'],  # compatibilité
            "total_points_6": t1.get('total_points_6', 0),
            "total_points_10": t1.get('total_points_10', 0),
            "total_points": t1.get('total_points_6', 0),  # compatibilité
            "serie_domicile": t1.get('serie_domicile', []),
            "buts_dom_marques": t1.get('buts_dom_marques', 0),
            "buts_dom_encaisses": t1.get('buts_dom_encaisses', 0),
            "buts_ext_marques": t1.get('buts_ext_marques', 0),
            "buts_ext_encaisses": t1.get('buts_ext_encaisses', 0),
            "total_marques": t1.get('total_marques', 0),
            "total_encaisses": t1.get('total_encaisses', 0)
        },
        "stats_away": {
            "moyenne_marques": t2['moyenne_marques'],
            "moyenne_encaisses": t2['moyenne_encaisses'],
            "form_6": t2['form_6'],
            "form_10": t2['form_10'],
            "recent_form": t2['form_6'],  # compatibilité
            "total_points_6": t2.get('total_points_6', 0),
            "total_points_10": t2.get('total_points_10', 0),
            "total_points": t2.get('total_points_6', 0),  # compatibilité
            "serie_exterieur": t2.get('serie_exterieur', []),
            "buts_dom_marques": t2.get('buts_dom_marques', 0),
            "buts_dom_encaisses": t2.get('buts_dom_encaisses', 0),
            "buts_ext_marques": t2.get('buts_ext_marques', 0),
            "buts_ext_encaisses": t2.get('buts_ext_encaisses', 0),
            "total_marques": t2.get('total_marques', 0),
            "total_encaisses": t2.get('total_encaisses', 0)
        },
        # ✅ NOUVEAUX CHAMPS : MATCHS COMPLETS AVEC NOUVELLE STRUCTURE + STATS DÉTAILLÉES
        "last_matches_home": t1.get('matches', []),  # Les 10 vrais matchs avec objets + STATS DÉTAILLÉES
        "last_matches_away": t2.get('matches', []),  # Les 10 vrais matchs avec objets + STATS DÉTAILLÉES
        # ✅ CLASSEMENT DES ÉQUIPES
        "classement": {
            name1: {"position": pos_home, "points": pts_home} if pos_home else None,
            name2: {"position": pos_away, "points": pts_away} if pos_away else None
        },
        # ✅ CLASSEMENT COMPLET DE LA LIGUE
        "classement_complet": full_standings_home if full_standings_home else full_standings_away,
        # ✅ CONFRONTATIONS DIRECTES AVEC STATISTIQUES DÉTAILLÉES
        "confrontations_saison_derniere": confrontations_h2h,
        # Anciens champs conservés pour compatibilité
        "logo_home": logo_home,
        "logo_away": logo_away,
        "classement_home": pos_home,
        "classement_away": pos_away,
        "points_classement_home": pts_home,
        "points_classement_away": pts_away,
        "nom_classement_home": nom_classement_home,
        "nom_classement_away": nom_classement_away,
        "country_fr": f"{country} - {league}"
    }

    # 🎲 NOUVEAU : Calcul des probabilités statistiques Monte-Carlo (garde les données mais ne les inclut PAS dans le prompt)
    print(f"\n🎯 Calcul des probabilités statistiques Monte-Carlo...")
    probabilites_mc = simulation_match_montecarlo(
        prediction_obj["stats_home"], 
        prediction_obj["stats_away"],
        h2h_data=confrontations_h2h,
        n=20000
    )

    print("\n🎯 PROBABILITÉS STATISTIQUES (Monte-Carlo + base mondiale + H2H)")
    print(json.dumps(probabilites_mc, indent=2, ensure_ascii=False))

    # Ajouter au JSON final (reste disponible dans les données mais PAS dans le prompt IA)
    prediction_obj["Probabilites"] = probabilites_mc

    # 🔮 Génération d'analyse IA avec DeepSeek (AVEC RETRY AUTOMATIQUE + STATS DÉTAILLÉES + NOUVELLES FONCTIONNALITÉS SANS MONTE-CARLO DANS LE PROMPT)
    print(f"\n🧠 Lancement de l'analyse IA DeepSeek avec retry automatique + stats détaillées + H2H enrichi + confiance + scores (sans Monte-Carlo dans le prompt)...")
    prompt = generate_detailed_prompt(prediction_obj)
    analyse_ia = call_deepseek_analysis(prompt, max_retries=5)  # ✅ 5 tentatives max

    # ✅ NOUVELLES EXTRACTIONS AMÉLIORÉES AVEC SUPPORT DES DEUX FORMATS
    confiance_pourcentage = extract_confidence_percentage(analyse_ia)
    prediction_principale = extract_prediction_principale(analyse_ia)
    corners_prevu = extract_corners_prevu(analyse_ia)  # Gardé dans la structure mais IA ne prédit plus
    tirs_cadres_prevu = extract_tirs_cadres_prevu(analyse_ia)  # Gardé dans la structure mais IA ne prédit plus
    scores_probables = extract_scores_probables(analyse_ia)

    prediction_obj["analyse_ia"] = analyse_ia
    prediction_obj["confiance_pourcentage"] = confiance_pourcentage  # ✅ Champ dédié
    prediction_obj["prediction_principale"] = prediction_principale  # ✅ Nouveau champ
    prediction_obj["corners_prevu"] = corners_prevu  # ✅ Gardé mais IA ne prédit plus
    prediction_obj["tirs_cadres_prevu"] = tirs_cadres_prevu  # ✅ Gardé mais IA ne prédit plus
    prediction_obj["scores_probables"] = scores_probables  # ✅ Nouveau champ
    
    print(f"\n🧠 Analyse IA DeepSeek :\n{'='*60}")
    print(analyse_ia)
    print(f"{'='*60}")
    
    # ✅ AFFICHAGE DES EXTRACTIONS
    if confiance_pourcentage is not None:
        print(f"\n📊 Pourcentage de confiance extrait : {confiance_pourcentage}%")
    else:
        print(f"\n⚠️ Pourcentage de confiance non détecté dans l'analyse")
    
    if prediction_principale:
        print(f"🎯 Prédiction principale extraite : {prediction_principale}")
    
    if corners_prevu:
        print(f"📐 Corners prévus extraits (présent mais IA ne prédit plus) : {corners_prevu}")
    
    if tirs_cadres_prevu:
        print(f"🎯 Tirs cadrés prévus extraits (présent mais IA ne prédit plus) : {tirs_cadres_prevu}")
    
    if scores_probables:
        print(f"⚽ Scores probables extraits : {scores_probables}")

    PREDICTIONS.append(prediction_obj)
    if résultats is not None:
        résultats.append(prediction_obj)

    print("\n📚 Note : Statistiques brutes avec cotes + analyse IA DeepSeek avec retry + matchs complets avec stats détaillées + classement complet + H2H enrichi avec stats + confiance + scores + extraction améliorée des deux formats + PROBABILITÉS MONTE-CARLO INTÉGRÉES (non incluses dans le prompt IA).")

def process_team(team_name, return_data=False):
    print(f"\n🧠 Analyse pour l'équipe : {get_espn_name(team_name)}")
    data = scrape_team_data(team_name, 'results')
    print("\n" + "-" * 60 + "\n")
    return data if return_data else None

# ✅ MODIFIÉ : Fonction de sauvegarde avec NOUVEAU nom de fichier simple
def sauvegarder_stats_brutes_json(predictions_simples, date_str):
    total_predictions = len(predictions_simples)

    for p in predictions_simples:
        p['country_fr'] = p['league']

    data_complete = {
        "metadata": {
            "date_generation": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "date_matchs": date_str,
            "version_algorithme": "8.3 - STATISTIQUES BRUTES + FORMES 6/10 + POINTS CLASSEMENT + COTES + ANALYSE IA DEEPSEEK ENRICHIE + MATCHS COMPLETS AVEC STATS DÉTAILLÉES + CLASSEMENT COMPLET + H2H ENRICHI AVEC STATS + CONFIANCE EXTRAITE + SCORES + RETRY IA + EXTRACTION AMÉLIORÉE 2 FORMATS + PROBABILITÉS MONTE-CARLO (NON INCLUSES DANS PROMPT IA)",
            "total_predictions": total_predictions,
            "mode": "stats_brutes_avec_cotes_et_ia_complete_enrichie_retry_nouvelle_structure_avec_stats_detaillees_h2h_enrichi_confiance_extraite_scores_extraction_amelioree_2_formats_montecarlo_hors_prompt",
            "note": "Collecte des statistiques brutes complètes : moyennes, formes récentes (6 et 10 matchs), séries domicile/extérieur, classements avec points + cotes des bookmakers + analyse IA DeepSeek ENRICHIE avec matchs détaillés (nouvelle structure objet avec game_id, date, home_team, away_team, score, status, competition + STATS DÉTAILLÉES ESPN) + classement complet + confrontations directes H2H élargies AVEC STATS DÉTAILLÉES + pourcentage confiance EXTRAIT AUTOMATIQUEMENT + 2 scores probables + retry automatique IA + suppression 'match nul' + EXTRACTION AMÉLIORÉE support des 2 formats (**FORMAT** et FORMAT simple) + PROBABILITÉS MONTE-CARLO autonomes (calculées mais NON incluses dans le prompt IA)",
            "ia_model": "deepseek-r1-distill-llama-70b",
            "groq_keys_count": len(groq_keys),
            "monte_carlo": {
                "enabled": True,
                "iterations": 20000,
                "calibrage": "moyennes_internationales + statistiques_équipes + ajustement_h2h",
                "probabilites_calculees": ["1x2", "double_chance", "over_under", "btts", "resultat_total", "scores_probables"],
                "inclus_dans_prompt_ia": False
            },
            "nouveautes_v8_3_modifiees": [
                "🎲 Module de probabilités Monte-Carlo intégré (20 000 simulations)",
                "🔢 Calibrage avec moyennes internationales FIFA/UEFA",
                "🆚 Ajustement automatique selon les confrontations H2H",
                "📊 Probabilités 1X2, Double Chance, Over/Under (0.5→5.5), BTTS",
                "🎯 Scores exacts les plus probables calculés statistiquement",
                "❌ MODIFICIATION : Probabilités Monte-Carlo NON incluses dans le prompt IA",
                "❌ MODIFICIATION : IA ne prédit plus corners et tirs cadrés (champs gardés dans structure)",
                "📁 MODIFICIATION : Nom de fichier simplifié prédiction-YYYY-MM-DD-analyse-ia.json",
                "✅ Maintien de toutes les autres fonctionnalités avancées v8.2"
            ]
        },
        "statistiques_brutes_avec_ia_hors_montecarlo": {
            "count": len(predictions_simples),
            "details": predictions_simples
        }
    }
    
    # ✅ NOUVEAU NOM DE FICHIER SIMPLE COMME DEMANDÉ
    nom_fichier = f"prédiction-{date_str}-analyse-ia.json"
    
    with open(nom_fichier, "w", encoding="utf-8") as f:
        json.dump(data_complete, f, ensure_ascii=False, indent=2)
    print(f"✅ Statistiques brutes complètes avec cotes et analyse IA enrichie sauvegardées dans : {nom_fichier}")
    print(f"📊 Total: {total_predictions} analyses complètes avec cotes + IA DeepSeek enrichie + retry + H2H enrichi avec stats + nouvelles fonctionnalités + extraction améliorée 2 formats + PROBABILITÉS MONTE-CARLO (hors prompt IA)")
    
    return nom_fichier

def save_failed_teams_json(failed_teams, date_str):
    chemin = f"teams_failed_{date_str}.json"
    data = {"teams_failed": sorted(list(failed_teams))}
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"❗ Liste des équipes sans données sauvegardée dans : {chemin}")

def save_ignored_teams_json(ignored_teams, date_str):
    chemin = f"teams_ignored_zero_form_{date_str}.json"
    data = {"teams_ignored_zero_form": sorted(list(set(ignored_teams)))}
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"🛑 Équipes ignorées pour forme nulle sauvegardées dans : {chemin}")

def git_commit_and_push(filepath):
    try:
        subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
        subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "add", filepath], check=True)
        subprocess.run(["git", "commit", "-m", f"Update predictions {datetime.now().strftime('%Y-%m-%d')}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ Fichier poussé avec succès sur GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur Git : {e}")

def main():
    print("📊 Lancement de l'analyse des matchs du jour...")
    get_today_matches_filtered()
    print(f"\n✅ Analyse terminée !")

if __name__ == "__main__":
    main()