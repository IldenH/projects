# Kaffediem data analyse

query basert på 2025-10-23 database:

```sql
SELECT
    o.id AS order_id,
    o.day_id,
    o.missing_information,
o.inserted_at,
o.updated_at,
    json_group_array(
        json_object(
            'order_item_id', oi.id,
            'item_id', i.id,
            'item_name', i.name,
            'customizations',
                (
                    SELECT json_group_array(
                        json_object(
                            'customization_id', ic.id,
                            'key', ck.name,
                            'value', cv.name
                        )
                    )
                    FROM json_each(oi.customization) jc
                    JOIN item_customization ic ON ic.id = jc.value
                    LEFT JOIN customization_key ck ON ck.id = ic.key
                    LEFT JOIN json_each(ic.value) jcv ON 1=1
                    LEFT JOIN customization_value cv ON cv.id = jcv.value
                )
        )
    ) AS order_items
FROM "order" o
JOIN json_each(o.items_data) je ON 1=1
JOIN order_item oi ON oi.id = je.value
JOIN item i ON i.id = oi.item
GROUP BY o.id, o.customer_id, o.day_id;
```
