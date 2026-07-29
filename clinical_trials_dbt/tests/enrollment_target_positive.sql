-- Enrollment target must be positive where provided
-- Any rows returned by this query are test failures

select
    trial_id,
    enrollment_target
from {{ ref('fct_enrollment') }}
where enrollment_target <= 0