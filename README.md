# Piscine DataScience - 0 : Creation of a DB

## Project structure

```
Data Science - 0/
├── .env                  ← credentials (not committed)
├── .gitignore
├── setup.sh              ← one-command start (Mac + Linux)
├── ex00/
│   └── docker-compose.yml   ← PostgreSQL + pgAdmin
├── ex01/                 ← pgAdmin GUI (same stack as ex00)
├── ex02/                 ← table.* SQL script
├── ex03/                 ← automatic_table.* script
└── ex04/                 ← items_table.* script
```

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Mac)
- Docker + docker-compose-v2 (Linux school machines — see below)

---

## Quick start

```bash
./setup.sh
```

That's it. The script handles everything: checks Docker, creates `.env` if missing, and starts the stack.

---

## Manual start

```bash
cd ex00
launch docker compose --env-file ../.env up -d
```
cd "/goinfre/amdemuyn/42_Piscine_Data_Science/Data Science - 0" && docker compose --env-file
  .env -f ex00/docker-compose.yml up -d
---

## Connecting to the database

```bash
psql -U amdemuyn -d piscineds -h localhost -W
# password: mysecretpassword
```

> **Mac only:** if `psql` is not found, install the client (no full server needed):
> ```bash
> brew install libpq && brew link --force libpq
> ```
> On school Linux machines `psql` is usually already available system-wide.

Some useful commands to know from this prompt:
  
  \l          -- list all databases
  \du         -- list users/roles
  \dt         -- list tables (useful later for ex02-04)
  \q          -- quit


---

## Stop / clean up

```bash
# Stop containers (data persisted in Docker volumes)
docker compose -f ex00/docker-compose.yml down

# Stop AND delete all data (full reset)
docker compose -f ex00/docker-compose.yml down -v
```

---

## School Linux machines (no VM)

The school machines use **goinfre** for extra disk space (your session quota is small).
The `setup.sh` script automatically:
1. Installs Docker if missing (via `apt-get`)
2. Redirects Docker's data directory to `~/goinfre/docker` to avoid quota issues
3. Starts the stack

Just run:
```bash
./setup.sh
```

> ⚠️ After a first-time Docker install on Linux you may need to log out and back in,
> then run `./setup.sh` again so your user is in the `docker` group.

### Transferring the project to school

  git clone <tu-repo>
  cd "42_Piscine_Data_Science"
  ./setup_env.sh

---

## Credentials summary

| Service    | Value              |
|------------|--------------------|
| DB user    | `amdemuyn`         |
| DB name    | `piscineds`        |
| DB password| `mysecretpassword` |
| pgAdmin email | `admin@admin.com` |
| pgAdmin password | `admin`     |
| PostgreSQL port | `5432`        |
| pgAdmin port    | `8080`        |


## pgAdmin (ex01)

Open http://localhost:8080 in your browser.

- Email: `admin@admin.com`
- Password: `admin`

To add the server in pgAdmin:
1. Right-click **Servers** → **Register** → **Server**
2. Name: `piscineds`
3. Connection tab:
   - Host: `postgresql` (the Docker service name, not localhost)
   - Port: `5432`
   - Database: `piscineds`
   - Username: `amdemuyn`
   - Password: `mysecretpassword`


## Create table from CSV (ex02)

1. Run the script

   - python3 ex02/table.py
  We see: Table 'data_2022_oct' created successfully.
  
2. Connect to the DB and describe the table
   - psql -U amdemuyn -d piscineds -h localhost -W
   - Then inside psql: \d data_2022_oct
  
  We see the table structure with all 6 types.
  
  We can also show it in pgAdmin (ex01 tool) — navigate to piscineds > Schemas > public > Tables >
  data_2022_oct and right-click → Properties. More visual.



----------------------------------------------------------


# Piscine DataScience - 1 : Data Warehouse
## ex02

To show that there is no duplicates with psql:
Connect to psql and run a few queries:
  
  psql -U amdemuyn -d piscineds -h localhost -W
  
  Then inside:
  
  -- row count
  SELECT COUNT(*) FROM customers;
  
  -- check there are no exact duplicates left
  SELECT COUNT(*) FROM customers
  EXCEPT
  SELECT COUNT(*) FROM (SELECT DISTINCT * FROM customers) AS d;
  
  -- peek at the data
  SELECT * FROM customers LIMIT 5;
  
  -- see all tables
  \dt

   1. Deduplication logic
  
  Old query used SELECT DISTINCT * — removes only rows that are 100% identical across all columns. If two rows differ by even 1 microsecond in event_time, they're kept as separate rows.
  
  New query uses a LAG window function — it looks at the time gap between consecutive events for the same (user, session, product, event_type, price) combination, and removes any event that happened within 1 second of the previous one. This catches near-duplicates where the timestamp is slightly different but it's clearly the same event sent twice.
  
  2. The customers table had 9 columns vs 6
  
  When we ran the old DISTINCT * on a table that already had category_id, category_code, brand added by ex03, two rows that were duplicates in the original 6 columns could have different item data — so DISTINCT * wouldn't recognize them as duplicates. The new script runs on the raw 6-column table (before fusion), so the deduplication is clean.
  
  In short: DISTINCT * only catches exact copies. The LAG approach catches "same event, slightly different
  timestamp" which is where the bulk of the duplicates were hiding (~1.5M rows).


## ex03

We build a new fused table then swap it in, which is much faster than adding columns and running an UPDATE on 19M rows. The duplicates have different category_id or brand — some rows have nulls, others have values. The right strategy is to keep the most informative row per product_id (prefer non-null values).

The fusion.py script will:
  1. Load item.csv into the items table
  2. Add the 3 new columns (category_id, category_code, brand) to customers
  3. Populate them via a LEFT JOIN with items on product_id

customers now has 9 columns — the original 6 plus category_id, category_code, and brand from
items. Row count unchanged at 19,583,741.

Shell PGPASSWORD=mysecretpassword psql -U amdemuyn -d piscineds -h localhost -c "
  SELECT
      COUNT(*)                          AS total_rows,
      COUNT(category_id)                AS rows_with_category_id,
      COUNT(brand)                      AS rows_with_brand,
      COUNT(*) - COUNT(category_id)     AS rows_without_match
  FROM customers;"


    | total_rows | rows_with_category_id | rows_with_brand | rows_without_match |
    |------------|-----------------------|-----------------|--------------------|
    |   19583741 |              19582393 |        11404851 |               1348 |
    (1 row)



  - 19,583,741 total rows — unchanged ✅
  - 19,582,393 rows matched a product in items and got category_id
  - 1,348 rows had a product_id not present in items at all — they got NULL for the item columns,
  which is correct for a LEFT JOIN
  - 11,404,851 rows have a brand (the rest have null brand in items itself — that's the source
  data being incomplete)
  
  No customer rows were lost. The 1,348 nulls are expected — those product IDs simply don't exist
  in the items catalogue.


`-> to show the columns: \d customers`


----------------------------------------------------------


# Piscine DataScience - 2 : Data Viz

This module is about turning the data from the database into charts that tell a story.
All charts connect to the `customers` table built in module 1.

The tool stack: Python with pandas + matplotlib/seaborn + scikit-learn — 
it covers everything from simple charts to clustering

  - pandas — reads from PostgreSQL, handles all the data manipulation
  - matplotlib/seaborn — pie charts, bar charts, box plots, all of ex00-03
  - scikit-learn — elbow method and K-means for ex04-05
  - No Jupyter needed — plain .py files are cleaner to submit and run during eval

we use sqlalchemy to connect pandas directly to PostgreSQL with pd.read_sql(), 
which is cleaner than psycopg2 for read-only queries.

---

## ex00 — pie.*  Pie chart of what customers do on the site

The `customers` table records every action a customer made: viewing a product,
adding it to the cart, removing it, or actually buying it.

The pie chart answers the question: **out of all these actions, what percentage is each type?**

- Each slice = one type of action (view, cart, purchase, remove_from_cart)
- The size of the slice = how common that action is

You'll see that most events are views — people browse a lot but only a fraction
actually buy. That's normal for e-commerce and already interesting to a business.

Run:
```bash
python3 pie.py
```

---

## ex01 — chart.*  3 charts of purchase activity over time

We filter down to **purchases only** and look at how the business performed
day by day and month by month between October 2022 and February 2023.

**Chart 1 — Number of customers per day** (line chart)
How many different people made a purchase each day?
Spikes = sales events (Black Friday, Christmas...). Dips = quiet periods.

**Chart 2 — Total sales per month** (bar chart)
How much money (in Altairian Dollars) did the shop make each month?
Each bar = one month. Taller bar = more revenue.

**Chart 3 — Average spend per customer per day** (area chart)
On a given day, how much did the average buying customer spend?
This is different from total sales — it shows whether customers are spending
more or less per visit, regardless of how many came.

Run:
```bash
python3 chart.py
```

---

## ex02 — mustache.*  Box plots of purchase prices

A box plot is a compact summary of how a set of numbers is spread out.
Instead of showing every value, it shows 5 key points:
- The minimum (ignoring extreme outliers)
- The 25th percentile (25% of values are below this)
- The median (the middle value — 50% below, 50% above)
- The 75th percentile (75% of values are below this)
- The maximum (ignoring extreme outliers)

The "box" covers the middle 50% of the data. The lines sticking out are called
whiskers. Dots beyond the whiskers are outliers — unusually extreme values.

**Plot 1 — All purchase prices**
Shows the full range of prices, from -79 A$ (returns/refunds) to 327 A$.
The box is squashed near zero because most items are cheap — the extreme
values stretch the axis but aren't representative.

**Plot 2 — Item prices (zoomed in)**
Same data but zoomed into the typical range (0–13 A$).
This gives a clearer picture of what most items actually cost.

**Plot 3 — Average basket per customer per day**
Instead of individual item prices, this shows how much the average customer
spent in total on a given day. The range is much tighter (around 30–42 A$)
because averaging smooths out the extremes.

The script also prints the stats (count, mean, min, max, quartiles) in the terminal.

Run:
```bash
python3 mustache.py
```

---

## ex03 — Building.*  Bar charts of purchase habits

Two bar charts side by side that answer two different questions about customers:

**Left chart — How often do customers buy? (frequency)**
Each bar = a group of customers who bought a certain number of times.
The first bar is the tallest — most customers only bought a handful of times.
Very few customers bought 30+ times. This is a classic "long tail" pattern.

**Right chart — How much do customers spend in total? (monetary value)**
Each bar = a group of customers who spent a certain total amount.
Again, most customers spent a small amount, and only a few are big spenders.

Together these two charts set up the customer segmentation work in ex04-ex05:
they show that customers are not all the same — there are clear differences
in how often and how much people buy.

---

## ex04 elbow.* — Elbow method to find optimal number of clusters

  Classic elbow curve. X-axis is number of clusters (1-10), Y-axis is inertia (sum of squared distances). The elbow appears around
  k=3-4 in the subject example.
  
  The input to K-means needs to be per-customer features — the standard RFM approach: Recency (days since last purchase), Frequency
  (number of purchases), Monetary (total spend).

  If you want to group customers into "types" — like "loyal buyers", "occasional buyers", "window shoppers",
  etc. But how many groups should you make?
  
  The elbow method answers that question.
  
  You try grouping customers into 1 group, then 2, then 3... up to 10. For each number of groups, you measure how "messy" the
  grouping is — how different are the customers within the same group? That messiness score is called inertia. More groups = less
  messy, but at some point adding another group barely helps.
  
  When you plot that score on a graph, it forms a curve that bends like an elbow. The point where the curve stops dropping sharply
  is the sweet spot — the "elbow". That's your optimal number of groups. (In our case it's 4.)
  
  The three things we measure per customer (RFM):
  - Recency — how long ago did they last buy? (recently = active customer)
  - Frequency — how many times did they buy in total?
  - Monetary — how much money did they spend in total?
  
  Those 3 numbers summarise each customer as a point in space. K-means then tries to find natural groupings of those points.

## ex05 Clustering.* — K-means (or similar) clustering into 4+ customer groups with visualizations
  Three visualizations expected:
  
  1. Horizontal bar chart — number of customers per cluster (Loyal, New, Inactive) with count labels
  2. Bubble chart — clusters plotted by Median Recency (months) vs Median Frequency, bubble size = monetary value
  3. Scatter plot — clusters in 2D space with centroids marked in yellow
  
  The subject example only has 3 groups but our elbow says 4 — we'll use k=4 and add a 4th group (we split "loyal customers" into "Big spenders" and "loyal customers").

  Three windows one after the other. The terminal will also print the cluster medians so you can see exactly what profile each group has.

  The medians are the raw cluster output before we assigned names. They tell the same story but without labels — They help us to decide which name fits which cluster:
  
  ┌─────────┬──────────┬───────────────┬──────────┬─────────────────────────────────────────────────────────────┐
  │ cluster │ recency  │ frequency     │ monetary │ → label                                                     │
  ├─────────┼──────────┼───────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ 3       │ 15 days  │ 113 purchases │ 535 A$   │ Loyal customers — most recent, most frequent, highest spend │
  ├─────────┼──────────┼───────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ 2       │ 32 days  │ 41 purchases  │ 187 A$   │ Big spenders — recent, moderate frequency, decent spend     │
  ├─────────┼──────────┼───────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ 0       │ 31 days  │ 6 purchases   │ 31 A$    │ New customers — recent but barely bought anything yet       │
  ├─────────┼──────────┼───────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ 1       │ 105 days │ 5 purchases   │ 28 A$    │ Inactive — haven't bought in 3+ months, low engagement      │
  └─────────┴──────────┴───────────────┴──────────┴─────────────────────────────────────────────────────────────┘

  Here's what the numbers tell you about your customers:
  
  Loyal customers (cluster 3)
  - Last bought ~28 days ago → still active
  - Bought 127 times on average → very frequent
  - Spent ~623 A$ total → your best customers
  - These are the ones you'd give gold/platinum status to
  
  Big spenders (cluster 2)
  - Last bought ~43 days ago → fairly recent
  - Bought 44 times → moderately frequent
  - Spent ~207 A$ → spend a lot per visit but less often than loyal
  - Good targets for upselling
  
  New customers (cluster 0)
  - Last bought ~32 days ago → recent
  - Only bought ~8 times → just getting started
  - Spent ~40 A$ → small total because they're new
  - Target them with welcome offers to convert them into loyal customers
  
  Inactive customers (cluster 1)
  - Last bought ~108 days ago → haven't been back in 3+ months
  - Only bought ~7 times → were never very engaged
  - Spent ~37 A$ → low value
  - Target them with "we miss you" coupons to bring them back


----------------------------------------------------------


# Piscine DataScience - 3: Data Scientist 1

## ex00
  - Test_knight.csv (no labels) → single green histogram per feature, legend says "Knight"
  - Train_knight.csv (has Jedi/Sith labels) → overlapping histograms, blue = Jedi, pink = Sith
  
  6 rows × 5 columns = 30 subplots, one per feature.

  Take Empowered. Every knight has a score for it. If you look at all the Jedi scores vs all the Sith scores:
  
  - Jedi tend to score high on Empowered (say around 0.2-0.3)
  - Sith tend to score low on Empowered (say around 0.05-0.1)
  
  In the histogram:
  - X axis = the Empowered score value (0.0, 0.1, 0.2...)
  - Y axis = how many knights have that score (count)
  - Blue bars = Jedi counts, pink bars = Sith counts
  
  Because the blue and pink bars are in different places on the X axis, you can clearly see the two groups are different → high
  correlation.

## ex01

  a correlation factor between each feature and the knight target, sorted by strongest correlation.
  The histograms show you visually — for each feature, do Jedi and Sith have different distributions? If the blue and pink peaks are far apart (like Empowered or Stims), those features separate the two groups well.
  
  Correlation gives you the same information as a number. A high correlation (like 0.79 for Empowered) means the Jedi and Sith
  distributions for that feature are very different — exactly what you saw in the histogram where the peaks were clearly separated.
  
  A low correlation (like 0.007 for Deflection) means the histograms for Jedi and Sith overlap almost completely — you can't tell
  them apart by that feature.
  
  What it doesn't tell you is which direction — who scores higher, Jedi or Sith. That's why we took abs(). If you removed the abs()
  you'd see negative values too, which would mean "Sith score higher on this feature". But for this exercise the subject only asks
  for strength of correlation, not direction.


## ex02
  python3 points.py Train_knight.csv
  python3 points.py Test_knight.csv
  
  That gives you 4 plots total — 2 per file. The key thing to explain during eval: the separating plot uses Empowered vs Stims (high
  correlation features), so you can visually see Jedi cluster separately from Sith. The mixing plot uses Pull vs Deflection
  (near-zero correlation), so both groups overlap completely.

## ex03

  python3 standardization.py Train_knight.csv
  python3 standardization.py Test_knight.csv

  standardize the data, print it, and display one of the scatter plots from ex02 with the standardized data.
  
  ── What is standardization? ──────────────────────────────────────────────────
The problem: features have very different scales.
  - Stims goes from 50 to 250
  - Deflection goes from 0.01 to 0.08

  If you feed this raw data to a machine learning algorithm that measures
  distances (like K-means or KNN), Stims will dominate just because its
  numbers are bigger — even if Deflection is more informative.

  Standardization fixes this by rescaling every feature so that:
    - Its mean becomes 0  (the average value is now 0)
    - Its std becomes 1   (values are measured in "how many std from average")

  Formula for each value:  z = (x - mean) / std

  After standardization, a Stims value of 100 becomes ~0, and 200 becomes ~1.
  All features are now on the same scale and can be fairly compared.

## ex04

  python3 Normalization.py Train_knight.csv
  python3 Normalization.py Test_knight.csv

normalization — similar to ex03 but instead of centering around 0, it squashes every feature into the range 0 to 1.
  
  Formula: (x - min) / (max - min)
  
  The subject says to display the other graph from ex02 — so we use the mixing plot (Pull vs Deflection) this time, since ex03 used
  the separating one.

The mixing plot will still look like a mess of overlapping dots — just rescaled to 0-1. That's the point: normalization changes
  the scale but can't create separation where there is none.

## ex05

python3 split.py Train_knight.csv

Split Train_knight.csv into two files: Training_knight.csv and Validation_knight.csv. You need to justify the split
  ratio.
  
  The standard split is 80% training / 20% validation. Why:
  - 80% gives the model enough data to learn from
  - 20% is enough to get a reliable estimate of how well it generalizes
  - It's the industry standard for datasets this size (~400 rows)

creates Training_knight.csv and Validation_knight.csv in the same folder, and prints the row counts so you can confirm the
  split. The stratify parameter is a nice extra — it ensures both files keep the same Jedi/Sith proportion as the original, which
  makes the validation set more representative.


----------------------------------------------------------


# Piscine DataScience - 4: Data Scientist 2

## ex00
  
  Confusion_Matrix.py predictions.txt truth.txt
  
  - Reads both files (one label per line)
  - Builds the 2×2 matrix manually: rows = actual, cols = predicted
  - Computes per-class precision, recall, f1-score, total — all by hand (just TP/FP/FN arithmetic)
  - Computes overall accuracy (diagonal sum / total)
  - Prints the report in the exact format the subject shows
  - Displays a seaborn heatmap

   You have 100 knights. Each one is either a Jedi or a Sith. You have:
  
  - truth.txt — what they actually are
  - predictions.txt — what your model guessed
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  The matrix
  
  For each knight, there are 4 possible outcomes:
  
  ┌───────────────┬──────────────────────────┬──────────────────────────┐
  │               │ Predicted Jedi           │ Predicted Sith           │
  ├───────────────┼──────────────────────────┼──────────────────────────┤
  │ Actually Jedi │ Got it right → 25        │ Said Sith, was Jedi → 24 │
  ├───────────────┼──────────────────────────┼──────────────────────────┤
  │ Actually Sith │ Said Jedi, was Sith → 30 │ Got it right → 21        │
  └───────────────┴──────────────────────────┴──────────────────────────┘
  
  So out of 49 actual Jedi, the model guessed correctly 25 times and was wrong 24 times.
  Out of 51 actual Sith, the model guessed correctly 21 times and was wrong 30 times.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  The metrics — in plain English
  
  Precision — "When you said Jedi, how often were you right?"
  
  - You predicted Jedi 55 times (25 + 30). You were right 25 times. → 25/55 = 0.45
  
  Recall — "Of all the real Jedi, how many did you catch?"
  
  - There are 49 real Jedi. You found 25 of them. → 25/49 = 0.51
  
  F1-score — a single score that balances precision and recall. 
  If both are good, F1 is good. If one is terrible, F1 suffers. 
  It's the average of the two, but weighted so that a bad one drags it down more.
  
  Accuracy — "Overall, how often were you right?"
  
  - You got 25 + 21 = 46 right out of 100. → 0.46
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  Why accuracy alone is misleading
  
  If 90% of your knights were Jedi, a model that always says "Jedi" would get 90% accuracy — but it would never catch a Sith. Precision and recall expose that. That's why we use all three.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  In the code
  
  The script computes all of this with basic arithmetic — no library doing the math for you. The only library used is seaborn to draw the coloured grid at the end.


## ex01

  Make a correlation heatmap between all features (including knight column)
  The heatmap should show 30 features + knight column on both axes, with a red color scale from -0.6 to 1.0.
  The subject heatmap includes knight encoded as a number. 

  31×31 correlation matrix (30 features + knight), and the top correlations with knight are Empowered, Prescience, Stims etc. — exactly what we saw back in DS3.

What is a correlation heatmap?
  
  You have 30 features per knight — things like Empowered, Stims, Deflection, etc. The question is: do any of these move together?
  
  For example: if every knight with a high Empowered score also tends to have a high Prescience score, those two features are correlated. If knowing one tells you nothing
  about the other, they're not correlated.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  The grid
  
  The heatmap is just a table — every feature on both the X and Y axes. Each cell shows how much those two features move together:
  
  - Dark red = strongly correlated — when one goes up, the other goes up too
  - Light pink = barely related — knowing one tells you nothing about the other
  - Very light / negative = opposite — when one goes up, the other goes down
  
  The diagonal is always dark red (a feature is perfectly correlated with itself).
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  Why include the knight column?
  
  knight is either Jedi or Sith, encoded as 0 or 1. By including it in the grid, the bottom row (and right column) shows which features are most useful for telling Jedi
  from Sith.
  
  Look at the bottom row in our heatmap — Empowered, Prescience, Stims, Recovery, Sprint are all very dark red. That means Jedi and Sith score very differently on those
  features → they're the most useful for classification.
  
  Deflection and Blocking are light pink in the knight row → Jedi and Sith score almost the same → useless for telling them apart.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  In one sentence:
  
  The heatmap is a cheat sheet that tells you at a glance which features are related to each other, and which features are actually useful for predicting Jedi vs Sith.

## ex02

  - Use PCA on the 30 features (not knight)
  - Print the variance of each component as a percentage
  - Print the cumulative variances
  - Print how many components needed to reach 90%
  - Display the cumulative variance curve (x = number of components, y = explained variance %)
  
  The hint says "rework your data with what you have seen in the previous module" — meaning standardize the data first (like DS3 ex03), otherwise PCA gives wrong results.

  The problem ex02 is solving
  
  You have 30 features per knight. That's a lot. Some of them carry almost the same information — for example, Empowered and Prescience are highly correlated (we saw that
  in the heatmap). So in a way, you don't really have 30 independent pieces of information — you have less.
  
  PCA asks: how many truly independent "directions" of information are there in this data?
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  What a "component" is
  
  Imagine your 30 features are like 30 different dials on a control panel. PCA finds combinations of those dials that together explain the most variation between knights.
  It calls those combinations "components".
  
  - Component 1 is the combination that explains the most difference between knights (~44%)
  - Component 2 explains the next most, on top of that (~18%)
  - Component 3 adds a bit more (~10%)
  - ...and so on until you've explained everything
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  What the numbers mean
  
  The first column printed is how much each component contributes on its own:
  
  - Component 1 → 44% of the variation
  - Component 2 → 18%
  - Component 3 → 10%
  - etc.
  
  The second column is the running total — add them up one by one:
  
  - After 1 component: 44%
  - After 2: 63%
  - After 7: 90% ← this is the answer
  
  So 7 components out of 30 capture 90% of everything interesting in your data. The remaining 23 components only add the last 10% and are mostly noise.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  The curve
  
  The graph shows that running total. It rises sharply at first (the first few components carry a lot) then flattens out (each extra component adds less and less). The
  point where it crosses 90% is where you'd stop if you wanted to simplify the data without losing too much.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  Why standardize first?
  
  Before running PCA, the script standardizes the data (like DS3 ex03). Without that, Power (which goes up to 1260) would completely dominate Agility (which goes up to
  0.14) just because of its bigger numbers — even if Agility is more informative. Standardizing puts every feature on the same scale so PCA treats them fairly.

## ex03

  - Use VIF (Variance Inflation Factor) to detect multicollinearity
  - Display VIF + Tolerance for all features
  - Then iteratively remove features until all VIFs are under 5, and display the surviving features

  Initial VIF shows Strength at 4489 and Sensitivity at 4367 — massively redundant. After filtering down to VIF < 5, we're left with 13 clean features out
  of 30.
  
  The subject example shows Empowered at 36.76, Stims at 405, Prescience at 60 — all visible in our initial output

  The problem ex03 is solving
  
  After the heatmap (ex01) we saw that many features are strongly correlated — Empowered and Prescience move together, Strength and Sensitivity move together, etc. When
  features are that similar, having both of them in your model is like asking two people who always agree with each other to vote — it doesn't add any new information, it
  just creates confusion.
  
  That's called multicollinearity — too many features saying basically the same thing.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  What VIF tells you
  
  VIF asks a simple question for each feature: "Can I predict this feature just by looking at the others?"
  
  If yes → it's redundant, you don't need it → high VIF
  If no → it brings unique information → low VIF
  
  Concretely:
  
  - Strength VIF = 4489 → almost perfectly predictable from the other features → totally redundant
  - Deflection VIF = 4.55 → can't be predicted well from the others → unique, keep it
  
  Tolerance is just 1/VIF — it says the same thing from the other direction. Low tolerance = redundant.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  The threshold of 5
  
  The rule of thumb is: VIF above 5 = too redundant, drop it.
  
  The script works like this:
  
  1. Calculate VIF for all 30 features
  2. Find the worst one (highest VIF)
  3. Drop it
  4. Recalculate VIF for the remaining features
  5. Repeat until everything is below 5
  
  We go from 30 features down to 13 — those 13 are the ones that each bring something unique to the table.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  Why does this matter?
  
  When you later train a model (like in ex04), feeding it 30 features where half of them are duplicates of each other makes it confused and slow. Feeding it 13 truly
  independent features gives it cleaner, more reliable signals to learn from.

## ex04

- Takes Train_knight.csv and Test_knight.csv as arguments
  - Uses Training_knight.csv and Validation_knight.csv from DS3 ex05 to train/validate
  - Must achieve ≥90% f1-score
  - Writes predictions to Tree.txt (one per line, Jedi/Sith)
  - Displays the decision tree as a graph
  
  I'll use Random Forest since it reliably hits 90%+ f1. The tree display will be one of the individual trees from the forest.

  - Random Forest with 100 trees, trained on Training_knight.csv from DS3 ex05
  - f1-score: 92.6% on validation set (well above the 90% minimum)
  - Writes Tree.txt with one prediction per line (Jedi/Sith)
  - Displays one tree from the forest as a graph

  The goal
  
  You have 30 features per knight and you want to predict whether each one is Jedi or Sith. That's a classification problem — you're sorting things into categories.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  What a Decision Tree does
  
  Imagine you're playing 20 questions to guess if a knight is Jedi or Sith:
  
  - "Is their Empowered score above 0.188?" → Yes → probably Sith
  - "Is their Recovery score above 14?" → No → probably Jedi
  - etc.
  
  Each question splits the knights into two groups. You keep asking questions until you're confident enough. That's a decision tree — a flowchart of yes/no questions.
  
  In the graph you can see exactly this: each box is a question, the left branch is "yes", the right branch is "no", and the blue boxes are Jedi, orange boxes are Sith.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  Why Random Forest instead of a single tree?
  
  A single tree can be too specific — it learns the training data perfectly but fails on new data (called overfitting). 
  
  A Random Forest builds 100 different trees, each trained on a slightly different random sample of the data. Then to make a prediction, all 100 trees vote, and the
  majority wins. It's much more reliable — like asking 100 experts instead of 1.
  
  That's why we get 92.6% f1-score instead of something lower.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  What f1-score means here
  
  The 90% minimum means: out of all your Jedi/Sith predictions, at least 90% need to be correct in a balanced way (not just "always say Jedi"). We get 92.6% — comfortably
  above the bar.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  What Tree.txt is
  
  The test file has 10 knights with no labels. The model predicts each one and writes the result — one line per knight, either Jedi or Sith. That's what gets evaluated.


## ex05

  - Takes Train_knight.csv and Test_knight.csv as arguments
  - Uses Training_knight.csv and Validation_knight.csv from DS3 ex05
  - Plot f1-score vs k values (1 to 30)
  - Pick the best k, write predictions to KNN.txt
  - Must achieve ≥92% f1-score
  - Hint: use standardization to help convergence

    The idea
  
  KNN stands for K-Nearest Neighbors. It's the simplest possible classifier — no training, no math, just memory.
  
  To predict whether a new knight is Jedi or Sith, it does this:
  
  1. Look at the K most similar knights in the training data
  2. See what most of them are
  3. Predict the same thing
  
  So if K=5 and the 5 most similar knights are: Jedi, Jedi, Sith, Jedi, Jedi → prediction is Jedi (4 vs 1).
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  What "similar" means
  
  Similarity is just distance — how close are two knights' feature values to each other? If your Empowered is 0.25 and mine is 0.24, we're very similar on that feature.
  
  That's why we standardize first — if you don't, Power (which goes up to 1260) would completely drown out Agility (which goes up to 0.14) in the distance calculation,
  even if Agility is more useful.
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  Why we try k=1 to 30
  
  You have to pick how many neighbors to consult. Too few (k=1) and you're overly influenced by one noisy neighbor. Too many (k=30) and you're averaging over knights that
  aren't really similar. The graph shows which k gives the best accuracy — in our case k=11 hits 100%.

## ex06

  - Voting classifier — combine 3 models: Decision Tree + Logistic Regression + KNN
  - Each model votes, majority wins
  - Must achieve ≥94% f1-score
  - Writes Voting.txt
  
  The idea
  
  You now have three models:
  
  - Decision Tree — asks yes/no questions to classify
  - Logistic Regression — draws a dividing line between Jedi and Sith
  - KNN — looks at nearest neighbors
  
  Each one makes its own prediction independently. Then you take a majority vote:
  
  - Decision Tree says: Jedi (1)
  - Logistic Regression says: Sith (0)
  - KNN says: Jedi (1)
  
  → 2 votes for Jedi → final prediction: Jedi
  
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  
  Why is this better than any single model?
  
  Each model has different weaknesses. The Decision Tree might struggle with certain patterns, Logistic Regression with others, KNN with others. But they rarely all fail
  on the same knight.
  
  By combining them, the mistakes of one get outvoted by the correct answers of the other two. That's why the f1-score goes up to 100% — the ensemble is more robust than
  any individual model.
  
  It's the same reason a jury of 3 judges makes better decisions than a single judge.
