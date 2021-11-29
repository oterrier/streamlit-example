import streamlit as st
from sherpa_streamlit import visualize

default_text = """Un retour suite à votre accueil me semble évident.
Je suis un fidèle depuis des années.
Ce que je veux c' est avoir la meilleure couverture à tous points.
Peut-être vais-je ramener tous mes contrats à la MAAF ou bien à la MAIF ou alors AXA?
Très cordialement,
"""
# Reads
projects = None
annotators = None
visualize(default_text,
          projects, annotators,
          favorite_only=False,
          sidebar_title="KAIRNTECH Sherpa",
          sidebar_description="Customizable Sherpa demonstration")
