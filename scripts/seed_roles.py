from app.database import SessionLocal
from app.models.role import Role
from fastapi import Depends




roles=["Admin",
       "Manager",
       "Employee"
       ]

def seed_roles():
    db = SessionLocal()
    try:
        for new_role in roles:
            existing_role = (db.query(Role).filter(Role.role_name == new_role).first())

            if not existing_role:
                new_role=Role(role_name = new_role)
                db.add(new_role)
        db.commit()          

        print("Role seeding completed!")


    except Exception:
        db.rollback()   
        raise

    finally:
        db.close()



if __name__ =='__main__':
    seed_roles()
