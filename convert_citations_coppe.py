import re
import bibtexparser

def load_authors_from_bib(bib_path):
    with open(bib_path, 'r', encoding='utf-8') as f:
        bib_database = bibtexparser.load(f)
    
    author_map = {}
    for entry in bib_database.entries:
        if 'author' in entry:
            # Pega o primeiro autor
            authors = entry['author'].split(' and ')
            first_author = authors[0].strip()
            
            # Tenta pegar apenas o último nome (sobrenome)
            if ',' in first_author:
                last_name = first_author.split(',')[0].strip()
            else:
                last_name = first_author.split()[-1].strip()
            
            # Se houver mais de um autor, adiciona "et al."
            # Verifica " and " ou "," para identificar múltiplos autores
            if len(authors) > 1 or entry['author'].count(',') >= 2 or 'et al' in entry['author'].lower():
                author_map[entry['ID']] = f"{last_name} et al."
            else:
                author_map[entry['ID']] = last_name
        else:
            author_map[entry['ID']] = entry['ID'] # Fallback para usar o ID se não houver autor
            
    return author_map

def convert_tex_file(tex_path, author_map, output_path):
    with open(tex_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex para encontrar todas as ocorrências de \cite{...}
    # Funciona com citações simples: \cite{chave}
    def replace_citation(match):
        keys_str = match.group(1)
        keys = [k.strip() for k in keys_str.split(',')]
        
        # Se for apenas uma chave, substituímos por "Autor et al. \cite{chave}"
        if len(keys) == 1:
            key = keys[0]
            author_text = author_map.get(key, "Autor")
            return f"{author_text} \cite{{{key}}}"
        else:
            # Se for múltiplas chaves ex: \cite{k1,k2}, não é trivial transformar em "Autor1, Autor2".
            # Mantemos original para você revisar manualmente, ou podemos expandir.
            return match.group(0)

    # Substitui \cite{chave} usando a função acima
    # Nota: só vai alterar \cite{chave}. Se você estiver usando \citep ou outro, ajuste a regex.
    new_content = re.sub(r'\\cite\{([^}]+)\}', replace_citation, content)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Arquivo convertido salvo em: {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Converte \cite{key} para Autor et al. \cite{key}")
    parser.add_argument("tex_file", help="Caminho para o arquivo .tex original")
    parser.add_argument("bib_file", help="Caminho para o arquivo .bib")
    parser.add_argument("output_file", help="Caminho para o novo arquivo .tex a ser salvo")
    
    args = parser.parse_args()
    
    print("Carregando referências...")
    author_map = load_authors_from_bib(args.bib_file)
    print(f"{len(author_map)} referências mapeadas.")
    
    print("Processando arquivo LaTeX...")
    convert_tex_file(args.tex_file, author_map, args.output_file)
    print("Concluído!")
