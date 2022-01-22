from enum import Enum
from typing import List, Set

from fastapi import Body, FastAPI, Path, Query

from pydantic import BaseModel, Field, HttpUrl


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Image(BaseModel):
    url: HttpUrl
    name: str


class Item(BaseModel):
    name: str
    description: str | None = Field(
        None,
        title="The description of the item",
        max_length=300,
    )
    price: float = Field(
        ...,
        gt=0,
        description="The price must be greater than zero")
    tax: float | None = None
    tags: List[str] = []
    keks: Set[str] = set()
    images: List[Image] | None = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Foo",
                "description": "A very nice Item",
                "price": 35.4,
                "tax": 3.2,
                "tags": ["bar", "baz"],
                "keks": {"bar", "baz"},
                "images": [
                    { "url": "https://lol.kek", "name": "Lol kek" },
                    { "url": "https://kek.lol", "name": "Kek lol" },
                ],
            }
        }


class Offer(BaseModel):
    name: str = Field(..., example="Foo")
    description: str | None = Field(None, example="Bar")
    price: float = Field(..., example=5.4)
    items: List[Item]


class User(BaseModel):
    username: str
    full_name: str | None = None
    image: Image | None = None


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}


fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]

@app.post("/items/")
async def create_item(item: Item = Body(..., embed=True)):
    item_dict = item.dict()
    if item.tax:
        item_dict.update({
            "price_with_tax": item.price + item.tax
        })
    return item_dict

@app.put("/items/{item_id}")
async def update_item(
    item_id: int, item: Item, user: User, importance: int = Body(..., gt=5)
):
    results = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    return results


@app.get("/item/{item_id}")
async def read_item(
    item_id: int = Path(..., title="The ID of the item to get", ge=10, lt=1000),
    needy: List[str] = Query(
        ...,
        title="Querty string",
        description="Query string for the items to search in the database that have a good match",
        alias="kek-lol",
        regex="^[0-9]*$"),
    q: str | None = Query(None, min_length=2, max_length=5, regex="^[a-zA-Z]*$"),
    short: bool = False
):
    item = {"item_id": item_id, "needy": needy}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int,
    item_id: str,
    q: str | None = None,
    short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item
