with stg_data as (
    select distinct 
        message_date::date as date_day
    from {{ ref('stg_telegram') }}
    where message_date is not null
),

date_dim as (
    select
        date_day,
        to_char(date_day, 'YYYYMMDD')::int as date_key,
        to_char(date_day, 'Day') as day_name,
        extract(isodow from date_day) as day_of_week,
        extract(week from date_day) as week_of_year,
        extract(month from date_day) as month,
        extract(quarter from date_day) as quarter,
        extract(year from date_day) as year,
        case 
            when extract(isodow from date_day) in (6, 7) then true 
            else false 
        end as is_weekend
    from stg_data
)

select * from date_dim
