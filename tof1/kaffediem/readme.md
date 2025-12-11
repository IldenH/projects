# Kaffediem data analyse

query basert på 2025-10-23 database:

## Only order_items table:

```sql
SELECT
    o.id AS order_id,
    o.inserted_at,
    o.updated_at,
    i.name AS item_name,
    i.price_nok,
    c.name AS category_name,
    k.name AS customization_key,
    v.name AS customization_value,
    v.price_increment_nok,
    v.constant_price
FROM order_item o

JOIN item i ON o.item = i.id
JOIN category c ON i.category = c.id

JOIN json_each(o.customization) AS oc
    ON 1=1

JOIN item_customization ic
    ON ic.id = oc.value

JOIN json_each(ic.value) AS icv
    ON 1=1

JOIN customization_key k
    ON k.id = ic.key

JOIN customization_value v
    ON v.id = icv.value;
```
