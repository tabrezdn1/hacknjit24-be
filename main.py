from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()


HOST = '0.0.0.0'

if __name__ == '__main__':
    uvicorn.run('app.app:app', host = HOST, port = 8002, reload = True)