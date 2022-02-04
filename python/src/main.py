from datetime import datetime, time, timedelta
from enum import Enum
from typing import List, Set
from uuid import UUID

from fastapi import (
    Body, Cookie, FastAPI, Form, Header, Path, Query, status, File, UploadFile,
    HTTPException, Request,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse

from pydantic import BaseModel, EmailStr, Field, HttpUrl

from starlette.exceptions import HTTPException as StarletteHTTPException


class UnicornException(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id


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


class Tags(Enum):
    items = "items"
    users = "users"


app = FastAPI()


@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )

# @app.exception_handler(StarletteHTTPException)
# async def http_exception_handler(request, exc):
#     return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    print(f"OMG! An HTTP error!: {repr(exc)}")
    return await http_exception_handler(request, exc)


# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
#     )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"OMG! The client sent invalid data!: {exc}")
    return await request_validation_exception_handler(request, exc)


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

@app.get("/items/", tags=Tags.items)
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]

@app.post(
    "/items/",
    status_code=status.HTTP_201_CREATED,
    tags=Tags.items,
    summary="Create an item",
    response_description="The created item",
)
async def create_item(item: Item = Body(..., embed=True)):
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """

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
    if item_id < 20:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
    elif item_id == 20:
        raise UnicornException(item_id=item_id)
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


@app.post("/user/", response_model=UserOut, tags=Tags.users)
async def create_user(user_in: UserIn):
    user_saved = fake_save_user(user_in)
    return user_saved


@app.post("/login/")
async def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}


@app.post("/files/")
async def create_file(
    file: bytes = File(...),
    fileb: UploadFile = File(...),
    token: str = Form(...)
):
    if not file:
        return {"message": "No file sent"}
    else:
        return {"file_size": len(file)}


@app.post("/uploadfile/")
async def create_upload_file(
    file: UploadFile = File(..., description="A file read as UploadFile")
):
    if not file:
        return {"message": "No upload file sent"}
    else:
        return {"filename": file.filename}


@app.post("/files-multiple/")
async def create_files_multiple(files: list[bytes] = File(...)):
    return {"file_sizes": [len(file) for file in files]}


@app.post("/uploadfiles-multiple/")
async def create_upload_files_multiple(
    files: list[UploadFile] = File(..., description="Multiple files as UploadFile")
):
    return {"filenames": [file.filename for file in files]}
