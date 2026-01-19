with raw_detections as (
    select * from {{ source('raw', 'image_detections') }}
),

messages as (
    select * from {{ ref('fct_messages') }}
),

final as (
    select
        r.message_id,
        m.channel_key,
        m.date_key,
        r.detected_class,
        r.confidence as confidence_score,
        r.image_category
    from raw_detections r
    left join messages m on r.message_id::text = m.message_id::text
)

select * from final
