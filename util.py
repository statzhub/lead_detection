from bs4 import BeautifulSoup


def remove_script_tags(html_content: str) -> str:
    """Removes the <script> tags from html_content"""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup.find_all("script"):
        tag.decompose()
    return str(soup)
