# ldapstat
Specific purpose app.

## How to run

1. Copy `config.sample.py` to `config.py` and configure
1. Install virtualenv (https://virtualenv.pypa.io/en/stable/)
1. Create environment with Python 3: `virtualenv -p python3 venv`
1. Activate environment: `source venv/bin/activate`
1. `pip install -r requirements.txt`
1. `export FLASK_ENV=development` (or production)
1. `flask run`