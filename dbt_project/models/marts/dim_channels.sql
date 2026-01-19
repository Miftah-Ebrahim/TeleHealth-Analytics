with stg_data as (
    select * from {{ ref('stg_telegram') }}
),

channel_stats as (
    select
        channel_name,
        min(channel_title) as channel_title, -- Take one title if multiple exist
        count(message_id) as total_posts,
        avg(view_count) as avg_views
    from stg_data
    group by 1
),

final as (
    select
        channel_name,
        md5(channel_name) as channel_key, -- Surrogate key
        total_posts,
        avg_views
    from channel_stats
)

select * from final
