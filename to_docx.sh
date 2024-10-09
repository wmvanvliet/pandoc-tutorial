python pandoc-vanvliet-preprocess.py
pandoc -s beamformer_framework_pandoc.tex -f latex+raw_tex --citeproc --bibliography beamformer_framework.bib -F ./pandoc-vanvliet.py --resource-path ./paper --reference-doc template.docx -o beamformer_framework.docx
pandoc -s paper/beamformer_framework.tex -f latex+raw_tex --citeproc --bibliography beamformer_framework.bib --resource-path ./paper -o beamformer_framework.json
python -m json.tool beamformer_framework.json > beamformer_framework_formatted.json
