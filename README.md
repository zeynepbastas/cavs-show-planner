# Show Planner: Concessions Pricing Challenge

**2026 Cavs Sports Business & Analytics Night Hackathon**
Blessing Masanga, Daniel Youngquist, Zeynep Bastas · Case Western Reserve University

- **Live app:** https://zeynepbastas-cavs-show-planner.streamlit.app
- **Presentation:** [Show_Planner.pdf](Show_Planner.pdf) (cover slide and dashboard)
- **Write-up:** [CWRU_Writeup.pdf](CWRU_Writeup.pdf)
- **Main analysis:** [CWRU_Concessions_Analysis.ipynb](CWRU_Concessions_Analysis.ipynb)

## The challenge

Rocket Arena hosts dozens of third-party shows every year, and every crowd buys differently. We were asked to group
past shows by what drives guest spending, forecast the five best-selling concession items for 9 upcoming shows,
recommend prices that flex by group, and build a visual a business leader can read in seconds.

## What we found

1. **Five crowd groups, one simple rule.** A sports event, or a family show where most ticket buyers are men:
   Family Night & Sports. Other family shows: Family Day. Rock or country concert: Bar. Pop concert: Pop.
   Everything else (hip-hop/R&B, comedy): Social.
2. **The groups make forecasts more accurate.** Predicting each act only from the other shows in its group cuts the
   error from 34% (no groups) to 22%. Giving pop its own group wins in 98% of bootstrap resamples.
3. **Each crowd buys differently.** Bar crowds spend 7 times more on alcohol per fan than Family Day ($13.30 vs $1.80).
   Pop fans buy the most water (168 bottles per 1,000 fans), while hip-hop and comedy crowds lean on cocktails.
4. **Prices flex by group** (table below): water is cheaper everywhere, both family groups get family prices, and
   drinks cost more where the crowd spends the most on them.
5. **For the 9 upcoming shows** (base crowd, published price sensitivity): gross $221,923 vs
   $220,868 at the old prices (+0.5%), and 20,663 items sold
   vs 19,866 (+4.0%). It brings in more than the old prices at every price sensitivity from 0x to 2x the published values.

## Price card

| Item | Family Day | Family Night & Sports | Pop | Social | Bar | Menu today |
|---|---|---|---|---|---|---|
| 20oz Dasani Water | $4.99 | $4.99 | $4.99 | $4.99 | $4.99 | $5.62 |
| Double Cocktail | $22.99 | $22.99 | $30.25 | $30.25 | $30.99 | $28.79 |
| 24oz Fountain Drink | $6.49 | $6.49 | $7.79 | $7.79 | $7.79 | $7.79 |
| Bavarian Pretzel | $7.49 | $7.49 | $10.59 | $10.59 | $10.59 | $10.59 |
| 16oz Michelob Ultra | $12.99 | $12.99 | $17.49 | $17.49 | $17.99 | $16.99 |

## How it works

- **Forecast:** units = crowd x units per ticket x (new price / price paid before) ^ elasticity, and gross = units x price.
  Units per ticket come from the performer's own past shows when they played here before, otherwise from their group.
- **Crowd:** the base case is Rule 2; low and high come from Rules 1 to 3 (notebook, section 7).
- **Backtest:** hide every show by one performer, predict them from the rest of their group, and compare with what they
  actually sold (section 6). Other methods we tried, and why we kept the simple rule, are in section 11.
- **Price sensitivity:** the menu price was the same at every past show, so our data can't measure it. We use published
  values (beer -0.46, spirits -0.80, soft drinks -0.79, food -0.81) and test the price card from 0x to 2x of them.

## What's in this repo

| Path | What it is |
|---|---|
| `Show_Planner.pdf` | Our visual presentation: cover slide and dashboard |
| `Show_Planner.html` | An offline copy of the dashboard |
| `CWRU_Concessions_Analysis.ipynb` | Main analysis: groups, backtest, forecast, price card and both CSV files |
| `event_groups.csv` | The group for all 45 shows (36 past, 9 upcoming) |
| `upcoming_forecast.csv` | Units, recommended price and gross for the 5 items at the 9 upcoming shows |
| `show-planner/` | The Streamlit app: `streamlit_app.py`, `model.py` (the formulas) and `data.json` (the numbers) |
| `exploration/` | Our early exploration notebook and first ideas, the 260-scheme grouping search from our write-up (`Cavs_260_broad_grouping_tests.zip`: unzip it, add the challenge CSVs to its `data` folder and run `broad_search.py`), and a second script that rebuilds the same 45 groups (its forecast part is an earlier, simpler version) |

## Run it yourself

- **Notebook:** open it in Google Colab, click Runtime > Run all, and upload the 8 challenge CSV files when asked.
- **App:** `pip install -r show-planner/requirements.txt`, then `streamlit run show-planner/streamlit_app.py`.

The challenge data was shared with participants and is not included in this repo.

## Tools and sources

Python (pandas, NumPy, SciPy, scikit-learn, matplotlib), Streamlit and Altair.
Price sensitivities: Wagenaar et al. (2009) for beer and spirits, Andreyeva et al. (2010) for soft drinks and food.
