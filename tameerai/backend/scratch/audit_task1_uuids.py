import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"

from app.core.database import get_session_factory
from sqlalchemy import text

SET_A = [
    "3803875e-9ea1-4c6e-8260-2fe5eb9cf48c",
    "0e5c92ce-8c54-47a3-b9db-bcbe3ba10243",
    "bf863c0a-0498-4680-bc90-951da6607ae9",
    "3a8f33ae-158a-4467-b52b-7ca6560934e6",
    "28ce57eb-3ce3-448e-9403-2410a8d76a7e",
    "be4e4c27-3a1b-410a-b1eb-5a67c473a216",
]

SET_B = [
    "3310797b-470e-4321-85a2-d137f3d6e8f9",
    "4d1bc418-b2ad-4d23-9a02-e09d58fca2d1",
    "92e53358-9567-46bc-b917-f1ad2f8f03c5",
    "a497c459-f203-4f2b-a707-7bf2f5dbfaef",
    "aa50dae4-ba05-46dd-a188-23b91a7b08f1",
    "2d5c553f-1ef4-4dde-992b-8cf9b4dfb858",
]

async def audit_uuids():
    session_factory = get_session_factory()
    async with session_factory() as sess:
        print("=== CHECKING SET A (PREVIOUS REPORT) ===")
        for u in SET_A:
            res = await sess.execute(text("""
                SELECT o.id, o.product_id, p.code as product_code, p.canonical_name,
                       o.source_id, s.code as source_code, s.name as source_name,
                       o.city, o.observed_price_pkr, o.normalized_price_pkr,
                       o.observed_unit, o.normalized_unit,
                       o.observation_metadata->>'price_basis' as price_basis,
                       o.published_at, o.observation_metadata
                FROM material_rate_observations o
                LEFT JOIN material_rate_products p ON o.product_id = p.id
                LEFT JOIN material_rate_sources s ON o.source_id = s.id
                WHERE o.id = :uid
            """), {"uid": u})
            row = res.fetchone()
            if row:
                d = dict(row._mapping)
                print(f"FOUND Set A: {u} -> Product: {d['product_code']} | City: {d['city']} | Observed: {d['observed_price_pkr']} | Norm: {d['normalized_price_pkr']} | NormUnit: {d['normalized_unit']} | Source: {d['source_code']} | Meta: {d['observation_metadata']}")
            else:
                print(f"NOT FOUND Set A: {u}")

        print("\n=== CHECKING SET B (LATEST REPORT) ===")
        for u in SET_B:
            res = await sess.execute(text("""
                SELECT o.id, o.product_id, p.code as product_code, p.canonical_name,
                       o.source_id, s.code as source_code, s.name as source_name,
                       o.city, o.observed_price_pkr, o.normalized_price_pkr,
                       o.observed_unit, o.normalized_unit,
                       o.observation_metadata->>'price_basis' as price_basis,
                       o.published_at, o.observation_metadata
                FROM material_rate_observations o
                LEFT JOIN material_rate_products p ON o.product_id = p.id
                LEFT JOIN material_rate_sources s ON o.source_id = s.id
                WHERE o.id = :uid
            """), {"uid": u})
            row = res.fetchone()
            if row:
                d = dict(row._mapping)
                print(f"FOUND Set B: {u} -> Product: {d['product_code']} | City: {d['city']} | Observed: {d['observed_price_pkr']} | Norm: {d['normalized_price_pkr']} | NormUnit: {d['normalized_unit']} | Source: {d['source_code']} | Meta: {d['observation_metadata']}")
            else:
                print(f"NOT FOUND Set B: {u}")

        print("\n=== SCANNING ALL UNUSUAL / MALFORMED OBSERVATIONS IN DB ===")
        # Look for observations where normalized_price < 10000 for steel or normalized_unit not canonical
        res_all = await sess.execute(text("""
            SELECT o.id, o.product_id, p.code as product_code,
                   s.code as source_code, o.city, o.observed_price_pkr, o.normalized_price_pkr,
                   o.observed_unit, o.normalized_unit, o.published_at,
                   o.observation_metadata->>'item_name' as item_name
            FROM material_rate_observations o
            LEFT JOIN material_rate_products p ON o.product_id = p.id
            LEFT JOIN material_rate_sources s ON o.source_id = s.id
            WHERE p.category = 'steel' AND (o.normalized_price_pkr < 50000 OR o.normalized_unit NOT IN ('metric_ton', 'tonne', 'ton'))
        """))
        unusual = res_all.fetchall()
        print(f"Total unusual/malformed steel records found: {len(unusual)}")
        for r in unusual:
            print(dict(r._mapping))

if __name__ == "__main__":
    asyncio.run(audit_uuids())
