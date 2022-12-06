## Beispiel
```shell
./venv/bin/python3 main.py -u USER -p PASSWORD -b 7 -t 14:00 -m 4
```
Bucht sofort einen Raum für (heute + 7 Tage um 14:00 Uhr), in den mindestens vier Leute reinpassen.

Parameter -h zeigt Hilfe an.

## Abhängigkeiten
- Geckodriver: https://github.com/mozilla/geckodriver/releases, herunterladen und zu PATH hinzufügen

## Installation
```shell
git clone https://github.com/rellimn/bibbucher.git
cd bibbucher
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```