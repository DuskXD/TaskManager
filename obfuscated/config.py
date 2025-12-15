from pydantic_settings import BaseSettings
class Settings(BaseSettings):
	DATABASE_URL:str;SECRET_KEY:str;ALGORITHM:str='HS256';ACCESS_TOKEN_EXPIRE_MINUTES:int=30;REFRESH_TOKEN_EXPIRE_DAYS:int=7;DEBUG:bool=False;PROJECT_NAME:str='TaskManager API'
	class Config:env_file='.env';case_sensitive=True
settings=Settings()