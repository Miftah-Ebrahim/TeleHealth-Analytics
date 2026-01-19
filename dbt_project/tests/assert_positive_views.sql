select *
from {{ ref('stg_telegram') }}
where view_count < 0
