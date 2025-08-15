import os

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if '<meta charset="UTF-8">' not in content:
                content = content.replace("<head>", "<head>\n<meta charset=\"UTF-8\">")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)