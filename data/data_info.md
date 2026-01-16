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
         
---

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

---

# olist_order_items_dataset.csv ('items')
dataset containing information about the items orders
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
| `order_id`                   | object | 0.0    |    98666  | ID identifying orders                |
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

---

# olist_order_payments_dataset.csv ('payments')
dataset containing information about orders payments
- **Grain**: One row per payment event for an order
- **Shape**: (103886, 5)
- **Approx Memory**: ~4 MB
     
## Keys and cardinalities
- primary key (composite): (`order_id`, `payment_sequential`)
- `order_id`:
    - `is_unique = False`
    - `num_unique = 99440`
- `payment_sequential`:
    - `num_unique = 29`
    - sequence number of the payment record within the order (1, 2, …)

## Columns

| Column                       | Dtype  | Null % | #Distinct | Notes                                 |
|------------------------------|--------|--------|----------:|---------------------------------------|
| `order_id`                   | object | 0.0    |    99440  | ID indentifying orders                |
| `payment_sequential`         | int64  | 0.0    |    29     | sequence of this payment record for the order (1 = first payment, …)  |
| `payment_type`               | object | 0.0    |    5      | category identifying the payment method (credit_card, voucher, ...) |
| `payment_installments`       | int64  | 0.0    |    24     | number of installments for this payment |
| `payment_value`              | float64| 0.0    |    29077  | amount payed in R$                    |

- payment_type distribution

| payment_type | count |
|--------------|------:|
| credit_card  | 76795 |
| boleto       | 19784 |
| voucher      | 5775  |
| debit_card   | 1529  |
| not_defined  | 3      |

## Notes
- Most orders have `payment_sequential = 1` only; some have multiple payment rows (split payments)
- Total amount paid per order is obtained by summing `payment_value` over all rows with the same `order_id`
- `payment_installments` is the number of installments for a given payment, **not** the count of payment rows
- This table will be joined with `orders` using `order_id` and typically aggregated to the order level in the ETL
- `payment_type = "not_defined"` appears very rarely (3 rows)

---

# olist_order_reviews_dataset.csv ('reviews')
dataset containing reviews information on orders
- **Grain (intended)**: one review per order
- **Grain (observed)**: one review record per row; some `review_id` and `order_id` appear more than once due to duplicated records in the public dataset
- **Shape**: (99224, 7)
- **Approx Memory**: ~5.3 MB

## Keys and cardinalities
- No clean primary key in the raw data:
  - `review_id` is intended to be a unique review identifier but appears duplicated
  - The pair (`order_id`, `review_id`) is candidate key (no duplicates)
- `order_id`:
    - `is_unique = False`
    - `num_unique = 98673`
- `review_id`:
    - `is_unique = False`
    - `num_unique = 98410`

## Columns

| Column                       | Dtype  | Null % | #Distinct | Notes                                 |
|------------------------------|--------|--------|----------:|---------------------------------------|
| `review_id`                  | object | 0.0    |    98410  | ID indentifying reviews               |
| `order_id`                   | object | 0.0    |    98673  | ID identifying orders                 |
| `review_score`               | int64  | 0.0    |    5      | review score 1 - 5                    |
| `review_comment_title`       | object | 88.3   |    4527   | review's title                        |
| `review_comment_message`     | object | 58.7   |    36159  | review's comment message              |
| `review_creation_date`       | object | 0.0    |    636    | review's date (yyyy-mm-dd 00:00:00)   |
| `review_answer_timestamp`    | object | 0.0    |    98248  | review's answer timestamp (yyyy-mm-dd HH:MM:SS) |

- review_score distribution

| review_score | count |
|--------------|------:|
| 5            | 57328 |
| 4            | 19142 |
| 1            | 11424 |
| 3            | 8179  |
| 2            | 3151  |

## Notes
- Some `review_id` values are associated with more than one `order_id`, with all other fields identical:
  - we will treat these as duplicated records and define a cleaning rule
    (e.g. keep a single record per `review_id` or per `order_id`)
- Many reviews have no text:
  - `review_comment_title` is missing for ~88% of rows
  - `review_comment_message` is missing for ~59% of rows
  - For NLP tasks we will likely filter to rows with non-null `review_comment_message`
- `review_creation_date` and `review_answer_timestamp` will be converted to proper datetime columns
- Review scores are skewed positive (most are 4–5), which matters for modeling (class imbalance)

---

# olist_orders_dataset.csv ('orders')
dataset containing orders informations (status, delivery time, client,...)
- **Grain**: one row per order id
- **Shape**: (99441, 8)
- **Approx Memory**: ~6.1 MB

## Keys and cardinalities
- primary key: `order_id`
- `order_id`:
    - `is_unique = True`
    - `num_unique = 99441`
- `customer_id`:
    - `is_unique = True`
    - `num_unique = 99441`
    - foreign key to `customers` table

## Columns

| Column                       | Dtype  | Null % | #Distinct | Notes                                 |
|------------------------------|--------|--------|----------:|---------------------------------------|
| `order_id`                   | object | 0.0    |    99441  | ID identifying an order               |
| `customer_id`                | object | 0.0    |    99441  | ID identifying a customer             |
| `order_status`               | object | 0.0    |    8      | order status (delivered, invoiced, canceled, ...) |
| `order_purchase_timestamp`   | object | 0.0    |    98875  | purchase timestamp (yyyy-mm-dd HH:MM:SS) |
| `order_approved_at`          | object | 0.16   |    90733  | approving timestamp (yyyy-mm-dd HH:MM:SS) |
| `order_delivered_carrier_date` | object | 1.8  |    81018  | timestamp of delivering for shipment (yyyy-mm-dd HH:MM:SS) |
| `order_delivered_customer_date`| object | 2.98 |    95664  | delivery timestamp (yyyy-mm-dd HH:MM:SS) |
| `order_estimated_delivery_date`| object | 0.0  |    459    | estimated delivery date (yyyy-mm-dd 00:00:00) |

- order_status distribution

| order_status | count |
|--------------|------:|
| delivered    | 96478 |
| shipped      | 1107  |
| canceled     | 625   |
| unavailable  | 609   |
| invoiced     | 314   |
| processing   | 301   |
| created      | 5     |
| approved     | 2     |

## Notes
- all `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date` will be converted to datetime
- `order_id` is the true primary key of this table and will be used to join with items, payments, and reviews
- `customer_id` is unique in this file and acts as a foreign key to the `customers` table
- `order_status` is heavily skewed towards `delivered` (most orders). Non-delivered statuses
  (canceled, unavailable, etc.) usually have missing delivery timestamps and may be excluded
  from delivery-time analyses and forecasting targets

---

# olist_products_dataset.csv ('products')
dataset containing information about products (category, weight, description, ...)
- **Grain**: one row per product id
- **Shape**: (32951, 9)
- **Approx Memory**: ~2.3 MB

## Keys and cardinalities
- primary key: `product_id`
- `product_id`:
    - `is_unique = True`
    - `num_unique = 32951`

## Columns

| Column                       | Dtype  | Null % | #Distinct | Notes                                 |
|------------------------------|--------|--------|----------:|---------------------------------------|
| `product_id`                 | object | 0.0    |    32951  | ID identifying products               |
| `product_category_name`      | object | 1.8    |    73     | name of the product's category (perfumaria, artes, ...) |
| `product_name_lenght`        | float64| 1.8    |    66     | length of product name                |
| `product_description_lenght` | float64| 1.8    |    2960   | length of product description         |
| `product_photos_qty`         | float64| 1.8    |    19     | how many photo of the product are visible on product page |
| `product_weight_g`           | float64| 0.01  |    2204   | product weight in grams               |
| `product_length_cm`          | float64| 0.01  |    99     | product length in centimeters         |
| `product_height_cm`          | float64| 0.01  |    102    | product height in centimeters         |
| `product_width_cm`           | float64| 0.01  |    95     | product width in centimeters          |

- products['product_category_name'].value_counts().head()

| product_category_name | count |
|-----------------------|------:|
| cama_mesa_banho       | 3029  |
| esporte_lazer         | 2867  |
| moveis_decoracao      | 2657  |
| beleza_saude          | 2444  |
| utilidades_domesticas | 2335  |

## Notes
- `product_id` is the primary key and links to `items.product_id`
- `product_category_name`, `product_name_lenght`, `product_description_lenght`,
  and `product_photos_qty` have ~1.9% missing values (610 products)
- `product_weight_g`, `product_length_cm`, `product_height_cm`, and
  `product_width_cm` have only 2 missing values each (~0.006%)
- The “length” and “qty” fields are counts but stored as floats due to missing values;
  they can be safely treated as integers after appropriate imputation
- `product_category_name` is in Portuguese and relatively high-cardinality (73 categories);
  for modeling we may:
  - group rare categories,
  - or use target encoding / embeddings rather than one-hot encoding

---

# olist_sellers_dataset.csv ('sellers')
dataset containing sellers information (id, zip prefix, city, state)
- **Grain**: one row per seller id
- **Shape**: (3095, 4)
- **Approx Memory**: ~0.1 MB

## Keys and cardinalities
- primary key: `seller_id`
- `seller_id`:
    - `is_unique = True`
    - `num_unique = 3095`

## Columns

| Column                       | Dtype  | Null % | #Distinct | Notes                                 |
|------------------------------|--------|--------|----------:|---------------------------------------|
| `seller_id`                  | object | 0.0    |    3095   | ID identifying sellers (links to `items.seller_id`) |
| `seller_zip_code_prefix`     | int64  | 0.0    |    2246   | ZIP code prefix of seller location    |
| `seller_city`                | object | 0.0    |    611    | Seller city (Brazilian Portuguese, similar issues as `customer_city`)     |
| `seller_state`               | object | 0.0    |    23     | State abbreviation (SP, RJ, MG, …); subset of the 27 Brazilian states |

- sellers['seller_state'].value_counts().head()

| seller_state   | count |
|----------------|------:|
| SP             | 1849  |
| PR             | 349   |
| MG             | 244   |
| SC             |  190  |
| RJ             |  171  |

- sellers['seller_city'].value_counts().head()

| seller_city    | count |
|----------------|------:|
| sao paulo      | 694   |
| curitiba       | 127   |
| rio de janeiro | 96    |
| belo horizonte | 68    | 
| ribeirao preto | 52    | 

## Notes
- `seller_id` is the primary key and is used in `items` to link each order item to a seller
- `seller_zip_code_prefix` can be joined with `geolocation.geolocation_zip_code_prefix` to get lat/long for sellers
- Only **23** of the **27** Brazilian states present in `customers` / `geolocation` appear for sellers: some states have buyers but no sellers in this dataset
- City names will have the same normalization issues as `customer_city` / `geolocation_city` (accents, casing); we will normalize them when needed

---

# olist_category_name_translation.csv ('categories')
Dataset containing the names for product categories in Portuguese and English
- **Grain**: one row per category
- **Shape**: (71, 2)
- **Approx Memory**: ~1.2 KB

## Columns

| Column                       | Dtype  | Null % | #Distinct | Notes                                 |
|------------------------------|--------|--------|----------:|---------------------------------------|
| `product_category_name`      | object | 0.0    |    71     | product category name in Portuguese   |
| `product_category_name_english` | object | 0.0 |    71     | product category name in English      |


## Notes
- This table provides a 1–1 mapping between Portuguese and English category names.
- `product_category_name` links to `products.product_category_name`
- The `products` table has 73 distinct categories, while this mapping file has 71:
  a small number of categories in `products` have no English translation here and
  will need special handling (e.g. keep original name or map to `"unknown"`)

---

# Relationship overview

- **Main table**: `orders`

- **Customer side**:
    - `customers` &harr; `orders` via (`customer_id`)
    - `customers` &harr; `geolocation` via (`*_zip_code_prefix`) (after aggregating `geolocation` at ZIP-prefix level)

- **Items/Products/Sellers**:
    - `items` &harr; `orders` via (`order_id`)
    - `items` &harr; `products` via (`product_id`)
    - `items` &harr; `sellers` via (`seller_id`)
    - `products` &harr; `categories` via (`product_category_name`)
    - `sellers` &harr; `geolocation` via (`*_zip_code_prefix`)

- **Payments and Reviews**:
    - `payments` &harr; `orders` via (`order_id`)
    - `reviews` &harr; `orders` via (`order_id`)

![Olist schema diagram](../docs/olist_schema.png)

*Figure 1 – ER diagram for the Olist dataset (source: “Brazilian E-Commerce Public Dataset by Olist” on Kaggle).*