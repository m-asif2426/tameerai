import asyncio, os, sys
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@127.0.0.1:5433/tameerai_isolated_test"
sys.path.insert(0, r"d:\new idea project\tameerai\backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.material_rate import MaterialRateObservation

uuids_to_check = [
    # Set A (Draft / Acceptance Challenge Report)
    "3803875e-9ea1-4c6e-8260-2fe5eb9cf48c",
    "0e5c92ce-8c54-47a3-b9db-bcbe3ba10243",
    "bf863c0a-0498-4680-bc90-951da6607ae9",
    "3a8f33ae-158a-4467-b52b-7ca6560934e6",
    "28ce57eb-3ce3-448e-9403-2410a8d76a7e",
    "be4e4c27-313d-4c3e-8625-f6d20387be58",
    # Set B (Database Malformed Records)
    "3310797b-470e-4321-85a2-d137f3d6e8f9",
    "4d1bc418-b2ad-4d23-9a02-e09d58fca2d1",
    "92e53358-9567-46bc-b917-f1ad2f8f03c5",
    "a497c459-f203-4f2b-a707-7bf2f5dbfaef",
    "aa50dae4-ba05-46dd-a188-23b91a7b08f1",
    "2d5c553f-1ef4-4dde-992b-8cf9b4dfb858",
    # Also check if there were earlier Set B variants reported:
    "3310797b-3b36-419b-a010-ea1ee77eb3ae",
    "4d1bc418-c0eb-49ee-8959-71578f7bf859",
    "92e53358-fc24-4f81-8178-5e581297a7e8",
    "a497c459-70dc-4dd9-a548-6a3f120e5c26",
    "aa50dae4-1317-4db3-982d-20516fc29a39",
    "2d5c553f-42e8-4665-9273-51829e92d77d",
]

async def check_all():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        for u in uuids_to_check:
            res = await session.execute(
                select(MaterialRateObservation).where(MaterialRateObservation.id == u)
            )
            o = res.scalar_one_or_none()
            if o:
                print(f"EXISTS: {u} | Prod: {o.product_id} | Src: {o.source_id} | Coll: {o.collected_at} | Orig: {o.observed_price_pkr} {o.observed_unit} | Norm: {o.normalized_price_pkr} {o.normalized_unit} | Fp: {o.duplicate_fingerprint}")
            else:
                print(f"NOT_FOUND: {u}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_all())

