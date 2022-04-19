echo "Starting Dev image and installing Valory app dependencies."
sudo chown -R ubuntu:ubuntu /home/ubuntu
sudo chown -R ubuntu:ubuntu /open-aea

pipenv install --skip-lock --dev

INSTALL=1 pipenv run bash start.sh
pipenv run python /home/ubuntu/watcher.py
