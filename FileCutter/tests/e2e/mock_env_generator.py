import os
import random
import string
from pathlib import Path

def create_mock_env(base_dir: str, num_files: int = 5000):
    """
    Creates a mock environment with thousands of dummy files.
    - 80% garbage/installers (zero byte files like .exe, .tmp, .msi, .iso)
    - 20% protected/documents (small text files like .pdf, .docx, .pptx containing keywords)
    """
    os.makedirs(base_dir, exist_ok=True)

    garbage_exts = ['.exe', '.tmp', '.msi', '.iso', '.dmg', '.zip', '.tar.gz', '.log']
    doc_exts = ['.pdf', '.docx', '.txt', '.pptx']
    keywords = ['homework', 'report', 'assignment', 'project', 'financial', 'notes']

    for i in range(num_files):
        is_garbage = random.random() < 0.8

        # generate random filename
        filename_length = random.randint(5, 15)
        filename_base = ''.join(random.choices(string.ascii_lowercase + string.digits, k=filename_length))

        if is_garbage:
            ext = random.choice(garbage_exts)
            filename = f"{filename_base}_{i}{ext}"
            filepath = os.path.join(base_dir, filename)
            # Create zero-byte file
            with open(filepath, 'w') as f:
                pass
        else:
            ext = random.choice(doc_exts)
            filename = f"{filename_base}_{i}{ext}"

            # sometimes add keyword to filename
            if random.random() < 0.3:
                keyword = random.choice(keywords)
                filename = f"{keyword}_{filename}"

            filepath = os.path.join(base_dir, filename)

            # Create small file with text
            with open(filepath, 'w') as f:
                if ext == '.txt' and random.random() < 0.5:
                    f.write(f"This is a {random.choice(keywords)} document.")
                else:
                    f.write("Some dummy content here.")

if __name__ == '__main__':
    base_dir = os.path.join(os.path.dirname(__file__), 'dummy_downloads')
    print(f"Creating mock environment in {base_dir}...")
    create_mock_env(base_dir, 5000)
    print("Done!")
