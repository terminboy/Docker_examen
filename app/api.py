from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import City, Country
from app.schemas import (
    CityCreate,
    CityResponse,
    CountryCreate,
    CountryResponse,
)


router = APIRouter(prefix="/api", tags=["API"])


@router.post(
    "/countries",
    response_model=CountryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_country(
    country_data: CountryCreate,
    db: AsyncSession = Depends(get_db),
):
    country = Country(name=country_data.name)
    db.add(country)
    await db.commit()
    await db.refresh(country)
    return country


@router.get("/countries", response_model=list[CountryResponse])
async def get_countries(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Country).order_by(Country.name))
    return result.scalars().all()


@router.post(
    "/cities",
    response_model=CityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_city(
    city_data: CityCreate,
    db: AsyncSession = Depends(get_db),
):
    country = await db.get(Country, city_data.country_id)
    if country is None:
        raise HTTPException(status_code=404, detail="Страна не найдена")

    city = City(**city_data.model_dump())
    db.add(city)
    await db.commit()
    await db.refresh(city)
    return city


@router.get("/cities", response_model=list[CityResponse])
async def get_cities(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(City)

    if search:
        query = query.where(City.name.ilike(f"%{search}%"))

    query = query.order_by(City.name).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/cities/{city_id}", response_model=CityResponse)
async def get_city(city_id: int, db: AsyncSession = Depends(get_db)):
    city = await db.get(City, city_id)
    if city is None:
        raise HTTPException(status_code=404, detail="Город не найден")
    return city
