"""
Example using the components provided by spacy-streamlit in an existing app.
Prerequisites:
python -m spacy download en_core_web_sm
"""
from visualizer import visualize

models = ["en_core_web_sm", "en_core_web_md"]
default_text = "Sundar Pichai is the CEO of Google."
visualize(models, default_text,
          sidebar_title="Sherpa demo",
          sidebar_description="Customizable Sherpa demonstration",
          show_json_doc=False,
          show_meta=False,
          show_config=False,
          show_visualizer_select=False,
          show_pipeline_info=False)
