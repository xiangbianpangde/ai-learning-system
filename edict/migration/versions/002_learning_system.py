"""learning system schema - Phase 2 Week 6

Revision ID: 002_learning_system
Revises: 001_initial
Create Date: 2026-03-26 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_learning_system"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── user_learning_styles 表 - 用戶學習風格 (VARK 模型) ──
    op.create_table(
        "user_learning_styles",
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("v_score", sa.Float(), server_default="0.0", nullable=False),  # Visual 0-100
        sa.Column("a_score", sa.Float(), server_default="0.0", nullable=False),  # Auditory 0-100
        sa.Column("r_score", sa.Float(), server_default="0.0", nullable=False),  # Read/Write 0-100
        sa.Column("k_score", sa.Float(), server_default="0.0", nullable=False),  # Kinesthetic 0-100
        sa.Column("dominant_style", sa.String(1), server_default="", nullable=False),  # V/A/R/K
        sa.Column("confidence", sa.Float(), server_default="0.0", nullable=False),  # 0-1
        sa.Column("questionnaire_completed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("behavior_data_collected", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("questionnaire_answers", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("behavior_metrics", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_user_learning_styles_dominant", "user_learning_styles", ["dominant_style"])
    op.create_index("ix_user_learning_styles_confidence", "user_learning_styles", ["confidence"])

    # ── item_parameters 表 - 題目難度參數 (IRT 2PL 模型) ──
    op.create_table(
        "item_parameters",
        sa.Column("item_id", sa.String(64), nullable=False),
        sa.Column("difficulty", sa.Float(), nullable=False),  # b parameter (-3 to +3)
        sa.Column("discrimination", sa.Float(), nullable=False),  # a parameter (0.5 to 2.0)
        sa.Column("difficulty_level", sa.Integer(), server_default="3", nullable=False),  # L1-L5
        sa.Column("knowledge_point_id", sa.String(64), server_default="", nullable=False),
        sa.Column("calibrated_by", sa.String(20), server_default="'expert'", nullable=False),  # 'expert' | 'sample_test'
        sa.Column("calibration_date", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("sample_size", sa.Integer(), server_default="0", nullable=False),  # 校準樣本數
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("item_id"),
    )
    op.create_index("ix_item_parameters_difficulty", "item_parameters", ["difficulty"])
    op.create_index("ix_item_parameters_level", "item_parameters", ["difficulty_level"])
    op.create_index("ix_item_parameters_kp", "item_parameters", ["knowledge_point_id"])

    # ── user_responses 表 - 用戶作答記錄 ──
    op.create_table(
        "user_responses",
        sa.Column("response_id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("item_id", sa.String(64), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("response_time", sa.Float(), nullable=False),  # seconds
        sa.Column("ability_estimate", sa.Float(), server_default="0.0", nullable=False),  # theta at response time
        sa.Column("is_cold_start", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("attempt_metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("response_id"),
    )
    op.create_index("ix_user_responses_user", "user_responses", ["user_id"])
    op.create_index("ix_user_responses_item", "user_responses", ["item_id"])
    op.create_index("ix_user_responses_attempted", "user_responses", ["attempted_at"])
    op.create_index("ix_user_responses_user_item", "user_responses", ["user_id", "item_id"])

    # ── forgetting_curves 表 - 遺忘曲線記錄 ──
    op.create_table(
        "forgetting_curves",
        sa.Column("curve_id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("item_id", sa.String(64), nullable=False),
        sa.Column("learned_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("decay_coefficient", sa.Float(), server_default="2.5", nullable=False),  # S parameter
        sa.Column("ease_factor", sa.Float(), server_default="2.5", nullable=False),  # SM-2 EF
        sa.Column("interval_days", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("retention_rate", sa.Float(), server_default="1.0", nullable=False),  # 0-1
        sa.Column("next_review", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_reviews", sa.Integer(), server_default="0", nullable=False),
        sa.Column("review_history", postgresql.JSONB(), server_default="[]", nullable=False),  # [{review_number, quality, interval_days, reviewed_at}]
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("curve_id"),
        sa.UniqueConstraint("user_id", "item_id", name="uq_forgetting_curves_user_item"),
    )
    op.create_index("ix_forgetting_curves_user", "forgetting_curves", ["user_id"])
    op.create_index("ix_forgetting_curves_item", "forgetting_curves", ["item_id"])
    op.create_index("ix_forgetting_curves_next_review", "forgetting_curves", ["next_review"])
    op.create_index("ix_forgetting_curves_retention", "forgetting_curves", ["retention_rate"])

    # ── knowledge_dependencies 表 - 知識依賴關係 ──
    op.create_table(
        "knowledge_dependencies",
        sa.Column("dep_id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("knowledge_point_id", sa.String(64), nullable=False),
        sa.Column("prerequisite_id", sa.String(64), nullable=False),  # 前置知識點
        sa.Column("dependency_type", sa.String(20), server_default="'required'", nullable=False),  # 'required' | 'recommended' | 'related'
        sa.Column("strength", sa.Float(), server_default="1.0", nullable=False),  # 依賴強度 0-1
        sa.Column("metadata", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("dep_id"),
        sa.UniqueConstraint("knowledge_point_id", "prerequisite_id", name="uq_knowledge_deps_kp_prereq"),
    )
    op.create_index("ix_knowledge_deps_kp", "knowledge_dependencies", ["knowledge_point_id"])
    op.create_index("ix_knowledge_deps_prereq", "knowledge_dependencies", ["prerequisite_id"])
    op.create_index("ix_knowledge_deps_type", "knowledge_dependencies", ["dependency_type"])


def downgrade() -> None:
    op.drop_table("knowledge_dependencies")
    op.drop_table("forgetting_curves")
    op.drop_table("user_responses")
    op.drop_table("item_parameters")
    op.drop_table("user_learning_styles")
