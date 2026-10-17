from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import City, Country


router = APIRouter(tags=["Страницы"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", include_in_schema=False)
async def home():
    return RedirectResponse(url="/countries")


@router.get("/countries")
async def countries_page(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Country).order_by(Country.name))
    countries = result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="countries.html",
        context={"countries": countries},
    )


@router.get("/countries/{country_id}/cities")
async def country_cities_page(
    country_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    country = await db.get(Country, country_id)
    if country is None:
        raise HTTPException(status_code=404, detail="Страна не найдена")

    result = await db.execute(
        select(City)
        .where(City.country_id == country_id)
        .order_by(City.name)
    )
    cities = result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="country_cities.html",
        context={"country": country, "cities": cities},
    )


@router.get("/cities")
async def cities_page(
    request: Request,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    condition = City.name.ilike(f"%{search}%") if search else None

    count_query = select(func.count()).select_from(City)
    cities_query = select(City, Country).join(Country)
    if condition is not None:
        count_query = count_query.where(condition)
        cities_query = cities_query.where(condition)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        cities_query.order_by(City.name).offset((page - 1) * limit).limit(limit)
    )
    cities = [
        {"city": city, "country": country}
        for city, country in result.all()
    ]

    return templates.TemplateResponse(
        request=request,
        name="cities.html",
        context={
            "cities": cities,
            "search": search or "",
            "page": page,
            "limit": limit,
            "has_next": page * limit < total,
        },
    )


@router.get("/cities/add")
async def add_city_form(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Country).order_by(Country.name))
    countries = result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="city_form.html",
        context={"countries": countries},
    )


@router.post("/cities/add")
async def add_city(
    name: str = Form(),
    population: int = Form(),
    country_id: int = Form(),
    db: AsyncSession = Depends(get_db),
):
    country = await db.get(Country, country_id)
    if country is None:
        raise HTTPException(status_code=404, detail="Страна не найдена")

    city = City(name=name, population=population, country_id=country_id)
    db.add(city)
    await db.commit()
    await db.refresh(city)
    return RedirectResponse(url=f"/cities/{city.id}", status_code=303)


@router.get("/cities/{city_id}")
async def city_detail_page(
    city_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(City, Country)
        .join(Country)
        .where(City.id == city_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Город не найден")

    city, country = row
    return templates.TemplateResponse(
        request=request,
        name="city_detail.html",
        context={"city": city, "country": country},
    )
