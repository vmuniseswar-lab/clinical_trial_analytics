-- Dimension: Sponsor
-- One row per unique trial sponsor organisation

with source as (

    select distinct
        sponsor_name
    from {{ ref('staging_clinical_trials') }}
    where sponsor_name is not null
      and trim(sponsor_name) != ''

)

select
    {{ dbt_utils.generate_surrogate_key(['sponsor_name']) }}    as sponsor_id,
    sponsor_name
from source