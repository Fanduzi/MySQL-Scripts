#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#已orzdba为模版重写，计算方式均根据orzdba

import MySQLdb as mdb
import sys
import argparse
import datetime
import time
import re

headline1 = ''
headline2 = ''
mysql_headline1 = ''
mysql_headline2 = ''
mycount = 0
not_first = 0
interval = 1
#myType = ['com','innodb_hit','innodb_rows','innodb_pages','innodb_data','innodb_log','innodb_status','threads','bytes']
mystat1 = {'Com_select':0, \
           'Com_delete':0 ,\
           'Com_update':0 ,\
           'Com_insert': 0,\
           'Innodb_buffer_pool_read_requests': 0,\
           'Innodb_rows_inserted': 0 ,\
           'Innodb_rows_updated': 0 ,\
           'Innodb_rows_deleted': 0 ,\
           'Innodb_rows_read': 0,\
           'Threads_created': 0,\
           'Bytes_received': 0,\
           'Bytes_sent':0,\
           'Innodb_buffer_pool_pages_flushed': 0,\
           'Innodb_data_read':0,\
           'Innodb_data_reads': 0,\
           'Innodb_data_writes': 0,\
           'Innodb_data_written': 0,\
           'Innodb_os_log_fsyncs': 0,\
           'Innodb_os_log_written': 0}

def dealWithData1(res):
    outputs=[]
    for i in res:
        r = i[0]
        outputs.append("%s" % r)
    outputs = ','.join(outputs)
    return outputs

def dealWithData2(res):
    outputs=[]
    for i in res:
        r = "%s:[%s]" % (i[0],i[1])
        outputs.append("%s" % r)
    outputs = ','.join(outputs)
    return outputs

def print_title(con):
    LOG_OUT = '''
.=================================================.
|       Welcome to use the orzdba tool !          |
|  因需要监控的机器太旧，安装perl十分麻烦，故用重新  |
|  python重新了orzdba,参数的计算方式均来自orzdba    |
|          Yep...Chinese English~                 |
'=========== Date : %s ==========='
            '''  % time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
    print LOG_OUT
    cursor = con.cursor()
    cursor.execute("show databases")
    res = cursor.fetchall()
    rel = dealWithData1(res)
    print "DB : %s" % (rel)
    sql = 'show variables where Variable_name in ("sync_binlog","max_connections","max_user_connections","max_connect_errors","table_open_cache","table_definition_cache","thread_cache_size","binlog_format","open_files_limit","max_binlog_size","max_binlog_cache_size")'
    cursor.execute(sql)
    res = cursor.fetchall()
    rel = dealWithData2(res)
    print "Var : %s" % (rel)
    sql = 'show variables where Variable_name in ("innodb_flush_log_at_trx_commit","innodb_flush_method","innodb_buffer_pool_size","innodb_max_dirty_pages_pct","innodb_log_buffer_size","innodb_log_file_size","innodb_log_files_in_group","innodb_thread_concurrency","innodb_file_per_table","innodb_adaptive_hash_index","innodb_open_files","innodb_io_capacity","innodb_read_io_threads","innodb_write_io_threads","innodb_adaptive_flushing","innodb_lock_wait_timeout","innodb_log_files_in_group")'
    cursor.execute(sql)
    res = cursor.fetchall()
    outputs=[]
    for val in res:
        if val[0] == 'innodb_buffer_pool_size' or val[0] == 'innodb_log_file_size' or val[0] == 'innodb_log_buffer_size' or val[0] == 'max_binlog_cache_size' or val[0] == 'max_binlog_size':
            if (int(val[1])/1024/1024/1024) >= 1 :
                r = "%d G" % (int(val[1])/1024/1024/1024)
            elif (int(val[1])/1024/1024)>=1:
                r = "%d M" % (int(val[1])/1024/1024)
            else:
                r = val[1]
        else:
            r = val[1]
        rel = "%s:[%s]" % (val[0],r)
        outputs.append("%s" % rel)
    outputs =  ','.join(outputs)
    print outputs
    return

def get_options(myType):
    global mysql_headline1
    global mysql_headline2
    if 'com' in myType:
        mysql_headline1 +="         -QPS- -TPS-           "
        mysql_headline2 +="  ins   upd   del    sel   iud|"
    if 'innodb_hit' in myType:
        mysql_headline1 += "         -Hit%- "
        mysql_headline2 += "     lor    hit|"

    if 'innodb_rows' in myType:
        mysql_headline1 += "---innodb rows status--- "
        mysql_headline2 += "  ins   upd   del   read|"

    if 'innodb_pages' in myType:
        mysql_headline1 += "---innodb bp pages status-- "
        mysql_headline2 += "   data   free  dirty flush|"

    if 'innodb_data' in myType:
        mysql_headline1 += "-----innodb data status---- "
        mysql_headline2 += "   reads writes  read written|"

    if 'innodb_log' in myType:
        mysql_headline1 += "--innodb log-- "
        mysql_headline2 += "fsyncs written|"

    if 'innodb_status' in myType:
        mysql_headline1 += "  his --log(byte)--  read ---query--- "
        mysql_headline2 += " list uflush  uckpt  view inside  que|"

    if 'threads' in myType:
        mysql_headline1 += "------threads------ "
        mysql_headline2 += " run  con  cre  cac|"

    if 'bytes' in myType:
        mysql_headline1 += "-----bytes---- "
        mysql_headline2 += "   recv   send|"

def get_innodb_status(con):
    sql = 'show engine innodb status'
    cursor = con.cursor()
    cursor.execute(sql)
    res = cursor.fetchone()
    result = res[2].split('\n')
    innodb_status = {}
    for i in result:
        try:
            if i.index("History list length") == 0:
                r = re.compile("\s+")
                rel = r.split(i)
                innodb_status['history_list'] = rel[-1]
                #print  innodb_status
        except Exception,e:
            #print e
            pass
        try:
            if i.index("Log sequence number") == 0:
                r = re.compile("\s+")
                rel = r.split(i)
                innodb_status['log_bytes_written'] = rel[-1]
        except Exception,e:
            pass
        try:
            if i.index("Log flushed up to") == 0:
                r = re.compile("\s+")
                rel = r.split(i)
                innodb_status['log_bytes_flushed'] = rel[-1]
        except Exception,e:
            pass
        try:
            if i.index("Last checkpoint at") == 0:
                r = re.compile("\s+")
                rel = r.split(i)
                innodb_status['last_checkpoint'] = rel[-1]
        except Exception,e:
            pass

        try:
            if i.index("queries inside InnoDB") == 2:
                #print i
                r = re.compile("\s+")
                rel = r.split(i)
                innodb_status['queries_inside'] = rel[0]
                innodb_status['queries_queued'] = rel[4]
        except Exception,e:
            pass

        try:
            if i.index("read views open inside InnoDB") == 2:
                #print i
                r = re.compile("\s+")
                rel = r.split(i)
                innodb_status['read_views'] = rel[0]
        except Exception,e:
            pass
    innodb_status["unflushed_log"] = int(innodb_status['log_bytes_written']) - int(innodb_status['log_bytes_flushed'])
    innodb_status["uncheckpointed_bytes"] = int(innodb_status['log_bytes_written']) - int(innodb_status['last_checkpoint'])
    return innodb_status

def get_mysqlstat(con,myType):
    global not_first
    global mystat1
    global interval
    sql = 'show global status where Variable_name in ("Com_select","Com_insert","Com_update","Com_delete","Innodb_buffer_pool_read_requests","Innodb_buffer_pool_reads","Innodb_rows_inserted","Innodb_rows_updated","Innodb_rows_deleted","Innodb_rows_read","Threads_running","Threads_connected","Threads_cached","Threads_created","Bytes_received","Bytes_sent","Innodb_buffer_pool_pages_data","Innodb_buffer_pool_pages_free","Innodb_buffer_pool_pages_dirty","Innodb_buffer_pool_pages_flushed","Innodb_data_reads","Innodb_data_writes","Innodb_data_read","Innodb_data_written","Innodb_os_log_fsyncs","Innodb_os_log_written")'
    cursor = con.cursor()
    cursor.execute(sql)
    res = cursor.fetchall()
    mydata = dict(res)
    mystat2 = mydata
    output = ''
    if not_first == 0:
        if 'com' in myType:
            output += "%4d %5d %5d %6d %5d" % (0,0,0,0,0)
        if 'innodb_hit' in myType:
            output += "%8d %8.2f" % (0,100)

        if 'innodb_rows' in myType:
            output += "%6d %5d %5d %6d" % (0,0,0,0)

        if 'innodb_pages' in myType:
            output += "%7d %6d %6d %5d" % (0,0,0,0)

        if 'innodb_data' in myType:
            output += "%8d %6d %6d %6d" % (0,0,0,0)

        if 'innodb_log' in myType:
            output += "%6d %7d" % (0,0)

        if 'innodb_status' in myType:
            output += "%8d %6d %6d %5d %5d %5d"% (0,0,0,0,0,0)

        if 'threads' in myType:
            output += "%5d %4d %4d %4d"%(0,0,0,0)

        if 'bytes' in myType:
            output += "%7d %7d" % (0,0)
        not_first += 1
        mystat1 = mystat2
    else:
        insert_diff = (int(mystat2['Com_insert']) - int(mystat1['Com_insert'])) / interval
        update_diff = (int(mystat2['Com_update']) - int(mystat1['Com_update'])) / interval
        delete_diff = (int(mystat2['Com_delete']) - int(mystat1['Com_delete'])) / interval
        select_diff = (int(mystat2['Com_select']) - int(mystat1['Com_select'])) / interval
        read_request = (int(mystat2['Innodb_buffer_pool_read_requests']) - int(mystat1['Innodb_buffer_pool_read_requests'])) / interval
        read = (int(mystat2['Innodb_buffer_pool_reads']) -int( mystat1['Innodb_buffer_pool_reads'])) / interval
        innodb_rows_inserted_diff = (int(mystat2['Innodb_rows_inserted']) - int(mystat1['Innodb_rows_inserted'])) / interval
        innodb_rows_updated_diff = (int(mystat2['Innodb_rows_updated']) - int(mystat1['Innodb_rows_updated'])) / interval
        innodb_rows_deleted_diff = (int(mystat2['Innodb_rows_deleted']) - int(mystat1['Innodb_rows_deleted'])) / interval
        innodb_rows_read_diff = (int(mystat2['Innodb_rows_read']) - int(mystat1['Innodb_rows_read'])) / interval
        innodb_bp_pages_flushed_diff = (int(mystat2['Innodb_buffer_pool_pages_flushed']) - int(mystat1['Innodb_buffer_pool_pages_flushed']) ) / interval
        innodb_data_reads_diff = (int(mystat2['Innodb_data_reads']) - int(mystat1['Innodb_data_reads'])) / interval
        innodb_data_writes_diff = (int(mystat2['Innodb_data_writes']) - int(mystat1['Innodb_data_writes'])) / interval
        innodb_data_read_diff = (int(mystat2['Innodb_data_read']) - int(mystat1['Innodb_data_read'])) / interval
        innodb_data_written_diff = (int(mystat2['Innodb_data_written']) - int(mystat1['Innodb_data_written'])) / interval
        innodb_os_log_fsyncs_diff = (int(mystat2['Innodb_os_log_fsyncs']) - int(mystat1['Innodb_os_log_fsyncs'])) / interval
        innodb_os_log_written_diff = (int(mystat2['Innodb_os_log_written']) - int(mystat1['Innodb_os_log_written'])) / interval
        threads_created_diff = (int(mystat2['Threads_created']) - int(mystat1['Threads_created'])) / interval
        bytes_received_diff = (int(mystat2['Bytes_received']) - int(mystat1['Bytes_received'])) / interval
        bytes_sent_diff = (int(mystat2['Bytes_sent']) - int(mystat1['Bytes_sent'])) / interval

        if 'com' in myType:
           output += "\33[37m"
           output += "%4d %5d %5d" % (insert_diff,update_diff,delete_diff)
           output += "\33[33m"
           output += "%7d %5d" % (select_diff,insert_diff+update_diff+delete_diff)
           output += "\33[0m"

        if 'innodb_hit' in myType:
            output += "\33[37m"
            output += " %7d" %  read_request
            if read_request:
                hit = (read_request-read)/read_request*100
                if hit > 99:
                    output += "\33[32m"
                else:
                    output += "\33[31m"
                output += "%8.2f" % hit
            else:
                hit = 100.00
                output += "\33[32m"
                output += " %8.2f" % hit
            output += "\33[0m"

        if 'innodb_rows' in myType:
            output += "\33[37m"
            output += "%6d %5d %5d %6d" % (innodb_rows_inserted_diff,innodb_rows_updated_diff,innodb_rows_deleted_diff,innodb_rows_read_diff)
            output += "\33[0m"

        if 'innodb_pages' in myType:
            output += "\33[37m"
            output += "%7s %6s %6s %5d" % (mystat2['Innodb_buffer_pool_pages_data'],mystat2['Innodb_buffer_pool_pages_free'],mystat2['Innodb_buffer_pool_pages_dirty'],innodb_bp_pages_flushed_diff)
            output += "\33[0m"

        if 'innodb_data' in myType:
            innodb_data_read_diff_ = 0
            innodb_data_written_diff_ = 0
            output += "\33[37m"
            output += "%8d %6d" % (innodb_data_reads_diff,innodb_data_writes_diff)
            if (innodb_data_read_diff/1024/1024) > 9:
                output += "\33[31m"
            else:
                output += "\33[37m"

            if (innodb_data_read_diff/1024/1024) > 1:
                output += "%6.1fm" % (innodb_data_read_diff/1024/1024)
            elif (innodb_data_read_diff/1024) > 1 :
                output += "%7s" % (str((innodb_data_read_diff/1024)+0.5)+'k')
            else:
                output += "%7s" % str(innodb_data_read_diff)

            if (innodb_data_written_diff/1024/1024) > 9:
                output += "\33[31m"
            else:
                output += "\33[37m"

            if (innodb_data_written_diff/1024/1024) > 1:
                output += "%6.1fm" % (innodb_data_written_diff/1024/1024)
            elif (innodb_data_written_diff/1024) > 1 :
                output += "%7s" % (str((innodb_data_written_diff/1024)+0.5)+'k')
            else:
                output += "%7s" % str(innodb_data_written_diff)
            output += "\33[0m"

        if 'innodb_log' in myType:
            output += "\33[37m"
            output += "%6d" % innodb_os_log_fsyncs_diff

            if (innodb_os_log_written_diff/1024/1024) > 1:
                output += "\33[31m"
            else:
                output += "\33[33m"

            if (innodb_os_log_written_diff/1024/1024) > 1:
                output += "%8.1fm" % (innodb_os_log_written_diff/1024/1024)
            elif (innodb_data_written_diff/1024) > 1 :
                output += "%7s" % (str((innodb_os_log_written_diff/1024)+0.5)+'k')
            else:
                output += "%8s" % str(innodb_os_log_written_diff)
            output += "\33[0m"

        if 'innodb_status' in  myType:
            innodb_status = get_innodb_status(con)
            output += "\33[37m"
            innodb_status['history_list'] = innodb_status['history_list']
            output += "%8s " % innodb_status['history_list']
            output += "\33[33m"
            if (int(innodb_status['unflushed_log'])/1024/1024) > 1:
                innodb_status['unflushed_log'] = int(innodb_status['unflushed_log'])/1024/1024
                output += "%5.1fm" % (innodb_status['unflushed_log'])
            elif (int(innodb_status["unflushed_log"])/1024) > 1:
                innodb_status['unflushed_log'] =  int(innodb_status['unflushed_log'])/1024 + 0.5
                output += "%6fk" % innodb_status['unflushed_log']
            else:
                 output += "%6s" % innodb_status['unflushed_log']

            if (int(innodb_status['uncheckpointed_bytes'])/1024/1024) > 1:
                innodb_status['uncheckpointed_bytes'] = int(innodb_status['uncheckpointed_bytes'])/1024/1024
                output += "%6.1fm" % innodb_status['uncheckpointed_bytes']
            elif (int(innodb_status['uncheckpointed_bytes'])/1024) > 1:
                innodb_status['uncheckpointed_bytes'] = int(innodb_status['uncheckpointed_bytes'])/1024 + 0.5
                output += "%7fk" % innodb_status['uncheckpointed_bytes']
            else:
                innodb_status['uncheckpointed_bytes'] = str(innodb_status['uncheckpointed_bytes'])
                output += "%7s" % innodb_status['uncheckpointed_bytes']
            output += "%6s %5s %5s" %  (innodb_status['read_views'],innodb_status['queries_inside'],innodb_status['queries_queued'])
	    output += "\33[0m"

        if 'threads' in  myType :
            output += "\33[37m"
            output += "%5s %4s %4d %4s" % (mystat2['Threads_running'],mystat2['Threads_connected'],threads_created_diff,mystat2['Threads_cached'])
  	    output += "\33[0m"	   

        if 'bytes' in myType:
            output += "\33[37m"
            if (bytes_received_diff/1024/1024) > 1:
                output += "%7.1f m" % (bytes_received_diff/1024/1024)
            elif (bytes_received_diff/1024) > 1:
                output += "%8s k" % str(bytes_received_diff/1024 + 0.5)
            else:
                output += "%8s" % str(bytes_received_diff)

            if (bytes_sent_diff/1024/1024) > 1:
                output += "%7.1f m" % (bytes_sent_diff/1024/1024)
            elif (bytes_sent_diff/1024) > 1:
                output += "%8s k" % str(bytes_sent_diff/1024 + 0.5)
            else:
                output += "%7s" % str(bytes_sent_diff)
            output += "\33[0m"
    print output
    return


if __name__ == "__main__":
   
    parser = argparse.ArgumentParser(description='数据库监控脚本')
    parser.add_argument('host',help='数据库实例IP',default='localhost')
    parser.add_argument('user',action="store",help='用户')
    parser.add_argument('password',action="store",help='密码')
    parser.add_argument('port',type=int,help='端口号',default=3306)
    parser.add_argument('type',nargs='*',help="com innodb_hit innodb_rows innodb_pages innodb_data innodb_log innodb_status threads bytes 可多个一起，例如：innodb_log innodb_status")
    args = parser.parse_args()
    myHost = args.host
    myUser = args.user
    myPasswd = args.password
    myPort = args.port
    myType = args.type
    
    try:
        con = mdb.connect(host=myHost,user=myUser,passwd=myPasswd,port=myPort,charset='utf8')
        print_title(con)
        get_options(myType)
        while 1:
            if mycount%15 == 0 :
                print mysql_headline1
                print mysql_headline2
            mycount += 1
            time.sleep(1)
            get_mysqlstat(con,myType)
        con.close()
    except Exception,e:
        print e






