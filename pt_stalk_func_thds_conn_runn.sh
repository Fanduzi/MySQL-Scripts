#!/bin/bash
trg_plugin() {
mysqladmin -uroot -p"fanboshi" -S /data/mysqldata/3308/mysql.sock extended-status |\
awk -F"|" \
"BEGIN{ count=0; }"\
'{ if ($2 ~ /Threads_connected/){Threads_connected=$3;}\
else if ($2 ~ /Threads_running/){Threads_running=$3;}\
else if ($2 ~ /Uptime / && count >= 0){\
  print Threads_connected,Threads_running;\
}}' | awk 'BEGIN{counter=0} \
{ if ($1 > 1000 || $2 > 32 ) counter++ ; } END {print counter}'
}
trg_plugin
