import psycopg

for db_name in ["canopy_test_control_plane", "canopy_test_tenant_data"]:
    conn = psycopg.connect(f"postgresql://postgres:postgres@127.0.0.1:5432/{db_name}")
    cur = conn.cursor()
    cur.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    """)
    tables = [r[0] for r in cur.fetchall()]
    for t in tables:
        cur.execute(f'TRUNCATE TABLE "{t}" CASCADE')
    conn.commit()
    cur.close()
    conn.close()
    print(f"Truncated {len(tables)} tables in {db_name}")
