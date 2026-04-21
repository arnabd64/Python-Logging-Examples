from datetime import datetime
from logging import Formatter, Handler, LogRecord
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine


class SQLogRecord(SQLModel, table=True):
    """
    Data Model to store logs

    Attributes:
        timestamp (datetime) : when the log was created
        loglevel (str) : INFO, DEBUG, ERROR, WARNING ...
        name (str) : Name of the logger
        module (str) : module/script where the event was recorded
        funcName (str) : Name of parent function
        lineno (int) : Line Number where logger was called
        message (str) : Log Message
    """

    __tablename__ = "logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    loglevel: str = Field(index=True)
    name: str = Field(index=True)
    module: str = Field(index=True)
    funcName: str
    lineno: int
    message: str


class SQLFormatter(Formatter):
    """
    Converts a Log Event object (`LogRecord`) into a Pydantic
    object
    """

    def format(self, record: LogRecord) -> SQLogRecord:
        return SQLogRecord(
            timestamp=datetime.fromtimestamp(record.created),
            loglevel=record.levelname,
            name=record.name,
            module=record.module,
            funcName=record.funcName,
            lineno=record.lineno,
            message=record.getMessage(),
        )


class SQLHandler(Handler):
    def __init__(self, connection_string: str, level=0):
        super().__init__(level)

        # store connection string
        self._connection_string = connection_string

        # create the engine
        self._engine = create_engine(self._connection_string)

        # create all the engines
        with self._engine.begin() as conn:
            SQLModel.metadata.create_all(conn)

    def emit(self, record: LogRecord):
        row: SQLogRecord = self.format(record)
        with Session(self._engine) as session:
            try:
                session.add(row)
                session.commit()

            except Exception as e:
                session.rollback()
                self.handleError(record)


if __name__ == "__main__":
    import logging

    from sqlmodel import select

    DATABASE_URL = "sqlite:///app.log"

    handler = SQLHandler(DATABASE_URL)

    handler.setFormatter(SQLFormatter())

    logger = logging.getLogger("demo")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    logger.info("Application started successfully")
    logger.warning("Cache is running low: 15%% remaining")
    logger.error("Failed to connect to upstream service: timeout after 30s")

    # Verify all three records were persisted
    with Session(handler._engine) as session:
        records = session.exec(select(SQLogRecord)).all()
        print(f"\n{'ID':<5} {'LEVEL':<10} {'MESSAGE'}")
        print("-" * 60)
        for r in records:
            print(f"{r.id:<5} {r.loglevel:<10} {r.message}")
