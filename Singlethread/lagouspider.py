#! /usr/bin/env python
# -*-coding:utf-8

import re
import urllib2
from bs4 import BeautifulSoup
import json
from cprint import cprint
import random
import time
from openpyxl import Workbook

# 业务需求：
# 1、可以遍历抓取拉勾网上的职位信息，例如广州的所有python岗位信息
# 2、保存到excel表格中

# 划分4个类：
# HtmlMan、 ResearchMan、AllMan
# HtmlMan: 主要获取单个网页，然后返回结果
# ResearchMan: 主要分析获取到的网页，从网页内拿出需要的信息，并保存
# LinkMan：主要用于遍历整个站点，返回可以抓取的网页链接
# CallMan ：用于和用户终端交互



# 全局变量
ALL_POSTION_NUMBERS = 0 # 用来保存岗位个数，例如广州有93个岗位
ALL_POSTION_LINK = [] # 用来保存所有岗位详情页的链接
ALL_POSITION_DATE_LIST = [] # 用来保存所有的爬到的岗位数据

# 类：

class LinkMan():

    def __init__(self,city="",position=""):

        self.url = r"https://m.lagou.com/search.html"
        # 初始化时候获取到地区、岗位关键字
        if city != "" or position != "":

            self.city = city
            self.position = position
        else:
            self.city = "全国"
            self.position = "python"

        self.url_with_arg = r"https://m.lagou.com/search.json?city=%E5%B9%BF%E5%B7%9E&positionName=%E5%AE%89%E5%85%A8&pageNo=1&pageSize=15"  # 广州安全
        # 移动版
        self.m_url_with_arg = r"https://m.lagou.com/search.json?city=%E5%B9%BF%E5%B7%9E&positionName=python&pageNo=1&pageSize=15"
        self.url_china = r"https://m.lagou.com/search.json?city=%E5%85%A8%E5%9B%BD&positionName=%E5%AE%89%E5%85%A8&pageNo=1&pageSize=15"  # 全国安全
        self.position_url = "https://www.lagou.com/jobs/" # 例如https://www.lagou.com/jobs/3284150.html
        self.all_links_list = []
        self.get_all_links_is_run = False
        self.get_all_position_is_run = False

    def make_search_url(self,city="",keyword=""):
    # 函数用来构造url，例如北京地区的python岗位，返回url地址
        #
        if city == "" or keyword == "":

            city = self.city
            keyword = self.position

        print city,keyword

        url = r"https://m.lagou.com/search.json?city=" + str(urllib2.quote(city)) + "&positionName=" + str(urllib2.quote(keyword)) + r"&pageNo=1&pageSize=15"
        print url
        return url


    def get_all_links(self,city="",position=""):
    # 函数作用：把拉勾关键岗位的，输入：输入地方、岗位关键字，返回：装满岗位链接的list
    # 思路： 构建request -> urlopen -> 拿到json -> 正则表达式获取链接 -> 放入链接list

        # 城市，岗位参数可以是初始化时候传，也可以调用这个再传
        if city == "" or position == "":

            city = self.city
            position = self.position
        else:

            self.city = city
            self.position = position

        # 构建request  构造url、构造user-agent

        # 通过make_search_url 构造链接
        url = self.make_search_url(city=city,keyword=position)
        print url

        headers = {'User-Agent':r"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:54.0) Gecko/20100101 Firefox/54.0"}
        req = urllib2.Request(url=url,headers=headers)

        # 打开网页,，获取json字符串
        x = urllib2.urlopen(req)
        json_str = x.read()
        # print(type(json_str))
        # print(json_str)


        # 从json中读取所有的岗位数量,例如拿到了93，说明一页15个，则要分7页，要遍历7次
        global ALL_POSTION_NUMBERS
        print "日志：正在获取岗位数量"
        a = re.findall(r".totalCount.:.(\d+).", json_str)
        ALL_POSTION_NUMBERS = int(a[0])
        print "共有%s个岗位符合所有条件" % str(ALL_POSTION_NUMBERS)

        # 用来装id的
        all_links_list = [] #用来装link

        for i in range(1,ALL_POSTION_NUMBERS/15 + 2):

            print i
            links = re.findall(r"https.*&pageNo=",url)[0] + str(i) + "&pageSize=15"
            print links

            # 针对每一个链接，都访问一遍，然后把里面多有岗位id都拿出来
            url = links
            headers = {'User-Agent':r"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:54.0) Gecko/20100101 Firefox/54.0"}
            req = urllib2.Request(url=url,headers=headers)
            x = urllib2.urlopen(req)
            json_text = x.read()

            # 正则把id拿出来，通过id构建职位详情页的链接
            re_str = r".positionId.:(\d{7})" # 这个正则目的是提取出来"positionId":1435905 里面的id部分
            all_position_links_id = re.findall(re_str, json_text)
            print all_position_links_id

            # 构造所有职位链接
            for id in all_position_links_id:

                links = self.position_url + str(id) + ".html"
                print links
                all_links_list.append(links)


        # 返回列表
        print all_links_list
        print "列表共有 %s 个链接" % len(all_links_list)
        self.all_links_list = all_links_list
        self.get_all_links_is_run = True
        return all_links_list

    def get_all_position(self):
    # 函数作用：爬去所有里面的链接
    # 思路： 单线程，一个一个处理
        # 必须保证已经获取链接
        if self.get_all_links_is_run == False:

            self.get_all_links()

        self.get_all_position = True
        # 做好标记


        # 开始处理链接里面的内容
        links = self.all_links_list
        # 循环一个一个获取职位
        x = 1
        for one_position_link in links:

            print "正在抓取第 %s 个网页" % str(x)
            print one_position_link
            z = one_position_link

            a = HtmlMan(url=z)
            a_page_text = a.get_text()
            # a.print_html()
            # a.save_html()
            b = ResearchMan(a_page_text)
            b.get_text()
            b.print_position()
            x = x + 1

            # 程序暂停2~15随机。降低访问频率，能有效避免服务器屏蔽。
            time.sleep(random.randint(5,30))


        global ALL_POSITION_DATE_LIST
        cprint(ALL_POSITION_DATE_LIST) # 打印全局变量
        print(len(ALL_POSITION_DATE_LIST))

    def save_date_to_excel(self,save_path=""):

    # 函数作用：把所有爬到的数据，保存到表格中
    # 思路： for循环处理 -> 循环列表，然后一个一个写入工作表 -> 保存工作表
        # # 必须先获取到内容才行
        # if self.get_all_position_is_run == False:

        #     self.get_all_position()


        global ALL_POSITION_DATE_LIST

        # 判断数据不能为空
        if ALL_POSITION_DATE_LIST != []:

            # 准备好表格
            wb = Workbook()
            ws1 = wb.active
            # 做好表头
            ws1["A1"] = r"岗位"
            ws1["B1"] = r"地区"
            ws1["C1"] = r"公司"
            ws1["D1"] = r"薪资"
            ws1["E1"] = r"详情"


            # for循环,遍历为列表长度
            for i in range(1,len(ALL_POSITION_DATE_LIST)+1):
                # 要从A2、B2、C2、D2开始存

                ws1["A%s"%str(i+1)] = ALL_POSITION_DATE_LIST[i-1]["Position"]
                ws1["B%s"%str(i+1)] = ALL_POSITION_DATE_LIST[i-1]["City"]
                ws1["C%s"%str(i+1)] = ALL_POSITION_DATE_LIST[i-1]["Company"]
                ws1["D%s"%str(i+1)] = ALL_POSITION_DATE_LIST[i-1]["Pay"]
                ws1["E%s"%str(i+1)] = ALL_POSITION_DATE_LIST[i-1]["Description"]
                print i

            # 保存到本地
            wb.save("DATA.xlsx")

        else:

            print("暂无数据，无法保存到excel")
            return False


class HtmlMan():

    """这个类用来构建HTML报头，发送获取网页反馈"""

    def __init__(self,url='',body={}):

        # 一个报头文需要的信息
        self.url = url
        self.headers = {'User-Agent':r"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:54.0) Gecko/20100101 Firefox/54.0"}
        self.body = None
        self.webpage_html = ''
        self.run_start_spider = False


    def start_spider(self):

        """这个方法用来构建报文头request对象，和直接获取网页"""
        # 多弄几个列表
        a = r"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:54.0) Gecko/20100101 Firefox/54.0"
        b = r"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
        c = r"Opera/9.27 (Windows NT 5.2; U; zh-cn)"
        d = r"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)"
        e = r"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;"
        f = r"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)"
        g = r"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)"
        h = r"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11"
        user_agent_list= [a,b,c,d,e,f,g,h]
        print("正在构建请求报头")
        self.headers["User-Agent"] =  user_agent_list[random.randint(0,4)]
        print self.headers
        webpage_request = urllib2.Request(url=self.url,headers=self.headers)
        print("构建成功")

        print("正在爬取网页...")
        res = urllib2.urlopen(webpage_request)
        res_html_text =res.read()
        print("爬取成功!")

        # 设置变量，标记已经运行过一次了
        self.webpage_html = res_html_text
        self.run_start_spider = True


        return res_html_text


    def print_headers(self):

        """这个方法打印request报头"""
        pass

    def print_html(self):

        """这个方法打印返回的html"""

        if self.run_start_spider == False:

            self.start_spider()

        print("正在打印!")
        print self.webpage_html
        return self.webpage_html


    def save_html(self):

        if self.run_start_spider == False:

            self.start_spider()

        print("正在打开文件...")
        save_file = open("Test.html",'w')
        save_file.write(self.webpage_html)
        print("保存成功，已保存到桌面文件Test.html中")
        save_file.close()

        pass
    def get_text(self):

        """这个方法打印返回的html"""

        if self.run_start_spider == False:

            self.start_spider()

        return self.webpage_html



class ResearchMan():
    """这个类用于把输出的内容分析出内容来"""


    def __init__(self,web_html_text=""):


        # 这个是原始的html文档字符串
        self.html_text = web_html_text

        # 用字典来存储爬出来的关键信息
        self.position_dict = {'Position':"None",'Company':"None",'Pay':"None",'Description':"None",'Date':"None",'City':"None"}


    def get_text(self,web_html_text=''):
        """
        这个方法作用：用来把HTML文档提取出岗位信息。
        传入：传入html的字符串
        返回：字典 { 公司、岗位、薪资、职位描述、更新时间 }
        """

        # 思路： -> 构建文档对象 -> 找到职位、公司、薪资、时间、介绍几个内容，放入字典中

        web_html_text = self.html_text

        # print self.html_text
        # 构建文档对象
        soup = BeautifulSoup(web_html_text,"lxml")
        print("日志：构建文档对象...")

        # print(soup)

        # 提取职位
        print("日志：正在提取职位...")
        x = []
        if  soup.find_all('span',class_="name") == []:
            print "页面正在加载中...，没有获取到数据"
            return {}
        else:
            x = soup.find_all('span',class_="name")
            x = x[0] # 返回不是直接Tag对象，是一个列表，包含了Tag对象
            position_str = x.get_text() # 用Tag实例的get_text()方法可以直接获取内容
            self.position_dict['Position'] = position_str
        # print(type(x))
        # print(x)
        # print(x.get_text())
        # 提取成功，存到字典中

        print(self.position_dict['Position'])

        # 提取地区
        print("日志：正在提取地区...")
        j = soup.find_all("span",text=re.compile(r"/(.+) /")) #通过内容和正则匹配搜索
        j = j[0]
        # 提取成功，存到字典中,
        city_str = j.get_text() # 用Tag实例的get_text()方法可以直接获取内容
        city_str = re.findall(r"/(.+) /", city_str)[0]
        self.position_dict['City'] = city_str
        print(self.position_dict['City'])


        # 提取公司
        print("日志：正在提取公司...")
        y = soup.find_all(class_="company")
        y = y[0]
        # 提取成功，存到字典中
        company_str = y.get_text() # 用Tag实例的get_text()方法可以直接获取内容
        self.position_dict['Company'] = company_str
        print(self.position_dict['Company'])

        # 提取薪资
        print("日志：正在提取薪资...")
        z = soup.find_all(class_="salary")
        z = z[0]
        # 提取成功，存到字典中
        pay_str = z.get_text() # 用Tag实例的get_text()方法可以直接获取内容
        self.position_dict['Pay'] = pay_str
        print(self.position_dict['Pay'])


        # 提取岗位描述
        print("日志：正在提取岗位描述...")
        d = soup.find_all(class_="job_bt")
        d = d[0]
        # 提取成功，存到字典中
        description_str = d.get_text() # 用Tag实例的get_text()方法可以直接获取内容
        self.position_dict['Description'] = description_str
        print(self.position_dict['Description'])


        # 把获取到的数据，放入全局列表中[{岗位1信息}，{岗位2信息}，{岗位3信息}]

        global ALL_POSITION_DATE_LIST
        ALL_POSITION_DATE_LIST.append(self.position_dict)


    def save_to_file(self,save_file_path="File_Text.txt",position_dict={}):
        """
        这个方法作用：把读出来的东西存到文件中
        传入：保存路径、保存内容
        返回：成功的状态
        """
        pass

    def save_to_excel(self,save_file_path="File_Text.txt",position_dict={}):
        """
        这个方法作用：把读出来的东西存到文件中，形式为excel表格
        传入：保存路径、已经提取好的字典内容
        返回：成功的状态
        """
        pass


    def print_position(self,position_dict=None):
        """
        这个方法作用：打印到终端
        传入：已经提取好的字典内容
        返回：成功的状态
        """
        if position_dict == None:

            position_dict = self.position_dict

        # print(json.dumps(position_dict,ensure_ascii=False,encoding='utf-8'))

        cprint(position_dict)


    def text_spilit(self,position_dict={}):
        """
        这个方法作用：用正则表达式，将职位描述再拆出来，然后在放入新的字典中
        传入：已经提取好的字典内容
        返回：新的更详细的字典
        """
        pass


# 执行入口
if __name__ == "__main__":

    # a = HtmlMan(url="https://www.lagou.com/jobs/1234751.html")
    # a.save_html()

    # html_text = a.get_text()

    # #
    # # print(html_text)

    # lagou_date = ResearchMan(html_text)
    # lagou_date.get_text()
    # lagou_date.print_position()



    city = ""
    position_keyword = ""


    while True:


        print "-------------------------------------------------------"
        print "| lagou单线程爬虫1.0 by yg "
        print ""
        print "| 简介：输入城市、岗位关键字，自动爬相关岗位信息到桌面excel表中|"
        print "-------------------------------------------------------"

        # 用户选择
        user_choose = raw_input("输入任意键继续使用程序,或 q 退出程序：")
        print "您的选择是" + user_choose

        if user_choose == "q" or user_choose =="Q":

            exit()

        else:

            # 要求用户输入城市
            city_dict = {"1":"全国","2":"北京","3":"上海","4":"广州","5":"深圳","6":"杭州","7":"成都"}
            print "请输入序号选择城市(1:全国 2:北京 3:上海 4:广州 5:深圳 6:杭州 7:成都)"
            list = ["1","2","3","4","5","6","7","q","Q"]
            user_input_city = raw_input(":")

            # 判断城市是否正确
            while True :

                if user_input_city == "1":
                    city = city_dict["1"]
                    break
                elif user_input_city == "2":
                    city = city_dict["2"]
                    break
                elif user_input_city == "3":
                    city = city_dict["3"]
                    break
                elif user_input_city == "4":
                    city = city_dict["4"]
                    break
                elif user_input_city == "5":
                    city = city_dict["5"]
                    break
                elif user_input_city == "6":
                    city = city_dict["6"]
                    break
                elif user_input_city == "7":
                    city = city_dict["7"]
                    break
                elif user_input_city == "q" or user_input_city =="Q":

                    print("用户退出程序")
                    exit()
                else:
                    print "请输入对应序号"

            # print city
            # 要求用户输入岗位关键字
            print "请输入需要爬去的岗位关键字(例如：产品经理)"
            user_input_city = raw_input(":")
            position_keyword = user_input_city

            break

    print city,position_keyword
    # 获取用户输入的地区、岗位，开始爬数据

    x = LinkMan(city,position_keyword)
    x.get_all_links()
    x.get_all_position()
    x.save_date_to_excel()


