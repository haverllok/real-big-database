# Real big database

A large, e-commerce dataset for practicing SQL on real volume:
query optimization, indexing, `EXPLAIN`/`EXPLAIN ANALYZE`, and general
"working with millions of rows" skills. Ships as ready-to-import SQL dumps
for **PostgreSQL and MySQL**

## What's inside

An e-commerce schema: customers, addresses, categories, suppliers,
products, orders, order items, payments, shipments, reviews, coupons.

| Table | Rows (approx.) |
|---|---|
| orders | 800,000 |
| order_items | 2,120,000 |
| payments | 800,000 |
| shipments | 600,000 |
| reviews | 300,000 |
| addresses | 260,000 |
| customers | 200,000 |
| products | 30,000 |
| suppliers | 300 |
| coupons | 300 |
| categories | 60 |
| **Total** | **~5.1 million rows** |

**Foreign keys are present**, but the schema intentionally ships **without
any secondary indexes** — only what a `PRIMARY KEY` gives you (and, on
MySQL, the index InnoDB auto-creates for each `FOREIGN KEY`, which is
unavoidable there). This is on purpose: run a few realistic queries first,
watch them do a full table scan on millions of rows, then design your own
indexes. `schema/<dialect>/indexes_solution.sql` has a reference answer —
try not to peek until you've made an attempt.

## Getting the data

Generated dumps (`.sql.gz`) are published as
[GitHub Releases](../../releases) for this repo rather than committed to
git, so the repository itself stays small. Download the archive for your
database engine and gunzip it.

## Importing

**PostgreSQL:**
```bash
gunzip -k dump_postgresql.sql.gz
createdb rbd
psql -d rbd -f dump_postgresql.sql
```

**MySQL:**
```bash
gunzip -k dump_mysql.sql.gz
mysql -u root -p -e "CREATE DATABASE rbd"
mysql -u root -p rbd < dump_mysql.sql
```

Importing ~5.1 million rows takes roughly 1 minute on a typical laptop.

## Practicing optimization

1. Run a few realistic queries against the fresh import and time them, e.g.:
   ```sql
   SELECT * FROM orders WHERE status = 'delivered';
   SELECT o.* FROM orders o WHERE o.customer_id = 12345;
   SELECT c.first_name, c.last_name, count(*) FROM orders o
     JOIN customers c ON c.id = o.customer_id
     GROUP BY c.id, c.first_name, c.last_name
     ORDER BY count(*) DESC LIMIT 10;
   ```
2. Prefix them with `EXPLAIN ANALYZE` (PostgreSQL) or `EXPLAIN ANALYZE` /
   `EXPLAIN FORMAT=JSON` (MySQL 8) to see the sequential/full table scans.
3. Design and add your own indexes, re-run the same queries, and compare.
4. Check your answer against `schema/<dialect>/indexes_solution.sql`.

Other things worth trying on this dataset: partitioning `orders` by date,
covering indexes for the top-N-customers report, pagination with
`OFFSET` vs. keyset pagination on `order_items`, materialized views for
sales aggregates, and query rewriting for the `JSON`/`JSONB` `attributes`
column on `products`.

## Regenerating / making your own size

The dump is produced by a dependency-free Python 3 script. The same data
is written once and shared between both dialects — only the `CREATE
TABLE` statements differ, everything else is byte-for-byte identical.

```bash
python3 generator/generate.py --scale small   # a few thousand rows, fast, for testing
python3 generator/generate.py --scale full    # the ~5.1M row dataset described above
python3 generator/generate.py --scale full --seed 7   # different random data, same shape
```

Output goes to `dist/`: `dist/dump_postgresql.sql.gz` and
`dist/dump_mysql.sql.gz`, plus the intermediate per-table fragments under
`dist/data/`. `dist/` is git-ignored — it's a build output, not something
to commit.

Row counts per scale are defined in `SCALES` at the top of
`generator/generate.py` if you want to tune the dataset shape yourself.

## Repository layout

```
schema/postgresql/schema.sql            CREATE TABLE statements (PostgreSQL)
schema/postgresql/indexes_solution.sql  reference indexes to add as an exercise
schema/mysql/schema.sql                 CREATE TABLE statements (MySQL)
schema/mysql/indexes_solution.sql       reference indexes to add as an exercise
generator/generate.py                   the data generator
dist/                                   build output (git-ignored)
```
