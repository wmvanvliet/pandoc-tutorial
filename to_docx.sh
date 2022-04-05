python pandoc-vanvliet-preprocess.py
pandoc -s beamformer_framework_pandoc.tex -f latex+raw_tex --citeproc --bibliography beamformer_framework.bib -F ./pandoc-vanvliet.py --resource-path ./paper --reference-doc template.docx -o beamformer_framework.docx
