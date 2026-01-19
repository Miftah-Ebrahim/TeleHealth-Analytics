with stg_data as (
    select * from {{ ref('stg_telegram') }}
),

final as (
    select
        message_id,
        md5(channel_name) as channel_key,
        to_char(message_date, 'YYYYMMDD')::int as date_key,
        view_count,
        forward_count,
        message_length,
        has_image,
        has_media
    from stg_data
)

select * from final
