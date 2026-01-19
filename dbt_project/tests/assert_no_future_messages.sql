select *
from {{ ref('stg_telegram') }}
where message_date > current_date
