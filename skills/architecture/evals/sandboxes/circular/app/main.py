import hashlib

from fastapi import FastAPI, HTTPException

from app.models import Member
from app.schemas import MemberIn, MemberOut

app = FastAPI()
MEMBERS: dict[int, Member] = {}


@app.post("/members", status_code=201)
def create_member(body: MemberIn) -> MemberOut:
    member = body.to_member(len(MEMBERS) + 1, hashlib.sha256(body.password.encode()).hexdigest())
    MEMBERS[member.id] = member
    return member.to_out()


@app.get("/members/{member_id}")
def get_member(member_id: int) -> MemberOut:
    if member_id not in MEMBERS:
        raise HTTPException(404, f"member {member_id} not found")
    return MEMBERS[member_id].to_out()
