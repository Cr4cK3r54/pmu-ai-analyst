import streamlit as st
import google.generativeai as genai
import requests
import json
from datetime import datetime, timedelta
import asyncio
from playwright.async_api import async_playwright

# Configuration de la page
st.set_page_config(page_title="PMU AI Analyst Pro", page_icon="🐎", layout="wide")

# --- 0. SYSTÈME D'AUTHENTIFICATION ---
def check_login(username, password):
    """Vérifie les identifiants"""
    VALID_USERNAME = "Cr4cK3r"
    VALID_PASSWORD = "Tom05101990-Oe"
    return username == VALID_USERNAME and password == VALID_PASSWORD

def login_page():
    """Page de connexion"""
    st.title("🔐 Connexion - PMU AI Analyst Pro")
    st.markdown("Accès réservé - Veuillez vous connecter")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("Se connecter", type="primary")
            
            if submit:
                if check_login(username, password):
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects")

# Vérifier si l'utilisateur est connecté
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    login_page()
    st.stop()  # Arrête l'exécution si pas connecté

# --- 1. CONFIGURATION ---
st.sidebar.title("⚙️ Configuration")
st.sidebar.success(f"👤 Connecté : {st.session_state['username']}")
if st.sidebar.button("🚪 Se déconnecter"):
    st.session_state['authenticated'] = False
    st.rerun()

api_key = st.sidebar.text_input("Ta clé API Gemini", type="password", help="Obtenue sur Google AI Studio")
if api_key:
    genai.configure(api_key=api_key)

# --- 2. API PMU HISTORIQUE (2004-2026) ---
PMU_API_URL = "https://open-pmu-api.vercel.app/api/arrivees"

def get_historical_results(hippodrome=None, date=None):
    """Récupère l'historique des courses depuis l'API PMU"""
    params = {}
    if hippodrome:
        params['hippo'] = hippodrome
    if date:
        params['date'] = date
    
    try:
        response = requests.get(PMU_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if not data.get('error'):
                return data.get('message', [])
        return []
    except Exception as e:
        st.error(f"Erreur API PMU: {e}")
        return []

# --- 3. WEB SCRAPER POUR LES PARTANTS DU JOUR ---
async def scrape_todays_runners():
    """Scrape les partants du jour depuis Zone-Turf"""
    runners_data = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto("https://www.zone-turf.fr/programme-pmu", timeout=30000)
            await page.wait_for_load_state("networkidle")
            
            courses = await page.query_selector_all('.course-item')
            
            for course in courses[:5]:
                try:
                    nom_course = await course.query_selector('.course-name')
                    nom = await nom_course.inner_text() if nom_course else "Course inconnue"
                    
                    hippo = await course.query_selector('.hippodrome-name')
                    hippodrome = await hippo.inner_text() if hippo else "Inconnu"
                    
                    heure = await course.query_selector('.course-time')
                    time = await heure.inner_text() if heure else ""
                    
                    partants = await course.query_selector_all('.runner-item')
                    runners_list = []
                    
                    for runner in partants:
                        try:
                            num = await runner.query_selector('.runner-number')
                            numero = await num.inner_text() if num else "?"
                            
                            name = await runner.query_selector('.runner-name')
                            nom_cheval = await name.inner_text() if name else "Inconnu"
                            
                            jockey = await runner.query_selector('.jockey-name')
                            nom_jockey = await jockey.inner_text() if jockey else "Inconnu"
                            
                            entraineur = await runner.query_selector('.trainer-name')
                            nom_entraineur = await entraineur.inner_text() if entraineur else "Inconnu"
                            
                            musique = await runner.query_selector('.music')
                            mus = await musique.inner_text() if musique else ""
                            
                            cote = await runner.query_selector('.odds')
                            cote_prob = await cote.inner_text() if cote else "N/A"
                            
                            runners_list.append({
                                "numero": numero.strip(),
                                "nom": nom_cheval.strip(),
                                "jockey": nom_jockey.strip(),
                                "entraineur": nom_entraineur.strip(),
                                "musique": mus.strip(),
                                "cote": cote_prob.strip()
                            })
                        except Exception as e:
                            continue
                    
                    runners_data.append({
                        "hippodrome": hippodrome.strip(),
                        "course": nom.strip(),
                        "heure": time.strip(),
                        "partants": runners_list
                    })
                except Exception as e:
                    continue
            
            await browser.close()
            
    except Exception as e:
        st.error(f"Erreur lors du scraping: {e}")
        return None
    
    return runners_data

def run_scraper():
    """Wrapper pour exécuter le scraper async dans Streamlit"""
    return asyncio.run(scrape_todays_runners())

# --- 4. MOTEUR D'ANALYSE IA AMÉLIORÉ ---
def analyze_race_with_gemini(race_data, historical_data):
    if not api_key:
        return "⚠️ Veuillez entrer votre clé API Gemini dans la barre latérale."

    hist_summary = []
    for race in historical_data[:15]:
        hist_summary.append({
            "date": race.get('date'),
            "lieu": race.get('lieu'),
            "distance": race.get('distance'),
            "type": race.get('type'),
            "arrivee": race.get('arrivee'),
            "partants": race.get('partants')
        })

    prompt = f"""
    Agis comme un expert hippique professionnel et un data scientist spécialisé dans les courses PMU.
    
    📊 DONNÉES DE LA COURSE DU JOUR :
    - Hippodrome : {race_data['hippodrome']}
    - Course : {race_data['course']}
    - Heure : {race_data['heure']}
    - Partants : {json.dumps(race_data['partants'], ensure_ascii=False, indent=2)}
    
    📈 HISTORIQUE DES COURSES SUR CET HIPPODROME (données réelles 2004-2026) :
    {json.dumps(hist_summary, ensure_ascii=False, indent=2)}
    
    🎯 TA MISSION D'ANALYSE APPROFONDIE :
    
    1. **ANALYSE DES TENDANCES HISTORIQUES** :
       - Sur les 15 dernières courses à {race_data['hippodrome']}, quels numéros sortent le plus souvent dans le Top 3 ?
       - Y a-t-il des patterns récurrents ?
       - Le type de course influence-t-il les résultats ?
    
    2. **ANALYSE DES PARTANTS DU JOUR** :
       - Croise la "musique" avec l'historique de l'hippodrome
       - Analyse les cotes probables
       - Le jockey est-il en forme ?
    
    3. **DÉTECTION DES PIÈGES** :
       - Identifie 1-2 chevaux qui semblent forts mais présentent des signaux faibles
    
    4. **RECOMMANDATIONS PRÉCISES** :
       - 🏆 **Le Favori Fiable** : Cheval le plus solide logiquement
       - 💎 **L'Outsider Pertinent** : Cheval sous-estimé mais dont l'analyse est positive
       - ⚠️ **Le Piège à éviter** : Cheval à écarter absolument
    
    📝 FORMAT DE RÉPONSE (en Markdown clair pour un novice) :
    
    ### 📊 Analyse Contextuelle
    [3-4 phrases sur les tendances de l'hippodrome et les conditions du jour]
    
    ### 🏆 Recommandations de Jeu
    - **Favori** : [Numéro] - [Nom]
      - Raison : [Explication précise basée sur les données]
      - Confiance : [Étoiles ⭐⭐⭐⭐⭐]
    
    - **Outsider** : [Numéro] - [Nom]
      - Raison : [Pourquoi ce cheval est sous-estimé]
      - Potentiel : [Étoiles ⭐⭐⭐⭐]
    
    ### ⚠️ Alertes et Pièges
    - **À éviter** : [Numéro] - [Nom]
      - Pourquoi : [Explication claire du risque]
    
    ### 💡 Conseil de Jeu
    [Type de pari recommandé : Simple, Couplé, Tiercé, etc. avec justification]
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erreur lors de l'appel à l'IA : {e}"

# --- 5. INTERFACE UTILISATEUR ---
st.title("🐎 PMU AI Analyst Pro")
st.markdown("Analyse quotidienne intelligente avec données historiques réelles (2004-2026) + Partants du jour en temps réel")

# Bouton de récupération
if st.button("🔄 Récupérer les courses du jour", type="primary"):
    with st.spinner("Scraping des partants du jour en cours..."):
        todays_races = run_scraper()
        
        if todays_races:
            st.session_state['todays_races'] = todays_races
            st.success(f"✅ {len(todays_races)} courses récupérées")
        else:
            st.error("❌ Impossible de récupérer les courses.")

# Affichage des courses
if 'todays_races' in st.session_state and st.session_state['todays_races']:
    st.markdown("---")
    st.subheader("📋 Courses du jour")
    
    race_options = [f"{r['heure']} - {r['hippodrome']} - {r['course']}" for r in st.session_state['todays_races']]
    selected_race = st.selectbox("Choisir une course à analyser", race_options)
    
    if st.button("🔍 Lancer l'analyse IA", type="primary"):
        selected_index = race_options.index(selected_race)
        race_data = st.session_state['todays_races'][selected_index]
        
        with st.spinner("Récupération de l'historique et analyse en cours..."):
            st.info(f"📡 Connexion à l'API PMU pour récupérer l'historique de {race_data['hippodrome']}...")
            historical_data = get_historical_results(hippodrome=race_data['hippodrome'])
            
            if historical_data:
                st.success(f"✅ {len(historical_data)} courses historiques récupérées")
                
                with st.expander("📊 Voir les partants du jour"):
                    st.json(race_data)
                
                with st.expander("📈 Voir l'historique (15 dernières courses)"):
                    st.json(historical_data[:15])
                
                st.markdown("---")
                st.subheader("🧠 Analyse de l'Intelligence Artificielle")
                analysis = analyze_race_with_gemini(race_data, historical_data)
                st.markdown(analysis)
                
                st.info("💡 **Rappel** : Cette analyse combine les données historiques réelles avec les partants du jour. "
                       "Les courses restent imprévisibles. Jouez avec modération.")
            else:
                st.error("❌ Impossible de récupérer les données historiques.")
