import re

with open("FileCutter/frontend/src/components/ReviewInterface.jsx", "r") as f:
    content = f.read()

content = content.replace("""      // const data = await getFiles();
      // Mocking data for development since backend might not be up
      const mockData = Array.from({ length: 10000 }).map((_, i) => ({
        id: `file-${i}`,
        name: `document-${i}.pdf`,
        size: Math.floor(Math.random() * 10000000),
        confidence: Math.floor(Math.random() * 3) + 1,
        type: 'application/pdf',
        url: 'about:blank' // Mock URL
      }));
      setFiles(mockData);""", """      const data = await getFiles();
      setFiles(data);""")

with open("FileCutter/frontend/src/components/ReviewInterface.jsx", "w") as f:
    f.write(content)
