class Config:
    SECRET_KEY = '4321'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/payment_app'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
