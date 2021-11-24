from typing import List, Sequence, Tuple, Optional, Dict, Union, Callable

import pandas as pd
import spacy
import streamlit as st
from spacy import displacy
from spacy.language import Language

# fmt: off
from util import LOGO, get_svg, get_html, get_token, get_projects, get_plans

# from .util import load_model, process_text, get_svg, get_html, LOGO

NER_ATTRS = ["text", "label_", "start", "end", "start_char", "end_char"]
TOKEN_ATTRS = ["idx", "text", "lemma_", "pos_", "tag_", "dep_", "head", "morph",
               "ent_type_", "ent_iob_", "shape_", "is_alpha", "is_ascii",
               "is_digit", "is_punct", "like_num", "is_sent_start"]
# fmt: on
FOOTER = """<span style="font-size: 0.75em">&hearts; Built with [`spacy-streamlit`](https://github.com/explosion/spacy-streamlit)</span>"""


def visualize(
    plans: Union[List[str], Dict[str, str]],
    default_text: str = "",
    default_model: Optional[str] = None,
    visualizers: List[str] = [],
    ner_labels: Optional[List[str]] = None,
    ner_attrs: List[str] = NER_ATTRS,
    similarity_texts: Tuple[str, str] = ("apple", "orange"),
    token_attrs: List[str] = TOKEN_ATTRS,
    show_json_doc: bool = True,
    show_meta: bool = True,
    show_config: bool = True,
    show_visualizer_select: bool = False,
    show_pipeline_info: bool = True,
    sidebar_title: Optional[str] = None,
    sidebar_description: Optional[str] = None,
    show_logo: bool = True,
    color: Optional[str] = "#09A3D5",
    key: Optional[str] = None,
    get_default_text: Callable[[Language], str] = None,
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

    col1, col2 = st.columns(2)

    if 'token' in st.session_state:
        with col1:
            with st.form('Projects'):
                projects = get_projects(url_input, st.session_state.token)
                project_option = st.selectbox('Select project', [p['label'] for p in projects], key=1)
                project_submitted = st.form_submit_button('Submit')
                if project_submitted:
                    for p in projects:
                        if p['label'] == project_option:
                            st.session_state['project'] = p['name']
        with col2:
            with st.form('Plans'):
                plans = get_plans(url_input, st.session_state.project,
                                  st.session_state.token) if 'project' in st.session_state else []
                plan_option = st.selectbox('Select plan', [p['label'] for p in plans], key=1)
                plan_submitted = st.form_submit_button('Submit')
                if plan_submitted:
                    for p in plans:
                        if p['label'] == plan_option:
                            st.session_state['plan'] = p['name']

    # Allow both dict of model name / description as well as list of names
    model_names = plans
    format_func = str
    if isinstance(plans, dict):
        format_func = lambda name: plans.get(name, name)
        model_names = list(plans.keys())

    default_model_index = (
        model_names.index(default_model)
        if default_model is not None and default_model in model_names
        else 0
    )

    text = st.text_area("Text to analyze", default_text, key=f"{key}_visualize_text")

    if show_json_doc or show_meta or show_config:
        st.header("Pipeline information")
        if show_json_doc:
            json_doc_exp = st.expander("JSON Doc")
            #json_doc_exp.json(doc.to_json())

        if show_meta:
            meta_exp = st.expander("Pipeline meta.json")
            # meta_exp.json(nlp.meta)

        if show_config:
            config_exp = st.expander("Pipeline config.cfg")
            # config_exp.code(nlp.config.to_str())

    st.sidebar.markdown(
        FOOTER,
        unsafe_allow_html=True,
    )


def visualize_parser(
    doc: spacy.tokens.Doc,
    *,
    title: Optional[str] = "Dependency Parse & Part-of-speech tags",
    key: Optional[str] = None,
) -> None:
    """Visualizer for dependency parses."""
    if title:
        st.header(title)
    cols = st.columns(4)
    split_sents = cols[0].checkbox(
        "Split sentences", value=True, key=f"{key}_parser_split_sents"
    )
    options = {
        "collapse_punct": cols[1].checkbox(
            "Collapse punct", value=True, key=f"{key}_parser_collapse_punct"
        ),
        "collapse_phrases": cols[2].checkbox(
            "Collapse phrases", key=f"{key}_parser_collapse_phrases"
        ),
        "compact": cols[3].checkbox("Compact mode", key=f"{key}_parser_compact"),
    }
    docs = [span.as_doc() for span in doc.sents] if split_sents else [doc]
    for sent in docs:
        html = displacy.render(sent, options=options, style="dep")
        # Double newlines seem to mess with the rendering
        html = html.replace("\n\n", "\n")
        if split_sents and len(docs) > 1:
            st.markdown(f"> {sent.text}")
        st.write(get_svg(html), unsafe_allow_html=True)


def visualize_ner(
    doc: Union[spacy.tokens.Doc, List[Dict[str, str]]],
    *,
    labels: Sequence[str] = tuple(),
    attrs: List[str] = NER_ATTRS,
    show_table: bool = True,
    title: Optional[str] = "Named Entities",
    colors: Dict[str, str] = {},
    key: Optional[str] = None,
    manual: Optional[bool] = False,
) -> None:
    """Visualizer for named entities."""
    if title:
        st.header(title)

    if manual:
        if show_table:
            st.warning("When the parameter 'manual' is set to True, the parameter 'show_table' must be set to False.")
        if not isinstance(doc, list):
            st.warning("When the parameter 'manual' is set to True, the parameter 'doc' must be of type 'list', not 'spacy.tokens.Doc'.")
    else:
        labels = labels or [ent.label_ for ent in doc.ents]
 
    if not labels:
        st.warning("The parameter 'labels' should not be empty or None.")
    else:
        exp = st.expander("Select entity labels")
        label_select = exp.multiselect(
            "Entity labels",
            options=labels,
            default=list(labels),
            key=f"{key}_ner_label_select",
        )
        html = displacy.render(
            doc, style="ent", options={"ents": label_select, "colors": colors}, manual=manual
        )
        style = "<style>mark.entity { display: inline-block }</style>"
        st.write(f"{style}{get_html(html)}", unsafe_allow_html=True)
        if show_table:
            data = [
                [str(getattr(ent, attr)) for attr in attrs]
                for ent in doc.ents
                if ent.label_ in label_select
            ]
            if data:
                df = pd.DataFrame(data, columns=attrs)
                st.dataframe(df)


def visualize_textcat(
    doc: spacy.tokens.Doc, *, title: Optional[str] = "Text Classification"
) -> None:
    """Visualizer for text categories."""
    if title:
        st.header(title)
    st.markdown(f"> {doc.text}")
    df = pd.DataFrame(doc.cats.items(), columns=("Label", "Score"))
    st.dataframe(df)


def visualize_similarity(
    nlp: spacy.language.Language,
    default_texts: Tuple[str, str] = ("apple", "orange"),
    *,
    threshold: float = 0.5,
    title: Optional[str] = "Vectors & Similarity",
    key: Optional[str] = None,
) -> None:
    """Visualizer for semantic similarity using word vectors."""
    meta = nlp.meta.get("vectors", {})
    if title:
        st.header(title)
    if not meta.get("width", 0):
        st.warning("No vectors available in the model.")
    else:
        cols = st.columns(2)
        text1 = cols[0].text_input(
            "Text or word 1", default_texts[0], key=f"{key}_similarity_text1"
        )
        text2 = cols[1].text_input(
            "Text or word 2", default_texts[1], key=f"{key}_similarity_text2"
        )
        doc1 = nlp.make_doc(text1)
        doc2 = nlp.make_doc(text2)
        similarity = doc1.similarity(doc2)
        similarity_text = f"**Score:** `{similarity}`"
        if similarity > threshold:
            st.success(similarity_text)
        else:
            st.error(similarity_text)

        exp = st.expander("Vector information")
        exp.code(meta)


def visualize_tokens(
    doc: spacy.tokens.Doc,
    *,
    attrs: List[str] = TOKEN_ATTRS,
    title: Optional[str] = "Token attributes",
    key: Optional[str] = None,
) -> None:
    """Visualizer for token attributes."""
    if title:
        st.header(title)
    exp = st.expander("Select token attributes")
    selected = exp.multiselect(
        "Token attributes",
        options=attrs,
        default=list(attrs),
        key=f"{key}_tokens_attr_select",
    )
    data = [[str(getattr(token, attr)) for attr in selected] for token in doc]
    df = pd.DataFrame(data, columns=selected)
    st.dataframe(df)
