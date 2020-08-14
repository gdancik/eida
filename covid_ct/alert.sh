#!/bin/bash
# Call func function on exit
trap func ERR 

# Declare the function
function func() {
 
  echo "Error in alert check" 
  exit -1
}


git pull

curdir=$PWD
echo "executing extract_data_for_html.py ..."

d=$(date +"%Y_%m_%d")

python extract_data_for_html.py scorecard.csv alerts/CT_alert_$d.html CT True

echo "uploading to github..."
git add alerts/*
git commit -m "Alert issued on $d"
git push


