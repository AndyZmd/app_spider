# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )
import urllib2
import re
import json
from bs4 import BeautifulSoup
import pymongo
import hashlib
import seting
import os
import time

global logfile

class AppSipder:
    def __init__(self,category_num):
        # URL模式：http://shouji.baidu.com/software/502/list_x.html,分成三个部分
        """

        :rtype : object
        """
        self.base_URL = 'http://shouji.baidu.com/software/'
        # 类别数字
        self.category_num  = category_num
        print self.category_num
        #分页编号
        self.page_num = [1,2, 3, 4, 5, 6, 7, 8]
        logfile.flush()

    # 获得所有应用 类别 页的url
    def getAppCategoryPageURL(self):
        # 所有应用类别的URLlist
        categoryPageURL_list = []
        #for x in self.category_num:
        for y in self.page_num:
            categoryPageURL_list.append(self.base_URL + str(self.category_num) + '/list_' + str(y) + '.html')
        return categoryPageURL_list

    # 爬取所有应用 详情 页的url
    @property
    def getAppDetailPageURL(self):
        categoryPageURL_list = self.getAppCategoryPageURL()
        print self.getAppCategoryPageURL()
        appDetailPageURL_list = []
        for url in categoryPageURL_list:
            # 构造request请求对象
            print url, "----------------------"
            logfile.flush()
            request = urllib2.Request(url)
            response = urllib2.urlopen(request,timeout=30)
            content = response.read().decode("unicode-escape")
            #re模块用于对正则表达式的支持,pattern可以理解为一个匹配模式,re.S指"."可以匹配换行"\n"
            pattern = re.compile(r'''<a class="app-box" href="(.*?)" target="_blank"''', re.U|re.S)
            resultStr = re.findall(pattern, content)

            print len(resultStr)
            for result in resultStr:
                #print 'crawling ' + result
                appDetailPageURL = 'http://shouji.baidu.com' + result
                appDetailPageURL_list.append(appDetailPageURL)
        return appDetailPageURL_list

    # 爬取App详情页中的所需内容
    def getAppInfo(self, appURL):
        try:
            request = urllib2.Request(appURL)
            response = urllib2.urlopen(request,timeout=30)
        except urllib2.URLError, e:
            print "Get appInfo failed:", e.reason
            return None
        content = response.read().decode("utf-8")
        # 创建保存结果的dict
        result = {}
        #得到app名字
        pattern = re.compile('<span>(.*?)</span>')
        resultStr = re.search(pattern, content)
        if resultStr:
            
            result['app_name'] = resultStr.group(1)#.encode('utf8')#.encode('utf8')
            print '正在抓取：',result['app_name'],u'详细信息... ...'
        # 得到app大小，需要对字符串处理
        pattern = re.compile('<span class="size">(.*?)</span>')
        resultStr = re.search(pattern, content)
        if resultStr:
            result['size'] = (((resultStr.group(1)).split(':'))[1]).strip()

        #APP 类别
        pattern =re.compile('<a target="_self" href="/software/.*/">(.*?)</a>')
        resultStr=re.search(pattern,content)

        if resultStr:
            result["type"]=resultStr.group(1)
        else:
            result["type"] = ""
        #版本
        pattern = re.compile('<span class="version">(.*?)</span>')
        resultStr = re.search(pattern, content)
        if resultStr:
            result['version'] = (((resultStr.group(1)).split(':'))[1]).strip()

        #下载量
        pattern = re.compile('<span class="download-num">(.*?)</span>')
        resultStr = re.search(pattern, content)
        if resultStr:
            result['download-num'] = (((resultStr.group(1)).split(':'))[1]).strip()

        #下载地址
        pattern = re.compile('<div.*?area-download">.*?<a target="_blank.*?href="(.*?)".*?>', re.S)
        resultStr = re.search(pattern, content)
        if resultStr:
            result['url'] = resultStr.group(1)

        # #LOGO URL
        # pattern = re.compile('<img src="(.*?)".*?/>')
        # resultStr = re.search(pattern, content)
        # if resultStr:
        #     result['app-pic'] = resultStr.group(1)


        # #详情页
        # result['page-url'] = appURL
        #
        # #应用描述
        # pattern = re.compile('<p.*?content content_hover">(.*?)<span.*?>.*?</span></p>', re.S)
        # resultStr = re.search(pattern, content)
        # if resultStr:
        #     result['description'] = resultStr.group(1)
        # else:
        #     pattern = re.compile('<div class=.*?brief-long">.*?<p.*?content">(.*?)</p>.*?</div>', re.S)
        #     resultStr = re.search(pattern, content)
        #     if resultStr:
        #         result['description'] = resultStr.group(1)
        #
        # #应用截图
        # pattern = re.compile('<li><img data-default=.*?src="(.*?)".*?>', re.S)
        # resultStr = re.search(pattern, content)
        # if resultStr:
        #     result['screen-shot'] = resultStr.group(1)
        #print result
        return result

    #爬虫开始入口
    def startSpider(self):
        print 'Start crawling please wait...'
        appDetailPageURL_list = self.getAppDetailPageURL
        resultInfo = []
        for url in appDetailPageURL_list:
            resultInfo.append(self.getAppInfo(url))
        print len(resultInfo), 'apps have been crawled.'
        print '开始入库 ... ...'
        client = pymongo.MongoClient(host=seting.MongoDBIP,port=seting.MongoDBPort,connect=False)
        mondb = seting.MongoDBdb
        montab = seting.MongoDBtb

        db = client[mondb]
        table = db[montab]
        for i in resultInfo:
            i=json.dumps(i)
            i=json.loads(i)
            print i['app_name'],i['version']
            app_info = i['app_name'] +'|'+ i['version']
            print app_info
            m2 = hashlib.md5()   
            m2.update(app_info)   
            app_md5=m2.hexdigest()   
            i["_id"]=app_md5
            i["dw_status"]=0
            i["source"]= '百度手机助手'
            i["company"] = ""
            i["label"] = ""
            i["apk_lange"] = ""
            i["phone_system"] = ""
            i["apkupdatetime"] = ""
            
            # print type(i)
            # print i["_id"]
            
            try:
                table.insert(i)
                print i['_id'],"-------okokokokok-----------"
            except Exception,e:
                print "-------nono-----------------"
        print 'Finished.'
        logfile.flush()
if __name__ == "__main__":
    list = [401, 403, 405, 408, 402, 406, 404, 407]
    logtime = time.strftime('%Y%m%d',time.localtime(time.time()))
    logtemp = 'baidugamedownapk'+str(logtime)+'.log'
    logfile=open(os.path.join(seting.logpath,logtemp),"a")
    sys.stderr = logfile
    sys.stdout = logfile
    logfile.flush()
    for category_num in list:
        print category_num
        Spider = AppSipder(category_num)
        Spider.startSpider()

