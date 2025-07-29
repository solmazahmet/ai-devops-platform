"""
Database Konfigürasyonu
SQLAlchemy async database bağlantısı ve session yönetimi
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError
import logging
from typing import AsyncGenerator, Optional
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings, get_database_config

logger = logging.getLogger(__name__)

# Database metadata
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

# Base class for models
Base = declarative_base(metadata=metadata)

# Database configuration
db_config = get_database_config()

# Async database engine
async_engine = None
async_session_maker = None

# Sync database engine (for migrations and testing)
sync_engine = None
SessionLocal = None


async def init_database() -> None:
    """Async database başlatma"""
    global async_engine, async_session_maker, sync_engine, SessionLocal
    
    try:
        # Async engine oluştur
        async_engine = create_async_engine(
            db_config["url"].replace("postgresql://", "postgresql+asyncpg://"),
            pool_size=db_config["pool_size"],
            max_overflow=db_config["max_overflow"],
            pool_timeout=db_config["pool_timeout"],
            pool_recycle=db_config["pool_recycle"],
            echo=db_config["echo"],
            future=True
        )
        
        # Async session maker
        async_session_maker = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        # Sync engine (migrations için)
        sync_engine = create_engine(
            db_config["url"],
            pool_size=db_config["pool_size"],
            max_overflow=db_config["max_overflow"],
            pool_timeout=db_config["pool_timeout"],
            pool_recycle=db_config["pool_recycle"],
            echo=db_config["echo"]
        )
        
        # Sync session maker
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=sync_engine
        )
        
        logger.info("Database engines başarıyla oluşturuldu")
        
    except Exception as e:
        logger.error(f"Database başlatma hatası: {e}")
        raise


async def close_database() -> None:
    """Database bağlantılarını kapat"""
    global async_engine, sync_engine
    
    try:
        if async_engine:
            await async_engine.dispose()
            logger.info("Async database engine kapatıldı")
        
        if sync_engine:
            sync_engine.dispose()
            logger.info("Sync database engine kapatıldı")
            
    except Exception as e:
        logger.error(f"Database kapatma hatası: {e}")


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Async database session dependency"""
    if not async_session_maker:
        await init_database()
    
    async with async_session_maker() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


def get_sync_db():
    """Sync database session dependency"""
    if not SessionLocal:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()


def get_test_db():
    """Test database session dependency"""
    test_engine = create_engine(
        settings.TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        test_engine.dispose()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions"""
    if not async_session_maker:
        await init_database()
    
    async with async_session_maker() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """Database bağlantısını kontrol et"""
    try:
        if not async_engine:
            await init_database()
        
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        logger.info("Database bağlantısı başarılı")
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def create_tables() -> None:
    """Database tablolarını oluştur"""
    try:
        if not sync_engine:
            raise RuntimeError("Database not initialized")
        
        # Import all models to register them
        from app.models import user, test, jira
        
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Database tabloları oluşturuldu")
        
    except Exception as e:
        logger.error(f"Table creation error: {e}")
        raise


async def drop_tables() -> None:
    """Database tablolarını sil (sadece test için)"""
    try:
        if not sync_engine:
            raise RuntimeError("Database not initialized")
        
        Base.metadata.drop_all(bind=sync_engine)
        logger.info("Database tabloları silindi")
        
    except Exception as e:
        logger.error(f"Table deletion error: {e}")
        raise


async def reset_database() -> None:
    """Database'i sıfırla (sadece test için)"""
    try:
        await drop_tables()
        await create_tables()
        logger.info("Database sıfırlandı")
        
    except Exception as e:
        logger.error(f"Database reset error: {e}")
        raise


class DatabaseManager:
    """Database yönetim sınıfı"""
    
    def __init__(self):
        self.engine = None
        self.session_maker = None
    
    async def initialize(self) -> None:
        """Database manager'ı başlat"""
        await init_database()
        self.engine = async_engine
        self.session_maker = async_session_maker
    
    async def get_session(self) -> AsyncSession:
        """Database session al"""
        if not self.session_maker:
            await self.initialize()
        
        return self.session_maker()
    
    async def execute_query(self, query: str, params: Optional[dict] = None) -> any:
        """Raw SQL query çalıştır"""
        async with self.get_session() as session:
            try:
                result = await session.execute(query, params or {})
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logger.error(f"Query execution error: {e}")
                raise
    
    async def health_check(self) -> dict:
        """Database sağlık kontrolü"""
        try:
            is_connected = await check_database_connection()
            
            if is_connected:
                # Pool durumunu kontrol et
                pool_info = {
                    "pool_size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow()
                }
                
                return {
                    "status": "healthy",
                    "connected": True,
                    "pool_info": pool_info,
                    "message": "Database connection is healthy"
                }
            else:
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "message": "Database connection failed"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e),
                "message": "Database health check failed"
            }


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_manager() -> DatabaseManager:
    """Database manager instance'ını döndür"""
    if not db_manager.engine:
        await db_manager.initialize()
    return db_manager


# Database event handlers
async def on_startup():
    """Uygulama başlangıcında database'i başlat"""
    try:
        await init_database()
        await check_database_connection()
        logger.info("Database startup completed")
    except Exception as e:
        logger.error(f"Database startup failed: {e}")
        raise


async def on_shutdown():
    """Uygulama kapanışında database'i kapat"""
    try:
        await close_database()
        logger.info("Database shutdown completed")
    except Exception as e:
        logger.error(f"Database shutdown failed: {e}")


# Database exception handlers
class DatabaseException(Exception):
    """Base database exception"""
    pass


class DatabaseConnectionException(DatabaseException):
    """Database bağlantı hatası"""
    pass


class DatabaseQueryException(DatabaseException):
    """Database query hatası"""
    pass


class DatabaseIntegrityException(DatabaseException):
    """Database integrity hatası"""
    pass


def handle_database_error(error: SQLAlchemyError) -> DatabaseException:
    """Database hatalarını handle et"""
    if isinstance(error, OperationalError):
        return DatabaseConnectionException(f"Database connection error: {error}")
    elif isinstance(error, IntegrityError):
        return DatabaseIntegrityException(f"Database integrity error: {error}")
    else:
        return DatabaseQueryException(f"Database query error: {error}")


# Database utilities
async def execute_in_transaction(func, *args, **kwargs):
    """Transaction içinde fonksiyon çalıştır"""
    async with get_db_session() as session:
        try:
            result = await func(session, *args, **kwargs)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            logger.error(f"Transaction error: {e}")
            raise


async def bulk_insert(model_class, data_list: list):
    """Bulk insert işlemi"""
    async with get_db_session() as session:
        try:
            objects = [model_class(**data) for data in data_list]
            session.add_all(objects)
            await session.commit()
            return objects
        except Exception as e:
            await session.rollback()
            logger.error(f"Bulk insert error: {e}")
            raise


async def bulk_update(model_class, filter_criteria: dict, update_data: dict):
    """Bulk update işlemi"""
    async with get_db_session() as session:
        try:
            result = await session.execute(
                f"UPDATE {model_class.__tablename__} SET {', '.join([f'{k} = :{k}' for k in update_data.keys()])} WHERE {filter_criteria}",
                update_data
            )
            await session.commit()
            return result.rowcount
        except Exception as e:
            await session.rollback()
            logger.error(f"Bulk update error: {e}")
            raise 