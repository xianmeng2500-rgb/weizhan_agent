"""轻量幂等表结构迁移

背景：本项目线上用宝塔面板部署，未引入 alembic。
`Base.metadata.create_all()` 只能建新表，**不会给已存在的表补列**。
新增列时用这里的 ensure_columns() 做幂等 ALTER，启动时自动补，
避免每次上线都要手动执行 SQL。

用法（main.py lifespan 内调用）：
    from app.utils.migrate import ensure_schema
    ensure_schema(engine)
"""
import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# 表名 -> [(列名, 建列 DDL 片段), ...]
_REQUIRED_COLUMNS: dict[str, list[tuple[str, str]]] = {}

# 幂等加索引：表名 -> [(索引名, 列名), ...]
_REQUIRED_INDEXES: dict[str, list[tuple[str, str]]] = {}


def ensure_schema(engine: Engine) -> None:
    """补齐缺失的列与索引（已存在则跳过，可重复执行）"""
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
    except Exception as e:  # noqa: BLE001 数据库不可用时不应阻断启动
        logger.warning(f"[MIGRATE] 跳过表结构检查（无法连接数据库）: {e}")
        return

    with engine.begin() as conn:
        for table, columns in _REQUIRED_COLUMNS.items():
            if table not in existing_tables:
                continue  # 新表由 create_all 负责
            try:
                present = {c["name"] for c in inspect(engine).get_columns(table)}
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[MIGRATE] 读取 {table} 列信息失败: {e}")
                continue
            for col_name, ddl in columns:
                if col_name in present:
                    continue
                logger.info(f"[MIGRATE] {table} 补列: {col_name}")
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {ddl}"))

        for table, indexes in _REQUIRED_INDEXES.items():
            if table not in existing_tables:
                continue
            try:
                present_idx = {i["name"] for i in inspect(engine).get_indexes(table)}
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[MIGRATE] 读取 {table} 索引信息失败: {e}")
                continue
            for idx_name, col in indexes:
                if idx_name in present_idx:
                    continue
                logger.info(f"[MIGRATE] {table} 补索引: {idx_name}")
                conn.execute(text(f"CREATE INDEX {idx_name} ON {table} ({col})"))
