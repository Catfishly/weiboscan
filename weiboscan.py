# -*- coding:utf-8 -*-

import ConfigParser
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import requests
from bs4 import BeautifulSoup
import tempfile
from PIL import Image
import math
import random
import MySQLdb
import json

#db = MySQLdb.connect("localhost","weibo","weibo1qaz","weibo",charset='utf8')

#firefox_profile = webdriver.FirefoxProfile()
#firefox_profile.set_preference("browser.privatebrowsing.autostart", True)

# 创建一个logger
logger = logging.getLogger('weiboscan')
logger.setLevel(logging.DEBUG)

# 创建一个handler，用于写入日志文件
fh = logging.FileHandler('weiboscan.log')
fh.setLevel(logging.DEBUG)

# 再创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# 定义handler的输出格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# 给logger添加handler
logger.addHandler(fh)
logger.addHandler(ch)

# 记录一条日志
logger.info('start weiboscan logging')

def mysqlu(account_file):
    logger.info('account start config file')
    cf = ConfigParser.ConfigParser()
    cf.read(account_file)
    mysql={}
    mysql['username'] = cf.get("mysql","username")
    mysql['password'] = cf.get("mysql","password")
    mysql['port'] = cf.get("mysql","port")
    mysql['host'] = cf.get("mysql","host")
    mysql['database'] = cf.get("mysql","database")

    return mysql



def account(account_file):
    logger.info('account start config file')
    cf = ConfigParser.ConfigParser()
    cf.read(account_file)
    username = cf.get("account","username")
    password = cf.get("account","password")
    names = cf.get("account","names")
    return username,password,names

class webbrowse(object):

    def __init__(self,username,password,names,mysql):
        logger.info('__init__ webbrowse')
        self.username = username
        self.password = password
        self.names = names
        self.mysql_username=mysql['username']
        self.mysql_password=mysql['password']
        self.mysql_port=int(mysql['port'])
        self.mysql_host=mysql['host']
        self.mysql_database=mysql['database']
        self.cookies = {}
	self.gsid = ""
        self.db = MySQLdb.connect(host = self.mysql_host, user = self.mysql_username, \
                                passwd = self.mysql_password , db = self.mysql_database , port = self.mysql_port, charset='utf8mb4')
        self.cursor = self.db.cursor()
        logger.info('username %s and password xxxx and names %s' % (username,names))
        logger.info('mysql username %s and password xxxx and host %s' % (mysql['username'],mysql['host']))
#        self.bro = webdriver.Firefox(firefox_profile=firefox_profile)
        #self.bro = webdriver.Firefox()

        self.bro = webdriver.PhantomJS()

    def __exit__(self):
        try:
            self.bro.close()
        except:
            logger.info('close webdriver error')

        logger.info('close webbrowse')


    def login(self):
        logger.info('exec login def')
        self.bro.get("http://weibo.cn/")

        logger.info('check login in ')
        login1 = self.bro.find_element_by_link_text('登录')
        login1.click()


        logger.info('find element username')
        u1 = self.bro.find_element_by_name("mobile")
#        u1.clear()
        u1.send_keys(self.username)

        logger.info('find element password')
        p1 = self.bro.find_element_by_xpath('/html/body/div[2]/form/div/input[2]')
#        p1.clear()
        p1.send_keys(self.password)

	ver_re = re.compile(u'请输入图片中的字符',re.U)
	try:
	    ver = ver_re.search(self.bro.page_source)
            logger.info('ver is %s' % ver)
	    if ver:
		img_s = self.bro.find_element_by_xpath('/html/body/div[2]/form/div/img')
		img = img_s.get_attribute('src')
                print "img %s" % img
		r = requests.get(img)
		tmpfile = tempfile.mktemp()
                print "tmpfile %s " % tmpfile
		f = open(tmpfile,'wb+')
		for chunk in r.iter_content(chunk_size=1024):
		    if chunk:
		    	f.write(chunk)
		f.close()
		images = Image.open(tmpfile)
		images.show()

		ver_code = raw_input("请输入验证码")
                print "ver_code %s" % ver_code
	        vc = self.bro.find_element_by_name("code")
    		vc.send_keys(ver_code)
		
	except:
	    print "tttttttttttttttttttt"
	    
#        time.sleep(2)

        if ver:
            logger.info('click enter and login in and ver')
            b2 = self.bro.find_element_by_xpath('/html/body/div[2]/form/div/input[10]')
            b2.click()

        else:
            logger.info('click enter and login in')
            b1 = self.bro.find_element_by_xpath('/html/body/div[2]/form/div/input[8]')
            b1.click()


    def login_is(self):
        self.login()
        logger.info('exec login_is def')
        test = EC.text_to_be_present_in_element(
                (By.CLASS_NAME,"ut"),self.names.decode('utf-8'))
        n = 0
        while n < 3:
	     
            try:
                #print test(self.bro)
                if test(self.bro):
                    logger.info('1')
                    logger.info('login in the weibo')
                    ret = self.bro.get_cookies()
		    print ret,self.bro.current_url
                    for cookie in ret:
                        self.cookies[str(cookie['name'])] = str(cookie['value'])
		    print self.cookies
		    self.gsid=self.cookies['SUB']
		    print self.gsid
                    break
                else:
                    logger.info('2')
                    n +=1
                    self.login()
            except:
                n += 1
                time.sleep(1)
                logger.info('4')

        logger.info('3')
        logger.info('n is %s' % n)
        if n >3:
            logger.info('not to login in weibo and quit')
            self.bro.quit()

    def userinfo(self,uid):
        url = 'http://weibo.cn/' + uid + '/info'
        logger.info('check userinfo url %s' % url)
#        print self.cookies
        r = requests.get(url,cookies=self.cookies)
        if r.status_code == 200:
            html = r.text
	    soup = BeautifulSoup(html, 'html.parser')
            logger.info('access url is OK' )
            #level = re.findall(u'会员等级：[^<]+',html)
            #logger.info('user level %s' % level )
#            print level
	    htmldiv = soup.find_all('div')
            #print htmldiv
            #logger.info('htmldiv is %s' % htmldiv)
            level_re = re.compile(r'会员等级：(.+)')
	    uname_re = re.compile(r'昵称:(.+)')
	    renzhen_re = re.compile(r'认证:(.+)')
	    sex_re = re.compile(r'性别:(.+)')
	    location_re = re.compile(r'地区:(.+)')
            birthday_re = re.compile(r'生日:(.+)')
	    renzheninfo_re = re.compile(r'认证信息：(.+)')
            brief_re = re.compile(r'简介:(.+)')

	    level = uname = renzhen = sex = location = birthday = renzheninfo = brief = ""
            for div in htmldiv:
                for x in div.strings:

                    #logger.info('x type %s is %s' % (type(x),x))
                #x = j.decode('utf-8')
#                    logger.info('x string %s' % x)
                    #level_1 = level_re.search(x.encode('utf-8'))
                    #if level_1:
                    #    logger.info('level_re is match')
                    x = x.encode('utf-8')
                    try:
                        level_1 = level_re.search(x)
                        if level_1:
                            level = level_1.group(1)
	                    logger.info('levle %s' % level)
                            #logger.info('x is %s' % x)
                    except:
                        #logger.info('x is %s' % x)
                        logger.info('not regex level')

                    try:
                        uname_1 = uname_re.search(x)
                        if uname_1:
                            uname = uname_1.group(1)
	                    logger.info('uname %s' % uname)
                            #logger.info('x is %s' % x)
                    except:
                        #logger.info('x is %s' % x)
                        logger.info('not regex uname ')

                    try:
                        renzhen_1 = renzhen_re.search(x)
                        if renzhen_1:
                            renzhen = renzhen_1.group(1)
	                    logger.info('renzhen %s' % renzhen)
                            #logger.info('x is %s' % x)
                    except:
                        #logger.info('x is %s' % x)
                        logger.info('not regex renzhen ')

                    try:
                        sex_1 = sex_re.search(x)
                        if sex_1:
                            sex = sex_1.group(1)
	                    logger.info('sex %s' % sex)
                            #logger.info('x is %s' % x)
                    except:
                        #logger.info('x is %s' % x)
                        logger.info('not regex sex ')

                    try:
                        location_1 = location_re.search(x)
                        if location_1:
                            location = location_1.group(1)
	                    logger.info('location %s' % location)
                            #logger.info('x is %s' % x)
                    except:
                        #logger.info('x is %s' % x)
                        logger.info('not regex location ')

                    try:
                        birthday_1 = birthday_re.search(x)
                        if birthday_1:
                            birthday = birthday_1.group(1)
	                    logger.info('birthday %s' % birthday)
                            #logger.info('x is %s' % x)
                    except:
                        #logger.info('x is %s' % x)
                        logger.info('not regex birthday ')

                    try:
                        renzheninfo_1 = renzheninfo_re.search(x)
                        if renzheninfo_1:
                            renzheninfo = renzheninfo_1.group(1)
	                    logger.info('renzheninfo %s' % renzheninfo)
                            #logger.info('x is %s' % x)
                    except:
                        #logger.info('x is %s' % x)
                        logger.info('not regex renzheninfo ')

                    try:
                        brief_1 = brief_re.search(x)
                        if brief_1:
                            brief = brief_1.group(1)
	                    logger.info('brief %s' % brief)
                            #logger.info('x is %s' % x)
                    except:
                        #logger.info('x is %s' % x)
                        logger.info('not regex brief ')

	    #print level,uname,renzhen,sex,location,birthday,renzheninfo,brief
            data=(int(uid),level,uname,renzhen,sex,location,birthday,renzheninfo,brief)
            add_user = ("INSERT INTO user "
                    "(uid,level,uname,renzhen,sex,location,birthday,renzheninfo,brief) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)" )
            try:
                self.cursor.execute(add_user,data)
		logger.info(add_user % data)
            except:
                pass
            self.db.commit()

	    #level_temp = htmldiv[2].contents[0]
	    #print level_temp
	    #try:
	    #    level_re = re.search(u'会员等级：(.+)',level_temp)
	    #    level = level_re.group(1)
	    #    logger.info('levle %s' % level)
	    #except:
	    #	level = ""

#	    user_n = len(htmldiv[4].contents)
#	    i = 0
#	    uname = ""
#            renzhen = ""
#            sex = ""
#            location = ""
#            birthday = ""
#            renzheninfo = ""
#            brief = ""
#
#	    while user_n -1 > i:
#		print htmldiv[4].contents[i]
#		logger.info('html %s ' % htmldiv[4].contents[i])
#
#  		try:
#		    uname_re = re.search(u'昵称:(.+)',htmldiv[4].contents[i])
#         	    uname = uname_re.group(1)
#		except:
#		    pass
#		    #uname = ""
#		
#  		try:
#		    renzhen_re = re.search(u'认证:(.+)',htmldiv[4].contents[i])
#         	    renzhen = renzhen_re.group(1)
#		except:
#		    pass
#		    #renzhen = ""
#		
#  		try:
#		    sex_re = re.search(u'性别:(.+)',htmldiv[4].contents[i])
#         	    sex = sex_re.group(1)
#		except:
#		    pass
#		    #sex = ""
#		
#  		try:
#		    location_re = re.search(u'地区:(.+)',htmldiv[4].contents[i])
#         	    location = location_re.group(1)
#		except:
#		    pass
#		    #location = ""
#		
#  		try:
#		    birthday_re = re.search(u'生日:(.+)',htmldiv[4].contents[i])
#         	    birthday = birthday_re.group(1)
#		except:
#		    pass
#		    #birthday = ""
#		
#  		try:
#		    renzheninfo_re = re.search(u'认证信息：(.+)',htmldiv[4].contents[i])
#         	    renzheninfo = renzheninfo_re.group(1)
#		except:
#		    pass
#		    #renzheninfo = ""
#		
#  		try:
#		    brief_re = re.search(u'简介:(.+)',htmldiv[4].contents[i])
#         	    brief = brief_re.group(1)
#		except:
#		    pass
#		    #brief = ""
#
#		i += 1
#            print "*" * 80
#	    print uname,renzhen,sex,location,birthday,renzheninfo,brief
 
        else:
            logger.info('access url is Error' )

    def userinfo2(self,uid):
	url = 'http://weibo.cn/u/' + uid
        logger.info('userinfo2 access url %s' % url)
        r = requests.get(url,cookies=self.cookies)
        if r.status_code == 200:
            logger.info('access url is OK' )
            html = r.text
            #print html
            soup = BeautifulSoup(html, 'html.parser')
	    htmldiv = soup.find_all('div')
#	    n = len(htmldiv[4].contents)
#	    i = 0
	    self.profile = ""
	    self.follow = ""
	    self.fans = ""
            #print n,i,
	    #print htmldiv[4].contents
	    #for x in htmldiv[3].contents:
	    #	print x
	    profile_re = re.compile(r'微博\[(\d+)\]')
	    follow_re = re.compile(r'关注\[(\d+)\]')
            fans_re = re.compile(r'粉丝\[(\d+)\]')

	    for div in htmldiv:
		for x in div.strings:
		    #logger.info('x string %s' % x)
		    x = x.encode('utf-8')
                    try:
                        profile_1 = profile_re.search(x)
                        if profile_1:
                            self.profile = profile_1.group(1)
                            #logger.info('x is %s' % x)
                            logger.info('profile %s' % self.profile)
                    except:
			pass
                        #logger.info('x is %s' % x)
                        #logger.info('not regex profile')

                    try:
                        follow_1 = follow_re.search(x)
                        if follow_1:
                            self.follow = follow_1.group(1)
                            #logger.info('x is %s' % x)
                            logger.info('follow %s' % self.follow)
                    except:
			pass
                        #logger.info('x is %s' % x)
                        #logger.info('not regex follow')

                    try:
                        fans_1 = fans_re.search(x)
                        if fans_1:
                            self.fans = fans_1.group(1)
                            #logger.info('x is %s' % x)
                            logger.info('fans %s' % self.fans)
                    except:
			pass
                        #logger.info('x is %s' % x)
                        #logger.info('not regex fans')

	    print self.profile,self.follow,self.fans
	    try:
                data=(int(self.profile),int(self.follow),int(self.fans),int(uid))
	    except:
		pass
	
            add_user = ("UPDATE user SET "
                    "profile = %s ,follow = %s,fans = %s "
                    " where uid = %s " )
	    try:
                self.cursor.execute(add_user,data)
		logger.info(add_user % data)
	    except:
		pass
            self.db.commit()
#	    while n-1 > i:
#		print htmldiv[3].contents[i]
#		logger.info('html %s ' % htmldiv[3].contents[i])	
#
#		try:
#                    profile_re = re.search(r'微博\[(\d+)\]',htmldiv[3].contents[i].encode('utf8'))
#                    profile = profile_re.group(1)
#                except:
#                    pass
#
#		try:
#                    follow_re = re.search(r'关注\[(\d+)\]',htmldiv[3].contents[i].encode('utf8'))
#                    follow = follow_re.group(1)
#                except:
#                    pass
#
#		try:
#                    fans_re = re.search(r'粉丝\[(\d+)\]',htmldiv[3].contents[i].encode('utf8'))
#                    fans = fans_re.group(1)
#                except:
#                    pass
#
#		i += 1
#	    print profile,follow,fans

	else:
	    logger.info('access url is Error' )

    def userfollow(self,uid):
        #print type(self.follow),self.follow
        if self.follow == '0':
            logger.info('user follow is null')
            return 0

	url = 'http://weibo.cn/' + uid + '/follow'
        logger.info('userfollow access url1   %s' % url)
        r = requests.get(url,cookies=self.cookies)
        if r.status_code == 200:
            logger.info('userfollow url is OK' )
	    self.follow_user(r.text,"1")

	    #logger.info('follow user %s' % r.text)
	else:
	    logger.info('userfollow url is Error')

        pagenumber = 10.0
        n = 0
	if int(self.follow) >= pagenumber:
	    n = int(math.ceil(int(self.follow)/pagenumber+1))
	    print "page number %s" % n
	    if n > 21:
		n = 21	    

	    for page in xrange(2,n):
	        url1 = url + '?page=' + str(page)
   	        logger.info('userfollow access url2 %s %s' % (url1,page))
 	        r = requests.get(url1,cookies=self.cookies)
                if r.status_code == 200:
                    logger.info('userfollow url is OK' )
                    self.follow_user(r.text,page)
                    #logger.info('follow user %s' % r.text)
                else:
                    logger.info('userfollow url is Error')



    def follow_user(self,html,page):
	logger.info('follow_user exec')
        soup = BeautifulSoup(html, 'html.parser')
        followlist  = soup.find(attrs={"name":"uidList"})
        try:
            uidlist = [x for x in followlist.attrs["value"].split(",")]
        except:
            uidlist=""

	logger.info("uidlist %s page %s" % (uidlist,page) )
        for x in uidlist:
            print "uid list x %s --- " % x
            self.userinfo(x)
            self.userinfo2(x)

    def userfans(self,uid):
	print "111" * 80
        if self.fans == '0':
            logger.info('user fans is null')
            return 0

	print "222" * 80
	url = 'http://weibo.cn/' + uid + '/fans'
        logger.info('userfans access url %s' % url)
        r = requests.get(url,cookies=self.cookies)
	print "333" * 80
        if r.status_code == 200:
            logger.info('userfans url is OK' )
	    self.fans_user(r.text)

	    #logger.info('follow user %s' % r.text)
	    print "444" * 80
	else:
	    logger.info('userfans url is Error')

	    print "666" * 80
	print "555" * 80
        pagenumber = 10.0
        n = 0

	print "--------------------self.fans %s ---------------" % self.fans
	if int(self.fans) >= pagenumber:
	    n = int(math.ceil(int(self.fans)/pagenumber+1))
	    print "page number %s" % n
	    if n > 21:
		n = 21	    

	    for page in xrange(2,n):
	        url1 = url + '?page=' + str(page)
   	        logger.info('userfans access url2 %s' % url1)
 	        r = requests.get(url1,cookies=self.cookies)
                if r.status_code == 200:
                    logger.info('userfans url is OK' )
                    self.fans_user(r.text)
                    #logger.info('follow user %s' % r.text)
                else:
                    logger.info('userfans url is Error')

	
    def fans_user(self,html):
	logger.info('fans_user exec')
        soup = BeautifulSoup(html, 'html.parser')
        followlist  = soup.find(attrs={"name":"uidList"})
        try:
            uidlist = [x for x in followlist.attrs["value"].split(",")]
        except:
            uidlist =""

	logger.info("uidlist %s" % uidlist )
        for x in uidlist:
            self.userinfo(x)
            self.userinfo2(x)
	
    def userprofile(self,uid):

	pagenumber = 10.0
        url = 'http://weibo.cn/' + uid 

        time.sleep(random.random())

        logger.info('userprofile access url %s' % url)
        r = requests.get(url, cookies=self.cookies)
        if r.status_code == 200:
            logger.info('userprofile url is OK')
            self.profile_parser(r.text)
        else:
            logger.info('userprofile url is Error')
        n = 0
        if self.profile > pagenumber :
            n = int(math.ceil(int(self.profile)/pagenumber+1))
            print "page number %s" % n
            n = 118
            for page in xrange(2,n):
                url1 = url + '?page=' + str(page)
                logger.info('userprofile access url %s' % url1)
 	        r = requests.get(url1,cookies=self.cookies)
                if r.status_code == 200:
                    logger.info('userprofile url is OK' )
                    self.profile_parser(r.text)
                else:
                    logger.info('userprifile url is Error')
                
    def profile_parser(self,html):
        #print html
        logger.info('profile_parser exec')
        soup = BeautifulSoup(html, 'html.parser')
        weibolist = soup.find_all('div', attrs={"id":re.compile("M_"), "class":"c"})
	weibopicurl = "http://weibo.cn/mblog/pic/"
	weibourl = "http://weibo.cn/"

	attitude_re = re.compile(r'赞\[(\d+)\]')
	repost_re = re.compile(r'转发\[(\d+)\]')
	comment_re = re.compile(r'评论\[(\d+)\]')
        forwarduser_re = re.compile(r'转发了 (\S+) 的微博')
        forwardweiboid_re = re.compile(weibopicurl+'([^?]+)\?')
	
        forwarduser = ""

	n = len(weibolist)
	for weibo in weibolist:
	    logger.info('find weibo list')
	    #print weibo
	    print "*" * 100
	    weiboid_re = re.compile(r'id="M_([^"]+)"')
	    weiboid_1 = weiboid_re.search(str(weibo))
	    weiboid = weiboid_1.group(1)
	    weibofrom = weibo.find(class_="ct").text
	    weibotext = weibo.find(class_="ctt").text
	    if weibo.find(class_="cmt"):
		print "转发"
		logger.info('parser forward weibo')
		logger.info('parser forward weibo %s' % weibo)
		#print weibo

		forwardattitude = ""
		forwardrepost = ""
		forwardcomment = ""
		attitude = ""
		repost = ""
		comment = ""

		for cmt in weibo.find_all(class_="cmt"):
		    #print "cmt %s" % cmt
                    forwarduser_1 = forwarduser_re.search(str(cmt.text.encode('utf-8')))
		    #print forwarduser_1
                    if forwarduser_1:
                        forwarduser = forwarduser_1.group(1)
                
                        urlid = "http://weibo.cn/n/" + forwarduser
		        try:
                            r = requests.get(urlid, cookies=self.cookies)
			    if r.status_code == 200:
			        r_url = r.url
			    else:
				r_url = ""
 		        except:
		            r_url = ""
		    else:
			r_url = ""
	

                    forwardweiboid_1  = forwardweiboid_re.search(str(weibo))
                    if forwardweiboid_1:
                        forwardweiboid = forwardweiboid_1.group(1)
                    else:
                        forwardweiboid = ""

                    attitude_2 = attitude_re.search(str(cmt.text.encode('utf-8')))
                    if attitude_2:
                        forwardattitude = attitude_2.group(1)

                    repost_2 = repost_re.search(str(cmt.text.encode('utf-8')))
                    if repost_2:
                        forwardrepost = repost_2.group(1)

                comment_2 = comment_re.search(str(weibo.find(class_="cc")))
#		print comment_2
                if comment_2:
                    forwardcomment = comment_2.group(1)
	    
		div = weibo.find_all('div')
		div_n = len(div) 
#		print "div %s div[div_n -1] %s " % (div,div[div_n -1])
		
                attitude_1 = attitude_re.search(str(div[div_n-1]))
                if attitude_1:
                    attitude = attitude_1.group(1)

                repost_1 = repost_re.search(str(div[div_n-1]))
                if repost_1:
                    repost = repost_1.group(1)

                comment_1 = comment_re.search(str(div[div_n-1]))
                if comment_1:
                    comment = comment_1.group(1)
		    
		    

                forwarduserpic = weibopicurl + forwardweiboid
                forwardtext = weibotext

                print weiboid,weibotext,forwardweiboid,r_url,forwarduserpic,weibofrom,forwardattitude,forwardrepost,forwardcomment,attitude,repost,comment
                logger.info('weiboid %s weibotext %s forwardweiboid %s r_url %s forwarduserpic %s weibofrom %s forwardattitude %s forwardrepost %s forwardcomment %s attitude %s repost %s comment %s' % (weiboid,weibotext,forwardweiboid,r_url,forwarduserpic,weibofrom,forwardattitude,forwardrepost,forwardcomment,attitude,repost,comment))
		print "=" * 120
	    else:
		print "原创"
		logger.info('parser source weibo')
		logger.info('parser source weibo %s' % weibo)
		#print weibo
                if re.search(r'<a href="http://weibo.cn/mblog/pic/' + weiboid, str(weibo)):
		    weibopic = weibopicurl + weiboid
		else: 
		    weibopic = ""

		attitude_1 = attitude_re.search(str(weibo))
		if attitude_1:
		    attitude = attitude_1.group(1)
		    attitudeurl = weibourl + 'attitde/' + weiboid

		repost_1 = repost_re.search(str(weibo))
		if repost_1:
		    repost = repost_1.group(1)
		    reposturl = weibourl + 'repost/' + weiboid

		comment_1 = comment_re.search(str(weibo))
		if comment_1:
		    comment = comment_1.group(1)
		    commenturl = weibourl + 'comment/' + weiboid

	        print weiboid,weibotext,weibopic,attitude,attitudeurl,repost,reposturl,comment,commenturl,weibofrom
	        logger.info('weiboid %s weibotext %s weibopic %s attitude %s attitudeurl %s repost %s reposturl %s comment %s commenturl %s weibofrom %s' % (weiboid,weibotext,weibopic,attitude,attitudeurl,repost,reposturl,comment,commenturl,weibofrom))

		print "-" * 120

    def httprequest(self,url):
        try:
            http = requests.get(url,cookies=self.cookies)
            if http.status_code == 200:
                logger.info('url %s is access ok' % url)
                return http.text
            else:
                logger.info('url %s is access not ok' % url)
                logger.info('html  status_code %s and html content %s' % (http.status_code,http.text))
                time.sleep(30)
                return "error"

        except  requests.exceptions.RequestException as e:
            logger.info('requests.exceptions.RequestException %s' % e)
        except requests.exceptions.Timeout as t:
            logger.info('requests.exceptions.Timeout %s' % t)
        except requests.exceptions.TooManyRedirects as b:
            logger.info('requests.exceptions.TooManyRedirects %s' % b)
        except requests.exceptions.ConnectionError as x:
            logger.info('requests.exceptions.ConnectionError %s' % x)
        except requests.exceptions.HTTPError as y:
            logger.info('requests.exceptions.HTTPError %s' % y)
        except requests.exceptions.URLRequired as u:
            logger.info('requests.exceptions.URLRequired %s' % u)
        except requests.exceptions.ConnectTimeout as c:
            logger.info('requests.exceptions.URLRequired %s' % c)
        except requests.exceptions.ReadTimeout as r:
            logger.info('requests.exceptions.URLRequired %s' % r)

        #finally:
        #    logger.info('raise_for_status() infomation %s' % http.raise_for_status())

    def api_userinfo(self,uid):
	url = "http://api.weibo.cn/2/profile?gsid=" + self.gsid + "&from=1057093010&c=iphone&networktype=wifi&v_p=26&skin=default&v_f=1&s=6197cbd3&lang=zh_CN&sflag=0&ua=iPhone7,1__weibo__5.7.0__iphone__os9.2&aid=01AiCiHinjWNxNr44aZVIR2tLwblUvyy5pkfyqRN6o-tpDRYU.&uicode=10000198&featurecode=10000085&luicode=10000003&fid=2302835548533089&sourcetype=page&lcardid=user&user_domain="+ uid
	#html = requests.get(url)
	html = self.httprequest(url)
	#data = json.loads(html.text)
        try:
	    data = json.loads(html)
        except :
            return

	uid = data['userInfo']['idstr']
	fans = data['userInfo']['followers_count']
	profile = data['userInfo']['statuses_count']
	follow = data['userInfo']['friends_count']
        try:
	    location = data['userInfo']['location']
        except:
            location = ""
	brief = data['userInfo']['description']
	uname = data['userInfo']['name']
	renzhen = data['userInfo']['verified_reason']
	renzheninfo = data['userInfo']['verified_reason']
	sex = data['userInfo']['gender']
	birthday = data['userInfo']['birthday']
	level = data['userInfo']['urank']
        #containerid = data['tabsInfo']['tabs'][1]['containerid']

        data=(int(uid),level,uname,renzhen,sex,location,birthday,renzheninfo,brief,
		int(profile),int(follow),int(fans))
        add_user = ("INSERT INTO user "
                    "(uid,level,uname,renzhen,sex,location,birthday,renzheninfo,brief,profile,follow,fans) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" )
        try:
            self.cursor.execute(add_user,data)
            logger.info(add_user % data)
        except:
            pass
        self.db.commit()

    def api_follows(self,uid):

        follows =[]
        for page in xrange(1,11):
            #print "follows %s" % follows
            url = "http://api.weibo.cn/2/friendships/friends?gsid=" + self.gsid + "&wm=3333_2001&i=f56290c&b=1&from=1057093010&c=iphone&networktype=wifi&v_p=26&skin=default&v_f=1&s=6197cbd3&lang=zh_CN&sflag=1&ua=iPhone7,1__weibo__5.7.0__iphone__os9.2&aid=01AiCiHinjWNxNr44aZVIR2tLwblUvyy5pkfyqRN6o-tpDRYU.&cat=0&count=20&luicode=10000198&trim_status=0&featurecode=10000001&uicode=10000195&has_pages=1&lastmblog=1&has_relation=1&has_member=1&page=" + str(page) + "&has_top=1&uid=" + uid
    	    #html = requests.get(url)
    	    html = self.httprequest(url)
            time.sleep(2)
            try:
       	        data = json.loads(html)
            except:
                continue
            
            try:
                bb = data['users'][0]['idstr']
            except:
                continue
            
            for x in data['users']:
                try:
                    xuid = x['idstr']
                    int(xuid)
                except:
                    continue
                    xuid = '0'
                follows.append(xuid)
                fans = x['followers_count']
                profile = x['statuses_count']
                follow = x['friends_count']
                location = x['location']
                brief = x['description']
                uname = x['name']
                renzhen = x['verified_reason']
                renzheninfo = x['verified_reason']
                sex = x['gender']
                birthday = ""
                try:
                    level = x['urank']
                except:
                    level = ""
                #print "-"*60
                #print xuid,level,uname,renzhen,sex,location,birthday,renzheninfo,brief,profile,follow,fans
                data=(xuid,level,uname,renzhen,sex,location,
                           birthday,renzheninfo,brief,
                            int(profile),int(follow),int(fans))
                add_user = ("INSERT INTO user "
                                    "(uid,level,uname,renzhen,sex,location,"
                                    "birthday,renzheninfo,brief,profile,follow,fans) "
                                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" )
                try:
                    self.cursor.execute(add_user,data)
                    logger.info(add_user % data)
                except:
                    pass
                    
                self.db.commit()

        logger.info("SELECT * FROM user_relation where uid = %s "% uid)
        self.cursor.execute("SELECT * FROM user_relation where uid = '%s'" % int(uid))
        data_t = self.cursor.fetchone()
        if not data_t:

            data_follows = (int(uid),','.join(follows))
            add_follows = ("INSERT INTO user_relation " 
                           "(uid,follows) VALUES (%s,\"%s\")")
        else:
            for x in data_t[2].split(","):
                follows.append(x)

            follows_uid = list(set(follows))
            #print "follows_uid %s" % follows_uid
            data_follows = (','.join(follows_uid),int(uid))
            add_follows = ("UPDATE user_relation set follows = \"%s\" "
                            "WHERE uid = %s")

        try:
            logger.info(add_follows % data_follows)
            self.cursor.execute(add_follows,data_follows)
        except:
            pass

        self.db.commit()


    def api_fans(self,uid):

        fans_l =[]
        for page in xrange(1,11):
            url = "http://api.weibo.cn/2/friendships/followers?gsid=" + self.gsid + "&wm=3333_2001&i=f56290c&b=1&from=1057093010&c=iphone&networktype=wifi&v_p=26&skin=default&v_f=1&s=6197cbd3&lang=zh_CN&sflag=1&ua=iPhone7,1__weibo__5.7.0__iphone__os9.2&aid=01AiCiHinjWNxNr44aZVIR2tLwblUvyy5pkfyqRN6o-tpDRYU.&uid=" + uid + "&cat=1&count=20&luicode=10000198&trim_status=0&featurecode=10000001&uicode=10000081&lastmblog=1&has_relation=1&has_member=1&page=" + str(page)
    	    #html = requests.get(url)
            print "api_fans is url %s" % url
    	    html = self.httprequest(url)
            time.sleep(2)
            try:
                data = json.loads(html)
            except:
                continue
            try:
                bb = data['users'][0]['idstr']
            except:
                continue
            
            for x in data['users']:
                try:
                    xuid = x['idstr']
                    int(xuid)
                except:
                    continue
                    xuid = '0'
                fans_l.append(xuid)
                fans = x['followers_count']
                profile = x['statuses_count']
                follow = x['friends_count']
                try:
                    location = x['location']
                except:
                    location = ""
                brief = x['description']
                uname = x['name']
                renzhen = x['verified_reason']
                renzheninfo = x['verified_reason']
                sex = x['gender']
                birthday = ""
                level = x['urank']
                #print "="*60
                #print xuid,level,uname,renzhen,sex,location,birthday,renzheninfo,brief,profile,follow,fans
                data=(xuid,level,uname,renzhen,sex,location,
                               birthday,renzheninfo,brief,
                                int(profile),int(follow),int(fans))
                add_user = ("INSERT INTO user "
                                    "(uid,level,uname,renzhen,sex,location,"
                                    "birthday,renzheninfo,brief,profile,follow,fans) "
                                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" )
                try:
                    self.cursor.execute(add_user,data)
                    logger.info(add_user % data)
                except:
                    pass
                    
                self.db.commit()

        self.cursor.execute("SELECT * FROM user_relation where uid = '%s'" % int(uid))
        data_t = self.cursor.fetchone()
        if data_t:
            for x in data_t[2].split(","):
                fans_l.append(x)

            fans_uid = list(set(fans_l))

            data_fans = (",".join(fans_uid),int(uid))
            add_fans = ("UPDATE user_relation set fans = \"%s\" " 
                        "WHERE uid = %s")
        else:
            data_fans = (int(uid),",".join(fans_uid))
            add_fans = ("INSERT INTO user_relation "
                        "(uid,fans) VALUES (%s,\"%s\")")

        try:
            self.cursor.execute(add_fans,data_fans)
        except:
            pass

        logger.info(add_fans % data_fans)
        self.db.commit()

    def mysql_fans(self,uid):
        select_fans = ("SELECT fans FROM user_relation where uid=%s")
        data_fans = (int(uid),)
        self.cursor.execute(select_fans,data_fans)
        data = self.cursor.fetchone()
        return data[0]
            
    def mysql_follows(self,uid):
        select_follows = ("SELECT follows FROM user_relation where uid=%s")
        data_follows = (int(uid),)
        self.cursor.execute(select_follows,data_follows)
        data = self.cursor.fetchone()
        return data[0]

    def api_mblog(self,uid):
        for n in xrange(1,6):
            url = "http://api.weibo.cn/2/cardlist?gsid=" + self.gsid + "&wm=3333_2001&i=f56290c&b=1&c=iphone&networktype=wifi&v_f=1&s=6197cbd3&lang=zh_CN&sflag=1&mid=3930827685894737&containerid=107603" + uid + "_-_WEIBO_SECOND_PROFILE_WEIBO&count=20&page="+ str(n)
            html = self.httprequest(url)
            time.sleep(2)
            try:
                data = json.loads(html)
            except:
                continue
            #print len(data['cards'])
            try:
                len(data['cards'])
            except:
                continue

            for x in xrange(len(data['cards'])):
                #print data['cards'][x]
                mpics = []
                if data['cards'][x]['card_type'] == 9:
                    mblogid = data['cards'][x]['mblog']['mblogid']
                    create_time = data['cards'][x]['mblog']['created_at']
                    text = data['cards'][x]['mblog']['text']
                    try:
                        source = data['cards'][x]['mblog']['source']
                    except:
                        source = ""
                    try:
                        reposts = data['cards'][x]['mblog']['reposts_count']
                    except:
                        reposts = ""
                    try:
                        comments = data['cards'][x]['mblog']['comments_count']
                    except:
                        comments = ""
                    try:
                        attitudes = data['cards'][x]['mblog']['attitudes_count']
                    except:
                        attitudes = ""
                    try:
                        ids = data['cards'][x]['mblog']['pic_ids']
                    except:
                        ids = ""
                    if ids:
                        for pic in ids:
                            mpics.append(data['cards'][x]['mblog']['pic_infos'][pic]['original']['url'])

                if data['cards'][x]['card_type'] == 11:
                    continue
                    #print  data['cards'][x]
                    #mblogid = data['cards'][x]['card_group']['mblog']['mblogid']
                    #create_time = data['cards'][x]['card_group']['mblog']['created_at']
                    #text = data['cards'][x]['card_group']['mblog']['text']
                    #source = data['cards'][x]['card_group']['mblog']['source']
                    #reposts = data['cards'][x]['card_group']['mblog']['reposts_count']
                    #comments = data['cards'][x]['card_group']['mblog']['comments_count']
                    #attitudes = data['cards'][x]['card_group']['mblog']['attitudes_count']

                try:
                    retweeted = data['cards'][x]['mblog']['retweeted_status']
                except:
                    retweeted = ""

                r_mpics = []
                #print retweeted
                if retweeted:
                    r_mblogid = retweeted['mblogid']
                    r_create_time = retweeted['created_at']
                    r_text = retweeted['text']
                    try:
                        r_source = retweeted['source']
                    except:
                        r_source = ""
                    try:
                        r_reposts = retweeted['reposts_count']
                    except:
                        r_reposts = ""
                    try:
                        r_comments = retweeted['comments_count']
                    except:
                        r_comments = ""
                    try:
                        r_attitudes = retweeted['attitudes_count']
                    except:
                        r_attitudes = ""
                    try:
                        r_ids = retweeted['pic_ids']
                    except:
                        r_ids = ""
                    if r_ids:
                        for r_pic in r_ids:
                            r_mpics.append(retweeted['pic_infos'][r_pic]['original']['url'])

                #print mblogid,create_time,text,source,reposts,comments,attitudes,mpics
                createdate_t = create_time[:-10] + create_time[-4:]
                createdate_t2 = time.strptime(createdate_t,"%a %b %d %H:%M:%S %Y")
                createdate = time.strftime('%Y-%m-%d %H:%M:%S', createdate_t2)

                mpics_s = ",".join(mpics)

                insert_blog = ("INSERT INTO mblog "
                    "(uid,mblogid,createdate,text,source,reposts,comments,attitudes,mpics) "
                    "VALUES (%s,%s,%s,\"%s\",%s,%s,%s,%s,\"%s\")")
                data_blog = (uid,mblogid,createdate,text,self.get_source(source),reposts,comments,attitudes,mpics_s)
                try:
                    logger.info(insert_blog % data_blog)
                    self.cursor.execute(insert_blog, data_blog)
                except:
                    pass
                self.db.commit()
                if retweeted:
                    
                    #print r_mblogid,r_create_time,r_text,r_source,r_reposts,r_comments,r_attitudes,r_mpics
                    createdate_t = r_create_time[:-10] + r_create_time[-4:]
                    createdate_t2 = time.strptime(createdate_t,"%a %b %d %H:%M:%S %Y")
                    createdate = time.strftime('%Y-%m-%d %H:%M:%S', createdate_t2)
   
                    mpics_s = ",".join(r_mpics)

                    insert_blog = ("INSERT INTO mblog "
                        "(uid,mblogid,createdate,text,source,reposts,comments,attitudes,mpics) "
                        "VALUES (%s,%s,%s,\"%s\",%s,%s,%s,%s,\"%s\")")
                    data_blog = (uid,r_mblogid,createdate,r_text,self.get_source(source),r_reposts,r_comments,r_attitudes,mpics_s)
                    try:
                        logger.info(insert_blog % data_blog)
                        self.cursor.execute(insert_blog, data_blog)
                    except:
                        pass
                    self.db.commit()




#select_follows = ("SELECT follows FROM user_relation where uid=%s")
#data_follows = (int(uid),)
#self.cursor.execute(select_follows,data_follows)
#data = self.cursor.fetchone()


    def get_source(self,source):
        select_source = ("SELECT id FROM user_source where source = \"%s\"")
        data_source = (source,)
        logger.info(select_source % data_source)
        self.cursor.execute(select_source, data_source)
        source_data = self.cursor.fetchone()
        #print "source_data 11 %s" % source_data
        if source_data is None:
            #print "insert"
            insert_source = ("INSERT INTO user_source (source) VALUES (\"%s\")")
            self.cursor.execute(insert_source, data_source)
            logger.info(insert_source % data_source)
            self.cursor.execute(select_source, data_source)
            logger.info(select_source % data_source)
            source_data = self.cursor.fetchone()
            #print "source_data 22 %s" % source_data
        self.db.commit()
        return source_data

    def get_user(self,uid):
        self.api_userinfo(uid)
        self.api_follows(uid)
        self.api_fans(uid)
        self.api_mblog(uid)

        data1 = self.mysql_fans(uid)
        print "data1 %s " % data1
        for xx in data1.split(","):
            tt = xx.replace("'","")
            if tt != "":
                try:
                    int(tt)
                except:
                    continue
                self.api_follows(tt)
                self.api_fans(tt)
                self.api_mblog(tt)
                time.sleep(5)

        data2 = self.mysql_follows(uid)
        print "data2 %s" % data2
        for yy in data2.split(","):
            zz = yy.replace("'","")
            if zz != "":
                try:
                    int(zz)
                except:
                    continue
                self.api_follows(zz)
                self.api_fans(zz)
                self.api_mblog(zz)
                time.sleep(5)

        data = data1 + "," + data2
        for x in data.split(","):
            z = x.replace("'","")
            self.get_user(z)

if __name__ == "__main__":
    (username,password,names) = account("weiboscan.cfg")
    mysql = mysqlu("weiboscan.cfg")
    logger.info('username %s and password XXXX and names %s' % (username,names))
    web = webbrowse(username,password,names,mysql)
    web.login_is()

    web.get_user('2549228714')



