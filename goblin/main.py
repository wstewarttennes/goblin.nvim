###############################################################################################
# Goblin is a server that can run workflows both by command or based on predefined triggers.  #
###############################################################################################
from fastapi import FastAPI
import uvicorn



app = FastAPI()


@app.get("/")
async def root():
    print("triggered")
    return {"message": "Hello wowww"}

@app.get("/trigger")
async def trigger():
    print("triggered")
    return {"message": "Hello wowww"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008, reload=True)
