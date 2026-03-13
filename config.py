class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/fitnessdb"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "supersecretkey"
    OTP_EXPIRE_TIME = 300 
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    MAIL_USERNAME = "velisalanaveen7477@gmail.com"
    MAIL_PASSWORD = "qbph sawl jtvn dwdl"