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


# Piscine DataScience - 2 : Data Warehouse
## ex02


----------------------------------------------------------


# Piscine DataScience - 3 : Data Viz

The tool stack of my choice: Python with pandas + matplotlib/seaborn + scikit-learn — it covers everything from simple charts to clustering and runs identically on Mac and Linux:

  - pandas — reads from PostgreSQL, handles all the data manipulation
  - matplotlib/seaborn — pie charts, bar charts, box plots, all of ex00-03
  - scikit-learn — elbow method and K-means for ex04-05
  - Runs identically on Mac and school Linux
  - No Jupyter needed — plain .py files are cleaner to submit and run during eval

we use sqlalchemy to connect pandas directly to PostgreSQL with pd.read_sql(), 
which is cleaner than psycopg2 for read-only queries.

## ex00 pie.* — Pie chart of event types (view, cart, purchase…) from the customers table

  a pie chart showing what people do on the site — that's the breakdown of event_type values (view, cart, purchase,
  remove_from_cart) from the customers table.

## ex01 chart.* — 3 charts of purchase data from Oct 2022 to Feb 2023
  1. Line chart — Number of customers per day (Oct–Jan, without Feb in the example but we add it)
  2. Bar chart — Total sales per month in millions of A$
  3. Area chart — Average spend per customer per day (filled area, not just a line)

## ex02 mustache.* — Statistical summary (mean, median, quartiles) + box plots of purchase prices
  1. Horizontal box plot of all purchase prices — shows the full range including outliers/negatives (the squashed one going from -50
  to 325)
  2. Horizontal box plot of individual item prices — zoomed in, green, range 0-13 (this is the same data without extreme outliers,
  or the IQR view)
  3. Horizontal box plot of average basket per customer — blue, range 28-42
  
  Plus the stats printout from the subject:
  
  count  741644
  mean   5.57
  std    10.26
  min   -79.37
  25%    1.59
  50%    3.33
  75%    6.03
  max  327.78

  Three windows open one after the other, stats printed in the terminal. Close each window to proceed to the next.

## ex03 Building.* — Bar charts: number of orders by frequency, and spend by customer
  Two bar charts side by side:
  
  1. Left — number of customers by purchase frequency (how many times they bought), x-axis is frequency (0-35), y-axis is customers
  2. Right — number of customers by monetary value spent (total spend in A$), x-axis is monetary value, y-axis is customers

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

  Three windows one after the other. The terminal will also print the cluster medians so you can see exactly what profile each group has 

  The medians are the raw cluster output before we assigned names. They tell the same story but without labels — They help us to
  decide which name fits which cluster:
  
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

# Piscine DataScience - 4: Data Scientist 1

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