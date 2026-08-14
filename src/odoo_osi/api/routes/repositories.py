from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from odoo_osi.db.models import Repository
from odoo_osi.db.session import get_session

router = APIRouter(prefix="/repositories", tags=["repositories"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class RepositoryListItem(BaseModel):
    owner: str
    name: str
    full_name: str
    url: str
    description: str | None
    default_branch: str | None
    stars: int
    forks: int
    open_issues: int
    license: str | None
    archived: bool
    module_count: int
    branch_count: int


class RepositoryListResponse(BaseModel):
    repositories: list[RepositoryListItem]


class RepositoryDetailResponse(RepositoryListItem):
    branches: list[str]
    odoo_versions: list[str]


@router.get("", response_model=RepositoryListResponse)
async def list_repositories(session: SessionDep) -> RepositoryListResponse:
    result = await session.execute(
        select(Repository).options(
            selectinload(Repository.branches),
            selectinload(Repository.modules),
        )
    )
    repositories = result.scalars().all()
    return RepositoryListResponse(
        repositories=[_repository_list_item(repository) for repository in repositories]
    )


@router.get("/{owner}/{name}", response_model=RepositoryDetailResponse)
async def get_repository(owner: str, name: str, session: SessionDep) -> RepositoryDetailResponse:
    result = await session.execute(
        select(Repository)
        .where(Repository.owner == owner, Repository.name == name)
        .options(
            selectinload(Repository.branches),
            selectinload(Repository.modules),
        )
    )
    repository = result.scalar_one_or_none()
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    return RepositoryDetailResponse(
        **_repository_list_item(repository).model_dump(),
        branches=sorted(branch.name for branch in repository.branches),
        odoo_versions=sorted(
            {branch.odoo_version for branch in repository.branches if branch.odoo_version}
        ),
    )


def _repository_list_item(repository: Repository) -> RepositoryListItem:
    return RepositoryListItem(
        owner=repository.owner,
        name=repository.name,
        full_name=repository.full_name,
        url=repository.url,
        description=repository.description,
        default_branch=repository.default_branch,
        stars=repository.stars,
        forks=repository.forks,
        open_issues=repository.open_issues,
        license=repository.license,
        archived=repository.archived,
        module_count=len(repository.modules),
        branch_count=len(repository.branches),
    )

