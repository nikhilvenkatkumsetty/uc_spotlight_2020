# Baseline Tools
sudo yum -y install net-tools vim git wget tree

# Install Miniconda
wget -P /opt https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash /opt/Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda

# Fetch UC 2020 Spotlight Code
git clone https://github.com/Jwmazzi/uc_spotlight_2020.git /opt/uc_flask

# Ensure SQLite can be Updated
chmod 777 /opt/uc_flask/app/info.db

# Create Environment
/opt/miniconda/bin/conda create --name uc python=3.6 -y

# Install Dependencies
source /opt/miniconda/bin/activate uc
pip install -r /opt/uc_flask/env/req.txt
python -c "import nltk; nltk.download('punkt')"

# Create Certificate
openssl req -newkey rsa:2048 -nodes -keyout /opt/esri_flask.key -x509 -days 365 -out /opt/esri_flask.crt -subj "/C=US/ST=ST/L=L/O=O/CN=CN"

# Print IP
hostname -I

# Run Flask with Gunicorn
#gunicorn --bind 0.0.0.0:5000 --chdir /opt/uc_flask/ manage:app --certfile=/opt/esri_flask.crt --keyfile=/opt/esri_flask.key
