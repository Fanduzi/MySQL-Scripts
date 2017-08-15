#!/bin/sh
function collect(){
  sql1="SELECT t.table_schema,t.table_name,t.engine,IF(ISNULL(c.constraint_name),'NOPK','') AS nopk,IF(s.index_type = 'FULLTEXT','FULLTEXT','') as ftidx,IF(s.index_type = 'SPATIAL','SPATIAL','') as gisidx FROM information_schema.tables AS t LEFT JOIN information_schema.key_column_usage AS c ON (t.table_schema = c.constraint_schema AND t.table_name = c.table_name AND c.constraint_name = 'PRIMARY') LEFT JOIN information_schema.statistics AS s ON (t.table_schema = s.table_schema AND t.table_name = s.table_name AND s.index_type IN ('FULLTEXT','SPATIAL')) WHERE t.table_schema NOT IN ('information_schema','performance_schema','mysql') AND t.table_type = 'BASE TABLE' AND  c.constraint_name IS NULL ORDER BY t.table_schema,t.table_name"
  echo "############没有使用主键的########"
  mysql -p123456 -e "$sql1"
  sql2="SELECT object_schema, object_name, index_name FROM performance_schema.table_io_waits_summary_by_index_usage WHERE index_name IS NOT NULL AND index_name != 'PRIMARY' AND count_star = 0 AND OBJECT_SCHEMA != 'mysql' ORDER BY object_schema, object_name;"
  echo "############索引一次没有使用的############"
  mysql -p123456 -e "$sql2"
  sql3=" SELECT SCHEMA_NAME,DIGEST_TEXT,COUNT_STAR,AVG_TIMER_WAIT,SUM_ROWS_SENT,SUM_ROWS_EXAMINED,FIRST_SEEN,LAST_SEEN FROM performance_schema.events_statements_summary_by_digest ORDER BY AVG_TIMER_WAIT desc LIMIT 10\G"
  echo "###########历史耗时最长的TOP10语句#####"
  mysql -p123456 -e "$sql3" 
  sql4="SELECT C.TABLE_SCHEMA,C.REFERENCED_TABLE_NAME,C.REFERENCED_COLUMN_NAME,C.TABLE_NAME,C.COLUMN_NAME,C.CONSTRAINT_NAME,T.TABLE_COMMENT,R.UPDATE_RULE,R.DELETE_RULE  FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE C JOIN INFORMATION_SCHEMA.TABLES T ON T.TABLE_NAME = C.TABLE_NAME JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS R ON R.TABLE_NAME = C.TABLE_NAME AND R.CONSTRAINT_NAME = C.CONSTRAINT_NAME AND R.REFERENCED_TABLE_NAME = C.REFERENCED_TABLE_NAME WHERE C.REFERENCED_TABLE_NAME IS NOT NULL;"     
  echo "############主外键约束的############"
  mysql -p123456 -e "$sql4"
  sql5="SELECT table_schema,table_name,table_rows,data_length,index_length,CONCAT(ROUND((data_length+index_length)/(1024*1024),2),'M') AS 'Total',CONCAT(ROUND(DATA_FREE/(1024*1024),2),'M') FROM information_schema.TABLES where table_schema not in ('information_schema','mysql','performance_schema','test') order by  DATA_FREE desc limit 10;"
  echo "##########碎片最多的TOP10表#########"
  mysql -p123456 -e "$sql5"
  sql6="SELECT table_schema,table_name,table_rows,data_length,index_length,CONCAT(ROUND((data_length+index_length)/(1024*1024),2),'M') AS 'Total',CONCAT(ROUND(DATA_FREE/(1024*1024),2),'M') FROM information_schema.TABLES where table_schema not in ('information_schema','mysql','performance_schema','test') order by  table_rows desc limit 10;"
  echo "############行数据统计TOP10表#######"
  mysql -p123456 -e "$sql6"
}
collect

