from bs4 import BeautifulSoup
import requests


def get_course_image(url):
    try:
        result = requests.get(url)
        doc = BeautifulSoup(result.text, "html.parser")
        img_elms = doc.find_all("span", {"class": "intro-asset--img-aspect--3fbKk"})
        if len(img_elms) > 0:
            return img_elms[0].findChildren()[0]["src"]
        else:
            img_elms = doc.find_all("div", {"class": "intro-asset--img-aspect--3fbKk"})
            return img_elms[0].findChildren()[0]["src"]

    except Exception:
        return "Not Found"
