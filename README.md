# Déploiement (Streamlit Community Cloud, gratuit)
1. Poussez ce dossier sur un dépôt GitHub (public ou privé).
2. share.streamlit.io → "New app" → dépôt, branche, fichier `app.py`.
3. Advanced settings → Secrets :
   OPENAI_API_KEY = "sk-..."
   OPENAI_MODEL = "gpt-4o-mini"        # optionnel
   OPENAI_BASE_URL = "https://..."     # optionnel (API compatible)
4. Deploy, puis ouvrez l'URL sur votre téléphone → "Ajouter à l'écran d'accueil".
⚠️ Le disque du Cloud est éphémère : data/portfolio.json peut être réinitialisé au redémarrage.
Lancement local : pip install -r requirements.txt && streamlit run app.py
