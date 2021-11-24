"""
Example using the components provided by spacy-streamlit in an existing app.
Prerequisites:
python -m spacy download en_core_web_sm
"""
import streamlit as st
from visualizer import visualize

models = ["en_core_web_sm", "en_core_web_md"]
default_text = "Sundar Pichai is the CEO of Google."
# Reads
if 'token' in st.session_state:
    st.write(st.session_state.token)
if 'project' in st.session_state:
    st.write(st.session_state.project)
if 'plan' in st.session_state:
    st.write(st.session_state.plan)
visualize(models, default_text,
          sidebar_title="Sherpa demo",
          sidebar_description="Customizable Sherpa demonstration",
          show_json_doc=False,
          show_meta=False,
          show_config=False,
          show_visualizer_select=False,
          show_pipeline_info=False)
