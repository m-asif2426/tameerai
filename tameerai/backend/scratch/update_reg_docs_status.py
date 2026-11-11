import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test')
    
    # Update documents that have no version with a valid source_file_sha256
    # In our case, all 5 pilot documents have version with source_file_sha256 IS NULL
    query = """
    UPDATE regulatory_documents
    SET status = 'REVIEW_REQUIRED', updated_at = NOW()
    WHERE id IN (
        SELECT d.id
        FROM regulatory_documents d
        LEFT JOIN regulatory_document_versions v ON d.id = v.document_id
        GROUP BY d.id
        HAVING COUNT(v.source_file_sha256) = 0
    )
    RETURNING id, document_code, title, status;
    """
    rows = await conn.fetch(query)
    print(f"Updated {len(rows)} documents to REVIEW_REQUIRED:")
    for r in rows:
        print(f" - {r['document_code']}: {r['title']} -> {r['status']}")
        
    # Verify current status of all documents
    all_docs = await conn.fetch("SELECT document_code, status FROM regulatory_documents")
    print("\nAll regulatory documents current status:")
    for r in all_docs:
        print(f" - {r['document_code']}: {r['status']}")
        
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())

