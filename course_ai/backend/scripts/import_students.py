import asyncio
import csv
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Student


async def run(path: str):
    async with SessionLocal() as db:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                number, name = row["student_no"].strip(), row["name"].strip()
                student = (await db.execute(select(Student).where(Student.student_no == number))).scalar_one_or_none()
                if student:
                    student.name, student.status = name, "active"
                else:
                    db.add(Student(student_no=number, name=name))
        await db.commit()


if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))

