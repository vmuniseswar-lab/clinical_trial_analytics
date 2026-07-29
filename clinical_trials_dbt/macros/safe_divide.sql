{% macro safe_divide(numerator, denominator) %}
    case
        when {{ denominator }} = 0 or {{ denominator }} is null
            then null
        else round({{ numerator }} * 100.0 / {{ denominator }}, 1)
    end
{% endmacro %}