from sqlalchemy import text
from app.database import engine

with engine.connect() as connection:
    result = connection.execute(text("SELECT DB_NAME()"))
    print("Connected database:", result.scalar())

# from app.database import engine

# print("Database URL:", engine.url.render_as_string(hide_password=True))
# print("Host:", engine.url.host)
# print("Database:", engine.url.database)