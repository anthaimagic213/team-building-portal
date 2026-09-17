from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.db.session import get_db
from app.schemas.journey import MyJourneyResponse
from app.services import journey_svc

router = APIRouter()

@router.get(
    "/tools/my-journey",
    response_model=MyJourneyResponse,
    description="Tool dành cho Agent: Truy xuất toàn bộ thông tin hành trình của User (Chuyến bay, Xe, Khách sạn, Gala). Không yêu cầu truyền tham số ID vì hệ thống tự bóc tách từ JWT token của người dùng."
)
async def tool_get_my_journey(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RAG Agent sẽ gọi endpoint này khi người dùng hỏi các câu như:
    - "Mai tôi bay lúc mấy giờ?"
    - "Xe nào đón tôi ở sân bay?"
    - "Tôi ngồi bàn nào đêm Gala?"
    """
    return journey_svc.get_full_journey(db, current_user)