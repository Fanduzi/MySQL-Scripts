#/usr/bin/python

import sys
import os
import re
import optparse
import pymysql




MYSQL_SHOW_SLAVE_STATUS     = 'SHOW SLAVE STATUS;'
GTID_MODE = "select @@gtid_mode"
com_mysqlbinlog = "/usr/local/mysql/bin/mysqlbinlog"

r1062 = r"Could not execute Write_rows event on table (.*); Duplicate entry '(\d+)' for key 'PRIMARY', Error_code: 1062; handler error HA_ERR_FOUND_DUPP_KEY; the event's master log (.*), end_log_pos (\d+)"
u1032 = r"Could not execute (.*)_rows event on table (.*); Can't find record in (.*), Error_code: 1032; handler error HA_ERR_KEY_NOT_FOUND; the event's master log (.*), end_log_pos (\d+)"

GET_FROM_LOG="%s -v --base64-output=decode-rows -R --host='%s' --port=%d --user='%s' --password='%s' --start-position=%d --stop-position=%d %s |grep @%s|head -n 1"


FLAGS = optparse.Values()
parser = optparse.OptionParser()


def DEFINE_string(name, default, description, short_name=None):
    if default is not None and default != '':
        description = "%s (default: %s)" % (description, default)
    args = [ "--%s" % name ]
    if short_name is not None:
        args.insert(0, "-%s" % short_name)

    parser.add_option(type="string", help=description, *args)
    parser.set_default(name, default)
    setattr(FLAGS, name, default)

def DEFINE_integer(name, default, description, short_name=None):
    if default is not None and default != '':
        description = "%s (default: %s)" % (description, default)
    args = [ "--%s" % name ]
    if short_name is not None:
        args.insert(0, "-%s" % short_name)

    parser.add_option(type="int", help=description, *args)
    parser.set_default(name, default)
    setattr(FLAGS, name, default)

DEFINE_integer('db_port', '3306', 'DB port : 3306')
DEFINE_string('db_user', 'wubx', 'DB user ')
DEFINE_string('db_password', '', 'DB password')
DEFINE_string('db_host', '127.0.0.1', 'DB  Hostname')


def ShowUsage():
    parser.print_help()
    
def ParseArgs(argv):
    usage = sys.modules["__main__"].__doc__
    parser.set_usage(usage)
    unused_flags, new_argv = parser.parse_args(args=argv, values=FLAGS)
    return new_argv

def get_conn():
    return pymysql.connect(host=FLAGS.db_host, port=int(FLAGS.db_port), user=FLAGS.db_user,passwd=FLAGS.db_password)

def get_tb_pk(db_table):
    db, tb = db_table.split('.')
    conn = get_conn()
    sql = "select column_name,ordinal_position from information_schema.columns where table_schema='%s' and table_name='%s' and column_key='PRI';" % (db, tb)
    cursor = conn.cursor()
    cursor.execute(sql)
    r = cursor.fetchone()
    cursor.close()
    conn.close()
    return r




def get_rpl_mode(conn):
    cursor = conn.cursor()
    cursor.execute(GTID_MODE)
    r = cursor.fetchone()
    print r
    
    if (r[0] == "ON"):
        return 1
    else:
        return 0
    
def handler_1062(r,rpl):
    print r['Last_SQL_Error']
    p = re.compile(r1062)
    m = p.search(r['Last_SQL_Error'])
    db_table = m.group(1)
    pk_v = m.group(2)
    conn = get_conn()
    pk_col = get_tb_pk(db_table)[0]
    
    sql = "delete from %s where %s=%s" % (db_table, pk_col, pk_v)
    cursor = conn.cursor()
    cursor.execute("set session sql_log_bin=0;")
    cursor.execute(sql)
    #cursor.execute("set  session sql_log_bin=1")
    cursor.execute("start slave sql_thread")
    cursor.close()
    conn.commit()
    conn.close()
    return 0
    
    
    

    

def handler_1032(r, rpl):
    print r['Last_SQL_Error']
    p = re.compile(u1032)
    m = p.search(r['Last_SQL_Error'])
    db_table = m.group(2)
    tb_name = m.group(3)
    log_file_name = m.group(4)
    log_stop_position = m.group(5)
    log_start_position = r['Exec_Master_Log_Pos']
    pk_seq = get_tb_pk(db_table)[1]    
    do_getlog = GET_FROM_LOG % (com_mysqlbinlog, r['Master_Host'], int(r['Master_Port']),FLAGS.db_user,FLAGS.db_password, int(log_start_position), int(log_stop_position),  log_file_name,pk_seq)
    pk_value = os.popen(do_getlog).readlines()[0].split("=",2)[1].rstrip()
    print pk_value
    sql = mk_tb_replace(db_table, pk_value, pk_seq)
    
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("set session sql_log_bin=0;")
    cursor.execute(sql)
    #cursor.execute("set  session sql_log_bin=1")
    cursor.execute("start slave sql_thread")    
    conn.commit()
    cursor.close()
    conn.close()
    
    
    
    

def mk_tb_replace(db_table, pk_value, pk_seq):
    db, tb_name = db_table.split(".")
    r = "replace into %s.%s "%(db,tb_name)
    
    sql = "select column_name, ORDINAL_POSITION from information_schema.columns where table_schema='%s' and table_name='%s' and IS_NULLABLE='NO';" % (db, tb_name)
    #print sql
    
    col_list=''
    value_list=''
    
    conn = get_conn()
    cusror = conn.cursor()
    cusror.execute(sql)
    result = cusror.fetchall()
    for col in result:
        if (col[1] == pk_seq):
            col_list = col_list +"%s," % (col[0])
            value_list = value_list + "'%s'," % (pk_value)
        else:
            col_list = col_list +"%s," % (col[0])
            value_list = value_list + "'%s'," % ('1')
    print value_list
    r = r+"(%s) values(%s)" % ( col_list.rstrip(','), value_list.rstrip(','))
    cusror.close()
    conn.close()
    return r.rstrip(',')
        


def get_slave_status(conn):
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(MYSQL_SHOW_SLAVE_STATUS)
    result = cursor.fetchone()
    return result
    cursor.close()

if __name__ == '__main__':
        new_argv = ParseArgs(sys.argv[1:])

        print FLAGS
        conn = get_conn()
        
        
        r = get_slave_status(conn)
        
        if (r['Slave_IO_Running'] == "Yes" and r['Slave_SQL_Running'] == "Yes"):
            print "Rpl Ok"
            if (r['Seconds_Behind_Master'] > 0):
                print r['Seconds_Behind_Master']
                
            conn.close()
            exit(0) 
        
        while( 1 ):
            
            r = get_slave_status(conn)
            if (r['Slave_IO_Running'] == "Yes" and r['Slave_SQL_Running'] == "No"):
                rpl_mode = get_rpl_mode(conn)
                print "rpl_mode %s " % (rpl_mode)
                print r['Last_Errno']
                if ( r['Last_Errno'] == 1062 ):
                    r1062 = handler_1062(r, rpl_mode)
                    
                    
                if ( r['Last_Errno'] == 1032 ):
                    r1032 = handler_1032(r, rpl_mode)
            else:
                break
                     
                
        conn.close()
