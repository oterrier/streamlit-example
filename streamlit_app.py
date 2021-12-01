import streamlit as st
from sherpa_streamlit import visualize

default_text = """This is a sample text.
With two lines.
"""
# Reads
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)
visualize(default_text,
          favorite_only=False,
          sidebar_title="KAIRNTECH Sherpa",
          sidebar_description="Customizable Sherpa demonstration")
