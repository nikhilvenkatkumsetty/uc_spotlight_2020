# Baseline Tools
sudo yum -y install net-tools vim git wget tree


# Install Miniconda & Create Environment
wget -P /opt/miniconda https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda
opt/miniconda/conda create -n uc python=3.7 -y