"""
Example using the components provided by spacy-streamlit in an existing app.
Prerequisites:
python -m spacy download en_core_web_sm
"""
import streamlit as st
from visualizer import visualize

default_text = """Un retour suite à votre accueil me semble évident.

Je suis satisafaite de la MAAF.

Ce que je veux c' est avoir la meilleure couverture à tous points.
Peut-être vais-je ramener tous mes contrats à la MAAF ou bien à la MAIF?
Pour tout grouper.

Très cordialement,

Mme Valérie LAVRIL
"""
# Reads
projects = None
plans = None
visualize(projects, plans, default_text,
          sidebar_title="Sherpa demo",
          sidebar_description="Customizable Sherpa demonstration",
          show_visualizer_select=False)
