import streamlit as st
import spacy
import base64


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_model(name: str) -> spacy.language.Language:
    """Load a spaCy model."""
    # return spacy.load(name)
    return None


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def process_text(model_name: str, text: str) -> spacy.tokens.Doc:
    """Process a text and create a Doc object."""
    nlp = load_model(model_name)
    return text


def get_svg(svg: str, style: str = "", wrap: bool = True):
    """Convert an SVG to a base64-encoded image."""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}" style="{style}"/>'
    return get_html(html) if wrap else html


def get_html(html: str):
    """Convert HTML so it can be rendered."""
    WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""
    # Newlines seem to mess with the rendering
    html = html.replace("\n", " ")
    return WRAPPER.format(html)


LOGO_SVG = """<svg version="1.1" id="Calque_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
	 viewBox="0 0 189.44 181.76" style="enable-background:new 0 0 189.44 181.76;" xml:space="preserve">
<g>
	<g>
		<path d="M168.92,70.54c-11.31-39.15-52.13-56.9-92.2-48.88c-39.95,8-73.05,27.97-63.43,55.18
			c13.58,38.42,64.88,96.69,104.03,85.39C156.47,150.93,180.22,109.69,168.92,70.54z M122.11,140.92
			c-29.13,8.41-72.68-6.58-83.03-35.08c-8.93-24.58,29.22-62.7,58.35-71.12s53.89,5.97,62.31,35.1S151.23,132.51,122.11,140.92z"/>
		<path d="M128.99,59.47C111.86,54.85,81,61.42,76.37,78.54c-4.62,17.12,18.74,38.32,35.87,42.94c17.12,4.62,34.75-5.51,39.38-22.63
			C156.24,81.73,146.11,64.1,128.99,59.47z"/>
	</g>
</g>
</svg>"""

LOGO = get_svg(LOGO_SVG, wrap=False, style="max-width: 100%; margin-bottom: 25px")
