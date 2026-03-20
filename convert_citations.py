import re
import sys
import argparse

def parse_bib(bib_path):
    import bibtexparser
    with open(bib_path, 'r', encoding='utf-8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    
    author_map = {}
    for entry in bib_database.entries:
        if 'author' in entry:
            # Assuming author format "Lastname, Firstname and Lastname, Firstname"
            # Get the first author's last name
            first_author = entry['author'].split(' and ')[0].strip()
            if ',' in first_author:
                last_name = first_author.split(',')[0].strip()
            else:
                last_name = first_author.split()[-1].strip()
            
            # Check if there are multiple authors
            if ' and ' in entry['author'] or entry['author'].count(',') >= 2:
                author_map[entry['ID']] = f"{last_name} et al."
            else:
                author_map[entry['ID']] = last_name
    return author_map

def convert_tex(tex_path, author_map, out_path=None):
    with open(tex_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We want to find cases like \cite{Zhang2020} that are used as nouns.
    # It's safer to just replace all for demonstration, or use LaTeX natbib.
    # But since natbib is the best way, maybe the script just replaces \cite with \citet ?
    pass

