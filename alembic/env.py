import os
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

# Make sure project root (C:\dev\valhalla) is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.base import Base

# Import models so Alembic autogenerate can detect them.
# Previous packs
from app.models.pack_sp import CrisisEvent, CrisisResponsePlan, CrisisResolutionLog
from app.models.pack_sq import HouseholdMember, SharedResponsibility, HouseholdExpense, MealPlan
from app.models.pack_so import LegacyDocument, LegacyRecipient, SuccessionStage, SuccessionTransfer

# PACK ST, SU, SV
from app.models.pack_st import FinancialIndicator, FinancialStressEvent, FinancialStressSummary
from app.models.pack_su import SafetyCategory, SafetyChecklist, SafetyPlan, SafetyEventLog
from app.models.pack_sv import EmpireGoal, GoalMilestone, ActionStep

# PACK SW, SX, SY
from app.models.pack_sw import LifeEvent, LifeMilestone, LifeTimelineSnapshot
from app.models.pack_sx import EmotionalStateEntry, StabilityLog, NeutralSummary
from app.models.pack_sy import StrategicDecision, DecisionRevision, DecisionChainSnapshot

# PACK SZ, TA, TB
from app.models.pack_sz import PhilosophyRecord, EmpirePrinciple, PhilosophySnapshot
from app.models.pack_ta import RelationshipProfile, TrustEventLog, RelationshipMapSnapshot
from app.models.pack_tb import DailyRhythmProfile, TempoRule, DailyTempoSnapshot

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
