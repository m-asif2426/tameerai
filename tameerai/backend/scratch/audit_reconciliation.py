import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    
    # 1. Inspect all steel products
    steel_prods = await conn.fetch("""
        SELECT id, code, canonical_name, category, subcategory, standard_unit, spec_attributes
        FROM material_rate_products
        WHERE category ILIKE '%steel%' OR canonical_name ILIKE '%steel%' OR canonical_name ILIKE '%rebar%'
        ORDER BY canonical_name;
    """)
    print("=== STEEL PRODUCTS IN CATALOG ===")
    for sp in steel_prods:
        print(f"Product [{sp['code']}]: {sp['canonical_name']} | Cat: {sp['category']}/{sp['subcategory']} | Unit: {sp['standard_unit']} | Specs: {sp['spec_attributes']}")

    # 2. Count observations by product and grade
    steel_obs = await conn.fetch("""
        SELECT p.code, p.canonical_name, p.spec_attributes, count(o.id) as obs_count,
               min(o.normalized_price_pkr) as min_price, max(o.normalized_price_pkr) as max_price,
               o.normalized_unit, string_agg(DISTINCT s.name, '; ') as sources
        FROM material_rate_observations o
        JOIN material_rate_products p ON o.product_id = p.id
        JOIN material_rate_sources s ON o.source_id = s.id
        WHERE p.category ILIKE '%steel%' OR p.canonical_name ILIKE '%steel%' OR p.canonical_name ILIKE '%rebar%'
        GROUP BY p.code, p.canonical_name, p.spec_attributes, o.normalized_unit
        ORDER BY p.canonical_name;
    """)
    print("\n=== STEEL OBSERVATIONS BY PRODUCT ===")
    for so in steel_obs:
        print(f"[{so['code']}] {so['canonical_name']}: count={so['obs_count']} | range=PKR {so['min_price']} - {so['max_price']} per {so['normalized_unit']} | sources={so['sources']}")

    # 3. Specifically verify Grade 40 vs Grade 60 products and their distinct identities
    grade_comparison = await conn.fetch("""
        SELECT p.id, p.code, p.canonical_name, p.standard_unit, p.spec_attributes,
               count(o.id) as total_obs,
               count(CASE WHEN s.name IN ('Pakistan Bureau of Statistics - Monthly Construction Items', 'SteelRateToday Rebar & Scrap Market Monitor', 'Pakistan Bureau of Statistics') THEN 1 END) as authentic_obs,
               count(CASE WHEN s.name NOT IN ('Pakistan Bureau of Statistics - Monthly Construction Items', 'SteelRateToday Rebar & Scrap Market Monitor', 'Pakistan Bureau of Statistics') THEN 1 END) as test_obs,
               min(o.normalized_price_pkr) as min_norm_price,
               max(o.normalized_price_pkr) as max_norm_price
        FROM material_rate_products p
        LEFT JOIN material_rate_observations o ON o.product_id = p.id
        LEFT JOIN material_rate_sources s ON o.source_id = s.id
        WHERE p.canonical_name ILIKE '%grade 40%' OR p.canonical_name ILIKE '%grade 60%'
           OR p.code ILIKE '%g40%' OR p.code ILIKE '%g60%'
           OR (p.spec_attributes->>'grade' IN ('40', '60', 'Grade 40', 'Grade 60'))
        GROUP BY p.id, p.code, p.canonical_name, p.standard_unit, p.spec_attributes
        ORDER BY p.canonical_name;
    """)
    print("\n=== GRADE 40 VS GRADE 60 PRODUCT IDENTITY & VERIFICATION ===")
    for gc in grade_comparison:
        print(f"Product ID: {gc['id']}")
        print(f"  Code: {gc['code']}")
        print(f"  Canonical Name: {gc['canonical_name']}")
        print(f"  Standard Unit: {gc['standard_unit']}")
        print(f"  Spec Attributes: {gc['spec_attributes']}")
        print(f"  Observations: total={gc['total_obs']}, authentic={gc['authentic_obs']}, test={gc['test_obs']}")
        print(f"  Price Range: PKR {gc['min_norm_price']} to {gc['max_norm_price']}")
        print("-" * 60)

    # 4. Check canonical rates table
    canon_rates = await conn.fetch("SELECT * FROM material_rates;")
    print(f"\n=== CANONICAL MATERIAL RATES TABLE ({len(canon_rates)} rows) ===")
    for cr in canon_rates:
        print(dict(cr))

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
