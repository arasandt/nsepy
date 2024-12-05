cat fo/*_cleaned.csv > all.csv
cat fo/*1224_cleaned.csv > all.csv
awk '!seen[$0]++' all.csv > all_nodups.csv
aws s3 cp all_nodups.csv s3://aws-athena-query-results-127537946772-us-east-1/
aws s3 cp s3://aws-athena-query-results-127537946772-us-east-1/all_nodups.csv s3://nifty50optionsdata --acl bucket-owner-full-control
aws s3 cp index.html s3://aws-athena-query-results-127537946772-us-east-1/
aws s3 cp s3://aws-athena-query-results-127537946772-us-east-1/index.html s3://nifty50optionsdata --acl bucket-owner-full-control
# aws s3 rm s3://aws-athena-query-results-127537946772-us-east-1/index.html