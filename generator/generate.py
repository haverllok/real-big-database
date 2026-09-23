#!/usr/bin/env python3
"""
Generate the "Real Big Database" sample e-commerce dataset.

Data is generated ONCE and is byte-for-byte identical between the MySQL
and PostgreSQL dumps — only schema/{mysql,postgresql}/schema.sql differ
between dialects. This works because both dialects accept the exact same
literal syntax for every type used here (strings, numbers, TRUE/FALSE,
JSON text) as long as we never emit a backslash inside a string literal.

Usage:
    python3 generator/generate.py --scale small
    python3 generator/generate.py --scale full --seed 42

Output:
    dist/data/<table>.sql       shared INSERT fragments (one per table)
    dist/dump_postgresql.sql.gz  schema + data, gzipped
    dist/dump_mysql.sql.gz       schema + data, gzipped
"""
import argparse
import gzip
import json
import random
import shutil
import string
from array import array
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCH_SIZE = 1000
EPOCH_START = datetime(2019, 1, 1)
NOW = datetime(2026, 9, 23)

TABLE_ORDER = [
    "categories", "suppliers", "products", "customers", "addresses",
    "coupons", "orders", "order_items", "payments", "shipments", "reviews",
]

SCALES = {
    "tiny": dict(categories=12, suppliers=8, products=80, customers=200,
                 orders=400, reviews=200, coupons=10),
    "small": dict(categories=30, suppliers=60, products=3000, customers=8000,
                  orders=25000, reviews=10000, coupons=60),
    "full": dict(categories=60, suppliers=300, products=30000, customers=200000,
                 orders=800000, reviews=300000, coupons=300),
}

# --------------------------------------------------------------------------
# Word lists
# --------------------------------------------------------------------------
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
    "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Daniel",
    "Nancy", "Matthew", "Lisa", "Anthony", "Margaret", "Mark", "Betty",
    "Donald", "Sandra", "Steven", "Ashley", "Andrew", "Dorothy", "Paul",
    "Kimberly", "Joshua", "Emily", "Kenneth", "Donna", "Kevin", "Michelle",
    "Brian", "Carol", "George", "Amanda", "Edward", "Melissa", "Ronald",
    "Deborah", "Timothy", "Stephanie", "Jason", "Rebecca", "Jeffrey", "Laura",
    "Ryan", "Sharon", "Jacob", "Cynthia", "Gary", "Kathleen", "Nicholas",
    "Amy", "Eric", "Angela", "Jonathan", "Shirley", "Stephen", "Anna",
    "Larry", "Brenda", "Justin", "Pamela", "Scott", "Emma", "Brandon", "Nicole",
    "Oksana", "Ivan", "Olena", "Andriy", "Kateryna", "Mykola", "Iryna",
    "Taras", "Sofia", "Petro", "Hanna", "Yuriy", "Mariia", "Bohdan",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Melnyk", "Shevchenko", "Kovalenko", "Bondarenko",
    "Tkachenko", "Kravchenko", "Kovalchuk", "Oliynyk", "Shevchuk", "Boyko",
]
CITIES = [
    ("New York", "NY", "USA"), ("Los Angeles", "CA", "USA"),
    ("Chicago", "IL", "USA"), ("Houston", "TX", "USA"),
    ("Phoenix", "AZ", "USA"), ("Philadelphia", "PA", "USA"),
    ("San Antonio", "TX", "USA"), ("San Diego", "CA", "USA"),
    ("Dallas", "TX", "USA"), ("Austin", "TX", "USA"),
    ("Seattle", "WA", "USA"), ("Denver", "CO", "USA"),
    ("Boston", "MA", "USA"), ("Miami", "FL", "USA"),
    ("Atlanta", "GA", "USA"), ("Portland", "OR", "USA"),
    ("Toronto", "ON", "Canada"), ("Vancouver", "BC", "Canada"),
    ("Montreal", "QC", "Canada"), ("Ottawa", "ON", "Canada"),
    ("London", "England", "UK"), ("Manchester", "England", "UK"),
    ("Birmingham", "England", "UK"), ("Edinburgh", "Scotland", "UK"),
    ("Berlin", "Berlin", "Germany"), ("Munich", "Bavaria", "Germany"),
    ("Hamburg", "Hamburg", "Germany"), ("Frankfurt", "Hesse", "Germany"),
    ("Paris", "Ile-de-France", "France"), ("Lyon", "Auvergne-Rhone-Alpes", "France"),
    ("Madrid", "Madrid", "Spain"), ("Barcelona", "Catalonia", "Spain"),
    ("Rome", "Lazio", "Italy"), ("Milan", "Lombardy", "Italy"),
    ("Warsaw", "Masovian", "Poland"), ("Krakow", "Lesser Poland", "Poland"),
    ("Kyiv", "Kyiv Oblast", "Ukraine"), ("Lviv", "Lviv Oblast", "Ukraine"),
    ("Kharkiv", "Kharkiv Oblast", "Ukraine"), ("Odesa", "Odesa Oblast", "Ukraine"),
    ("Amsterdam", "North Holland", "Netherlands"), ("Vienna", "Vienna", "Austria"),
    ("Stockholm", "Stockholm", "Sweden"), ("Oslo", "Oslo", "Norway"),
    ("Dublin", "Leinster", "Ireland"), ("Lisbon", "Lisbon", "Portugal"),
    ("Sydney", "NSW", "Australia"), ("Melbourne", "VIC", "Australia"),
    ("Tokyo", "Tokyo", "Japan"), ("Osaka", "Osaka", "Japan"),
]
STREET_NAMES = [
    "Main St", "Oak Ave", "Maple Dr", "Cedar Ln", "Elm St", "Park Ave",
    "Washington St", "Lake View Rd", "Sunset Blvd", "River Rd", "Hill St",
    "Church St", "High St", "Station Rd", "Mill Ln", "Spring St",
    "Pine St", "Birch Rd", "Willow Way", "Meadow Ln",
]
CATEGORY_TOP = [
    "Electronics", "Home & Kitchen", "Sports & Outdoors", "Books",
    "Toys & Games", "Health & Beauty", "Automotive", "Garden & Tools",
    "Fashion", "Pet Supplies", "Office Products", "Grocery",
    "Music & Movies", "Baby", "Jewelry",
]
CATEGORY_SUB_WORDS = [
    "Accessories", "Parts", "Equipment", "Supplies", "Tools", "Gear",
    "Essentials", "Kits", "Bundles", "Basics",
]
ADJECTIVES = [
    "Premium", "Compact", "Wireless", "Portable", "Ergonomic", "Classic",
    "Rustic", "Modern", "Heavy-Duty", "Lightweight", "Adjustable",
    "Rechargeable", "Waterproof", "Stainless", "Organic", "Handmade",
    "Vintage", "Smart", "Deluxe", "Eco-Friendly", "Foldable", "Insulated",
]
NOUNS = [
    "Backpack", "Blender", "Headphones", "Desk Lamp", "Water Bottle",
    "Office Chair", "Coffee Maker", "Yoga Mat", "Bluetooth Speaker",
    "Sneakers", "Sunglasses", "Notebook", "Garden Hose", "Tool Set",
    "Phone Case", "Keyboard", "Mouse", "Backyard Grill", "Pet Bed",
    "Vacuum Cleaner", "Air Fryer", "Board Game", "Puzzle", "Wall Clock",
    "Picture Frame", "Sofa Cushion", "Bath Towel", "Running Shorts",
    "Winter Jacket", "Baseball Cap",
]
COLORS = ["Black", "White", "Red", "Blue", "Green", "Gray", "Beige", "Navy", "Silver", "Gold"]
SIZES = ["XS", "S", "M", "L", "XL", "One Size"]
SUPPLIER_WORDS = [
    "Northwind", "Globex", "Initech", "Umbrella", "Stark", "Wayne",
    "Acme", "Hooli", "Soylent", "Vandelay", "Cyberdyne", "Massive Dynamic",
    "Aperture", "Wonka", "Gekko", "Prestige", "Blue Sun", "Tyrell",
    "Oscorp", "Sterling",
]
SUPPLIER_SUFFIXES = ["Trading Co.", "Industries", "Supply Co.", "Group", "Wholesale", "Imports", "Manufacturing"]
CARRIERS = ["FedEx", "UPS", "DHL", "USPS", "Nova Post", "DPD"]
PAYMENT_METHODS = ["credit_card", "paypal", "debit_card", "bank_transfer", "cash_on_delivery"]
ORDER_STATUSES = ["delivered", "shipped", "processing", "pending", "cancelled", "returned"]
ORDER_STATUS_WEIGHTS = [0.55, 0.15, 0.10, 0.07, 0.08, 0.05]
REVIEW_TITLES = [
    "Great value", "Not what I expected", "Exceeded expectations", "Would buy again",
    "Broke after a week", "Exactly as described", "Highly recommend", "Mediocre quality",
    "Perfect gift", "Fast shipping, happy customer", "Could be better", "Love it!",
]
REVIEW_SNIPPETS = [
    "The build quality feels solid for the price.",
    "Shipping took longer than expected but the item was well packaged.",
    "Works exactly as advertised, no complaints.",
    "Color was slightly different from the photos.",
    "Customer support was helpful when I had a question.",
    "This is my second time ordering this item.",
    "A bit pricier than similar products but worth it.",
    "Instructions could be clearer.",
    "Perfect size and fits well.",
    "Would recommend to a friend.",
    "Battery life is better than I hoped.",
    "Packaging was damaged but the product was fine.",
]
EMAIL_DOMAINS = ["example.com", "mail-test.com", "sample-inbox.net", "webmail-demo.org"]


def esc(s) -> str:
    return str(s).replace("'", "''")


def q(s) -> str:
    return "'" + esc(s) + "'"


def b(flag: bool) -> str:
    return "TRUE" if flag else "FALSE"


def dt(value: datetime) -> str:
    return "'" + value.strftime("%Y-%m-%d %H:%M:%S") + "'"


def d(value: datetime) -> str:
    return "'" + value.strftime("%Y-%m-%d") + "'"


def rand_dt(rng: random.Random, start: datetime, end: datetime) -> datetime:
    span = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, span))


def weighted(rng: random.Random, population, weights):
    return rng.choices(population, weights=weights, k=1)[0]


def slugify(text: str) -> str:
    return text.lower().replace(" & ", "-").replace(" ", "-").replace("--", "-")


class TableWriter:
    def __init__(self, path: Path, table: str, columns: list[str]):
        self.f = open(path, "w", buffering=1024 * 1024)
        self.prefix = f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n"
        self.buffer = []

    def add(self, *values):
        self.buffer.append("(" + ", ".join(values) + ")")
        if len(self.buffer) >= BATCH_SIZE:
            self.flush()

    def flush(self):
        if not self.buffer:
            return
        self.f.write(self.prefix)
        self.f.write(",\n".join(self.buffer))
        self.f.write(";\n")
        self.buffer = []

    def close(self):
        self.flush()
        self.f.close()


def generate(scale: str, seed: int, outdir: Path):
    rng = random.Random(seed)
    counts = SCALES[scale]
    data_dir = outdir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    def writer(table, columns):
        return TableWriter(data_dir / f"{table}.sql", table, columns)

    # ---------------------------------------------------------- categories
    n_categories = counts["categories"]
    w = writer("categories", ["id", "name", "parent_id", "slug", "created_at"])
    category_names = {}
    top_n = min(len(CATEGORY_TOP), n_categories)
    for cid in range(1, n_categories + 1):
        if cid <= top_n:
            name = CATEGORY_TOP[cid - 1]
            parent_id = None
        else:
            parent_id = rng.randint(1, cid - 1)
            name = f"{category_names[parent_id]} {rng.choice(CATEGORY_SUB_WORDS)}"
        category_names[cid] = name
        created = rand_dt(rng, EPOCH_START, NOW)
        w.add(str(cid), q(name), str(parent_id) if parent_id else "NULL",
              q(slugify(name) + f"-{cid}"), dt(created))
    w.close()

    # ----------------------------------------------------------- suppliers
    n_suppliers = counts["suppliers"]
    w = writer("suppliers", ["id", "name", "country", "contact_email", "created_at"])
    for sid in range(1, n_suppliers + 1):
        name = f"{rng.choice(SUPPLIER_WORDS)} {rng.choice(SUPPLIER_SUFFIXES)}"
        country = rng.choice(CITIES)[2]
        email = f"contact{sid}@{slugify(name).replace('.', '')}.com"
        created = rand_dt(rng, EPOCH_START, NOW)
        w.add(str(sid), q(name), q(country), q(email), dt(created))
    w.close()

    # ------------------------------------------------------------ products
    n_products = counts["products"]
    product_price = array("d", [0.0] * n_products)
    w = writer("products", [
        "id", "sku", "name", "description", "category_id", "supplier_id",
        "price", "weight_kg", "is_active", "attributes", "created_at",
    ])
    for pid in range(1, n_products + 1):
        adj = rng.choice(ADJECTIVES)
        noun = rng.choice(NOUNS)
        name = f"{adj} {noun}"
        description = (f"{adj} {noun.lower()} designed for everyday use. "
                        f"Durable materials, reliable performance, and a design "
                        f"that fits any {rng.choice(['home', 'office', 'outdoor trip', 'gym bag'])}.")
        category_id = rng.randint(1, n_categories)
        supplier_id = rng.randint(1, n_suppliers)
        price = round(rng.uniform(4.99, 999.99), 2)
        product_price[pid - 1] = price
        weight = round(rng.uniform(0.05, 25.0), 3)
        is_active = rng.random() < 0.92
        attrs = json.dumps({"color": rng.choice(COLORS), "size": rng.choice(SIZES)})
        created = rand_dt(rng, EPOCH_START, NOW)
        w.add(str(pid), q(f"SKU-{pid:07d}"), q(name), q(description),
              str(category_id), str(supplier_id), f"{price:.2f}", f"{weight:.3f}",
              b(is_active), q(attrs), dt(created))
    w.close()

    # ----------------------------------------------------------- customers
    n_customers = counts["customers"]
    w = writer("customers", [
        "id", "first_name", "last_name", "email", "phone", "is_active", "created_at",
    ])
    for cid in range(1, n_customers + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        domain = rng.choice(EMAIL_DOMAINS)
        email = f"{first.lower()}.{last.lower()}{cid}@{domain}"
        phone = f"+1-{rng.randint(200,999)}-{rng.randint(200,999)}-{rng.randint(1000,9999)}"
        is_active = rng.random() < 0.95
        created = rand_dt(rng, EPOCH_START, NOW)
        w.add(str(cid), q(first), q(last), q(email), q(phone), b(is_active), dt(created))
    w.close()

    # ----------------------------------------------------------- addresses
    address_start = array("i", [0] * n_customers)
    address_count = array("i", [0] * n_customers)
    w = writer("addresses", [
        "id", "customer_id", "line1", "line2", "city", "state",
        "postal_code", "country", "is_default",
    ])
    next_address_id = 1
    for idx in range(n_customers):
        customer_id = idx + 1
        count = 2 if rng.random() < 0.3 else 1
        address_start[idx] = next_address_id
        address_count[idx] = count
        for k in range(count):
            city, state, country = rng.choice(CITIES)
            line1 = f"{rng.randint(1, 9999)} {rng.choice(STREET_NAMES)}"
            line2 = f"Apt {rng.randint(1, 400)}" if rng.random() < 0.3 else None
            postal = f"{rng.randint(10000, 99999)}"
            w.add(str(next_address_id), str(customer_id), q(line1),
                  q(line2) if line2 else "NULL", q(city), q(state), q(postal),
                  q(country), b(k == 0))
            next_address_id += 1
    w.close()

    # ------------------------------------------------------------- coupons
    n_coupons = counts["coupons"]
    w = writer("coupons", [
        "id", "code", "discount_percent", "valid_from", "valid_to", "max_uses", "times_used",
    ])
    letters = string.ascii_uppercase
    for cid in range(1, n_coupons + 1):
        percent = rng.choice([5, 10, 15, 20, 25, 30])
        code = f"SAVE{percent}-{''.join(rng.choices(letters, k=5))}"
        valid_from = rand_dt(rng, EPOCH_START, NOW - timedelta(days=30))
        valid_to = valid_from + timedelta(days=rng.randint(30, 365))
        max_uses = rng.randint(50, 5000)
        times_used = rng.randint(0, max_uses)
        w.add(str(cid), q(code), f"{percent:.2f}", d(valid_from), d(valid_to),
              str(max_uses), str(times_used))
    w.close()

    # ------------------------------------- orders + order_items + payments + shipments
    n_orders = counts["orders"]
    ow = writer("orders", [
        "id", "customer_id", "address_id", "status", "order_date", "total_amount", "created_at",
    ])
    iw = writer("order_items", [
        "id", "order_id", "product_id", "quantity", "unit_price", "discount_amount",
    ])
    pw = writer("payments", ["id", "order_id", "payment_method", "amount", "status", "paid_at"])
    sw = writer("shipments", [
        "id", "order_id", "carrier", "tracking_number", "status", "shipped_at", "delivered_at",
    ])

    item_id = 1
    shipment_id = 1
    items_weights = [0.2, 0.3, 0.25, 0.15, 0.1]
    qty_weights = [0.6, 0.3, 0.1]

    for order_id in range(1, n_orders + 1):
        customer_id = rng.randint(1, n_customers)
        idx = customer_id - 1
        addr_id = address_start[idx] + rng.randint(0, address_count[idx] - 1)
        status = weighted(rng, ORDER_STATUSES, ORDER_STATUS_WEIGHTS)
        order_date = rand_dt(rng, EPOCH_START, NOW)

        n_items = weighted(rng, [1, 2, 3, 4, 5], items_weights)
        total = 0.0
        for _ in range(n_items):
            product_id = rng.randint(1, n_products)
            base_price = product_price[product_id - 1]
            unit_price = round(base_price * rng.uniform(0.9, 1.05), 2)
            quantity = weighted(rng, [1, 2, 3], qty_weights)
            discount = round(unit_price * quantity * rng.choice([0, 0, 0, 0, 0.05, 0.1]), 2)
            total += unit_price * quantity - discount
            iw.add(str(item_id), str(order_id), str(product_id), str(quantity),
                   f"{unit_price:.2f}", f"{discount:.2f}")
            item_id += 1
        total = round(total, 2)
        ow.add(str(order_id), str(customer_id), str(addr_id), q(status),
               dt(order_date), f"{total:.2f}", dt(order_date))

        if status in ("delivered", "shipped"):
            pay_status = "completed"
        elif status == "returned":
            pay_status = "refunded"
        elif status == "cancelled":
            pay_status = rng.choice(["failed", "refunded"])
        else:
            pay_status = "pending"
        method = weighted(rng, PAYMENT_METHODS, [0.45, 0.25, 0.15, 0.10, 0.05])
        paid_at = order_date + timedelta(minutes=rng.randint(1, 120))
        pw.add(str(order_id), str(order_id), q(method), f"{total:.2f}", q(pay_status), dt(paid_at))

        if status in ("shipped", "delivered", "returned"):
            shipped_at = order_date + timedelta(days=rng.randint(1, 3))
            if status in ("delivered", "returned"):
                delivered_at = shipped_at + timedelta(days=rng.randint(1, 7))
                ship_status = "returned" if status == "returned" else "delivered"
            else:
                delivered_at = None
                ship_status = "in_transit"
            tracking = "".join(rng.choices(string.ascii_uppercase + string.digits, k=12))
            sw.add(str(shipment_id), str(order_id), q(rng.choice(CARRIERS)), q(tracking),
                   q(ship_status), dt(shipped_at),
                   dt(delivered_at) if delivered_at else "NULL")
            shipment_id += 1

    ow.close()
    iw.close()
    pw.close()
    sw.close()

    # ------------------------------------------------------------- reviews
    n_reviews = counts["reviews"]
    w = writer("reviews", [
        "id", "product_id", "customer_id", "rating", "title", "body", "created_at",
    ])
    rating_weights = [0.45, 0.25, 0.15, 0.08, 0.07]
    for rid in range(1, n_reviews + 1):
        product_id = rng.randint(1, n_products)
        customer_id = rng.randint(1, n_customers)
        rating = weighted(rng, [5, 4, 3, 2, 1], rating_weights)
        title = rng.choice(REVIEW_TITLES)
        body = " ".join(rng.sample(REVIEW_SNIPPETS, k=3))
        created = rand_dt(rng, EPOCH_START, NOW)
        w.add(str(rid), str(product_id), str(customer_id), str(rating), q(title), q(body), dt(created))
    w.close()

    return {t: counts.get(t) for t in TABLE_ORDER}


def build_dump(dialect: str, outdir: Path):
    schema_path = ROOT / "schema" / dialect / "schema.sql"
    data_dir = outdir / "data"
    dump_path = outdir / f"dump_{dialect}.sql.gz"
    with gzip.open(dump_path, "wt", encoding="utf-8") as out:
        out.write(schema_path.read_text(encoding="utf-8"))
        out.write("\n")
        for table in TABLE_ORDER:
            frag = data_dir / f"{table}.sql"
            out.write(f"-- {table}\n")
            with open(frag, "r", encoding="utf-8") as f:
                shutil.copyfileobj(f, out)
            out.write("\n")
    return dump_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scale", choices=SCALES.keys(), default="small")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", type=Path, default=ROOT / "dist")
    parser.add_argument("--skip-build", action="store_true",
                         help="only generate data fragments, don't assemble gzipped dumps")
    args = parser.parse_args()

    t0 = datetime.now()
    print(f"Generating scale={args.scale} seed={args.seed} ...")
    counts = generate(args.scale, args.seed, args.outdir)
    print(f"Data fragments written in {(datetime.now() - t0).total_seconds():.1f}s")
    for table, n in counts.items():
        print(f"  {table}: ~{n}")

    if not args.skip_build:
        for dialect in ("postgresql", "mysql"):
            t1 = datetime.now()
            path = build_dump(dialect, args.outdir)
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"Built {path} ({size_mb:.1f} MB) in {(datetime.now() - t1).total_seconds():.1f}s")


if __name__ == "__main__":
    main()