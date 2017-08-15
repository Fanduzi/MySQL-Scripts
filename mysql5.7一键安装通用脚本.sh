#!/bin/bash
#yum install wget gcc gcc-c++ make cmake ncurses-devel libtool zilib-devel openssl openssl-devel -y
#wget -N ftp://10.55.2.119/mysql/mysql-5.7.14-linux-glibc2.5-x86_64_x.tar.gz -P /usr/local/src/ 
groupadd  mysql
useradd -d /usr/local/mysql -s /sbin/nologin -g mysql -M -n mysql
cd /usr/local/src/
tar -zxf mysql-5.7.14-linux-glibc2.5-x86_64_x.tar.gz -C /usr/local
echo "解压完成"
cd ../
ln -s mysql-5.7.14-linux-glibc2.5-x86_64 mysql
echo "创建软连接"
chown -R mysql:mysql /usr/local/mysql
mkdir -p /data/mysql/3306/{data,logs,tmp}
chown -R mysql:mysql /data/mysql
echo "创建目录与授权完成"
cd /data/mysql/3306
echo "创建my.cnf"
cat >> my.cnf << EOP
#my.cnf
[client]
port            = 3306
socket          = /data/mysql/3306/tmp/mysql3306.sock

[mysql]
prompt="\\u@\\h:\\p [\\d]>" 
#pager="less -i -n -S"
#tee=/data/mysql/3306/query.log
no-auto-rehash

[mysqld]
#misc
user = mysql
basedir = /usr/local/mysql
datadir = /data/mysql/3306/data
port = 3306
socket = /data/mysql/3306/tmp/mysql3306.sock
event_scheduler = 0

tmpdir = /data/mysql/3306/tmp
#timeout
interactive_timeout = 3600
wait_timeout = 3600

#character set
character-set-server = utf8

open_files_limit = 65535
max_connections = 500
max_connect_errors = 100000
lower_case_table_names =1

#symi replication

#rpl_semi_sync_master_enabled=1
#rpl_semi_sync_master_timeout=1000 # 1 second
#rpl_semi_sync_slave_enabled=1

#logs
log-output=file
slow_query_log = 1
slow_query_log_file = slow.log
log-error = error.log
log_warnings = 2
pid-file = mysql.pid
long_query_time = 1
#log-slow-admin-statements = 1
#log-queries-not-using-indexes = 1
log-slow-slave-statements = 1

#binlog
#binlog_format = STATEMENT
binlog_format = row
server-id = 13306
log-bin = /data/mysql/3306/logs/mysql-bin
binlog_cache_size = 4M
max_binlog_size = 256M
max_binlog_cache_size = 1M
sync_binlog = 0
expire_logs_days = 10
#procedure 
log_bin_trust_function_creators=1

#
gtid-mode = on
enforce-gtid-consistency=1


#relay log
skip_slave_start = 1
max_relay_log_size = 128M
relay_log_purge = 1
relay_log_recovery = 1
relay-log=relay-bin
relay-log-index=relay-bin.index
log_slave_updates
#slave-skip-errors=1032,1053,1062
#skip-grant-tables

#buffers & cache
table_open_cache = 2048
table_definition_cache = 2048
table_open_cache = 2048
max_heap_table_size = 96M
sort_buffer_size = 128K
join_buffer_size = 128K
thread_cache_size = 200
query_cache_size = 0
query_cache_type = 0
query_cache_limit = 256K
query_cache_min_res_unit = 512
thread_stack = 192K
tmp_table_size = 96M
key_buffer_size = 8M
read_buffer_size = 2M
read_rnd_buffer_size = 16M
bulk_insert_buffer_size = 32M

#myisam
myisam_sort_buffer_size = 128M
myisam_max_sort_file_size = 1G
myisam_repair_threads = 1

#innodb
innodb_buffer_pool_size = 10G
innodb_buffer_pool_instances = 1
innodb_data_file_path = ibdata1:1024M:autoextend
innodb_flush_log_at_trx_commit = 2
innodb_log_buffer_size = 8M
innodb_log_file_size = 100M
innodb_log_files_in_group = 3
innodb_max_dirty_pages_pct = 50
innodb_file_per_table = 1
innodb_rollback_on_timeout
innodb_status_file = 1
innodb_io_capacity = 200
transaction_isolation = READ-COMMITTED
innodb_flush_method = O_DIRECT

EOP

echo "创建启动文件"
cat >> mysqld << EEP
#!/bin/bash
mysql_port=3306
#端口
mysql_user="root"
#用户
mysql_pwd=""
#密码
CmdPath="/usr/local/mysql/bin"
mysql_sock="/data/mysql/\${mysql_port}/tmp/mysql\${mysql_port}.sock"
#startup function
function_start_mysql()
{
        if [ ! -e "\$mysql_sock" ];then
      printf "Starting MySQL...\n"
      \${CmdPath}/mysqld --defaults-file=/data/mysql/\${mysql_port}/my.cnf 2>&1 > /dev/null &
        else
          printf "MySQL is running...\n"
          exit
        fi
}
function_stop_mysql()
{  
        if [ ! -e "\$mysql_sock" ];then
                printf "Stoping MySQL...\n"
                exit
        else
                printf "MySQL is stopped...\n"
                \${CmdPath}/mysqladmin -u\${mysql_user} -p\${mysql_pwd} -S \$mysql_sock shutdown
        fi
}
function_restart_mysql()
{
        printf "Restarting MySQL...\n"
        function_stop_mysql
        sleep 2
        function_start_mysql
}
case \$1 in
start)
        function_start_mysql
;;
stop)
        function_stop_mysql
;;
restart)
        function_restart_mysql
;;
*)
        printf "Usage: /data/mysql/\${mysql_port}/mysqld {start|stop|restart} \n"
esac

EEP

echo "完成"
/usr/local/mysql/bin/mysqld --defaults-file=/data/mysql/3306/my.cnf --basedir=/usr/local/mysql --datadir=/data/mysql/3306/data --user=mysql --initialize
echo "mysql初始化完成"
echo 'export PATH=/usr/local/mysql/bin:$PATH' >> /etc/profile
source /etc/profile
echo "变量配置完成"
cat /data/mysql/3306/data/error.log |grep "root@localhost"|awk -F " " '{print $11}' >/data/mysql/3306/password.txt
echo "root随机密码完成cat /data/mysql/3306/password.txt"
chmod +x /data/mysql/3306/mysqld
echo "启动命令/data/mysql/3306/mysqld start"
echo "关闭命令/data/mysql/3306/mysqld stop"
echo "脚本编写人叶梁坚 QQ88263188  微信yelj88263188"