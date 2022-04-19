sudo chown -R ubuntu:ubuntu /logs
sudo chown -R ubuntu:ubuntu /home/ubuntu/packages
sudo chown -R ubuntu:ubuntu /open-aea

pipenv install --skip-lock --dev

INSTALL=1 pipenv run bash start.sh
pipenv run python /home/ubuntu/watcher.py
