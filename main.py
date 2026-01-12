from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, HttpUrl, field_validator
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import httpx
import asyncio
from typing import List, Optional
import time

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/url_monitor.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class URLMonitor(Base):
    __tablename__ = "url_monitors"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    check_interval = Column(Integer)  # in minutes
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class HealthCheck(Base):
    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, index=True)
    status_code = Column(Integer, nullable=True)
    latency = Column(Float)  # in milliseconds
    is_up = Column(Boolean)
    error_message = Column(String, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Pydantic models
class URLMonitorCreate(BaseModel):
    url: HttpUrl
    check_interval: int

    @field_validator('check_interval')
    def validate_interval(cls, v):
        if v < 5 or v > 60:
            raise ValueError('check_interval must be between 5 and 60 minutes')
        return v

class URLMonitorResponse(BaseModel):
    id: int
    url: str
    check_interval: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class HealthCheckResponse(BaseModel):
    id: int
    monitor_id: int
    status_code: Optional[int]
    latency: float
    is_up: bool
    error_message: Optional[str]
    checked_at: datetime

    class Config:
        from_attributes = True

# FastAPI app
app = FastAPI(title="URL Monitor Service")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Background task to check URL
async def check_url(url: str, monitor_id: int):
    db = SessionLocal()
    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url)
                latency = (time.time() - start_time) * 1000  # Convert to ms

                health_check = HealthCheck(
                    monitor_id=monitor_id,
                    status_code=response.status_code,
                    latency=round(latency, 2),
                    is_up=response.status_code < 500,
                    checked_at=datetime.utcnow()
                )
            except Exception as e:
                latency = (time.time() - start_time) * 1000
                health_check = HealthCheck(
                    monitor_id=monitor_id,
                    latency=round(latency, 2),
                    is_up=False,
                    error_message=str(e),
                    checked_at=datetime.utcnow()
                )

        db.add(health_check)
        db.commit()
    finally:
        db.close()

# Background monitoring loop
async def monitoring_loop():
    while True:
        db = SessionLocal()
        try:
            monitors = db.query(URLMonitor).filter(URLMonitor.is_active == True).all()

            for monitor in monitors:
                last_check = db.query(HealthCheck)\
                    .filter(HealthCheck.monitor_id == monitor.id)\
                    .order_by(HealthCheck.checked_at.desc())\
                    .first()

                should_check = False
                if not last_check:
                    should_check = True
                else:
                    time_since_check = datetime.utcnow() - last_check.checked_at
                    if time_since_check >= timedelta(minutes=monitor.check_interval):
                        should_check = True

                if should_check:
                    asyncio.create_task(check_url(monitor.url, monitor.id))
        finally:
            db.close()

        await asyncio.sleep(30)  # Check every 30 seconds

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitoring_loop())

# API Endpoints
@app.post("/monitors/", response_model=URLMonitorResponse)
def create_monitor(monitor: URLMonitorCreate, db: Session = Depends(get_db)):
    db_monitor = URLMonitor(
        url=str(monitor.url),
        check_interval=monitor.check_interval
    )
    db.add(db_monitor)
    db.commit()
    db.refresh(db_monitor)
    return db_monitor

@app.get("/monitors/", response_model=List[URLMonitorResponse])
def list_monitors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    monitors = db.query(URLMonitor).offset(skip).limit(limit).all()
    return monitors

@app.get("/monitors/{monitor_id}", response_model=URLMonitorResponse)
def get_monitor(monitor_id: int, db: Session = Depends(get_db)):
    monitor = db.query(URLMonitor).filter(URLMonitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor

@app.delete("/monitors/{monitor_id}")
def delete_monitor(monitor_id: int, db: Session = Depends(get_db)):
    monitor = db.query(URLMonitor).filter(URLMonitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    monitor.is_active = False
    db.commit()
    return {"message": "Monitor deactivated"}

@app.get("/monitors/{monitor_id}/checks", response_model=List[HealthCheckResponse])
def get_health_checks(monitor_id: int, limit: int = 50, db: Session = Depends(get_db)):
    checks = db.query(HealthCheck)\
        .filter(HealthCheck.monitor_id == monitor_id)\
        .order_by(HealthCheck.checked_at.desc())\
        .limit(limit)\
        .all()
    return checks

@app.get("/")
def root():
    return {"message": "URL Monitor Service", "docs": "/docs"}
