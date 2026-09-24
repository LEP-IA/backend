from fastapi import APIRouter

router = APIRouter(
  prefix="/github",
  tags=["GitHub"],
)

@router.get("/setup")
def github_setup(installation_id: int, setup_action: str | None = None):
  return {
    "installation_id": installation_id,
    "setup_action": setup_action,
  }
  

