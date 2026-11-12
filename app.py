import pandas as pd, plotly.express as px, streamlit as st
from utils import finance as F, biotech as B, ai_agent as AI

st.set_page_config(page_title="Biotech Dashboard", page_icon="📈", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown("""<style>
.block-container{padding:1rem .8rem 3rem}
[data-testid=stMetric]{background:#1A1F2B;border-radius:12px;padding:10px 14px}
button[role=tab]{font-size:.85rem}</style>""", unsafe_allow_html=True)
st.title("📈 Biotech & Bourse")
st.caption("Information éducative — pas un conseil en investissement.")
t1, t2, t3, t4, t5 = st.tabs(["💼 Portefeuille", "🧬 Radar FDA", "🐦 Veille X", "📅 Calendrier", "🎯 Screener IA"])

if "pf" not in st.session_state:
    st.session_state.pf = F.load_portfolio()

# ---------- 1. PORTEFEUILLE ----------
with t1:
    with st.expander("✏️ Modifier mes positions"):
        ed = st.data_editor(st.session_state.pf, num_rows="dynamic", use_container_width=True, key="ed")
        if st.button("💾 Sauvegarder"):
            F.save_portfolio(ed); st.session_state.pf = ed; st.cache_data.clear(); st.rerun()
    pf = F.enrich(st.session_state.pf.dropna(subset=["Ticker"]))
    inv = (pf["PRU"] * pf["Quantité"]).sum(); val = pf["Valeur"].sum()
    c1, c2 = st.columns(2)
    c1.metric("Valorisation", f"{val:,.0f}")
    c2.metric("Plus/moins-value", f"{val-inv:,.0f}", f"{(val/inv-1)*100 if inv else 0:.1f}%")
    if not pf.empty:
        st.plotly_chart(px.pie(pf, names="Ticker", values="Valeur", hole=.55,
                               template="plotly_dark").update_layout(height=300, margin=dict(t=10, b=10)),
                        use_container_width=True)
        for _, r in pf.iterrows():  # cartes lisibles sur mobile
            with st.container(border=True):
                a, b, c = st.columns([1.2, 1, 1])
                a.markdown(f"**{r.Ticker}**  \n{r.Quantité:g} × {r.Cours:.2f}")
                b.metric("Jour", f"{r.Cours:.2f}", f"{r['Var %']:.2f}%")
                c.metric("PV latente", f"{r.PV:,.0f}", f"{r['PV %']:.1f}%")

# ---------- 2. RADAR FDA ----------
with t2:
    sel = st.multiselect("Sociétés suivies", list(B.BIOTECHS), default=list(B.BIOTECHS)[:5])
    months = st.slider("Horizon (mois)", 1, 18, 9)
    df = B.get_trials(tuple(sel), months)
    if df.empty:
        st.info("Aucun essai trouvé.")
    else:
        st.dataframe(df[["Entreprise", "Molécule", "Pathologie", "Phase", "Résultats estimés", "Statut"]],
                     use_container_width=True, hide_index=True)
        pick = st.selectbox("Essai", df.index, format_func=lambda i: f"{df.Ticker[i]} · {df.Molécule[i][:30]} · {df.NCT[i]}")
        if st.button("🤖 Analyser le catalyseur avec l'IA"):
            r = df.loc[pick]
            news = AI.fmt(AI.web_search(f"{r.Entreprise} {r.Molécule} {r.Pathologie} trial", 6, news=True))
            with st.spinner("Analyse…"):
                st.markdown(AI.ask("Résume l'enjeu scientifique, la probabilité de succès typique de cette phase, le potentiel "
                                   "boursier (upside/downside), le risque de dilution et un plan de gestion du risque.",
                                   f"{r.to_dict()}\nActualités:\n{news}"))

# ---------- 3. VEILLE X ----------
with t3:
    q = st.text_input("Sujet", "biotech catalyst FDA stocks")
    if st.button("🔎 Scanner X"):
        res = AI.web_search(f"site:x.com {q}", 20) + AI.web_search(f"site:x.com $ {q} bullish bearish", 10)
        if not res: st.warning("Aucun résultat (DuckDuckGo limite parfois les requêtes).")
        with st.spinner("Synthèse…"):
            st.markdown(AI.ask("Synthétise les discussions chaudes, liste les tickers ($XXX) les plus mentionnés avec un sentiment "
                               "(Haussier/Baissier/Spéculatif), ignore le spam/pump évident, signale la fiabilité limitée de la source.",
                               AI.fmt(res)))
        with st.expander("Sources"): st.markdown(AI.fmt(res))

# ---------- 4. CALENDRIER ----------
with t4:
    wl = st.text_input("Watchlist (séparée par des virgules)", "VRTX,CRSP,NVAX")
    tks = tuple(dict.fromkeys(list(st.session_state.pf["Ticker"].dropna()) + [x.strip().upper() for x in wl.split(",") if x.strip()]))
    e = F.get_earnings(tks)
    if e.empty: st.info("Pas de dates de résultats disponibles.")
    for _, r in e.iterrows():
        st.metric(r.Ticker, r["Résultats"].strftime("%d/%m/%Y"), f"J{(r['Résultats'].date()-pd.Timestamp.today().date()).days:+d}", delta_color="off")
    st.subheader("Macro de la semaine")
    if st.button("🌍 Charger les événements macro"):
        res = AI.web_search("Fed ECB CPI inflation rate decision calendar this week", 12, news=True)
        st.markdown(AI.ask(f"Nous sommes le {pd.Timestamp.today():%d/%m/%Y}. Liste les événements macro majeurs de la semaine "
                           "(taux Fed/BCE, CPI…) et leur impact probable sur les biotechs (sensibles aux taux).", AI.fmt(res)))

# ---------- 5. SCREENER IA ----------
with t5:
    univ = st.text_area("Univers (tickers)", "MRNA,VRTX,CRSP,NVAX,VKTX,MDGL,INSM,SRPT,NTLA")
    if st.button("🎯 Lancer le screener"):
        with st.spinner("Calcul des indicateurs…"):
            m = pd.DataFrame([F.get_metrics(t.strip().upper()) for t in univ.split(",") if t.strip()])
        st.dataframe(m, use_container_width=True, hide_index=True)
        st.markdown(AI.ask("Top 3 des opportunités à surveiller. Pour chacune : Thèse d'investissement, Catalyseur proche, "
                           "Niveau de risque (Faible/Moyen/Élevé + justification : runway, dilution, RSI, volume). "
                           "Base-toi uniquement sur ces données et signale ce qu'il faudrait vérifier.", m.to_string()))
