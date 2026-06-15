with source as (

    select * from read_csv_auto(
        'C:/Users/vmuni/Documents/clinical_trial_analytics/data/raw/clinical_trials/trials_flat_*.csv',
        header = true
    )

),

cleaned as (

    select
        trim(trial_id)                              as trial_id,
        trim(trial_title)                           as trial_title,
        trim(upper(overall_status))                 as trial_status,
        trim(study_type)                            as study_type,

        case
            when lower(phase) like '%phase4%'       then 'Phase 4'
            when lower(phase) like '%phase3%'       then 'Phase 3'
            when lower(phase) like '%phase2%'       then 'Phase 2'
            when lower(phase) like '%phase1%'       then 'Phase 1'
            when lower(phase) like '%early%'        then 'Early Phase 1'
            when phase = '' or phase is null        then 'Not Applicable'
            else trim(phase)
        end                                         as trial_phase,

        try_cast(enrollment_count as integer)       as enrollment_target,
        trim(enrollment_type)                       as enrollment_type,
        try_cast(start_date as date)                as start_date,
        try_cast(completion_date as date)           as completion_date,
        trim(sponsor_name)                          as sponsor_name,
        trim("condition")                           as primary_condition,

        datediff(
            'day',
            try_cast(start_date as date),
            try_cast(completion_date as date)
        )                                           as planned_duration_days,

        case
            when try_cast(completion_date as date) < current_date
             and upper(overall_status) = 'COMPLETED' then true
            else false
        end                                         as is_completed

    from source
    where trim(trial_id) is not null
      and trim(trial_id) != ''

)

select * from cleaned