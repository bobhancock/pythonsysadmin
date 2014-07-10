#!/bin/ksh


while :
    do
        /usr/local/python252/bin/python ./aggregator.py
        print "Sleeping " $(date)
        sleep 300
   done 
