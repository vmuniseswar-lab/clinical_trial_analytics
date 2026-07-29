-- Fact: Enrollment
-- One row per trial with enrollment metrics
-- Joins to all dimension tables

{{
    config(
        materialized='incremental',
        unique_key ='trial_id',
        incremental_strategy='merge'
    )
}}

with trials as (

    select * from {{ ref('staging_clinical_trials') }}

),

dim_ta as (

    select * from {{ ref('dim_therapeutic_area') }}

),

dim_sp as (

    select * from {{ ref('dim_sponsor') }}

),

final as (

    select
        -- Keys
        t.trial_id,
        ta.therapeutic_area_id,
        sp.sponsor_id,

        -- Enrollment metrics
        t.enrollment_target,
        t.enrollment_type,

        -- Simulated actual enrollment based on status
        -- In a real CRO system this would come from CTMS
        case
            when t.trial_status = 'COMPLETED'
                then t.enrollment_target
            when t.trial_status = 'RECRUITING'
                then round(t.enrollment_target * 0.6, 0)
            when t.trial_status = 'ACTIVE_NOT_RECRUITING'
                then round(t.enrollment_target * 0.9, 0)
            else 0
        end                                         as enrollment_actual,

        -- Dates for time intelligence in Power BI
        t.start_date,
        t.completion_date,
        t.planned_duration_days,
        t.is_completed

    from trials t

    left join dim_ta ta
        on t.primary_condition = ta.therapeutic_area_name

    left join dim_sp sp
        on t.sponsor_name = sp.sponsor_name

    where t.enrollment_target is not null

    {% if is_incremental() %}
      and t.start_date >= (select max(start_date) from {{ this }})
    {% endif %}
    
    qualify row_number() over (partition by t.trial_id order by ta.therapeutic_area_id) = 1
),

with_rates as (

    select
        *,
        {{ safe_divide('enrollment_actual', 'enrollment_target') }} as enrollment_rate_pct
    from final

)

select * from with_rates