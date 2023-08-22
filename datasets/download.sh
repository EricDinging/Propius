RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # no color

if [ ! -d "./datasets/femnist/client_data_mapping" ]; then
    echo "Downloading FEMNIST dataset(about 327M)..."
    wget -O ./datasets/femnist.tar.gz https://fedscale.eecs.umich.edu/dataset/femnist.tar.gz

    echo "Dataset downloaded, now decompressing..."
    tar -xf ./datasets/femnist.tar.gz -C ./datasets

    echo "Removing compressed file..."
    rm -f ./datasets/femnist.tar.gz

    echo -e "${GREEN}FEMNIST dataset downloaded!${NC}"
else
    echo -e "${RED}FEMNIST dataset already exists!"
fi