#!/bin/bash
# Call func function on exit
trap func ERR 

# Declare the function
function func() {
 
  echo "Error in weekly updates"
  echo "Error in weekly updates" 
  exit -1
}


git pull

curdir=$PWD
echo "executing read_data.R..."
cd ../..
Rscript read_data.R

echo "generating html files..."
cd $curdir
Rscript generate_html.R ../..

echo "uploading to github..."
git add updates/*
d=$(date +"%Y_%m_%d")
git commit -m "Weekly Update for $d"
git push


