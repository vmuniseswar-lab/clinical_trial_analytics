import duckdb

con = duckdb.connect('clinical_trials_dbt/dev.duckdb', read_only=True)

tables = [
    'dim_trial',
    'dim_therapeutic_area', 
    'dim_sponsor',
    'fct_enrollment'
]

for table in tables:
    output_path = f'data/gold/{table}.parquet'
    con.execute(f"COPY {table} TO '{output_path}' (FORMAT PARQUET)")
    print(f'Exported {table} → {output_path}')

con.close()
print('Done.')