"""Helper Functions"""
import json
import bs4
import certifi
import urllib3
from .errors import PortalXKeyError
# TODO: Patch disable_warnings, see: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
# HTTP = urllib3.disable_warnings().PoolManager()
HTTP = urllib3.PoolManager(
    cert_reqs="CERT_REQUIRED",
    ca_certs=certifi.where())
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome\
/61.0.3163.100 Safari/537.36" # TODO: Make this something else
UAHEAD = {"User-Agent":UA}

def generate_header(key):
    """Generate a Header with User Agent & Provided Portal Key"""
    return {
        "User-Agent":UA,
        "Cookie":"ASP.NET_SessionId={}".format(key)
    }
def baiting(key, link):
    """Send request to a page without fetching any response"""
    try:
        if "您尚未登入個人portal！" in HTTP.request("GET", link,
                                            headers=generate_header(key)).data.decode("utf-8"):
            raise PortalXKeyError
    except PortalXKeyError:
        raise
def switch_sub(key, class_id):
    """Switch fetching location to Desired Class Page"""
    baiting(key, "https://portalx.yzu.edu.tw/PortalSocialVB/FPage/FirstToPage.aspx?PageID="+str(class_id))
def rename_class(class_name):
    """Rename Class into Proper Style"""
    return class_name.replace("）", ")").replace("（", " (").replace("-", " - ")
def parse_homework_description(link_tag_title, item):
    """Parsing Homework Description"""
    if item in link_tag_title:
        start = link_tag_title.find(item)
        end = link_tag_title.find("\r", start+1)
        if end == -1:
            return link_tag_title[start+len(item):]
        return link_tag_title[start+len(item):end]
    else:
        return None
def get_post_page(key, page_num):
    """Get post in further pages"""
    req_body = json.dumps({
        "PageIndex": page_num
        }).encode('utf-8')
    page = HTTP.request("POST",
                        "https://portalx.yzu.edu.tw/PortalSocialVB/FMain/PostWall.aspx/GetPostWall",
                        headers={
                            "User-Agent":UA,
                            "Cookie": "ASP.NET_SessionId="+key,
                            "Content-Type": "application/json"
                        },
                        body=req_body)
    soup = bs4.BeautifulSoup(json.loads(page.data.decode("utf-8"))["d"], "lxml")
    return soup.select(".PanelPost")
def get_post_content(key, post_id):
    """Get content from post"""
    req_body = json.dumps({
        "ParentPostID": post_id,
        "pageShow": "0"
        }).encode('utf-8')
    page = HTTP.request("POST",
                        "https://portalx.yzu.edu.tw/PortalSocialVB/FMain/PostWall.aspx/divParentInnerHtml",
                        headers={
                            "User-Agent":UA,
                            "Cookie": "ASP.NET_SessionId="+key,
                            "Content-Type": "application/json"
                        },
                        body=req_body)
    soup = bs4.BeautifulSoup(json.loads(page.data.decode("utf-8"))["d"], "lxml")
    post = soup.select("#divPostBody"+post_id)[0]
    data = {
        "Text": soup.select("#txtPostBody"+post_id)[0].string,
        "Attachment": {
            "Name": post.find_all("a", class_="")[-1].text,
            "Link": post.find_all("a", class_="")[-1]["href"].replace("..", "https://portalx.yzu.edu.tw/PortalSocialVB")
        } if len(post.find_all("a", class_="")) != 0 else None
    }
    return data
