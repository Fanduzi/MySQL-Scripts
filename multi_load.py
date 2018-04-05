#!/usr/bin/python
# -*- coding: utf8 -*-
import pymysql
import time
import datetime
import subprocess
from multiprocessing import Process

class Fandb:
    def __init__(self, host, port, user, password, db, charset='utf8mb4', local_infile=True):
        self.host = host
        self.port = int(port)
        self.user = user
        self.password = password
        self.db = db
        self.charset = charset
        self.local_infile = local_infile=True
        try:
            self.conn = pymysql.connect(host=self.host, port=self.port, user=self.user,
                                        password=self.password, db=self.db, charset=self.charset, local_infile=self.local_infile)
            self.cursor = self.conn.cursor()
            self.diccursor = self.conn.cursor(pymysql.cursors.DictCursor)
        except Exception, e:
            logging.error('connect error', exc_info=True)
    def dml(self, sql, val=None):
        self.cursor.execute(sql, val)
    def version(self):
        self.cursor.execute('select version()')
        return self.cursor.fetchone()
    def dql(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    def commit(self):
        self.conn.commit()
    def close(self):
        self.cursor.close()
        self.diccursor.close()
        self.conn.close()

db_host='127.0.0.1'
db_port=3308
db_user='fan'
db_passwd='fanboshi'
db_use='test'

from multiprocessing import Process
import pymysql

class LoadDataExtractor(Process):
    def __init__(self,Fandb):
        Process.__init__(self)
        self.Fandb = Fandb
    def run(self):
        self.load_data()
    def load_data(self):
        conn1 = self.Fandb(db_host, db_port, db_user, db_passwd, db_use)
        child=subprocess.Popen("sed 's/2018\-01\-21\ 23\:54\:10/%s/g' /data/mysqldata/3308/adclickload201801212354.txt > /data/mysqldata/3308/adtmp.txt" % (datetime.datetime.now().strftime('%Y\-%m\-%d\ %H\:%M\:%S')),shell=True)
        child.wait()
        conn1.dql("load data local infile '/data/mysqldata/3308/adtmp.txt' into table test.new_mobile_ad")
        conn1.commit()
        conn1.close()

while True:
    processes = {}
    for i  in range(10):
        processes[i] = LoadDataExtractor(Fandb)
        processes[i].start()
    time.sleep(10)
