"""add contacts and support participants

Revision ID: c31b9f4d82a1
Revises: 74909fb30ff4
Create Date: 2026-08-03 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c31b9f4d82a1"
down_revision: Union[str, Sequence[str], None] = "74909fb30ff4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "name = btrim(name) AND char_length(name) >= 1",
            name="ck_contacts_name_valid",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_contacts_organization_id_organizations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_contacts_organization_email_ci",
        "contacts",
        ["organization_id", sa.text("lower(email)")],
        unique=True,
    )

    op.add_column(
        "conversations",
        sa.Column("contact_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("assigned_user_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("author_user_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("author_contact_id", sa.Uuid(), nullable=True),
    )

    op.execute(
        """
        INSERT INTO contacts (id, organization_id, name, email)
        SELECT gen_random_uuid(), old_contacts.organization_id,
               old_contacts.name, old_contacts.email
        FROM (
            SELECT DISTINCT ON (c.organization_id, lower(u.email))
                   c.organization_id, u.name, u.email
            FROM conversations AS c
            JOIN users AS u ON u.id = c.created_by_user_id
            ORDER BY c.organization_id, lower(u.email), c.created_at, c.id
        ) AS old_contacts
        """
    )
    op.execute(
        """
        UPDATE conversations AS c
        SET contact_id = contact.id,
            assigned_user_id = c.created_by_user_id
        FROM users AS u
        JOIN contacts AS contact
          ON lower(contact.email) = lower(u.email)
        WHERE u.id = c.created_by_user_id
          AND contact.organization_id = c.organization_id
        """
    )
    op.execute(
        """
        UPDATE messages
        SET author_user_id = author_id,
            sender_type = CASE
                WHEN sender_type = 'USER' THEN 'AGENT'
                ELSE sender_type
            END
        """
    )

    op.alter_column("conversations", "contact_id", nullable=False)
    op.create_foreign_key(
        "fk_conversations_contact_id_contacts",
        "conversations",
        "contacts",
        ["contact_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_conversations_assigned_user_id_users",
        "conversations",
        "users",
        ["assigned_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "fk_conversations_created_by_user_id_users",
        "conversations",
        type_="foreignkey",
    )
    op.drop_column("conversations", "created_by_user_id")

    op.drop_constraint(
        "ck_messages_sender_author_valid",
        "messages",
        type_="check",
    )
    op.drop_constraint(
        "ck_messages_sender_type_valid",
        "messages",
        type_="check",
    )
    op.drop_constraint(
        "fk_messages_author_id_users",
        "messages",
        type_="foreignkey",
    )
    op.drop_column("messages", "author_id")
    op.create_foreign_key(
        "fk_messages_author_user_id_users",
        "messages",
        "users",
        ["author_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_messages_author_contact_id_contacts",
        "messages",
        "contacts",
        ["author_contact_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_messages_sender_type_valid",
        "messages",
        "sender_type IN ('CONTACT', 'AGENT', 'AI', 'SYSTEM')",
    )
    op.create_check_constraint(
        "ck_messages_sender_author_valid",
        "messages",
        "(sender_type = 'CONTACT' "
        "AND author_contact_id IS NOT NULL "
        "AND author_user_id IS NULL) "
        "OR (sender_type = 'AGENT' "
        "AND author_user_id IS NOT NULL "
        "AND author_contact_id IS NULL) "
        "OR (sender_type IN ('AI', 'SYSTEM') "
        "AND author_user_id IS NULL "
        "AND author_contact_id IS NULL)",
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM conversations
                WHERE assigned_user_id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Cannot downgrade: an unassigned conversation has no old creator';
            END IF;

            IF EXISTS (
                SELECT 1 FROM messages
                WHERE author_contact_id IS NOT NULL
            ) THEN
                RAISE EXCEPTION
                    'Cannot downgrade: contact-authored messages cannot become user-authored';
            END IF;
        END $$
        """
    )

    op.add_column(
        "conversations",
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
    )
    op.execute(
        "UPDATE conversations "
        "SET created_by_user_id = assigned_user_id"
    )
    op.alter_column(
        "conversations",
        "created_by_user_id",
        nullable=False,
    )
    op.create_foreign_key(
        "fk_conversations_created_by_user_id_users",
        "conversations",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.add_column(
        "messages",
        sa.Column("author_id", sa.Uuid(), nullable=True),
    )
    op.execute(
        """
        UPDATE messages
        SET author_id = author_user_id,
            sender_type = CASE
                WHEN sender_type = 'AGENT' THEN 'USER'
                ELSE sender_type
            END
        """
    )
    op.drop_constraint(
        "ck_messages_sender_author_valid",
        "messages",
        type_="check",
    )
    op.drop_constraint(
        "ck_messages_sender_type_valid",
        "messages",
        type_="check",
    )
    op.drop_constraint(
        "fk_messages_author_contact_id_contacts",
        "messages",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_messages_author_user_id_users",
        "messages",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_messages_author_id_users",
        "messages",
        "users",
        ["author_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_messages_sender_type_valid",
        "messages",
        "sender_type IN ('USER', 'AGENT', 'AI', 'SYSTEM')",
    )
    op.create_check_constraint(
        "ck_messages_sender_author_valid",
        "messages",
        "(sender_type IN ('USER', 'AGENT') AND author_id IS NOT NULL) "
        "OR (sender_type IN ('AI', 'SYSTEM') AND author_id IS NULL)",
    )
    op.drop_column("messages", "author_contact_id")
    op.drop_column("messages", "author_user_id")

    op.drop_constraint(
        "fk_conversations_assigned_user_id_users",
        "conversations",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_conversations_contact_id_contacts",
        "conversations",
        type_="foreignkey",
    )
    op.drop_column("conversations", "assigned_user_id")
    op.drop_column("conversations", "contact_id")

    op.drop_index(
        "uq_contacts_organization_email_ci",
        table_name="contacts",
    )
    op.drop_table("contacts")
