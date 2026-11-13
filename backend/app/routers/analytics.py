from datetime import datetime, timedelta, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_roles
from app.config import CO2_KG_PER_KG_FOOD, COST_SAVED_PER_KG
from app.database import get_db
from app.models import DailyRecord, Kitchen, Pickup, SurplusListing, User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def month_bounds(month: str) -> tuple[datetime, datetime]:
    try:
        first = datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(422, "Month must use YYYY-MM format.")
    following_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return first, following_month


def summary(db: Session, kitchen_id: int | None = None, selected_month: str | None = None) -> dict:
    query = db.query(SurplusListing, Pickup.completed_at).outerjoin(
        Pickup, Pickup.listing_id == SurplusListing.id
    ).filter(SurplusListing.status == "DELIVERED")
    if kitchen_id is not None:
        query = query.filter(SurplusListing.kitchen_id == kitchen_id)
    delivered_rows = query.all()

    records_query = db.query(DailyRecord)
    if kitchen_id is not None:
        records_query = records_query.filter(DailyRecord.kitchen_id == kitchen_id)
    waste_by_month: dict[str, int] = {}
    for record in records_query.all():
        key = record.date.strftime("%Y-%m")
        waste_by_month[key] = waste_by_month.get(key, 0) + max(0, record.meals_prepared - record.meals_consumed)

    monthly_saved: dict[str, float] = {}
    for listing, completed_at in delivered_rows:
        key = (completed_at or listing.created_at).strftime("%Y-%m")
        monthly_saved[key] = monthly_saved.get(key, 0) + listing.quantity_kg

    all_months = sorted(set(waste_by_month) | set(monthly_saved))
    observed_waste_months = sorted(waste_by_month)
    baseline_waste = waste_by_month.get(observed_waste_months[0], 0) if observed_waste_months else 0
    monthly = []
    for key in all_months:
        waste = waste_by_month.get(key, 0)
        reduction = round((baseline_waste - waste) / baseline_waste * 100, 2) if baseline_waste and key in waste_by_month else 0
        monthly.append({
            "month": key, "food_saved_kg": round(monthly_saved.get(key, 0), 2),
            "waste_reduction_percent": reduction,
        })

    if selected_month:
        start, end = month_bounds(selected_month)
        delivered = [
            listing for listing, completed_at in delivered_rows
            if start <= (completed_at or listing.created_at) < end
        ]
    else:
        delivered = [listing for listing, _ in delivered_rows]
    saved_kg = round(sum(row.quantity_kg for row in delivered), 2)
    reduction = (
        round((baseline_waste - waste_by_month[observed_waste_months[-1]]) / baseline_waste * 100, 2)
        if baseline_waste and observed_waste_months else 0
    )
    return {
        "food_saved_kg": saved_kg,
        "meals_donated": round(saved_kg * 3),
        "co2_avoided_kg": round(saved_kg * CO2_KG_PER_KG_FOOD, 2),
        "cost_saved": round(saved_kg * COST_SAVED_PER_KG, 2),
        "waste_reduction_percent": reduction,
        "co2_factor_kg_per_kg": CO2_KG_PER_KG_FOOD,
        "monthly": monthly,
        "reporting_month": selected_month,
    }


@router.get("")
def analytics(
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kitchen_id = None
    if user.role == "KITCHEN_ADMIN":
        kitchen = db.query(Kitchen).filter_by(user_id=user.id).first()
        kitchen_id = kitchen.id if kitchen else -1
    return summary(db, kitchen_id, month)


@router.get("/report.pdf")
def esg_report(
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("KITCHEN_ADMIN", "SUPER_ADMIN")),
):
    kitchen_id = None
    title = "AnnaSetu Monthly ESG Impact Report"
    if user.role == "KITCHEN_ADMIN":
        kitchen = db.query(Kitchen).filter_by(user_id=user.id).first()
        kitchen_id = kitchen.id if kitchen else -1
        title = f"{kitchen.name if kitchen else 'Kitchen'} - ESG Impact Report"
    report_month = month or datetime.now(timezone.utc).strftime("%Y-%m")
    data = summary(db, kitchen_id, report_month)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(55, 740, title)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(55, 715, f"Generated: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
    pdf.drawString(55, 675, f"Impact metrics for {report_month} (delivered food only)")
    for index, (label, value) in enumerate([
        ("Food saved", f"{data['food_saved_kg']} kg"),
        ("Estimated meals donated", str(data["meals_donated"])),
        ("CO2 emissions avoided", f"{data['co2_avoided_kg']} kg CO2e"),
        ("Estimated food cost saved", f"INR {data['cost_saved']:,.2f}"),
        ("CO2 factor used", f"{data['co2_factor_kg_per_kg']} kg CO2e per kg food"),
    ]):
        pdf.drawString(65, 645 - index * 24, f"{label}: {value}")
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(55, 500, "Estimates use configurable factors; meals are estimated at 3 meals per kg.")
    pdf.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=annasetu-esg-report.pdf"})
