try:
    # To avoid a syntax error on Python 2 + use async / await syntax instead of @asyncio.coroutine
    exec(  # pylint: disable=exec-used
        """
async def get_asyncpg_record(dsn):
    import asyncpg

    connection = await asyncpg.connect(dsn)
    result = await connection.fetch("SELECT 1 as value")
    await connection.close()
    return result
    """,
        globals(),
    )
except SyntaxError:
    get_asyncpg_record = None
