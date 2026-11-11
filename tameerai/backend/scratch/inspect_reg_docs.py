import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'regulatory_documents'
    """)
    print("Columns:", [c['column_name'] for c in cols])
    
    rows = await conn.fetch("SELECT * FROM regulatory_documents")
    for r in rows:
        d = dict(r)
        # convert uuid and dates
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
            elif hasattr(v, '__str__') and not isinstance(v, (str, int, float, bool, type(None), dict, list)):
                d[k] = str(v)
        print("Doc:", json.dumps(d, indent=2))
        
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())

