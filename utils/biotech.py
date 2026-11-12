"""Radar d'essais cliniques Phase 2/3 via ClinicalTrials.gov API v2."""
from datetime import date, timedelta
import requests, pandas as pd, streamlit as st

# Sponsor ClinicalTrials.gov -> ticker (à personnaliser)
BIOTECHS = {"Moderna": "MRNA", "Vertex Pharmaceuticals": "VRTX", "CRISPR Therapeutics": "CRSP",
            "Novavax": "NVAX", "Biohaven": "BHVN", "Madrigal Pharmaceuticals": "MDGL",
            "Viking Therapeutics": "VKTX", "Insmed": "INSM", "Sarepta Therapeutics": "SRPT",
            "Intellia Therapeutics": "NTLA"}
API = "https://clinicaltrials.gov/api/v2/studies"

@st.cache_data(ttl=6 * 3600)  # 6 h
def get_trials(sponsors: tuple, months: int = 9) -> pd.DataFrame:
    end = date.today() + timedelta(days=30 * months)
    rows = []
    for sp in sponsors:
        params = {"query.spons": sp, "pageSize": 15,
                  "filter.overallStatus": "RECRUITING|ACTIVE_NOT_RECRUITING|NOT_YET_RECRUITING",
                  "filter.advanced": f"AREA[Phase](PHASE2 OR PHASE3) AND "
                                     f"AREA[PrimaryCompletionDate]RANGE[{date.today()},{end}]"}
        try:
            r = requests.get(API, params=params, timeout=20).json()
        except Exception:
            continue
        for s in r.get("studies", []):
            p = s["protocolSection"]
            ph = p.get("designModule", {}).get("phases", [])
            rows.append({
                "Entreprise": f"{sp} ({BIOTECHS.get(sp, '?')})", "Ticker": BIOTECHS.get(sp),
                "Molécule": ", ".join(i["name"] for i in p.get("armsInterventionsModule", {}).get("interventions", [])[:2]),
                "Pathologie": ", ".join(p.get("conditionsModule", {}).get("conditions", [])[:2]),
                "Phase": "/".join(x.replace("PHASE", "P") for x in ph),
                "Résultats estimés": p.get("statusModule", {}).get("primaryCompletionDateStruct", {}).get("date"),
                "Statut": p["statusModule"].get("overallStatus"),
                "NCT": p["identificationModule"]["nctId"],
                "Titre": p["identificationModule"].get("briefTitle", "")})
    df = pd.DataFrame(rows)
    return df.sort_values("Résultats estimés").reset_index(drop=True) if not df.empty else df
