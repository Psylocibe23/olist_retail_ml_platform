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
| `customer_state`          | object | 0.0    |    27     | State abbreviation (SP, RJ, …)  


- customers["customer_state"].value_counts().head()

customer_state

SP    41746

RJ    12852

MG    11635

RS     5466

PR     5045

- customers['customer_city'].value_counts().head()
customer_city
sao paulo         15540
rio de janeiro     6882
belo horizonte     2773
brasilia           2131
curitiba           1521
