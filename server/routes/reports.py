"""TIER 1 intake. Returns the public reference immediately; enrichment runs after the response."""
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from routes.deps import get_db
from services.core import assessment, intake, tickets
from services.workflow import pipeline

router = APIRouter(prefix='/api', tags=['tier1-intake'])


@router.post('/reports', status_code=201)
def create_report(request: Request, background: BackgroundTasks, image: UploadFile = File(...),
                  lat: float | None = Form(None), lng: float | None = Form(None),
                  description: str = Form(''), db: Session = Depends(get_db)):
    try:
        report = intake.validate(image.file.read(), lat, lng, description)
    except intake.IntakeError as e:
        raise HTTPException(422, {'code': e.code, 'message': e.message})

    dup = intake.find_duplicate(db, report)
    if dup:
        return JSONResponse(status_code=200, content={'public_ref': dup.public_ref, 'status': dup.status, 'duplicate': True})

    upload = intake.store_upload(db, report)
    result = assessment.assess(report.image_bytes)
    ticket = tickets.create_ticket(db, lat=report.lat, lng=report.lng, description=report.description,
                                   category=result.category, severity=result.severity, photo_asset_id=upload.id,
                                   needs_human_review=result.needs_human_review)
    tickets.add_event(db, ticket.id, 'ai_assessment', result.as_payload(), 'system:ai')
    upload.ticket_id = ticket.id
    db.commit()

    background.add_task(pipeline.run_enrichment, request.app.state.session_factory, ticket.id)
    return {'public_ref': ticket.public_ref, 'status': ticket.status, 'category': ticket.category,
            'severity': ticket.severity, 'needs_human_review': ticket.needs_human_review,
            'quality_flags': report.quality_flags, 'duplicate': False}
