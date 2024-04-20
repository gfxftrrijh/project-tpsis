class Config:
    SECRET_KEY = '4321'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@localhost/yourdatabase'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
