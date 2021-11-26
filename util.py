import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Tuple

import plac
import requests
import streamlit as st
from multipart.multipart import parse_options_header
from streamlit.uploaded_file_manager import UploadedFile, UploadedFileRec


# @st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_token(server: str, user: str, password: str):
    url = f"{server}/api/auth/login"
    auth = {"email": user, "password": password}
    r = requests.post(url, json=auth, params={'loginOnly':True},
                             headers={'Content-Type': "application/json", 'Accept': "application/json"},
                             verify=False)
    if r.ok:
        json_response = r.json()
        if 'access_token' in json_response:
            token = json_response['access_token']
            return token
        else:
            return
    else:
        raise r.raise_for_status()


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_projects(server: str, token: str):
    url = f"{server}/api/projects"
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "application/json", 'Accept': "application/json"}
    r = requests.get(url, headers=headers, verify=False)
    if r.ok:
        return r.json()
    return None


def get_project_by_label(server: str, label: str, token: str):
    projects = get_projects(server, token)
    for p in projects:
        if p['label'] == label:
            return p['name']
    return None


def get_project(server: str, name: str, token: str):
    projects = get_projects(server, token)
    for p in projects:
        if p['name'] == name:
            return p
    return None


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_annotators(server: str, project: str, annotator_types: Tuple[str], favorite_only: bool, token: str):
    # st.write("get_annotators(", server, ", ", project, ", ", annotator_types,", ", favorite_only, ")")
    url = f"{server}/api/projects/{project}/annotators_by_type"
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "application/json", 'Accept': "application/json"}
    r = requests.get(url, headers=headers, verify=False)
    annotators = []
    if r.ok:
        json_response = r.json()
        # st.write("get_annotators(", server, ", ", project, ", ", annotator_types, ", ", favorite_only,
        #          "): json_response=", str(json_response))
        for type, ann_lst in json_response.items():
            for annotator in ann_lst:
                # st.write("get_annotators(", server, ", ", project, ", ", annotator_types, ", ", favorite_only,
                #          "): annotator=", str(annotator))
                if annotator_types is None or type in annotator_types:
                    if not favorite_only or annotator.get('favorite', False):
                        annotator['type'] = type
                        annotators.append(annotator)
    return annotators


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_labels(server: str, project: str, token: str):
    url = f"{server}/api/projects/{project}/labels"
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "application/json", 'Accept': "application/json"}
    r = requests.get(url, headers=headers, verify=False)
    labels = {}
    if r.ok:
        json_response = r.json()
        for lab in json_response:
            labels[lab['name']] = lab
    return labels


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_annotator_by_label(server: str, project: str, annotator_types: Tuple[str], favorite_only: bool,
                           label: str, token: str):
    # st.write("get_annotator_by_label(", server, ", ", project, ", ", label, ")")
    annotators = get_annotators(server, project, annotator_types, favorite_only, token)
    # st.write("get_annotator_by_label(", server, ", ", project, ", ", label, "): annotators=", str(annotators))
    for i, ann in enumerate(annotators):
        # st.write("get_annotator_by_label(", server, ", ", project, ", ", label, "): p=", str(p))
        if ann['label'] == label:
            all_labels = {}
            if ann['type'] == 'plan':
                plan = get_plan(server, project, ann['name'], token)
                if plan is not None:
                    ann.update(plan)
                    definition = plan['parameters']
                    for step in definition['pipeline']:
                        # st.write("get_annotator_by_label(", server, ", ", project, ", ", label, "): step=", str(step))
                        if step.get('projectName', project) != project:
                            step_labels = get_labels(server, step['projectName'], token)
                            all_labels.update(step_labels)
            project_labels = get_labels(server, project, token)
            all_labels.update(project_labels)
            ann['labels'] = all_labels
            return ann
    return None


def has_converter(ann):
    result = 'converter' in ann['parameters'] if ann['type'] == 'plan' else False
    return result


def has_formatter(ann):
    result = 'formatter' in ann['parameters'] if ann['type'] == 'plan' else False
    return result


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_plan(server: str, project: str, name: str, token: str):
    url = f"{server}/api/projects/{project}/plans/{name}"
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "application/json", 'Accept': "application/json"}
    r = requests.get(url, headers=headers, verify=False)
    if r.ok:
        return r.json()
    return None
    # st.write("get_annotator(", server, ", ", project, ", ", name, ")")
    annotators = get_annotators(server, project, token)
    # st.write("get_annotator_by_label(", server, ", ", project, ", ", name, "): annotators=", str(annotators))
    for p in annotators:
        # st.write("get_annotator_by_label(", server, ", ", project, ", ", name, "): p=", str(p))
        if p['name'] == name:
            annotator = p['parameters']
            for annotator in annotator['pipeline']:
                if annotator.get('projectName', None) == ".":
                    annotator['projectName'] = project
                # annotator.pop('uuid', None)
            # if 'formatter' in annotator:
            #     annotator['formatter'].pop('uuid', None)
            #     # del annotator['formatter']
            return annotator
    return None


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def annotate_text(server: str, project: str, annotator: str, text: str, token: str):
    # st.write("annotate_with_annotator(", server, ", ", project, ", ", annotator, ")")
    url = f"{server}/api/projects/{project}/annotators/{annotator}/_annotate"
    # st.write("annotate_with_annotator(", server, ", ", project, ", ", annotator, "), url=", url)
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "text/plain", 'Accept': "application/json"}
    r = requests.post(url, data=text.encode(encoding="utf-8"), headers=headers, verify=False, timeout=1000)
    if r.ok:
        doc = r.json()
        # st.write("annotate_with_annotator(", server, ", ", project, ", ", annotator, "), doc=", str(doc))
        return doc
    return None


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def annotate_format_text(server: str, project: str, annotator: str, text: str, token: str):
    # st.write("annotate_format_text(", server, ", ", project, ", ", annotator, ")")
    url = f"{server}/api/projects/{project}/plans/{annotator}/_annotate_format_text"
    # st.write("annotate_format_text(", server, ", ", project, ", ", annotator, "), url=", url)
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': "text/plain", 'Accept': "application/octet-stream"}
    r = requests.post(url, data=text.encode(encoding="utf-8"), headers=headers, verify=False, timeout=1000)
    if r.ok:
        data = r.content
        type = r.headers.get('Content-Type', 'application/octet-stream')
        filename = "file"
        if 'Content-Disposition' in r.headers:
            content_type, content_parameters = parse_options_header(r.headers['Content-Disposition'])
            if b'filename' in content_parameters:
                filename = content_parameters[b'filename'].decode("utf-8")
        return UploadedFile(UploadedFileRec(id=0, name=filename, type=type, data=data))
    return None


def annotate_binary(server: str, project: str, annotator: str, datafile: UploadedFile, token: str):
    url = f"{server}/api/projects/{project}/plans/{annotator}/_annotate_binary"
    headers = {'Authorization': 'Bearer ' + token}
    files = {
        'file': (datafile.name, datafile.getvalue(), datafile.type)
    }
    r = requests.post(url, files=files, headers=headers, verify=False, timeout=1000)
    if r.ok:
        docs = r.json()
        # st.write("annotate_with_annotator(", server, ", ", project, ", ", annotator, "), doc=", str(doc))
        return docs
    return None


def annotate_format_binary(server: str, project: str, annotator: str, datafile: UploadedFile, token: str):
    url = f"{server}/api/projects/{project}/plans/{annotator}/_annotate_format_binary"
    headers = {'Authorization': 'Bearer ' + token}
    files = {
        'file': (datafile.name, datafile.getvalue(), datafile.type)
    }
    r = requests.post(url, files=files, headers=headers, verify=False, timeout=1000)
    if r.ok:
        data = r.content
        type = r.headers.get('Content-Type', 'application/octet-stream')
        filename = "file"
        if 'Content-Disposition' in r.headers:
            content_type, content_parameters = parse_options_header(r.headers['Content-Disposition'])
            if b'filename' in content_parameters:
                filename = content_parameters[b'filename'].decode("utf-8")
        return UploadedFile(UploadedFileRec(id=0, name=filename, type=type, data=data))
    return None


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def process_text(model_name: str, text: str):
    """Process a text and create a Doc object."""
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


def main():
    text = """ENTRE LES SOUSSIGNEES : 
ELYSEES PIERRE, société civile de placement immobilier à.capital variable dont le siège: social est à Paris 8™e, 103. avenue des Champs Elysêes., immatriculée au RCS" Paris sous le n° 334.850.575 représentée par la société HSBC REIM (France), société anonyme â directoire et conseil de surveillance, au capital de 230 000 eurps, en qualité de société de gestion, dont le siège social est à Paris 8éme, 15 rue Vernet, immatriculée au RCS Paris sous le n” 722.028.206 elle-même représentée par Madame Patricia DUPONT LIEVENS, directeur générai, ou Monsieur Jérôme COUTON, directeur général adjoint, dûment habilités à l'effet. des présentes ; 
Ci-après, dénommée !< ïe Bailleur » 
D’UNE PART 
ET : 
La COMMUNE DE CRETEIL, représentée par son maire, M. Laurent CATHALA, agissant, conformément aux dispositions de l’article L.2122-22 du codé général des collectivités territoriales et de la délibération D2017-1-6-0.01 du 6 mars 2017 prise pour son application ; 
Ci-après dénommée « le Preneur 
D’AUTRE PART 
Ci-aprés conjointement dénommées Mes Parties 
    """
    token = get_token("https://sherpa-sandbox.kairntech.com", "oterrier", "ktote123;")
    doc = annotate_format_text("https://sherpa-sandbox.kairntech.com", "mazars_officiel_24slash11", "mazars_pdf_excel",
                               text,
                               token)

    # pdffile = Path("/home/olivier/Téléchargements/3 -  Bail professionnel CG du Val d'oise.pdf")
    # with pdffile.open("rb") as fin:
    #     datafile = UploadedFile(UploadedFileRec(id=1, name=pdffile.name, type="application/pdf", data=fin.read()))
    #     token = get_token("https://sherpa-sandbox.kairntech.com", "oterrier", "ktote123;")
    #     doc = annotate_binary("https://sherpa-sandbox.kairntech.com", "mazars_officiel_24slash11", "mazars_pdf", datafile, token)
    #     pass

    wavfile = Path("/home/olivier/Téléchargements/ae26ccf4-ea2b-4bc7-b112-9bdb00931577.webm")
    with wavfile.open("rb") as fin:
        datafile = UploadedFile(UploadedFileRec(id=1, name=wavfile.name, type="video/webm", data=fin.read()))
        token = get_token("https://sherpa-sandbox.kairntech.com", "oterrier", "ktote123;")
        doc = annotate_binary("https://sherpa-sandbox.kairntech.com", "terrorisme_ner_v2", "audio", datafile, token)
        pass
if __name__ == "__main__":
    plac.call(main)
