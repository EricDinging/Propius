if [ $# -eq 0 ]; then
  echo "Error: Please provide a directory name as an argument."
  exit 1
fi

set -x 
dir_name="experiment/$1"
mkdir "$dir_name"
cp -r amg/fig amg/log "$dir_name"
rm amg/fig/* amg/log/*

set +x