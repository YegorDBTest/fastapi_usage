from datetime import datetime, time, timedelta
from enum import Enum
from typing import List, Set
from uuid import UUID

from fastapi import (
    Body, Cookie, FastAPI, Form, Header, Path, Query, status, File, UploadFile
)

from pydantic import BaseModel, EmailStr, Field, HttpUrl


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

@app.post("/items/", status_code=status.HTTP_201_CREATED)
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


@app.put("/data/{data_id}")
async def update_data(
    data_id: UUID,
    start_datetime: datetime | None = Body(None),
    end_datetime: datetime | None = Body(None),
    repeat_at: time | None = Body(None),
    process_after: timedelta | None = Body(None),
):
    if start_datetime and process_after:
        start_process = start_datetime + process_after
    else:
        start_process = datetime.now()

    duration = (end_datetime or datetime.now()) - start_process

    return {
        "data_id": data_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "repeat_at": repeat_at,
        "process_after": process_after,
        "start_process": start_process,
        "duration": duration,
    }


@app.get("/ads/")
async def read_ads(
    ads_id: str | None = Cookie(None),
    asd_token: str | None = Header(None),
    x_token: list[str] | None = Header(None)
):
    return {
        "ads_id": ads_id,
        "Asd-Token": asd_token,
        "X-Token": x_token,
    }


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserIn(UserBase):
    password: str


class UserOut(UserBase):
    pass


class UserInDB(UserBase):
    hashed_password: str


def fake_password_hasher(raw_password: str):
    return "supersecret" + raw_password


def fake_save_user(user_in: UserIn):
    hashed_password = fake_password_hasher(user_in.password)
    user_in_db = UserInDB(**user_in.dict(), hashed_password=hashed_password)
    print("User saved! ..not really")
    return user_in_db


@app.post("/user/", response_model=UserOut)
async def create_user(user_in: UserIn):
    user_saved = fake_save_user(user_in)
    return user_saved


@app.post("/login/")
async def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}


@app.post("/files/")
async def create_file(file: bytes | None = File(None)):
    if not file:
        return {"message": "No file sent"}
    else:
        return {"file_size": len(file)}


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile | None = None):
    if not file:
        return {"message": "No upload file sent"}
    else:
        return {"filename": file.filename}
