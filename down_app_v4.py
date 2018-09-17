#!/usr/bin/python
#coding=utf8

import urllib
import os
import pymongo
import time
from multiprocessing import Pool
import sys
import pymysql
reload(sys)
sys.setdefaultencoding('utf8')
import seting
import socket



global name,client,db,table,table1,apk_path,conn,cur


def mysql(url):
    
    app_path = 'http://192.168.2.251:8080/apk/'+url['app_name']+'.apk'
    date=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    pca_uploadpath = seting.pca_path
    print url["download-num"]
    uri = 'http://192.168.2.251:10009/file/upload'
    inserttime =  time.strftime('%Y-%m-%d',time.localtime(time.time()))
    if url.has_key('label') != True:
        url['label'] = ''
    try:
        print ("insert into app_info(Http_upload_uri,Pcap_nums,App_id,App_name,App_type,App_version,App_label,App_path,App_dwtime,App_source,Ask_status,Pcap_uploadpath,download_num) values\
       ('"+str(uri)+"',0,'"+url['_id']+"','"+url["app_name"]+"','"+url["type"]+"','"+url["version"]+"','"+url['label']+"','"+app_path+"','"+date+"','"+url["source"]+"',0,'"+pca_uploadpath+"','"+url["download-num"]+"')")

        cur.execute("insert into app_info(Http_upload_uri,Pcap_nums,App_id,App_name,App_type,App_version,App_label,App_path,App_dwtime,App_source,Ask_status,Pcap_uploadpath,download_num) values\
       ('"+str(uri)+"',0,'"+url['_id']+"','"+url["app_name"]+"','"+url["type"]+"','"+url["version"]+"','"+url['label']+"','"+app_path+"','"+date+"','"+url["source"]+"',0,'"+pca_uploadpath+"','"+url["download-num"]+"')")
       #cur.execute("insert into app_info(App_id,App_name,App_type,App_version,App_label,App_path,App_dwtime,App_source,Ftp_ip,Ftp_user,Ftp_pass,Ask_status,Pcap_uploadpath,download_num) values\
       #('"+url['_id']+"','"+url["app_name"]+"','"+url["type"]+"','"+url["version"]+"','"+url['label']+"','"+app_path+"','"+date+"','"+url["source"]+"','"+ftpip+"','"+ftpuser+"','"+ftppass+"',0,'"+pca_uploadpath+"','"+url["download-num"]+"')")
        conn.commit()
    except Exception,e:
        print str(e),'mysql fail ... ...'


def schedule(a, b, c):
    per = 100.0 * a * b / c
    if per > 100:
        per = 100
    print name+u"下载进度：",'%.2f%%' % per

def dowdnapp(url):
    socket.setdefaulttimeout(30)
    name=url["app_name"]+'.apk'
    dw_url=url["url"]
    filename = os.path.join(apk_path,name)
    try:
        print filename,"正在下载......."
        logfile.flush()
        urllib.urlretrieve(dw_url,filename)
        print filename,"下载已经完成！！！"
        logfile.flush()
        url["dw_status"]=1
        date=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        url["dw_time"]=date
        table.save(url)
        try:
            mysql(url)
            print 'mysql ok ...'
        except Exception,e:
            print str(e),'mysql erro ... ...'
            print url["_id"],"保存数据:",url
            logfile.flush()
    except Exception,e:
        table1.save(url)
        print filename,"下载失败，已送回fail数据库......"
        logfile.flush()

if __name__ == "__main__":
    #apk放置的路径
    apk_path=seting.apk_path
    print "----success-----"

    #conn = pymysql.connect(host='127.0.0.1',port=3306,user='app_ps',password='app_ps',db='app_ps',charset='utf8mb4',cursorclass = pymysql.cursors.DictCursor)
    conn = pymysql.connect(host=seting.MysqlIP,port=seting.MysqlPort,user=seting.Mysqluser,password=seting.Mysqlpawd,db=seting.MysqlDB,charset='utf8',cursorclass = pymysql.cursors.DictCursor)
    cur=conn.cursor()

    logtime = time.strftime('%Y%m%d',time.localtime(time.time()))
    logtemp = 'downapk'+str(logtime)+'.log'
    logfile=open(os.path.join(seting.logpath,logtemp),"a")
    #logfile=open("/tmp/downapp.log","a")
    sys.stderr = logfile
    sys.stdout = logfile
    logfile.flush()
    while True:
        client = pymongo.MongoClient(host=seting.MongoDBIP,port=seting.MongoDBPort,connect=False)
        mondb = seting.MongoDBdb
        montab = seting.MongoDBtb

        db = client[mondb]
        table = db[montab]
        table1=db['fail']
        pool = Pool(processes=3)
        for num in range(0,10):
            #url = table.find_one({"_id":"f7e189a20501e25f9de8c6b9318fc86b"})
            url=table.find_and_modify({"dw_status":0},remove=True)
            print url
            if url is None:
                print "No new app url......"
                num-=1
                time.sleep(1)
                continue
            result = pool.apply_async(dowdnapp, (url,))
        del db
        del table
        del table1
        del client
        pool.close()
        pool.join()
