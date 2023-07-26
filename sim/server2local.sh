#!/bin/bash
if [ $# -eq 0 ]; then
  echo "No argument provided."
  exit 1
fi

if [ $1 = 1 ]; then
    if [ $2 = "both" ]; then
        scp  EricD16@clnode238.clemson.cloudlab.us:~/amg/fig/* ./fig 
        scp  EricD16@clnode238.clemson.cloudlab.us:~/amg/log/* ./log
    else
        scp  EricD16@clnode238.clemson.cloudlab.us:~/amg/log/* ./log
    fi
elif [ $1 = 2 ]; then
    if [ $2 = "both" ]; then
        scp  EricD16@clnode226.clemson.cloudlab.us:~/amg/fig/* ./fig 
        scp  EricD16@clnode226.clemson.cloudlab.us:~/amg/log/* ./log
    else
        scp  EricD16@clnode226.clemson.cloudlab.us:~/amg/log/* ./log
    fi
elif [ $1 = 3 ]; then
    if [ $2 = "both" ]; then
        scp  EricD16@clnode244.clemson.cloudlab.us:~/amg/fig/* ./fig 
        scp  EricD16@clnode244.clemson.cloudlab.us:~/amg/log/* ./log
    else
        scp  EricD16@clnode244.clemson.cloudlab.us:~/amg/log/* ./log
    fi
elif [ $1 = 4 ]; then
    if [ $2 = "both" ]; then
        scp  EricD16@clnode192.clemson.cloudlab.us:~/amg/fig/* ./fig 
        scp  EricD16@clnode192.clemson.cloudlab.us:~/amg/log/* ./log
    else
        scp  EricD16@clnode192.clemson.cloudlab.us:~/amg/log/* ./log
    fi
fi