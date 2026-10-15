# Cross-Border Settlement Ledger (Demo)

## Requirements
- Windows 10/11
- Python 3.9 or newer
- Internet connection for the first install
- VS Code is optional

## Easiest way to run
1. Extract this ZIP to a folder.
2. Double-click `run_demo.bat`.
3. Wait for Streamlit to install (first run only) and start.
4. Your browser should open. If not, visit `http://localhost:8501`.

## Run manually
Open CMD in this folder and run:
```cmd
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m streamlit run app.py
```

## Demo steps
1. On the **New transfer** tab, enter sender and recipient names and an amount in INR.
2. Click **Record transfer on ledger**.
3. Open the **Ledger** tab to inspect block hashes and verification status.
4. In the Integrity test section, click **Simulate tampering** to see verification fail.
5. Click **Reset ledger** to start over.

## Important limitations
This is an educational, single-computer simulation. It does not transfer real money and is not a distributed blockchain. The ₹83/USD rate is fixed for demonstration, not a live exchange rate. No API key or crypto wallet is required.
