# if [ $# -eq 0 ]; then
#   echo "No argument provided."
#   exit 1
# fi

# if [ $1 = 1 ]; then
#     scp -r ./amg EricD16@clnode238.clemson.cloudlab.us:~/
# elif [ $1 = 2 ]; then
#     scp -r ./amg EricD16@clnode226.clemson.cloudlab.us:~/
# elif [ $1 = 3 ]; then
#     scp -r ./amg EricD16@clnode244.clemson.cloudlab.us:~/
# fi

NODENAME="EricD16@clgpu011.clemson.cloudlab.us"

scp -r ./evaluation ${NODENAME}:~/Propius/
scp -r ./propius ${NODENAME}:~/Propius/
scp -r ./propius_job ${NODENAME}:~/Propius/

scp -r ./fedscale* ${NODENAME}:~/Propius
scp -r ./propius* ${NODENAME}:~/Propius
scp -r ./sim ${NODENAME}:~/Propius
scp ./*.yml ${NODENAME}:~/Propius
scp ./*.py ${NODENAME}:~/Propius
scp ./*.sh ${NODENAME}:~/Propius
# scp -r ./datasets/device_info ${NODENAME}:~/Propius/datasets
# scp ./datasets/download.sh ${NODENAME}:~/Propius/datasets