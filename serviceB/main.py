import asyncio
import aio_pika
import random
import logging
from logging.handlers import RotatingFileHandler
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
import configparser


LOG_FILE = "/app/service_b.log"

# Setup logging
logger = logging.getLogger("service_b")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

config_parser = configparser.ConfigParser()
config_parser.read("config.ini")
rabbit_conf = config_parser["rabbitmq"]

app = Starlette()

@app.on_event("startup")
async def startup():
    logger.info("Starting service B")
    app.state.connection = await aio_pika.connect_robust(
        host=rabbit_conf["host"],
        port=int(rabbit_conf["port"]),
        login=rabbit_conf["login"],
        password=rabbit_conf["password"],
    )
    app.state.channel = await app.state.connection.channel()
    app.state.queue = await app.state.channel.declare_queue("ping", durable=True)

    async def consume():
        async with app.state.queue.iterator() as q:
            async for message in q:
                async with message.process():
                    logger.info(f"Received: {message.body.decode()}")

    async def cpu_check():
        while True:
            temp = round(random.uniform(45, 70), 1)
            logger.info(f"CPU temp: {temp}°C")
            await asyncio.sleep(5)

    asyncio.create_task(consume())
    asyncio.create_task(cpu_check())

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down service B")
    await app.state.connection.close()

@app.route("/")
async def index(request):
    return PlainTextResponse("Service B Running")
