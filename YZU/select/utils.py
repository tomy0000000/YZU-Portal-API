"""Helper Functions for Class Selection"""
import bs4
from ..utils import (
    HTTP,
    generate_header
)

def record_soup_and_params(user, soup, name):
    if not user.param:
        user.param = {}
    user.param["soups"][name] = soup
    fields = soup.select("#form1")[0].findAll("input")
    user.param["parameters"][name] = dict((field.get("name"), field.get("value")) for field in fields if field.get("name")[:2] == "__")
def baitFramePage(key):
    frame_page = HTTP.request("GET",
                              "https://isdna1.yzu.edu.tw/Cnstdsel/SelCurr.aspx?Culture=zh-tw",
                              headers=generate_header(key))
def refresh_CosList(user):
    list_page = HTTP.request("GET",
                             "https://isdna1.yzu.edu.tw/Cnstdsel/SelCurr/CosList.aspx",
                             headers=generate_header(user.class_select_key))
    list_soup = bs4.BeautifulSoup(list_page.data.decode("utf-8"), "lxml")
    if "已經逾時,請重新執行!" in str(list_soup):
        return False
    record_soup_and_params(user, list_soup, "CosList")
    return True
def refresh_CosTable(user):
    table_page = HTTP.request("GET",
                              "https://isdna1.yzu.edu.tw/Cnstdsel/SelCurr/CosTable.aspx",
                              headers=generate_header(user.class_select_key))
    table_soup = bs4.BeautifulSoup(table_page.data.decode("utf-8"), "lxml")
    if "已經逾時,請重新執行!" in str(table_soup):
        return False
    record_soup_and_params(user, table_soup, "CosTable")
    return True
