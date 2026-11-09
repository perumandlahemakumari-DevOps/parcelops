from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Response, status
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Shipment
from app.schemas import ShipmentCreate, ShipmentStatusUpdate, ShipmentView


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="ParcelOps API", version="0.1.0", lifespan=lifespan)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/health", tags=["operations"])
def health():
    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
def readiness(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ready"}


@app.post("/shipments", response_model=ShipmentView, status_code=status.HTTP_201_CREATED)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)):
    shipment = Shipment(
        tracking_number=f"PKG-{uuid4().hex[:12].upper()}",
        recipient=payload.recipient,
        destination=payload.destination,
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


@app.get("/shipments", response_model=list[ShipmentView])
def list_shipments(db: Session = Depends(get_db)):
    return db.query(Shipment).order_by(Shipment.created_at.desc()).all()


@app.get("/shipments/{tracking_number}", response_model=ShipmentView)
def get_shipment(tracking_number: str, db: Session = Depends(get_db)):
    shipment = db.get(Shipment, tracking_number)
    if shipment is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    return shipment


@app.patch("/shipments/{tracking_number}/status", response_model=ShipmentView)
def update_status(tracking_number: str, payload: ShipmentStatusUpdate, db: Session = Depends(get_db)):
    shipment = db.get(Shipment, tracking_number)
    if shipment is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    shipment.status = payload.status
    db.commit()
    db.refresh(shipment)
    return shipment


@app.get("/", include_in_schema=False)
def root():
    return Response(status_code=204)
