\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{vanvliet_paper}[2018/03/02 LaTeX class for readable scientific text]
\LoadClassWithOptions{article}
\RequirePackage{vanvliet_common}

% Styles common to multiple templates
\RequirePackage{vanvliet_common}


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Sizes and margins

% Increase line spacing a bit
\RequirePackage{setspace}
\onehalfspacing

% Margin notes
\RequirePackage{sidenotes}

% Fix the position of the footnote number when it occurs near a comma or period
\RequirePackage{fnpct_vanvliet}

% Place footnotes in the margin
\let\oldfootnote\footnote
\renewcommand{\footnote}[1]{\sidenote{\footnotesize#1}}


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Bibliography

\RequirePackage[american]{babel}
\RequirePackage{csquotes}
%\RequirePackage[style=apa, backend=biber, maxbibnames=99,
%                doi=true, isbn=true, url=true, natbib=true]{biblatex}
\RequirePackage[style=apa, maxbibnames=99,
                doi=true, isbn=true, url=true, natbib=true]{biblatex}
\DeclareLanguageMapping{american}{american-apa}
\let\oldcite\cite
\renewcommand{\cite}[2][]{\sidenote{\footnotesize\raggedright#1 \oldcite{#2}}}
\newcommand{\captioncite}[1]{(\oldcite{#1})}

\RequirePackage{vanvliet_bib}

% Make the text of the bibliography smaller than the main body text
\AtBeginBibliography{\small}


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Title and authors formatting
\RequirePackage{hyphenat} % To disable hyphenation in the title

% Title
\makeatletter
\def\maketitle{
	\begin{minipage}{17cm}
		\singlespacing
		\raggedright
		\today\\
		\thejournal
		\vspace*{1ex}

		\hrule
		\vspace*{2ex}
		
		\begin{flushleft}
		\LARGE\textbf{\nohyphens{\@title}}
		\end{flushleft}

		\vspace*{1ex}
		\normalsize\@author

		\vspace*{2ex}
		\hrule
	\end{minipage}
}
\makeatother

% Authors
\RequirePackage{authblk}
\renewcommand\Affilfont{\small}


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Abstract
\renewenvironment{abstract} {
	\vspace{0.5cm}\hspace{-2cm}%
	\begin{minipage}{\paperwidth}
		\centering
		\begin{minipage}{13cm}
			\begin{center}\textbf{\large Abstract}\end{center}
			\small
}{
		\end{minipage}
	\end{minipage}
}


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Referencing tables, figures, etc.

\def\figureautorefname{Figure}
\def\tableautorefname{Table}
\def\equationautorefname{equation}
\def\subsectionautorefname{section}
\def\subsubsectionautorefname{section}


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Commands for making journal articles (preprints)

% Allow for defining a journal name
\gdef \thejournal {}
\newcommand\draft{\gdef \thejournal {Draft version intended for future publication.}}
\newcommand\preprint{\gdef \thejournal {This is a preprint that has not undergone peer review yet.}}
\newcommand\submitted[1]{\gdef \thejournal {Manuscript submitted to #1}}
\newcommand\published[2]{\gdef \thejournal {Author copy. Original published in #1. DOI: \href{http://doi.org/#2}{#2}}}

\newenvironment{frontmatter}{}{}
\newenvironment{keyword}{\vspace{1em}\textit{Keywords:}}{}
\newcommand\sep{\unskip, }

% Format line numbers
\usepackage[right]{lineno}
\setlength\linenumbersep{2pt}
\renewcommand\linenumberfont{\normalfont\tiny\color{gray}}
