from fastapi import FastAPI

app = FastAPI()


from app.routes.role import router as role_router
app.include_router(role_router)

from app.routes.employee import router as employee_router  
app.include_router(employee_router)

from app.routes.skill import router as skill_router
app.include_router(skill_router)

from app.routes.employee_skill import router as employee_skill_router
app.include_router(employee_skill_router)

from app.routes.project import router as project_router
app.include_router(project_router)

from app.routes.project_required_skill import router as project_required_skill_router
app.include_router(project_required_skill_router)


@app.get("/")
def home():
    return {"message": "Employee Management API is running"}


