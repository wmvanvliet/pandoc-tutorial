# Converting from LaTeX to DOCX (and everything else): Pandoc and working around its limitations

LaTeX is the best tool for writing scientific papers.
Microsoft Word is the best tool for commenting on manuscripts.
Hence, ideally, you would write your paper in LaTeX, and send a `.docx` version to your co-authors for comments.


[Pandoc](https://pandoc.org/) is a tool for converting text between different markup languages.
Impressive as its capabilities are, there are some markup languages, such as LaTeX, that are essentially programming languages, and Pandoc cannot hope to cover all its commands, extensions, and so on.
In my experience, plain Pandoc will get you 90% of the way.
In this document, I'll describe how to get the final 10%.


## Example paper and code

To illustrate the process of converting a complex LaTeX document to Word for comfortable commenting by co-authors, we convert one of my papers that uses a [custom template](https://github.com/wmvanvliet/latex_templates) and employs many custom commands: [Post-hoc modification of linear models: combining machine learning with domain information to make solid inferences from noisy data](https://users.aalto.fi/~vanvlm1/papers/van_vliet_2020a.pdf).
So, this will be a challenge to convert perfectly.

You can download the LaTeX source for the paper, and the code we will write to convert it to DOCX, in this repository: https://github.com/wmvanvliet/pandoc-tutorial.


## Plain Pandoc

At its core, the command to convert a `.tex` file to a `.docx` file is:
```bash
pandoc paper/beamformer_framework.tex -o beamformer_framework.docx
```

Executing that will output a bunch of errors, as Pandoc is choking on the custom commands and other shenanigans in the file, but it plows on and indeed produces a `beamformer_framework.docx` file.
However, the DOCX file still has many shortcomings which we will address one-by-one below.


## References

To make Pandoc process `\cite{}` commands correctly, we can use the build-in `--citeproc` filter.
We just need to give it the bibliography file (`paper/beamformer_framework.bib`):
```bash
pandoc paper/beamformer_framework.tex \
    --citeproc --bibliography paper/beamformer_framework.bib \
    -o beamformer_framework.docx
```

Now we see that Pandoc processes the citation commands and generates a nice list of references at the end of the document.
However, inspecting the Word document closely, we see that there is no space between the text and the opening `(` of the citation:

![](https://i.imgur.com/1VPJtpx.png)

This is because the LaTeX template performs citations like this:
```latex
Linear models are the workhorst behind many of the multivariate analysis
techniques that are used to process neuroimaging data\cite{McIntosh2014}.
```
The customized `\cite{}` command inserts a non-breaking space before the opening `(`, but Pandoc doesn't know about that. 


## Examining the internals of Pandoc: the AST

During conversion, Pandoc first translates the LaTeX file into an internal abstract syntax tree (AST), which is a common representation that can then be converted into a great many different output formats.
The DOCX writer component of Pandoc does not know anything about LaTeX, it operates on the AST.
This allows Pandoc to convert from anything to anything.

We can inspect the AST by telling Pandoc to output JSON.
Specifying the input format as `latex+raw_tex` is helpful here as it puts all the LaTeX it doesn't understand in the AST unmodified:
```bash
pandoc paper/beamformer_framework.tex -f latex+raw_tex \
    --citeproc --bibliography paper/beamformer_framework.bib \
    -o beamformer_framework.json
```
The resulting `beamformer_framework.json` file is not formatted, which makes it difficult to read.
Python comes with a little tool to format it properly:
```bash
python -m json.tool beamformer_framework.json > beamformer_framework_formatted.json
```

## Fixing non-perfect output with Python+PanFlute

To correct little mistakes in the Pandoc output, you can write a filter program that operates on the AST and makes some small tweaks here and there to aid the DOCX writer.
The [PanFlute](http://scorreia.com/software/panflute/) Python module is helpful here, which contains convenience classes to parse and represent Pandoc's AST.

Here is a python script that places a space before citations.
Here is how the citation from the example above looks in Pandoc's AST:
```json=
{
    "t": "Cite",
    "c": [
        [
            {
                "citationId": "McIntosh2013",
                "citationPrefix": [],
                "citationSuffix": [],
                "citationMode": {
                    "t": "NormalCitation"
                },
                "citationNoteNum": 0,
                "citationHash": 0
            }
        ],
        [
            {
                "t": "Str",
                "c": "(McIntosh"
            },
            {
                "t": "Space"
            },
            {
                "t": "Str",
                "c": "and"
            },
            {
                "t": "Space"
            },
            {
                "t": "Str",
                "c": "Mi\u0161i\u0107"
            },
            {
                "t": "Space"
            },
            {
                "t": "Str",
                "c": "2013)"
            }
        ]
    ]
}
```

What the filter script needs to do is find the first `"t": "Str"` element in the tree and prepend a non-breaking space to the contents of that tag:

```python=
from panflute import *

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

def add_space_to_citation(elem, doc):
    """
    In the template, we use the \cite{} command without any preceding space.
    When converting with pandoc, we need to add this space.
    """
    if isinstance(elem, Cite):
        t = first_str(elem)
        if t is not None and t.text.startswith('('):
            t.text = '\u00a0' + t.text  # prepend a non-breaking space
            
def main(doc=None):
    """Run all the filters on the AST."""
    return run_filters([
        add_space_to_citation,
    ], doc=doc)

if __name__ == "__main__":
    main()
```

In the repository, the code above is found in the `pandoc-vanvliet.py` file.
You can instruct Pandoc to use this filter with the `-F` flag:
```bash
pandoc paper/beamformer_framework.tex -f latex+raw_tex \
    --citeproc --bibliography paper/beamformer_framework.bib \
    -F ./pandoc-vanvliet.py \
    -o beamformer_framework.docx
```

Now, we have spaces before our citations!

![](https://i.imgur.com/BJarJ1d.png)


## Fixing the math

Modifying the AST is an elegant way of fixing errors.
Unfortunately, it has its limitations.

Most of the errors produced by Pandoc during conversion of the document are related to the custom math commands used in the paper.
Since there is a lot of matrix notations used, I defined convenience commands for them, which Pandoc of course does not know about.
They even don't end up in the AST, because the LaTeX parser fails to parse equations containing the custom commands.

The template also uses the `figure*` environment to indicate figures that should span the entire width of the page (overlapping the sidebar).
Pandoc doesn't know about this either, so fails to incorporate figures into the document.

To address this, let's write a Python script that performs some well-aimed search-and-replace operations on the `paper/beamformer.tex` file before it is fed into Pandoc:

```python=
import re

# Search-and-replace patterns
patterns = [
    (re.compile(r'\\begin{figure\*}'), r'\\begin{figure}'),
    (re.compile(r'\\end{figure\*}'), r'\\end{figure}'),
    (re.compile(r'\\tcov{\\mat{([^}]+)}}'), r'$\\mathbf{\\Sigma}_\\mathbf{\1}$'),
    (re.compile(r'\\tcov{\\emat{([^}]+)}}'), r'$\\mathbf{\\Sigma}_{\\widehat{\\mathbf{\1}}}$'),
    (re.compile(r'\\tcov{\\text{([^}]+)}}'), r'$\\mathbf{\\Sigma}_\\text{\1}$'),
    (re.compile(r'\\icov{\\emat{([^}]+)}}'), r'\\mathbf{\\Sigma}^{-1}_{\\widehat{\\mathbf{\1}}}'),
    (re.compile(r'\\ticov{\\emat{([^}]+)}}'), r'$\\mathbf{\\Sigma}^{-1}_{\\widehat{\\mathbf{\1}}}$'),
    (re.compile(r'\\mat{([^}]+)}'), r'\\mathbf{\1}'),
    (re.compile(r'\\vec{([^}]+)}'), r'\\mathbf{\1}'),
    (re.compile(r'\\tmat{([^}]+)}'), r'$\\mathbf{\1}$'),
    (re.compile(r'\\tvec{([^}]+)}'), r'$\\mathbf{\1}$'),
    (re.compile(r'\\emat{([^}]+)}'), r'\\widehat{\\mathbf{\1}}'),
    (re.compile(r'\\evec{([^}]+)}'), r'\\widehat{\\mathbf{\1}}'),
    (re.compile(r'\\temat{([^}]+)}'), r'$\\widehat{\\mathbf{\1}}$'),
    (re.compile(r'\\tevec{([^}]+)}'), r'$\\widehat{\\mathbf{\1}}$'),
    (re.compile(r'\\trans'), r'^\\mathsf{T}'),
    (re.compile(r'\\hermconj'), r'^\\mathsf{H}'),
    (re.compile(r'\\cov{([^}]+)}'), r'\\mathbf{\\Sigma}_\\mathbf{\1}'),
    (re.compile(r'\\icov{([^}]+)}'), r'\\mathbf{\\Sigma}^{-1}_\\mathbf{\1}'),
    (re.compile(r'\\tcov{([^}]+)}'), r'$\\mathbf{\\Sigma}_\\mathbf{\1}$'),
    (re.compile(r'\\ticov{([^}]+)}'), r'$\\mathbf{\\Sigma}^{-1}_\\mathbf{\1}$'),
    (re.compile(r'\\vspace{2ex}'), r''),
]

file_in = open('paper/beamformer_framework.tex')
file_out = open('beamformer_framework_pandoc.tex', 'w')

# Perform search-and-replace line by line
for line in file_in:
    for pat, rep in patterns:
        line = pat.sub(rep, line)
    file_out.write(line.strip() + '\n')

file_in.close()
file_out.close()
```

You can find this file in the repo as `pandoc-vanvliet-preprocess.py`.
Invoking Pandoc now takes two commands:

```bash
python pandoc-vanvliet-preprocess.py
pandoc ./beamformer_framework_pandoc.tex -f latex+raw_tex \
    --citeproc --bibliography paper/beamformer_framework.bib \
    -F ./pandoc-vanvliet.py \
    -o beamformer_framework.docx
```

You can add these commands into a `to_docx.sh` or `to_docx.bat` file for easy execution.

We should now have properly rendered math symbols:

![](https://i.imgur.com/3LmJCBa.png)


## Fixing authors and affiliations

The LaTeX file uses the `authblk` package to handle proper formatting of authors and their affiliations using the `\author` and `\affil` commands.
Pandoc doesn't handle this package well, not showing the affiliations properly, and worse, not putting them in the AST at all!
So this is another thing we need to fix in the preprocessing script.
The idea is to collect author and affiliation strings as we read each line of LaTeX input and when we see the `\maketitle` command, inject the proper strings:

```python
author_pattern = re.compile(r"\\author\[(.*)\]{(.*)}")
affil_pattern = re.compile(r"\\affil\[(.*)\]{(.*)}")

authors = list()
affiliations = list()
for line in file_in:
    # Deal with authors and affiliations
    if match := author_pattern.search(line):
        annot, author = match.groups()
        authors.append(f"{author}$^{{{annot}}}$")
        continue
    if match := affil_pattern.search(line):
        annot, affil = match.groups()
        affiliations.append(f"$^{{{annot}}}${affil}")
        continue
    if line.strip() == r"\maketitle":
        file_out.write(r"\author{" + ", ".join(authors) + "\\\\\n")
        file_out.write("\\\\\n".join(affiliations) + "}\n")
```


## Embedding PDF figures

We also find that Pandoc attempts to include the figures, and cannot find them!
This is because the `\includegraphics` commands in the `.tex` file assume LaTeX is run in the `paper` folder, whereas we are running Pandoc in the root folder.
This can be fixed by passing the `--resource-dir` argument to tell Pandoc where to look for files to include:

```bash
python pandoc-vanvliet-preprocess.py
pandoc ./beamformer_framework_pandoc.tex -f latex+raw_tex \
    --citeproc --bibliography paper/beamformer_framework.bib \
    -F ./pandoc-vanvliet.py \
    --resource-path ./paper \
    -o beamformer_framework.docx
```

However, we have a bigger problem:  
![](https://i.imgur.com/Z76X49O.png)

Microsoft Word (at least on Windows) cannot display PDF images.
They need to be converted to JPEG or PNG first!

Most LaTeX installations come with the `pdftoppm` utility that can do this.
We can modify our AST filter script to find any `.pdf` images, convert them with `pdftoppm` and modify the `"t": "image"` tags to point to the rasterized images. Note in the code below that our filter script does not know about `--resource-path`, so in this example it is hardcoded that the images are in the `paper/` folder (be sure to change this when you adapt the script for your own purposes).

```python=
import os
from panflute import *

def first_str(elem):
    ...

def add_space_to_citation(elem, doc):
    ...
    
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

def main(doc=None):
    """Run all the filters on the AST."""
    return run_filters([
        add_space_to_citation,
        rasterize_pdf_images,
    ], doc=doc)

if __name__ == "__main__":
    main()
```

Now we have beautiful figures:
![](https://i.imgur.com/2tQaxqN.png)


## Fixing references to figures and tables

We now have figures, but the references to the figures, done with `\autoref{}` are not working:

![](https://i.imgur.com/fgRR5Tx.png)

Fixing this involves adding two filters to our Python script.
One that assigns a number to each "float" environment in the LaTeX file, and one that replaces instances of `\autoref` with the proper number:

```python=
figures = {}
tables = {}

def number_float(elem, doc):
    """
    Figures and Tables (that are floats in LaTeX) need to be given a proper number.
    This function also keeps track of them in a global dictionary (defined at
    the top of this file) so we can later resolve \autoref{} calls properly.
    """
    if isinstance(elem, Figure):
        fignum = f'Figure {len(figures) + 1}'
        figures[elem.identifier] = fignum
        t = first_str(elem.caption)
        t.text = fignum + ': ' + t.text
        return elem
    elif isinstance(elem, Table):
        tabnum = f'Table {len(tables) + 1}'
        tables[elem.parent.identifier] = tabnum
        t = first_str(elem.caption)
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
```

Figures and tables should now be properly referenced:
![](https://i.imgur.com/JS1PX5f.png)


## Acronyms

One of the reasons I love LaTeX for scientific writing is that rules and conventions can be enforced automatically.
Figure numbers, references and citations are good examples of this.
Another example is that acronyms should be spelled out upon first usage.
Keeping track of whether I've already used an acronym or not is something I rather leave up to LaTeX's excellent [glossaries](https://ctan.org/pkg/glossaries?lang=en) package.

While Pandoc does know about this package and will give acronyms a special tag in the AST, it doesn't know how to resolve them perfectly.
Hence, we will perform acronym resolution inside our filter script:

```python=
import re

def load_acronyms():
    """
    In order to deal with acronyms, we need to load and parse the acronyms.tex manually.
    """
    pattern = re.compile(r"\\newacronym(\[.*\])?\{(?P<label>[A-Za-z]+)\}\{.+\}\{(?P<value>[A-Za-z 0-9\-]+)\}")
    
    with open('paper/acrynyms.tex', 'r', encoding='utf-8') as f:
        for line in f:
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

def main(doc=None):
    load_acronyms()
    return run_filters([
        resolve_acronyms,
        add_space_to_citation,
        number_float,
        resolve_autoref,
        rasterize_pdf_images,
    ], doc=doc)


if __name__ == "__main__":
    main()
```


## Some final tweaks

We are almost there. I don't like the default way that the `\SIRange{}{}` command gets translated and there should be a `References` heading before the references list:

```python=
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

def add_references_section_heading(elem, doc):
    """
    Add a section heading for the references.
    """
    if isinstance(elem, Div) and elem.identifier == 'refs':
        return [Header(Str('References'), identifier='references'), elem]

```


## Adding a Word template


The default Word template is pretty good, but also here there could be a few tweaks here and there.
For example, I'd like the references list to have some indentation of subsequent lines:

default style:
![](https://i.imgur.com/77ULc42.png)

preferred style:
![](https://i.imgur.com/6r2og8q.png)

Layout tweaks like this can be made by making a Word template file.
The DOCX output of Pandoc makes careful use of Word Styles to mark things such as section headers, citations, references and so on.
Start with the `beamformer_framework.docx` as it is now and change the styles to reflect how you want things to look (be sure to "Update style to match selection" if you make any changes!).
To reduce the size of the template, you can trim down the content to only have one example per style, so one paragraph of text, one figure, one table, one reference, and so on.
Once you are happy with your template, you can pass it to Pandoc using the `--reference-doc` argument:

```bash
python pandoc-vanvliet-preprocess.py
pandoc ./beamformer_framework_pandoc.tex -f latex+raw_tex \
    --citeproc --bibliography paper/beamformer_framework.bib \
    -F ./pandoc-vanvliet.py \
    --resource-path ./paper \
    --reference-doc template.docx \
    -o beamformer_framework.docx
```



## Closing remarks

By now, the strategy should be clear to you. Start with plain Pandoc, examine the resulting DOCX file carefully and fix any mistakes by adding to the preprocessing and filter Python scripts.
This is a laborious process, but thankfully you only have to do this once.
Feel free to use my scripts as a jumping-off point, add any additional stuff you like to use but Pandoc doesn't handle well, and you are set for many writing projects.
