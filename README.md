## Beispiel
```bash
./venv/bin/python3 main.py -u USER -p PASSWORD -b 7 -t 14:00 -m 4
```
Bucht sofort einen Raum für heute in 7 Tagen um 14:00 Uhr, in den mindestens vier Leute reinpassen.

```bash
./venv/bin/python3 main.py -u USER -p PASSWORD -b 2 -t 14:00 -r 137
```
Bucht sofort Raum 137 für übermorgen um 14:00 Uhr.

Parameter -h zeigt Hilfe an.

## Abhängigkeiten
- Geckodriver: https://github.com/mozilla/geckodriver/releases, herunterladen und zu PATH hinzufügen

## Installation
```bash
git clone https://github.com/rellimn/bibbucher.git
cd bibbucher
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

### Docker
```
docker build -f Dockerfile -t bibbucher .
```
