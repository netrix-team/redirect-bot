from pydantic_settings import BaseSettings


class Config(BaseSettings):
    token: str

    # database
    mongo_url: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Config()
