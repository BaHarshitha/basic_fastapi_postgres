from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from databases import Database
import sqlalchemy
import uvicorn


DATABASE_URL = "postgresql://postgres:root123@localhost/project"

# Database
database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# SQLAlchemy
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class ProductCreate(BaseModel):
    name: str
    description: str

class ProductDB(ProductCreate):
    id: int

    class Config:
        orm_mode = True

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/products/", response_model=ProductDB)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(name=product.name, description=product.description)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/product/{product_id}", response_model=ProductDB)
async def read_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@app.get("/products/",response_model=list[ProductDB])
async def fetch_products(db: Session = Depends(get_db)):
    
    db_products = db.query(Product).all()
    if db_products is None:
        raise HTTPException(status_code=404, detail="Products not found")
    return db_products


@app.put("/product/{product_id}", response_model=ProductDB)
async def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db_product.name = product.name
    db_product.description = product.description
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/product/{product_id}", response_model=ProductDB)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return db_product

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
