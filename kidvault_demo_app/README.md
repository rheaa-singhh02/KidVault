KidVault demo app

Backend lives in `backend/` and the duplicated frontend lives in `frontend/`.

Run it:

1. `cd backend`
2. `python3 -m venv .venv`
3. `source .venv/bin/activate`
4. `python3 -m pip install -r requirements.txt`
5. `cp .env.example .env`
6. `python3 app.py`

Then open `frontend/demo-index.html` in a browser.

You can also just open [http://127.0.0.1:5050/](http://127.0.0.1:5050/) after starting Flask, because the backend now serves the demo frontend too.
