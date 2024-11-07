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
    (re.compile(r'\\centering'), r''),
]

author_pattern = re.compile(r"\\author\[(.*)\]{(.*)}")
affil_pattern = re.compile(r"\\affil\[(.*)\]{(.*)}")

file_in = open('paper/beamformer_framework.tex')
file_out = open('beamformer_framework_pandoc.tex', 'w')

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

    # Perform search-and-replace line by line
    for pat, rep in patterns:
        line = pat.sub(rep, line)
    file_out.write(line.strip() + '\n')

file_in.close()
file_out.close()
