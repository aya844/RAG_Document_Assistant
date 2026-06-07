import aiosqlite
from app.config import get_settings

settings = get_settings()

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    filename    TEXT NOT NULL,
    file_type   TEXT NOT NULL,
    chunk_count INTEGER DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parent_chunks (
    id          TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    content     TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER
);
"""


async def init_db():
    async with aiosqlite.connect(settings.sqlite_path) as db:
        await db.executescript(CREATE_TABLES)
        await db.commit()


async def insert_document(doc_id: str, filename: str, file_type: str):
    async with aiosqlite.connect(settings.sqlite_path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO documents (id, filename, file_type) VALUES (?, ?, ?)",
            (doc_id, filename, file_type),
        )
        await db.commit()


async def insert_parent_chunk(
    chunk_id: str, document_id: str, content: str, chunk_index: int, page_number: int | None
):
    async with aiosqlite.connect(settings.sqlite_path) as db:
        await db.execute(
            "INSERT INTO parent_chunks (id, document_id, content, chunk_index, page_number) "
            "VALUES (?, ?, ?, ?, ?)",
            (chunk_id, document_id, content, chunk_index, page_number),
        )
        await db.commit()


async def get_parent_chunk(chunk_id: str) -> dict | None:
    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM parent_chunks WHERE id = ?", (chunk_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_documents() -> list[dict]:
    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT d.*, COUNT(p.id) as parent_count "
            "FROM documents d LEFT JOIN parent_chunks p ON d.id = p.document_id "
            "GROUP BY d.id ORDER BY d.created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]