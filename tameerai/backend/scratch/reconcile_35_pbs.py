import asyncio
import os
import sys

sys.path.insert(0, r"D:\new idea project\tameerai\backend")
os.chdir(r"D:\new idea project\tameerai\backend")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.services.material_rates.ai_bridge import MaterialRateIntelligenceBridge
import json

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test")
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    bridge = MaterialRateIntelligenceBridge()
    async with session_maker() as session:
        # Fetch all 35 PBS steel records
        res = await session.execute(text("""
            SELECT 
                o.id,
                s.code as source_code,
                o.city,
                o.observed_price_pkr,
                o.observed_unit,
                o.normalized_price_pkr,
                o.normalized_unit,
                p.id as stored_product_id,
                p.code as stored_product_code,
                p.canonical_name as stored_canonical_name,
                o.observation_metadata,
                o.verification_status,
                o.published_at,
                o.collected_at,
                o.created_at
            FROM material_rate_observations o
            JOIN material_rate_sources s ON o.source_id = s.id
            JOIN material_rate_products p ON o.product_id = p.id
            WHERE s.code = 'PBS_STATISTICAL_MONTHLY'
              AND (p.code LIKE '%STEEL%' OR p.code LIKE '%REBAR%' OR o.observation_metadata::text ILIKE '%iron%' OR o.observation_metadata::text ILIKE '%steel%')
            ORDER BY o.city, o.created_at
        """))
        rows = res.fetchall()
        print(f"Total PBS Steel Records in PostgreSQL: {len(rows)}")
        
        # Test query for Grade 40 nationwide / multi-city to see eligibility
        res_g40_all = await bridge.resolve_material_rate_query("Steel Grade 40 in Pakistan", db=session)
        print(f"Grade 40 Pakistan Query: status={res_g40_all.status}, total_evidence={len(res_g40_all.evidence_items)}")
        
        # Check which observation IDs are in res_g40_all evidence
        g40_evidence_ids = {item.observation_id for item in res_g40_all.evidence_items}
        
        reconciliation_data = []
        for i, r in enumerate(rows, 1):
            meta = r.observation_metadata if isinstance(r.observation_metadata, dict) else json.loads(r.observation_metadata or "{}")
            item_name = meta.get("item_name")
            raw_spec = meta.get("raw_specification")
            
            # Detect grade
            name_lower = (item_name or "").lower()
            spec_lower = (raw_spec or "").lower()
            if "40" in name_lower or "40" in spec_lower or "grade 40" in name_lower:
                detected_grade = "Grade 40"
            elif "60" in name_lower or "60" in spec_lower or "grade 60" in name_lower:
                detected_grade = "Grade 60"
            else:
                detected_grade = "Unknown/Unspecified"
                
            resolved_code = "STEEL_REBAR_G40" if detected_grade == "Grade 40" else r.stored_product_code
            resolved_name = "Mild Steel Bar Grade 40" if detected_grade == "Grade 40" else r.stored_canonical_name
            
            is_eligible = str(r.id) in g40_evidence_ids
            exclusion_reason = "None (Eligible)" if is_eligible else "City filter / freshness / verification status"
            
            reconciliation_data.append({
                "index": i,
                "id": str(r.id),
                "city": r.city,
                "source_code": r.source_code,
                "raw_specification": raw_spec,
                "item_name": item_name,
                "stored_product_id": str(r.stored_product_id),
                "stored_product_code": r.stored_product_code,
                "detected_grade": detected_grade,
                "resolved_canonical_code": resolved_code,
                "resolved_canonical_name": resolved_name,
                "price_pkr": float(r.observed_price_pkr),
                "unit": r.observed_unit,
                "eligible_in_g40_query": is_eligible,
                "exclusion_reason": exclusion_reason
            })
            
        print(f"Reconciliation analyzed for {len(reconciliation_data)} records.")
        # Summary
        grade_40_count = sum(1 for d in reconciliation_data if d["detected_grade"] == "Grade 40")
        grade_60_count = sum(1 for d in reconciliation_data if d["detected_grade"] == "Grade 60")
        print(f"Summary: Genuine Grade 40 count: {grade_40_count} / 35")
        print(f"Summary: Genuine Grade 60 count: {grade_60_count} / 35")
        
        # Save to json for reference
        with open(r"D:\new idea project\tameerai\backend\scratch\pbs_35_reconciliation.json", "w", encoding="utf-8") as f:
            json.dump(reconciliation_data, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
