from pydantic import BaseModel, ConfigDict, Field


class CountryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CountryResponse(CountryCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    population: int = Field(ge=0)
    country_id: int


class CityResponse(CityCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
