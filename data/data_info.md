# olist_customers_dataset.csv ('customers')
- **Grain**: one row per customer *per order system entry*
- **Shape**: (99441, 5)
- **Approx Memory**: ~3.8 MB

## Keys and cardinalities
- **Candidate primary key**: `customer_id`
    - is_unique = True
    - num_unique = 99441
- **Alternative id**: `customer_unique_id`
    - num_unique = 96096

## Columns

| Column                    | Dtype  | Null % | #Distinct | Notes                                 |
|---------------------------|--------|--------|----------:|---------------------------------------|
| `customer_id`             | object | 0.0    |    99441  | Internal id for this dataset          |
| `customer_unique_id`      | object | 0.0    |    96096  | Stable customer id across orders      |
| `customer_zip_code_prefix`| int64  | 0.0    |    14994  | First digits of ZIP                   |
| `customer_city`           | object | 0.0    |    4119   | City name (Brazilian Portuguese)      |
| `customer_state`          | object | 0.0    |    27     | State abbreviation (SP, RJ, …)        |


- customers["customer_state"].value_counts().head()

| customer_state | count |
|----------------|------:|
| SP             | 41746 |
| RJ             | 12852 |
| MG             | 11635 |
| RS             |  5466 |
| PR             |  5045 |

- customers['customer_city'].value_counts().head()

| customer_city  | count |
|----------------|------:|
| sao paulo      | 15540 |
| rio de janeiro | 6882  |
| belo horizonte | 2773  |
| brasilia       | 2131  |
| curitiba       | 1521  |

## Notes 
- No missing values.  
- `customer_unique_id` will be useful for customer-level features (e.g. number of orders per person).
- For modeling, we’ll likely aggregate by `customer_unique_id`, not `customer_id`.
         

# olist_geolocation_dataset.csv ('geolocation')
A sample of raw latitude/longitude points grouped by ZIP code prefix, city and state.
- **Grain**: one row represents a point on the map
- **Shape**: (1000163, 5)
- **Approx Memory**: ~38.2 MB
     
## Keys and cardinalities
- No simple primary key: many fully duplicated rows.
- `geolocation_zip_code_prefix`:
    - `is_unique = False`
    - `num_unique = 19015`
    - Used as a key to link with customer/seller ZIP prefixes after aggregation.

## Columns

| Column                       | Dtype  | Null % | #Distinct | Notes                                 |
|------------------------------|--------|--------|----------:|---------------------------------------|
| `geolocation_zip_code_prefix`| int64  | 0.0    |    19015  | First digits of ZIP          |
| `geolocation_lat`            | float64| 0.0    |    717360 | Latitude      |
| `geolocation_lng`            | float64| 0.0    |    717613 | Longitude                   |
| `geolocation_city`           | object | 0.0    |    8011   | City name (Brazilian Portuguese)      |
| `geolocation_state`          | object | 0.0    |    27     | State abbreviation (SP, RJ, …)        |

- geolocation['geolocation_state'].value_counts()

| geolocation_state | count |
|----------------|------:|
| SP             | 404268 |
| MG             | 126336 |
| RJ             | 121169 |
| RS             |  61851 |
| PR             |  57859 |

- geolocation['geolocation_city'].value_counts().head()

| geolocation_city  | count |
|-------------------|------:|
| sao paulo         | 135800 |
| rio de janeiro    | 62151  |
| belo horizonte    | 27805  |
| são paulo         | 24918  |
| curitiba          | 16593  |
          
## Notes
- Both `customers` and `geolocation` cover **27 states**.
- City names are sometimes written differently (e.g. `sao paulo` vs `são paulo`), so we will:
  - normalize city names to lowercase and remove accents before comparison/join;
  - primarily rely on `*_zip_code_prefix` and state for geographic joins.
- `geolocation` has many more rows because it stores multiple coordinate points per ZIP prefix and city; for modeling we will aggregate to one row per ZIP prefix.


## olist_order_items_dataset.csv ('items')
dataset containing information about the items orders.
- **Grain**: one row per item line in an order
- **Shape**: (112650, 7)
- **Approx Memory**: ~6 MB
     
## Keys and cardinalities
- primary key (composite): (`order_id`, `order_item_id`)
- `order_id`:
    - `is_unique = False`
    - `num_unique = 98666`
- `order_item_id`:
    - `num_unique = 21`
    - line index within each order (starts at 1 for each order)
- `product_id`:
    - `num_unique = 32,951`
    - foreign key to `products` table


## Columns

| Column                       | Dtype  | Null % | #Distinct | Notes                                 |
|------------------------------|--------|--------|----------:|---------------------------------------|
| `order_id`                   | object | 0.0    |    98666  | ID indentifying orders                |
| `order_item_id`              | int64  | 0.0    |    21     | identifies the line number of the item in a given order  |
| `product_id`                 | object | 0.0    |    32951  | ID identifying the product sold       |
| `seller_id`                  | object | 0.0    |    3095   | ID of the seller                      |
| `shipping_limit_date`        | object | 0.0    |    93318  | shipping deadline (yyyy-mm-dd HH:MM:SS) |
| `price`                      | float64| 0.0    |    5968   | price of item sold in R$              |
| `freight_value`              | float64| 0.0    |    6999   | shipment cost                         |

## Notes
- Multiple rows share the same `order_id`: one per item line
- The composite key (`order_id`, `order_item_id`) uniquely identifies an item line within this table
- Across tables (e.g. joining with `orders`, `reviews`, `payments`), we will link on `order_id` only (order-level key)
- We will convert `shipping_limit_date` to a proper datetime when loading into our modeling/ETL pipeline
- Aggregating `price` and `freight_value` over all items in an order gives total order revenue and shipping cost

