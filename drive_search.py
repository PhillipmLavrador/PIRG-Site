import os
from docx import Document
from fuzzywuzzy import fuzz

def search_files(directory, query):
    """
    Search for files in the given directory that match the query in titles and contents.
    
    :param directory: The directory to search in.
    :param query: The query string to search for in file names and contents.
    :return: A list of matching file paths.
    """
    matching_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if fuzz.partial_ratio(query.lower(), file.lower()) > 70:
                matching_files.append(file_path)
            else:
                try:
                    if file.lower().endswith('.docx'):
                        doc = Document(file_path)
                        full_text = []
                        for para in doc.paragraphs:
                            full_text.append(para.text)
                        if fuzz.partial_ratio(query.lower(), '\n'.join(full_text).lower()) > 70:
                            matching_files.append(file_path)
                    else:
                        with open(file_path, 'r', errors='ignore') as f:
                            if fuzz.partial_ratio(query.lower(), f.read().lower()) > 70:
                                matching_files.append(file_path)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    continue
    return matching_files

if __name__ == "__main__":
    directory = "./documents"  # Update with the actual path to the documents folder
    query = input("Enter the search query: ")
    results = search_files(directory, query)
    if results:
        print("Found the following files:")
        for result in results:
            print(result)
    else:
        print("No matching files found.")
