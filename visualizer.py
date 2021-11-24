import html
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Callable

import pandas as pd
import plac
import streamlit as st
from annotated_text import div, annotation
from collections_extended import RangeMap

# fmt: off
from htbuilder import HtmlElement

from util import LOGO, get_svg, get_token, get_projects, get_plans, get_project_by_label, get_plan_by_label, \
    get_project, get_plan, annotate_with_plan

# from .util import load_model, process_text, get_svg, get_html, LOGO

NER_ATTRS = ["text", "label_", "start", "end", "start_char", "end_char"]
TOKEN_ATTRS = ["idx", "text", "lemma_", "pos_", "tag_", "dep_", "head", "morph",
               "ent_type_", "ent_iob_", "shape_", "is_alpha", "is_ascii",
               "is_digit", "is_punct", "like_num", "is_sent_start"]
# fmt: on
FOOTER = """<span style="font-size: 0.75em">&hearts; Built with [`spacy-streamlit`](https://github.com/explosion/spacy-streamlit)</span>"""


def visualize(
        projects: List[str] = None,
        plans: List[str] = None,
        default_text: str = "",
        visualizers: List[str] = [],
        ner_labels: Optional[List[str]] = None,
        ner_attrs: List[str] = NER_ATTRS,
        similarity_texts: Tuple[str, str] = ("apple", "orange"),
        token_attrs: List[str] = TOKEN_ATTRS,
        show_project: bool = True,
        show_plan: bool = True,
        show_visualizer_select: bool = False,
        sidebar_title: Optional[str] = None,
        sidebar_description: Optional[str] = None,
        show_logo: bool = True,
        color: Optional[str] = "#09A3D5",
        key: Optional[str] = None,
        get_default_text: str = None,
) -> None:
    """Embed the full visualizer with selected components."""

    if st.config.get_option("theme.primaryColor") != color:
        st.config.set_option("theme.primaryColor", color)

        # Necessary to apply theming
        st.experimental_rerun()

    if show_logo:
        st.sidebar.markdown(LOGO, unsafe_allow_html=True)
    if sidebar_title:
        st.sidebar.title(sidebar_title)
    if sidebar_description:
        st.sidebar.markdown(sidebar_description)
    # Forms can be declared using the 'with' syntax

    with st.sidebar.form(key='connect_form'):
        url_input = st.text_input(label='Sherpa URL', value="https://sherpa-sandbox.kairntech.com/")
        name_input = st.text_input(label='Name', value=st.secrets.sherpa_credentials.username)
        pwd_input = st.text_input(label='Password', value=st.secrets.sherpa_credentials.password, type="password")
        submit_button = st.form_submit_button(label='Connect')
        if submit_button:
            if 'token' not in st.session_state:
                st.session_state['token'] = get_token(url_input, name_input, pwd_input)

    plan = None
    project = None
    url = url_input[0:-1] if url_input.endswith('/') else url_input
    if 'token' in st.session_state:
        all_projects = get_projects(url, st.session_state.token)
        selected_projects = [p['label'] for p in all_projects if projects is None or p['name'] in projects]
        st.sidebar.selectbox('Select project', selected_projects, key="project")
        if st.session_state.get('project', None) is not None:
            project = get_project_by_label(url, st.session_state.project, st.session_state.token)
            all_plans = get_plans(url,
                              project,
                              st.session_state.token) if project is not None else []
            selected_plans = [p['label'] for p in all_plans if plans is None or p['name'] in plans]
            st.sidebar.selectbox('Select plan', selected_plans, key="plan")
            if st.session_state.get('plan', None) is not None:
                plan = get_plan_by_label(url, project, st.session_state.plan, st.session_state.token)

    text = st.text_area("Text to analyze", default_text, key=f"{key}_visualize_text")
    if project is not None:
        if show_project:
            project_exp = st.expander("Project definition (json)")
            project_exp.json(get_project(url, project, st.session_state.token))
        if plan is not None:
            pipe = get_plan(url, project, plan, st.session_state.token)
            if show_plan:
                plan_exp = st.expander("Plan definition (json)")
                plan_exp.json(pipe)
            doc = annotate_with_plan(url, project, plan, text, st.session_state.token)
            doc_exp = st.expander("Annotated doc (json)")
            doc_exp.json(doc)
            visualize_textcat(doc)
            visualize_ner(doc)
    st.sidebar.markdown(
        FOOTER,
        unsafe_allow_html=True,
    )

def visualize_ner(
        doc,
        *,
        show_table: bool = True,
        title: Optional[str] = "Named Entities",
        colors: Dict[str, str] = {},
        key: Optional[str] = None
) -> None:
    """Visualizer for named entities."""
    if title:
        st.header(title)
    labels = {}
    annotation_map = RangeMap()
    annotations = doc.get('annotations', [])
    text = doc['text']
    if annotations:
        for a in annotations:
            labels[a['labelName']] = a['label']
            annotation_map[a['start']:a['end']] = a['labelName']
        start = 0
        annotated = []
        for r in annotation_map.ranges():
            if r.start > start:
                annotated.append(text[start:r.start])
            annotated.append((text[r.start:r.stop], r.value))
            start = r.stop
    else:
        annotated = [text]
    if not labels:
        st.warning("The parameter 'labels' should not be empty or None.")
    else:
        exp = st.expander("Select annotation labels")
        label_select = exp.multiselect(
            "Entity labels",
            options=labels.values(),
            default=list(labels.values()),
            key=f"{key}_ner_label_select",
        )
        html = annotated_text(*annotated)
        html = html.replace("\n\n", "\n")
        # if split_sents and len(docs) > 1:
        #     st.markdown(f"> {sent.text}")
        st.write(get_svg(html), unsafe_allow_html=True)
        #
        # if show_table:
        #     data = [
        #         [str(getattr(ent, attr)) for attr in attrs]
        #         for ent in doc.ents
        #         if ent.label_ in label_select
        #     ]
        #     if data:
        #         df = pd.DataFrame(data, columns=attrs)
        #         st.dataframe(df)


def visualize_textcat(
        doc, *, title: Optional[str] = "Text Classification"
) -> None:
    """Visualizer for text categories."""
    if title:
        st.header(title)
    st.markdown(f"> {doc['text']}")
    cats = {c['label']:c.get('score', 1.0) for c in doc['categories']}
    df = pd.DataFrame(cats.items(), columns=("Label", "Score"))
    st.dataframe(df)

def main():
    testdir = Path(__file__).parent
    source = Path(testdir, 'slots.json')
    with source.open("r") as fin:
        docs = json.load(fin)
    visualize_ner(docs[0])

def annotated_text(*args):
    """Writes test with annotations into your Streamlit app.

    Parameters
    ----------
    *args : str, tuple or htbuilder.HtmlElement
        Arguments can be:
        - strings, to draw the string as-is on the screen.
        - tuples of the form (main_text, annotation_text, background, color) where
          background and foreground colors are optional and should be an CSS-valid string such as
          "#aabbcc" or "rgb(10, 20, 30)"
        - HtmlElement objects in case you want to customize the annotations further. In particular,
          you can import the `annotation()` function from this module to easily produce annotations
          whose CSS you can customize via keyword arguments.

    Examples
    --------

    >>> annotated_text(
    ...     "This ",
    ...     ("is", "verb", "#8ef"),
    ...     " some ",
    ...     ("annotated", "adj", "#faa"),
    ...     ("text", "noun", "#afa"),
    ...     " for those of ",
    ...     ("you", "pronoun", "#fea"),
    ...     " who ",
    ...     ("like", "verb", "#8ef"),
    ...     " this sort of ",
    ...     ("thing", "noun", "#afa"),
    ... )

    >>> annotated_text(
    ...     "Hello ",
    ...     annotation("world!", "noun", color="#8ef", border="1px dashed red"),
    ... )

    """
    out = div(style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem")

    for arg in args:
        if isinstance(arg, str):
            out(html.escape(arg))

        elif isinstance(arg, HtmlElement):
            out(arg)

        elif isinstance(arg, tuple):
            out(annotation(*arg))

        else:
            raise Exception("Oh noes!")

    return str(out)

if __name__ == "__main__":
    plac.call(main)