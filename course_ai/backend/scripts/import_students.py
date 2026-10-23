import asyncio
import csv
import sys

from argon2 import PasswordHasher
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Student


async def run(path: str):
    hasher = PasswordHasher()
    async with SessionLocal() as db:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                number, name = row["student_no"].strip(), row["name"].strip()
                password_hash = hasher.hash(row["password"].strip())
                student = (await db.execute(select(Student).where(Student.student_no == number))).scalar_one_or_none()
                if student:
                    student.name, student.password_hash, student.status = name, password_hash, "active"
                else:
                    db.add(Student(student_no=number, name=name, password_hash=password_hash))
        await db.commit()


if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

