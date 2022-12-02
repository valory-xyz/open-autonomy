sudo chown -R ubuntu:ubuntu /logs
sudo chown -R ubuntu:ubuntu /open-aea
sudo chown -R ubuntu:ubuntu /benchmarks
sudo chown -R ubuntu:ubuntu /home/ubuntu
sudo chown -R ubuntu:ubuntu /home/ubuntu/packages

echo "Starting Dev image and installing agent dependencies."

if [[ "$(ls -l /home/ubuntu/.local/share/virtualenvs | grep ubuntu | wc -l)" -eq "1" ]]
then
    echo "Venv already exists @ $(pipenv --venv), no need to install"
else
    echo "Installing venv"
    
    rm -rf /home/ubuntu/.local/share/virtualenvs/__temp__

    if [[ "$ID" -eq "0" ]]
    then
        echo "Installing venv with ID=$ID"
        pipenv --python 3.10
        pipenv install --skip-lock
        pipenv install --skip-lock --dev
        mkdir /home/ubuntu/.local/share/virtualenvs/__temp__
    else
        echo "Won't install with ID=$ID"
        echo "Waiting for installation"
        while [ "$(ls -l /home/ubuntu/.local/share/virtualenvs | grep __temp__ | wc -l)" != "1" ]
        do
            sleep 1
        done
        echo "Venv installed"
    fi
fi

echo "Using venv @ $(pipenv --venv)"

pipenv run python /home/ubuntu/watcher.py
