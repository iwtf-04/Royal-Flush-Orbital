# Royal-Flush-Orbital

# Backend — run locally
1. Open a terminal and change to the backend folder:
cd dealerkaki/backend

2. Create and activate a virtual environment (macOS / Linux):
python3 -m venv .venv
source .venv/bin/activate

3. Install Python dependencies:
pip install -r requirements.txt


4. Seed the database with test users:
python seed.py

Seeded users (username:password):
- `staff1:staff123` (frontline staff)
- `inventory1:inventory123` (inventory manager)
- `dealer1:dealer123` (dealer)
- `admin1:admin123` (admin)

5. Start the backend (development):
uvicorn main:app --reload --port 3000
or
python main.py

Health check: `http://127.0.0.1:3000/api/health`

# Frontend — run locally

1. Open a second terminal and change to the frontend folder:
cd dealerkaki/frontend

2. Install dependencies and start the dev server:
```bash
npm install
npm run dev
```

Vite will start on `http://localhost:5173/`. 

# Usage

- Open `http://localhost:5173` in your browser.
- Login using one of the seeded accounts, then try the "Vehicle Valuation" feature.
