#!/bin/bash
trg_plugin() {
mysqladmin -uroot -p"ac0c4950a38b" -S /data/mysqldata/3306/mysql.sock extended-status |\
awk -F"|" \
"BEGIN{ count=0; }"\
'{ if ($2 ~ /Threads_connected/){Threads_connected=$3;}\
else if ($2 ~ /Threads_running/){Threads_running=$3;}\
else if ($2 ~ /Uptime / && count >= 0){\
  print Threads_connected,Threads_running;\
}}' | awk 'BEGIN{counter=0} \
{ if ($1 > 1000 || $2 > 128 ) counter++ ; } END {print counter}'
}
trg_plugin

#使用
#/usr/bin/pt-stalk --collect-tcpdump --function /data/scripts/bin/pt_stalk_func_thds_conn_runn.sh --threshold 0 --daemonize --cycles 3 --user=root --ask-pass --socket=/data/mysqldata/3306/mysql.sock
