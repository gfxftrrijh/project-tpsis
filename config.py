class Config:
    SECRET_KEY = '4321'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:1234@localhost/payment_app'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
