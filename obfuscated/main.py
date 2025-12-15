from fastapi import FastAPI,APIRouter
from fastapi.middleware.cors import CORSMiddleware
from.config import settings
from.routers import auth,users,projects,tasks
app=FastAPI(title=settings.PROJECT_NAME,description='API для системы управления задачами',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
api_v1=APIRouter(prefix='/api/v1')
api_v1.include_router(auth.router)
api_v1.include_router(users.router)
api_v1.include_router(projects.router)
api_v1.include_router(tasks.router)
app.include_router(api_v1)
@app.get('/')
def root():return{'message':'TaskManager API','version':'1.0.0','docs':'/docs','redoc':'/redoc'}
@app.get('/health')
def health_check():return{'status':'healthy'}