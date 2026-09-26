
from pathlib import Path
import markdown

root = Path(__file__).resolve().parent

# MarkdownをHTMLに変換
source = (root / "CHANGELOG.md").read_text(encoding="utf-8")
content = markdown.markdown(source, extensions=["extra"])

# 公開用HTMLを作成
html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>更新履歴 | Daily Philosopher</title>
    <link rel="stylesheet" href="/philosophers/assets/style.css">
</head>
<body>
    <main class="changelog">
        {content}
    </main>
</body>
</html>
"""

(root / "changelog.html").write_text(html, encoding="utf-8")

print("changelog.html を生成しました")
