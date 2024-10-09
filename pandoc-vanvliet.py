#!/usr/bin/python3
#encoding: utf8
"""
Filter for pandoc to fix up some particularities with the vanvliet_paper.cls
LaTeX class.

Author: Marijn van Vliet <w.m.vanvliet@gmail.com>
"""
import os
from panflute import *
import re
import subprocess
import sys

acronyms = {}
refcounts = {}
figures = {}
tables = {}


def first_str(elem):
    """
    Helper function that returns the first Str() node under the given element.
    """
    if hasattr(elem, 'content'):
        for child in elem.content:
            if isinstance(child, Str):
                return(child)
            else:
                t = first_str(child)
                if t is not None:
                    return t
    return None


def load_acronyms():
    """
    In order to deal with acronyms, we need to load and parse the acronyms.tex
    manually.
    """
    pattern = re.compile(r"\\newacronym(\[.*\])?\{(?P<label>[A-Za-z]+)\}\{.+\}\{(?P<value>[A-Za-z 0-9\-]+)\}")

    d = os.path.dirname(__file__)
    filename = os.path.join(d, 'paper/acronyms.tex')
    with open(filename, 'r', encoding='utf-8') as acronymsFile:
        for line in acronymsFile:
            match = pattern.match(line)
            if match:
                acronyms[match.group('label')] = match.group('value')


def resolve_acronyms(elem, doc):
    """
    In the template, we use \gls{TIL} to denote acronyms. These need to be
    expended upon first use.
    """
    if isinstance(elem, Span) and "acronym-label" in elem.attributes:
        label = elem.attributes["acronym-label"]

        if label in acronyms:
            # this is the case: "singular" in form and "long" in form:
            value = acronyms[label]

            form = elem.attributes["acronym-form"]
            if label in refcounts and "short" in form:
                if "singular" in form:
                    value = label
                else:
                    value = label + "s"

            elif "full" in form or "short" in form:
                # remember that label has been used
                if "short" in form:
                    refcounts[label] = True

                if "singular" in form:
                    value = value + " (" + label + ")"
                else:
                    value = value + "s (" + label + "s)"

            elif "abbrv" in form:
                if "singular" in form:
                    value = label
                else:
                    value = label + "s"

            return Span(Str(value))


def add_space_to_citation(elem, doc):
    """
    In the template, we use the \cite{} command without any preceding space.
    When converting with pandoc, we need to add this space.
    """
    if isinstance(elem, Cite):
        t = first_str(elem)
        if t is not None and t.text.startswith('('):
            t.text = '\u00a0' + t.text  # prepend a non-breaking space


def number_float(elem, doc):
    """
    Figures and Tables (that are foats in LaTeX) need to be given a proper number.
    This function also keeps track of them in a global dictionary (defined at
    the top of this file) so we can later resolve \autoref{} calls properly.
    """
    if isinstance(elem, Figure):
        fignum = f'Figure {len(figures) + 1}'
        figures[elem.identifier] = fignum
        t = first_str(elem.caption)
        if t is not None:
            t.text = fignum + ': ' + t.text
        return elem
    elif isinstance(elem, Table):
        tabnum = f'Table {len(tables) + 1}'
        tables[elem.parent.identifier] = tabnum
        t = first_str(elem.caption)
        if t is not None:
            t.text = tabnum + ': ' + t.text
        return elem


autoref_pattern = re.compile(r"\\autoref\{(...):(.*)\}")
def resolve_autoref(elem, doc):
    """
    Do \autoref{} manually.
    """
    if isinstance(elem, RawInline):
        matches = autoref_pattern.match(elem.text)
        if matches:
            float_type = matches.group(1)
            identifier = float_type + ':' + matches.group(2)
            if float_type == 'fig' and identifier in figures:
                return Str(figures[identifier])
            elif float_type == 'tab' and identifier in tables:
                return Str(tables[identifier])

def add_references_section_heading(elem, doc):
    """
    Add a section heading for the references.
    """
    if isinstance(elem, Div) and elem.identifier == 'refs':
        return [Header(Str('References'), identifier='references'), elem]

def rasterize_pdf_images(elem, doc):
    """
    Rasterize PDF images to PNG with a reasonable resolution.
    """
    if isinstance(elem, Image):
        print('Rasterizing', elem.url, file=sys.stderr)
        if elem.url.endswith('.pdf'):
            url_png = 'paper/' + elem.url.replace('.pdf', '.png')
            if not os.path.exists(url_png):
                subprocess.run(['pdftoppm',
                                '-scale-to', '1024',
                                '-png',
                                '-singlefile',
                                f'paper/{elem.url}',
                                f'paper/{elem.url[:-4]}'])
            elem.url = url_png
        # Remove any width annotations made in the LaTeX file, which Word
        # cannot handle, so the width defaults to the pagewidth.
        if 'width' in elem.attributes:
            del elem.attributes['width']

    return elem

si_range_pattern = re.compile(r'(.+)\u00a0(.+)\u2013(.+)')
def fix_si_range(elem, doc):
    """
    By default, pandoc translates \SIRange{1}{2}{\milli\second} to 1 ms--2 ms,
    which I don't like. I prefer 1--2 ms.
    """
    if isinstance(elem, Str):
        matches = si_range_pattern.match(elem.text)
        if matches:
            elem.text = f'{matches.group(1)}\u2013{matches.group(3)}'
    return elem


def main(doc=None):
    load_acronyms()
    return run_filters([
        resolve_acronyms,
        add_space_to_citation,
        number_float,
        resolve_autoref,
        rasterize_pdf_images,
        fix_si_range,
        add_references_section_heading,
    ], doc=doc)


if __name__ == "__main__":
    main()
