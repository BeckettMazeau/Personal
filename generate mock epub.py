import random
from ebooklib import epub

def introduce_ocr_errors(text):
    # Dictionary of typical OCR confusions (target: replacement)
    replacements = [
        ("m", "rn"),     # Kerning issues
        ("rn", "m"),
        ("d", "cl"),
        ("cl", "d"),
        ("in", "m"),
        ("ni", "m"),
        ("I", "l"),      # Letter/number confusions
        ("l", "1"),
        ("O", "0"),
        ("0", "O"),
        ("B", "8"),
        ("S", "5"),
        ("c", "e"),      # Shape similarities
        ("e", "c"),
        ("h", "b"),
        ("fi", "ﬁ"),     # Ligature misinterpretations
        ("fl", "ﬂ"),
        ("ff", "ﬀ"),
        ("th", "t h"),   # Unintended spacing
        ("The", "T he"),
    ]

    garbled_paragraphs = []
    for para in text.split('\n\n'):
        words = para.split()
        garbled_words = []
        for word in words:
            # 1. Apply structural letter confusions
            for target, replacement in replacements:
                if target in word and random.random() < 0.25: # 25% probability per rule
                    word = word.replace(target, replacement, 1)

            # 2. Apply punctuation and layout artifacts
            rand_val = random.random()
            if rand_val < 0.05 and len(word) > 3:
                # Insert random spurious punctuation mid-word (e.g., dirt,y or w|ord)
                idx = random.randint(1, len(word) - 1)
                word = word[:idx] + random.choice(['.', ',', ':', ';', '|', '~', '`', '^']) + word[idx:]
            elif rand_val < 0.08 and len(word) > 5:
                # Simulate a hard line break with hyphenation (e.g., chal-<br/>lenging)
                idx = random.randint(2, len(word) - 2)
                word = word[:idx] + "-<br/>" + word[idx:]

            garbled_words.append(word)
        garbled_paragraphs.append(" ".join(garbled_words))

    return "\n\n".join(garbled_paragraphs)

def create_test_epub(filename="ocr_repair_test.epub"):
    """
    Generates a valid EPUB file containing the garbled text.
    """
    # Initialize the EPUB book
    book = epub.EpubBook()

    # Set mandatory metadata
    book.set_identifier("id_123456789")
    book.set_title("OCR Diagnostics and Repair Test Protocol")
    book.set_language("en")
    book.add_author("Diagnostic Script")

    # Base text to be garbled
    base_text = """
The Industrial Revolution marks a major turning point in history; almost every aspect of daily life was influenced in some way. In particular, average income and population began to exhibit unprecedented sustained growth. Some economists have said that the most important effect of the Industrial Revolution was that the standard of living for the general population began to increase consistently for the first time in history.

The First Industrial Revolution evolved into the Second Industrial Revolution in the transition years between 1840 and 1870, when technological and economic progress continued with the increasing adoption of steam transport, the large-scale manufacture of machine tools and the use of machinery in steam-powered factories.

However, the rapid urbanization brought by the revolution led to cramped living conditions and poor sanitation. Cities were often overwhelmed by the influx of workers from the countryside, leading to the spread of diseases like cholera and typhoid. Despite these challenges, the era paved the way for modern technological advancement.
    """.strip()

    garbled_text = introduce_ocr_errors(base_text)

    # Create a chapter
    c1 = epub.EpubHtml(title='Diagnostics Chapter', file_name='chap_01.xhtml', lang='en')
    
    # Convert garbled text (with potential <br/> tags) into HTML paragraphs
    html_content = "<h1>OCR Repair Diagnostics</h1>"
    for para in garbled_text.split('\n\n'):
        html_content += f"<p>{para}</p>"
    
    c1.content = html_content

    # Add chapter to the book
    book.add_item(c1)

    # Define Table of Contents
    book.toc = (epub.Link('chap_01.xhtml', 'Diagnostics Chapter', 'chap_01'),)

    # Add default NCX and Nav
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define Spine
    book.spine = ['nav', c1]

    # Write the EPUB file
    epub.write_epub(filename, book, {})
    print(f"Successfully generated: {filename}")

if __name__ == "__main__":
    create_test_epub()