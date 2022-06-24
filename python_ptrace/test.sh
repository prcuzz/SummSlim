#!/bin/bash

echo "zzc: test.sh"

mkdir zzzzzzzzzzzzzzzzzzc

ls

if test ! -e "./zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzc-test"
then
	touch zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzc-test
fi

for line in `cat zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzc-test`
do
    echo $line
done

exec python3 hello.py
