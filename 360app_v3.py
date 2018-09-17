#coding=utf-8
from bs4 import BeautifulSoup
import urllib2
import time
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import pymongo
from multiprocessing import Pool
from urlparse import urljoin
import json
import hashlib   
import seting
import os

global client,db,tale,date


def htmllist(url):
    print url
    req_timeout=10
    req_header={'User-Agent':'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'}
    req = urllib2.Request(url,None,req_header)
    response = urllib2.urlopen(req,None,req_timeout)
    data_all = response.read()
    soup = BeautifulSoup(data_all.decode('utf8','ignore'),"lxml")  #实例化一个BeautifulSoup对象
    print soup.title.string
    
    url_list = []
    for link in soup.find_all('a'):
        if '/detail/index/soft_id/' in link.get('href')  and '|' not in link.get('href'):
            index = urljoin(url,link.get('href'))
            if index not in url_list:
                print index
                url_list.append(index)
    print url_list
    htmlanalysis(url_list)
    
    
def htmlanalysis(url_list):
    print url_list,'11111111111111'
    for url in url_list:
        print url
        app_info = {}
        app_label = []
        
        req_timeout=10
        req_header={'User-Agent':'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'}
        req = urllib2.Request(url,None,req_header)
        response = urllib2.urlopen(req,None,req_timeout)
        data_all = response.read()
        soup = BeautifulSoup(data_all.decode('utf8','ignore'),"lxml")  #实例化一个BeautifulSoup对象
        
        cctag = soup.find_all(href=re.compile("http://shouji.360tpcdn.com"))
        
        
        for i in cctag:
            a=i.attrs['href'].split("&")
            print a[0],a[3],a[-1]
            #app_info["source"] = a[0].split('://')[0]
            app_info["app_name"] = a[3].split('=')[1]
            app_info["url"] = a[-1].split('=')[1]
        
        
        cctag = soup.find_all(href=re.compile("http://zhushou.360.cn/search/index/"))
        
        label=''
        
        for i in cctag:
            label = label+i.text+'|'
        print label
        
        
        a=soup.find_all("td")
        company = a[0].text.split('：')[1]
        apkupdatetime = a[1].text.split('：')[1]
        version = a[2].text.split('：')[1]
        phone_system = a[3].text.split('：')[1]
        apk_lange = a[4].text.split('：')[1]
        
        download_num = soup.select('.s-3')[0].text[3:]
        size = soup.select('.s-3')[1].text

        app_info["source"] = "360手机助手"
        app_info["label"] = label
        app_info["company"] = company
        app_info["version"] = version
        app_info["dw_status"] = 0
        app_info["download-num"] = download_num
        app_info["version"] = version
        app_info["size"] = size
        app_info["type"] = '软件'
        app_info["apkupdatetime"] = apkupdatetime
        app_info["phone_system"] = phone_system
        app_info["apk_lange"] = apk_lange

        m2 = hashlib.md5()
        m2.update(app_info['app_name']+'|'+app_info['version'])
        app_id = m2.hexdigest()
        app_info['_id'] = app_id
        
        new = json.dumps(app_info)
        newjson = json.loads(new)
        try:
            print newjson
            table.insert(newjson)
            print 'okokok'
            
        except Exception,e:
            print str(e),'APP 重复 ... ...'


#下载网页并解析app信息
def html(url):
    try:
        req_timeout=10
        req_header={'User-Agent':'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'}
        req = urllib2.Request(url,None,req_header)
        response = urllib2.urlopen(req,None,req_timeout)
        data_all = response.read()
        soup = BeautifulSoup(data_all.decode('utf8','ignore'),"lxml")  #实例化一个BeautifulSoup对象
        print soup.title.string
        cctag = soup.find_all(href=re.compile("http://shouji.360tpcdn.com"))

        for i in cctag:
            a=i.attrs['href'].split("&")
            print a[0],a[3],a[-1]
            souce=a[0].split("=")[0]
            name=a[3].split("=")[1]
            url=a[-1].split("=")[1]
            logfile.flush()
            try:
                tale.insert({"_id":name,"app_url":url,"time":date,"source":souce,"dw_status":0})
            except Exception,e:
                print "app url已存在........"
                logfile.flush()

    except Exception,e:
        print "网页解析失败........"
        logfile.flush()

if __name__ == "__main__":
    # src_url="http://zhushou.360.cn/list/index/cid/1/?page=50"
    client = pymongo.MongoClient(host=seting.MongoDBIP,port=seting.MongoDBPort,connect=False)
    mondb = seting.MongoDBdb
    montab = seting.MongoDBtb

    db = client[mondb]
    table = db[montab]
    date=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

    logtime = time.strftime('%Y%m%d',time.localtime(time.time()))
    logtemp = '360softcrawl'+str(logtime)+'.log'
    logfile=open(os.path.join(seting.logpath,logtemp),"a")
    sys.stderr = logfile
    sys.stdout = logfile
    logfile.flush()

    pool = Pool(processes=1)
    #src_url="http://zhushou.360.cn/list/index/cid/1/?page="
    src_url = "http://zhushou.360.cn/list/index/cid/1/?page="
    for num in range(1,105):
        url=src_url+str(num)
        result = pool.apply_async(htmllist, (url,))
        if num%3 == 0:
            print num
            time.sleep(40)
    pool.close()
    pool.join()
    client.close()



