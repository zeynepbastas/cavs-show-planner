# Show Planner app

The Streamlit version of our dashboard. Live: https://zeynepbastas-cavs-show-planner.streamlit.app

- `streamlit_app.py`: the app
- `model.py`: the forecast and pricing formulas, the same as in our notebook
- `data.json`: the numbers the notebook exports (group rates, past shows, the 9 upcoming shows)
- `make_app_data.py`: rebuilds `data.json` from the notebook (put the 8 challenge CSV files in a folder called `data` first)

Run it: `pip install -r requirements.txt`, then `streamlit run streamlit_app.py`
