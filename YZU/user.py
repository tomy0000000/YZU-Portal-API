"""Main User Class"""
import getpass
import io
import json
import re
import bs4
import pandas
import random
from PIL import Image
try:
    import IPython.core.display
except ImportError:
    pass
from .errors import LoginError, PortalXKeyError
from .utils import (
    UAHEAD,
    HTTP,
    generate_header,
    get_post_page,
    get_post_content,
    parse_homework_description,
    rename_class,
    switch_sub
)

class User(object):
    """Class to store user datas"""
    def __init__(self, userID="", password=""):
        if not userID:
            userID = input("User ID: ")
        if not password:
            password = getpass.getpass("Password: ")
        try:
            login_page = HTTP.request("POST",
                                      "https://portalx.yzu.edu.tw/PortalSocialVB/Login.aspx",
                                      fields={ # TODO: Make this dynamic
                                          "__VIEWSTATE":"/wEPDwUKLTkyMDk2NTcxNA9kFgICAw9kFgQCAQ8WAh4JaW5uZXJodG1sBfICPGRpdiBzdHlsZT0nY29sb3I6IHJlZDsgZm9udC13ZWlnaHQ6IGJvbGQ7Jz7luLPomZ/ngrpzIOWKoOS4iuaCqOeahOWtuOiZn++8jOWmgnM5MjExMDE8L2Rpdj48ZGl2IHN0eWxlPSdjb2xvcjogcmVkOyBmb250LXdlaWdodDogYm9sZDsnPuWvhueivOeCuiDouqvku73oqLzlrZfomZ8o6Iux5paH5a2X6KuL5aSn5a+rKTwvZGl2PjxkaXYgc3R5bGU9J2NvbG9yOiBibGFjazsnPueZu+WFpeW+jOiri+WLmeW/heS/ruaUueaCqOeahOWvhueivDwvZGl2PjxiciAvPjxkaXYgc3R5bGU9J2NvbG9yOiBibGFjazsnPuW/mOiomOWvhueivO+8muiri+mAlea0veWcluabuOmkqOarg+WPsCjlgpnorYnku7Yp77yM5oiW6Zu75qCh5YWn5YiG5qmfMjMyMTwvZGl2PmQCAw9kFgZmD2QWAmYPZBYCZg8PFgQeCENzc0NsYXNzBQ5Mb2dpbkJhY2s4MDBfWR4EXyFTQgICZBYCZg9kFgJmD2QWAgIBDw8WBB8BBQ5Mb2dpbkJhY2syNzBfWR8CAgJkFgJmD2QWAmYPZBYKAgEPDxYCHgRUZXh0BQbluLPomZ9kZAIFDw8WAh8DBQblr4bnorxkZAIJDw8WBB4HVG9vbFRpcAUPRW5nbGlzaCBWZXJzaW9uHghJbWFnZVVybAUcLi9JbWFnZXMvSWNvbnMvVmVyc2lvblRXLnBuZxYCHgdvbmNsaWNrBRVDaGFuZ2VMYW5ndWFnZSgnVFcnKTtkAgsPDxYCHwMFBueZu+WFpWRkAg0PDxYCHwMFDioq5paw55Sf5rOo5oSPZGQCAQ9kFgJmDw8WBB8BBQ90YWJDZWxsTWlkZGxlX1kfAgICZBYEAgMPDxYEHwEFDnRhYmxlSG90UGFnZV9ZHwICAmQWAmYPZBYCZg9kFgJmDw8WAh8DBQznhrHploDlsIjpoIFkZAIFDw8WBB8BBRF0YWJsZUhvdFBhZ2VFbmRfWR8CAgJkZAIDD2QWAmYPZBYCZg8PFgQfAQUNTG9naW5Gb290ZXJfWR8CAgJkZGTyT2gnXdKy6dcClhG2S9KvWwKitQ==",
                                          "__VIEWSTATEGENERATOR":"4F5352E6",
                                          "__EVENTVALIDATION":"/wEdAAYZE+NrQEMnXQZ2m08gbZJj1vGYFjrtzIuId5C42O0AzRaVgZp528BwL4Heg6ju5IFPJEHWQZAV39IrTgU3OMCuz9Epgz+OXGhhMky+n/+RyLga9dtgamGDPrZlwtr3L501mImYpIoFcNzIUq9OwA27skCHhA==",
                                          "Txt_UserID":userID,
                                          "Txt_Password":password,
                                          "ibnSubmit":"登入"
                                      }, headers=UAHEAD)
            if "Login Failed！登入失敗！" in login_page.data.decode("utf-8"):
                raise LoginError("Login Failed！登入失敗！")
            self.portal_x_key = [i for i in login_page.headers["Set-Cookie"].split(", ") if i.find("ASP.NET") != -1][0].split(";")[0].split("=")[1]
            self.portal_key = None
            self.user_id = userID
            self.__password = password
            self.name = bs4.BeautifulSoup(HTTP.request("GET",
                                                       "https://portalx.yzu.edu.tw/PortalSocialVB/FMain/DefaultPage.aspx?Menu=Default&LogExcute=Y",
                                                       headers=generate_header(self.portal_x_key)).data.decode("utf-8"), "lxml").select("#MainBar_lbnUserName")[0].string
        except LoginError:
            raise
    def __str__(self):
        return "Login ID: "+self.user_id+"\nWelcome! "+self.name
    def get_portal_key(self):
        """Use user-provided data to get access key of Legacy Portal"""
        try:
            HTTP.request("GET",
                         "https://portalx.yzu.edu.tw/PortalSocialVB/FMain/ClickMenuLog.aspx?type=App_&SysCode=A02",
                         headers=generate_header(self.portal_x_key)
                        )
            exchange_key_page = HTTP.request("GET",
                                             "https://portalx.yzu.edu.tw/PortalSocialVB/IFrameSub.aspx",
                                             headers=generate_header(self.portal_x_key))
            exchange_key = bs4.BeautifulSoup(exchange_key_page.data.decode("utf-8"), "lxml").select("#SessionID")[0]["value"]
            new_key_page = HTTP.request("POST",
                                        "https://portal.yzu.edu.tw/VC2/FFB_Login.aspx?sys=value",
                                        fields={
                                            "Account":self.user_id,
                                            "SessionID":exchange_key,
                                            "LangVersion":"TW",
                                            "Y":"",
                                            "M":"",
                                            "CosID":"",
                                            "CosClass":"",
                                            "UseType":"STD"
                                        }, headers=UAHEAD)
            self.portal_key = [i for i in new_key_page.headers["Set-Cookie"].split(", ") if i.find("ASP.NET") != -1][0].split(";")[0].split("=")[1]
        except PortalXKeyError:
            raise
    def get_class_codes(self):
        """Get Available Class codes of User"""
        codes = {}
        for each in json.loads(
                HTTP.request("POST",
                             "https://portalx.yzu.edu.tw/PortalSocialVB/Include/MainLeftMenuRequest.ashx",
                             body="{RequestType: \"MyPage\", UserAccount: \""+self.user_id+"\"}",
                             headers=generate_header(self.portal_x_key)
                            ).data.decode("utf-8")
        ):
            codes[rename_class(each["PageName"])] = each["PageID"]
        return codes
    def get_classes(self, include_teacher=False, include_codes=False):
        """Get Classes of a User"""
        if not self.portal_key:
            self.get_portal_key()
        page = HTTP.request("GET",
                            "https://portal.yzu.edu.tw/VC2/Student/SelCos/SelCosList.aspx",
                            headers=generate_header(self.portal_key)
                           ).data.decode("utf-8")
        table_soup = bs4.BeautifulSoup(page, "lxml").select(".table_1")[0]
        table = pandas.read_html(str(table_soup), header=0)[0]
        table = table.drop("選別", axis=1).drop("狀態", axis=1)
        table = table.set_index("課名")
        table.index = list(map(rename_class, table.index))
        if include_teacher or include_codes:
            codes = self.get_class_codes()
            for each in table.index:
                if include_teacher:
                    switch_sub(self.portal_x_key, codes[each])
                    page = HTTP.request("GET",
                                        "https://portalx.yzu.edu.tw/PortalSocialVB/FMain/PostWall.aspx?LogExcute=Y&Menu=Pot",
                                        headers=generate_header(self.portal_x_key)
                                       ).data.decode("utf-8")
                    soup = bs4.BeautifulSoup(page, "lxml").select("#PageHead_lblCourseName")[0].string
                    table.at[each, "教師姓名"] = re.match(r"^.*\((?P<teacherName>.*)\)$", soup).groups("teacherName")[0]
                if include_codes:
                    table.at[each, "Codes"] = codes[each]
        if include_codes:
            table.Codes = table.Codes.astype(int)
            table.Codes = table.Codes.astype(str)
        return table
    def get_material(self, class_id):
        """Get Material List of a class"""
        try:
            switch_sub(self.portal_x_key, class_id)
            page = HTTP.request("GET",
                                "https://portalx.yzu.edu.tw/PortalSocialVB/TMat/Materials_S.aspx?Menu=Mat",
                                headers=generate_header(self.portal_x_key))
            if "您尚未登入個人portal！" in page.data.decode("utf-8"):
                raise PortalXKeyError
            if "尚未上傳教材！" in page.data.decode("utf-8"):
                return pandas.DataFrame(columns=["大綱說明", "課程進度", "講義", "影音", "連結", "上傳時間"])
            table_soup = bs4.BeautifulSoup(page.data.decode("utf-8"), "lxml").select(".table_1")[0]
            for each in table_soup.find_all("tr", class_=""):
                for each_2 in each.find_all("td")[1:4]:
                    if each_2.find("a") is not None:
                        each_2.string = each_2.find("a")["href"].replace("..", "https://portalx.yzu.edu.tw/PortalSocialVB")
            table = pandas.read_html(str(table_soup), header=0, index_col="大綱說明")[0]
            table = table.drop(["下載次數"], axis=1)
            table["上傳時間"] = pandas.to_datetime(table["上傳時間"], format="%Y/%m/%d")
            table = table.sort_values("上傳時間", ascending=True)
            table = table.reset_index(level=["大綱說明"])
            table = table.set_index(["大綱說明", "上傳時間"])
            return table
        except PortalXKeyError:
            raise
    def get_homework(self, class_id):
        """Get Homework List of a class"""
        try:
            switch_sub(self.portal_x_key, class_id)
            page = HTTP.request("GET",
                                "https://portalx.yzu.edu.tw/PortalSocialVB/THom/HomeworkList.aspx?Menu=Hom",
                                headers=generate_header(self.portal_x_key))
            if "您尚未登入個人portal！" in page.data.decode("utf-8"):
                raise PortalXKeyError
            table_soup = bs4.BeautifulSoup(page.data.decode("utf-8"), "lxml").select(".table_1")[0]
            for empty_row in table_soup.find_all("tr", class_=""):
                empty_row.extract()
            for class_label in ["hi_line", "record2"]:
                for each in table_soup.find_all("tr", class_=class_label):
                    if len(each.find_all("td")) != 1:
                        if each.find_all("td")[3].find("a"):
                            each.find_all("td")[3].string = each.find_all("td")[3].find("a")["href"].replace("..", "https://portalx.yzu.edu.tw/PortalSocialVB")
                        homework_jsons = []
                        for each_2 in each.find_all("td")[5].find_all("a"):
                            homework_jsons.append({
                                "檔案名稱": each_2.string,
                                "上傳時間": parse_homework_description(each_2["title"], "上傳時間："),
                                "說明": parse_homework_description(each_2["title"], "說明：")
                            })
                        each.find_all("td")[5].string = json.dumps(homework_jsons)
            table = pandas.read_html(str(table_soup), header=0, na_values=None)[0]
            new_col = list(table.columns)
            new_col[2] = "作業名稱"
            for col_index in range(len(new_col)):
                new_col[col_index] = re.search(r"[\u4e00-\u9fa5]*", new_col[col_index]).group()
            table.columns = new_col
            table.insert(3, "作業內容", [""]*len(table.index))
            for item_num in range(int(len(table.index)//2)):
                table.at[table.index[item_num], "作業內容"] = table.at[table.index[item_num+1], "項次"]
                table = table.drop(table.index[item_num+1])
            table["截止日"] = pandas.to_datetime(table["截止日"], format="%Y/%m/%d")
            table = table.sort_values("截止日", ascending=True)
            table = table.set_index(["作業名稱", "截止日"])
            table = table.drop(["項次", "執行項目"], axis=1)
            return table
        except PortalXKeyError:
            raise
    def get_news(self, class_id):
        """Get News of a Class"""
        try:
            switch_sub(self.portal_x_key, class_id)
            page = HTTP.request("GET",
                                "https://portalx.yzu.edu.tw/PortalSocialVB/FMain/PostWall.aspx?Menu=New",
                                headers=generate_header(self.portal_x_key))
            if "您尚未登入個人portal！" in page.data.decode("utf-8"):
                raise PortalXKeyError
            soup = bs4.BeautifulSoup(page.data.decode("utf-8"), "lxml").select("#divPostWall")[0]
            item_divs = soup.select(".PanelPost")
            for page_tag in soup.select(".aPageNum")[:-1]:
                page_num = page_tag.string
                item_divs += get_post_page(self.portal_x_key, page_num)
            newses = []
            for item_div in item_divs:
                item_title = item_div.find("a").string
                item_id = item_div["id"].replace("divPost", "")
                if "【最新消息】" in item_title:
                    post = {
                        "ID": item_id,
                        "標題": re.match(r"^【最新消息】(.*)\(.*?\)$", item_title).groups()[0],
                        "內容": get_post_content(self.portal_x_key, item_id),
                        "發布者": item_div.find("img")["title"],
                        "發布日期": item_div.select(".TDtitle")[3].string
                    }
                    newses.append(post)
            table = pandas.read_json(json.dumps(newses))
            if list(table.columns.get_values()) == []:
                table = table.assign(ID=[], 內容=[], 標題=[], 發布日期=[], 發布者=[])
            table = table.set_index("ID")
            table = table.reindex_axis(["發布日期", "發布者", "標題", "內容"], axis=1)
            table["發布日期"] = pandas.to_datetime(table["發布日期"], format="%Y.%m.%d")
            return table
        except PortalXKeyError:
            raise
    def download_files(self, link, name_with_path):
        """Download materials, homework... etc. with User's Key"""
        stream = HTTP.request("GET",
                              link,
                              headers=generate_header(self.portal_x_key),
                              preload_content=False)
        with open(name_with_path, 'wb') as out:
            while True:
                data = stream.read(32)
                if not data:
                    break
                out.write(data)
        stream.release_conn()
    def init_class_select_agent(self):
        from .select.utils import (
            baitFramePage,
            record_soup_and_params,
            refresh_CosList,
            refresh_CosTable
        )
        # Get Session Key
        entry_page = HTTP.request("GET",
                                  "https://isdna1.yzu.edu.tw/Cnstdsel/Index.aspx",
                                  headers=UAHEAD)
        entry_soup = bs4.BeautifulSoup(entry_page.data.decode("utf-8"), "lxml")
        self.class_select_key = [i for i in entry_page.headers["Set-Cookie"].split(", ") if i.find("ASP.NET") != -1][0].split(";")[0].split("=")[1]
        record_soup_and_params(self, entry_soup, "index")

        # Get Verifications
        pic_page = HTTP.request("GET",
                                "https://isdna1.yzu.edu.tw/Cnstdsel/SelRandomImage.aspx",
                                headers = generate_header(self.class_select_key))
        captcha_img = Image.open(io.BytesIO(pic_page.data))
        try:
            IPython.core.display.display(IPython.core.display.Image(data=pic_page.data))
        except:
            captcha_img.show()

        # Login
        captcha = input()
        fields = self.param["parameters"]["index"].copy()
        fields["DPL_SelCosType"] = "107-2-2" # TODO: Make this dynamic
        fields["Txt_User"] = self.user_id
        fields["Txt_Password"] = self.__password
        fields["Txt_CheckCode"] = captcha
        fields["btnOK"] = "確定"
        login_page = HTTP.request_encode_body("POST",
                                              "https://isdna1.yzu.edu.tw/Cnstdsel/Index.aspx",
                                              fields=fields,
                                              headers=generate_header(self.class_select_key),
                                              encode_multipart=False)
        login_soup = bs4.BeautifulSoup(login_page.data.decode("utf-8"), "lxml")
        record_soup_and_params(self, login_soup, "index")
        
        # Check Login
        if "驗證碼錯誤" in str(login_soup):
            raise ValueError("Validation Failed!!!")
        baitFramePage(self.class_select_key)
        if not refresh_CosList(self) and not refresh_CosTable(self):
            raise ValueError("Login Failed!!!")
        degree = self.param["soups"]["CosList"].select("#Lab_DeptDegree")[0].string
        name = self.param["soups"]["CosList"].select("#Lab_NameStdno")[0].string
    def join_class_via_Time(self, course_code, course_class, time):
        from .select.utils import (
            record_soup_and_params,
            refresh_CosTable
        )
        # Fetcing Command
        list_page = HTTP.request("GET",
                                 "https://isdna1.yzu.edu.tw/Cnstdsel/SelCurr/CosList.aspx?schd_time=" + time,
                                 headers=generate_header(self.class_select_key))
        list_soup = bs4.BeautifulSoup(list_page.data.decode("utf-8"), "lxml")
        if "已經逾時,請重新執行!" in str(list_soup):
            return False
        record_soup_and_params(self, list_soup, "CosList")
        cmd = self.param["soups"]["CosList"].find_all("input", id=re.compile("^SelCos,"+course_code+","+course_class))[0].get("id")
        
        # Select Action 1
        fields = self.param["parameters"]["CosList"].copy()
        fields[cmd+".x"] = random.randint(0, 9)
        fields[cmd+".y"] = random.randint(0, 12)
        list_page = HTTP.request_encode_body("POST",
                                 "https://isdna1.yzu.edu.tw/Cnstdsel/SelCurr/CosList.aspx?schd_time=" + time,
                                 fields=fields,
                                 headers=generate_header(self.class_select_key),
                                 encode_multipart=False)
        list_soup = bs4.BeautifulSoup(list_page.data.decode("utf-8"), "lxml")
        if "已經逾時,請重新執行!" in str(list_soup):
            return False
        record_soup_and_params(self, list_soup, "CosList")
        
        # Select Action 2
        select_page = HTTP.request("GET",
                                 "https://isdna1.yzu.edu.tw/Cnstdsel/SelCurr/CurrMainTrans.aspx",
                                 fields={
                                     "mSelType": "SelCos",
                                     "mUrl": cmd+",B,"
                                 }, headers=generate_header(self.class_select_key))
        select_soup = bs4.BeautifulSoup(select_page.data.decode("utf-8"), "lxml")
        if "已經逾時,請重新執行!" in str(select_soup):
            return False
        record_soup_and_params(self, select_soup, "CurrMainTrans")
        
        # Parse Message
        msg_parser = re.compile(r"alert\(\'(.*)\'\)\;")
        msg = msg_parser.search(select_soup.find_all("script")[0].string).group(1)
        print(msg)
        
        # Cleanup & Verify Selection
        if not refresh_CosTable(self):
            print("Error")
            return False
        if course_code+","+course_class in str(self.param["soups"]["CosTable"]):
            return True
        return False
    def join_class_via_Dept(self, course_code, course_class, dept, degree):
        """
        course_code   課號      CS303
        course_class  班別      A
        dept          系別代號   304  ->資工系
        degree        年級      2
        """
        from .select.utils import (
            record_soup_and_params,
            refresh_CosTable
        )
        
        # Fetching Command
        if course_code+","+course_class not in self.param["soups"]["CosList"]:
            fields = self.param["parameters"]["CosList"].copy()
            fields["DPL_DeptName"] = dept
            fields["DPL_Degree"] = degree
            list_page = HTTP.request_encode_body("POST",
                                     "https://isdna1.yzu.edu.tw/Cnstdsel/SelCurr/CosList.aspx",
                                     fields=fields,
                                     headers=generate_header(self.class_select_key),
                                     encode_multipart=False)
            list_soup = bs4.BeautifulSoup(list_page.data.decode("utf-8"), "lxml")
            if "已經逾時,請重新執行!" in str(list_soup):
                return False
            record_soup_and_params(self, list_soup, "CosList")
        cmd = self.param["soups"]["CosList"].find_all("input", id=re.compile("^SelCos,"+course_code+","+course_class))[0].get("id")
        
        # Select Action 1
        fields = self.param["parameters"]["CosList"].copy()
        fields["DPL_DeptName"] = dept
        fields["DPL_Degree"] = degree
        fields[cmd+".x"] = random.randint(0, 9)
        fields[cmd+".y"] = random.randint(0, 12)
        list_page = HTTP.request_encode_body("POST",
                                 "https://isdna1.yzu.edu.tw/Cnstdsel/SelCurr/CosList.aspx",
                                 fields=fields,
                                 headers=generate_header(self.class_select_key),
                                 encode_multipart=False)
        list_soup = bs4.BeautifulSoup(list_page.data.decode("utf-8"), "lxml")
        if "已經逾時,請重新執行!" in str(list_soup):
            return False
        record_soup_and_params(self, list_soup, "CosList")
        
        # Select Action 2
        select_page = HTTP.request("GET",
                                 "https://isdna1.yzu.edu.tw/Cnstdsel/SelCurr/CurrMainTrans.aspx",
                                 fields={
                                     "mSelType": "SelCos",
                                     "mUrl": cmd+",B,"
                                 }, headers=generate_header(self.class_select_key))
        select_soup = bs4.BeautifulSoup(select_page.data.decode("utf-8"), "lxml")
        if "已經逾時,請重新執行!" in str(select_soup):
            return False
        record_soup_and_params(self, select_soup, "CurrMainTrans")
        
        # Parse Message
        msg_parser = re.compile(r"alert\(\'(.*)\'\)\;")
        msg = msg_parser.search(select_soup.find_all("script")[0].string).group(1)
        print(msg)
        
        # Cleanup & Verify Selection
        if not refresh_CosTable(self):
            return False
        if course_code+","+course_class in str(self.param["soups"]["CosTable"]):
            return True
        return False
    def leave_class(self, course_code, course_class):
        from .select.utils import (
            record_soup_and_params,
            refresh_CosTable
        )
        # Fetching Command
        cmd = re.search(r"TmpDelCos\([\"'](DelCos," + course_code + "," + course_class + ".*?)[\"']\)", str(self.param["soups"]["CosTable"])).group(1)
        
        # Action
        select_page = HTTP.request("GET",
                                 "https://isdna1.yzu.edu.tw/Cnstdsel/SelCurr/CurrMainTrans.aspx",
                                 fields={
                                     "mSelType": "DelCos",
                                     "mUrl": cmd
                                 }, headers=generate_header(self.class_select_key))
        select_soup = bs4.BeautifulSoup(select_page.data.decode("utf-8"), "lxml")
        if "已經逾時,請重新執行!" in str(select_soup):
            return False
        record_soup_and_params(self, select_soup, "CurrMainTrans")
        
        # Parse Message
        msg_parser = re.compile(r"alert\(\'(.*)\'\)\;")
        msg = msg_parser.search(select_soup.find_all("script")[0].string).group(1)
        print(msg)
        
        # Cleanup & Verify Selection
        if not refresh_CosTable(self):
            print("Error")
            return False
        if course_code+","+course_class not in str(self.param["soups"]["CosTable"]):
            return True
        return False
