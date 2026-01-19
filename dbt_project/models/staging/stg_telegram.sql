with source as (
    select * from {{ source('raw', 'telegram_messages') }}
),

renamed as (
    select
        message_id,
        channel_name,
        channel_title,
        message_date,
        message_text,
        has_media,
        image_path,
        views as view_count,
        forwards as forward_count
    from source
),

final as (
    select
        *,
        length(message_text) as message_length,
        (image_path is not null) as has_image
    from renamed
    where message_text is not null
)

select * from final
