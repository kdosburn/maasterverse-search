import streamlit as st
import os
import re
import nltk
import unicodedata

# Download tokenizer if not already present
nltk.download('punkt', quiet=True)

# Folder with your .txt files
TEXT_FOLDER = "texts"
all_files = sorted([f for f in os.listdir(TEXT_FOLDER) if f.endswith(".txt")])

# Map file names to human-readable book titles
BOOK_TITLES = {
    "ACOTAR_01.txt": "ACOTAR 1: A Court of Thorns and Roses",
    "ACOTAR_02.txt": "ACOTAR 2: A Court of Mist and Fury",
    "ACOTAR_03.txt": "ACOTAR 3: A Court of Wings and Ruin",
    "ACOTAR_04.txt": "ACOTAR 4: A Court of Frost and Starlight",
    "ACOTAR_05.txt": "ACOTAR 5: A Court of Silver Flames",
    "CC_01.txt": "Crescent City 1: House of Earth and Blood",
    "CC_02.txt": "Crescent City 2: House of Sky and Breath",
    "CC_03.txt": "Crescent City 3: House of Flame and Shadow",
    "TOG_00.txt": "Throne of Glass 0.5: The Assassin's Blade",
    "TOG_01.txt": "Throne of Glass 1: Throne of Glass",
    "TOG_02.txt": "Throne of Glass 2: Crown of Midnight",
    "TOG_03.txt": "Throne of Glass 3: Heir of Fire",
    "TOG_04.txt": "Throne of Glass 4: Queen of Shadows",
    "TOG_05.txt": "Throne of Glass 5: Empire of Storms",
    "TOG_06.txt": "Throne of Glass 6: Tower of Dawn",
    "TOG_07.txt": "Throne of Glass 7: Kingdom of Ash",
}

def normalize_text(s: str) -> str:
    """Normalize Unicode so smart quotes and dashes don't break search."""
    s = unicodedata.normalize("NFKD", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    return s

def search_texts(query, window=200, search_files=None):
    """Search selected books for query and return merged snippets with counts."""
    if search_files is None:
        search_files = all_files

    results = []
    total_matches = 0
    file_counts = {}

    norm_query = normalize_text(query)
    pattern = re.compile(re.escape(norm_query), re.IGNORECASE)

    for filename in search_files:
        with open(os.path.join(TEXT_FOLDER, filename), encoding="utf-8") as f:
            text = f.read()
            text = normalize_text(text)

            matches = list(pattern.finditer(text))
            if not matches:
                continue

            count = len(matches)
            total_matches += count
            file_counts[filename] = count

            i = 0
            while i < len(matches):
                start_index = max(0, matches[i].start() - window)
                end_index = min(len(text), matches[i].end() + window)

                j = i + 1
                while j < len(matches) and matches[j].start() <= end_index:
                    end_index = min(len(text), matches[j].end() + window)
                    j += 1

                snippet = text[start_index:end_index].replace("\n", " ")
                results.append((filename, snippet))

                i = j

    return results, total_matches, file_counts

# --- Streamlit UI ---

st.title("Maasterverse Crawler")
st.markdown(
    "### All text credit goes to the brilliant "
    "[Sarah J. Maas](https://sarahjmaas.com/)",
    unsafe_allow_html=False
)

# Choose which books to search
book_choices = st.multiselect(
    "Avoid spoilers! Select which books you have read (only these will be searched):",
    options=[BOOK_TITLES.get(f, f) for f in all_files],
    default=[BOOK_TITLES.get(all_files[0], all_files[0])]  # default: first book
)

# Convert choices back to filenames
selected_files = [fname for fname in all_files if BOOK_TITLES.get(fname, fname) in book_choices]

# Slider for context size
context_chars = st.slider("Context characters", 20, 1000, 200, step=10)

# Search input
search = st.text_input("Enter a search term or phrase and press Enter:")

# Button also triggers search
run_search = st.button("Search") or search

if run_search and search:
    results, total_matches, file_counts = search_texts(search, window=context_chars, search_files=selected_files)
    if results:
        st.success(f"Total matches found: {total_matches}")
        st.write("### Matches by book")
        for fname, count in file_counts.items():
            title = BOOK_TITLES.get(fname, fname)
            st.write(f"- **{title}**: {count}")

        st.divider()

        for fname, snippet in results:
            # Highlight search term(s)
            highlighted = re.sub(
                f"(?i)({re.escape(normalize_text(search))})",
                r"<mark>\1</mark>",
                snippet,
            )
            title = BOOK_TITLES.get(fname, fname)
            st.markdown(f"**{title}:**")
            st.markdown(f"…{highlighted}…", unsafe_allow_html=True)
            st.divider()
    else:
        st.write("No matches found.")
