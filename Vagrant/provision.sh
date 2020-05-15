# Baseline Tools
sudo yum -y install net-tools vim git wget tree

# Install Miniconda & Create Environment
wget -P /opt https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash /opt/Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda

# Fetch UC 2020 Spotlight Code
git clone https://github.com/Jwmazzi/uc_spotlight_2020.git /opt/uc_flask
