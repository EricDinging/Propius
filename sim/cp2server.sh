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

scp -r ./evaluation EricD16@clgpu011.clemson.cloudlab.us:~/Propius/
scp -r ./propius EricD16@clgpu011.clemson.cloudlab.us:~/Propius/
scp -r ./propius_job EricD16@clgpu011.clemson.cloudlab.us:~/Propius/

scp -r ./docker EricD16@clgpu011.clemson.cloudlab.us:~/Propius
scp -r ./evaluation EricD16@clgpu011.clemson.cloudlab.us:~/Propius
scp -r ./fedscale* EricD16@clgpu011.clemson.cloudlab.us:~/Propius
scp -r ./propius* EricD16@clgpu011.clemson.cloudlab.us:~/Propius
scp -r ./sim EricD16@clgpu011.clemson.cloudlab.us:~/Propius
scp ./*.yml EricD16@clgpu011.clemson.cloudlab.us:~/Propius
scp ./*.py EricD16@clgpu011.clemson.cloudlab.us:~/Propius

scp -r ./datasets/device_info EricD16@clgpu011.clemson.cloudlab.us:~/datasets