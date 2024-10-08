# Copyright 2022 Indoc Research
# 
# Licensed under the EUPL, Version 1.2 or – as soon they
# will be approved by the European Commission - subsequent
# versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the
# Licence.
# You may obtain a copy of the Licence at:
# 
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
# 
# Unless required by applicable law or agreed to in
# writing, software distributed under the Licence is
# distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.
# See the Licence for the specific language governing
# permissions and limitations under the Licence.
# 

"""Adding casbin table

Revision ID: e86797550c26
Revises: 4f5ec3f0ac37
Create Date: 2022-03-25 14:36:06.799722

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e86797550c26'
down_revision = '4f5ec3f0ac37'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('casbin_rule',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('ptype', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('v0', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('v1', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('v2', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('v3', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('v4', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('v5', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='casbin_rule_pkey'),
    schema='pilot_casbin'
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('casbin_rule')
    # ### end Alembic commands ###
