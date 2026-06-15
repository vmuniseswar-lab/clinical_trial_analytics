-- Dimension: Trial
-- One row per clinical trial with descriptive attributes

with source as (

    select
        trial_id,
        trial_title,
        trial_phase,
        trial_status,
        study_type,
        start_date,
        completion_date,
        planned_duration_days,
        is_completed
    from {{ ref('staging_clinical_trials') }}

)

select
    trial_id,
    trial_title,
    trial_phase,
    trial_status,
    study_type,
    start_date,
    completion_date,
    planned_duration_days,
    is_completed,

    -- Derived groupings useful for Power BI slicers
    case
        when trial_phase in ('Phase 3', 'Phase 4') then 'Late Stage'
        when trial_phase in ('Phase 1', 'Phase 2') then 'Early Stage'
        when trial_phase = 'Early Phase 1'         then 'Early Stage'
        else 'Other'
    end                                             as stage_group,

    case
        when planned_duration_days < 365            then 'Under 1 Year'
        when planned_duration_days < 730            then '1-2 Years'
        when planned_duration_days < 1825           then '2-5 Years'
        when planned_duration_days >= 1825          then 'Over 5 Years'
        else 'Unknown'
    end                                             as duration_band

from source