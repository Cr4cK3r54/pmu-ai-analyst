import streamlit as st
import google.generativeai as genai
import requests
import json
from datetime import datetime, timedelta
import asyncio
from playwright.async_api import async_playwright
import os

# Configuration de la page
st.set_page_config(page_title="PMU AI Analyst Pro", page_icon="🐎", layout="wide")

# --- 0. SYSTÈME D'AUTHENTIFICATION (SÉCURISÉ) ---
def check_login(username, password):
    """Vérifie les identifiants depuis les secrets Streamlit"""
    # Récupération des secrets
    valid_username = st.secrets.get("APP_USERNAME", "")
    valid_password = st.secrets.get("APP_PASSWORD", "")
    
    # Si les secrets ne sont pas configurés, afficher un message d'erreur
    if not valid_username or not valid_password:
        st.error("⚠️ Configuration manquante : Les identifiants n'ont pas été configurés dans les secrets Streamlit.")
        return False
    
    return username == valid_username and password == valid_password

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

# Récupération de la clé API Gemini depuis les secrets
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Ta clé API Gemini", type="password", help="Obtenue sur Google AI Studio")
if api_key:
    genai.configure(api_key=api_key)

# ... (le reste du code reste identique)