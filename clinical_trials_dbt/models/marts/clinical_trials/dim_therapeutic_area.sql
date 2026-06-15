-- Dimension: Therapeutic Area
-- One row per unique medical condition / therapeutic area

with source as (

    select distinct
        primary_condition
    from {{ ref('staging_clinical_trials') }}
    where primary_condition is not null
      and trim(primary_condition) != ''

)

select
    row_number() over (order by primary_condition)  as therapeutic_area_id,
    primary_condition                               as therapeutic_area_name
from source