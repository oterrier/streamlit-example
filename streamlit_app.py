"""
Example using the components provided by spacy-streamlit in an existing app.
Prerequisites:
python -m spacy download en_core_web_sm
"""
import streamlit as st
from visualizer import visualize

default_text = "Sundar Pichai is the CEO of Google."
# Reads
projects = None
plans = None
visualize(projects, plans, default_text,
          sidebar_title="Sherpa demo",
          sidebar_description="Customizable Sherpa demonstration",
          show_visualizer_select=False)
