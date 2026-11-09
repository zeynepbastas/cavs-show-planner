# Show Planner

**Concessions Pricing Challenge · Sports Business & Analytics Night 2026**
Zeynep Baştaş, Blessing Masanga, Daniel Youngquist · Case Western Reserve University

**Live app:** https://zeynepbastas-cavs-show-planner.streamlit.app

Place any show in one of our five crowd groups, forecast what its fans will buy, and test prices before the doors open.

## What's in here

| File | What it does |
|---|---|
| `streamlit_app.py` | The app |
| `model.py` | Forecast and pricing formulas, the same as in our notebook |
| `data.json` | The numbers the app uses: group rates, past shows and the 9 upcoming shows |
| `make_app_data.py` | Rebuilds `data.json` from the notebook |
| `analysis/CWRU_Concessions_Analysis.ipynb` | Our full analysis: groups, backtest, forecast and the two submission CSVs |

## Run it yourself

```
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The challenge data files are not in this repo. To rerun the notebook or `make_app_data.py`, put the 8 CSV files from the challenge email in a folder called `data`.
