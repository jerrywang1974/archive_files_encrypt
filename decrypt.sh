#!/bin/bash
FILENAME=$1
NEWFILE=${FILENAME::-4}
PASSWORD=`grep 'password' config.ini |awk '{print $3}'`

/usr/bin/openssl enc -aes-256-cbc -d -pbkdf2 -in $1 -out $NEWFILE -k $PASSWORD
/usr/bin/tar xfv $NEWFILE 
#unzip $NEWFILE
