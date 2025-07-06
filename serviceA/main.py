import asyncio
import aio_pika
import logging
from logging.handlers import RotatingFileHandler
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse


LOG_FILE = "/app/service_a.log"

# Setup logging
logger = logging.getLogger("service_a")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Starlette()

@app.on_event("startup")
async def startup():
    logger.info("Starting service A")
    app.state.connection = await aio_pika.connect_robust(
        host="192.168.1.123",
        port=5672,
        login="guest",
        password="guest",
    )
    app.state.channel = await app.state.connection.channel()
    app.state.queue = await app.state.channel.declare_queue("ping", durable=True)

    async def send_loop():
        count = 0
        while True:
            msg = f"ping {count}"
            await app.state.channel.default_exchange.publish(
                aio_pika.Message(body=msg.encode()),
                routing_key=app.state.queue.name
            )
            logger.info(f"Sent: {msg}")
            count += 1
            await asyncio.sleep(2)

    async def heartbeat():
        while True:
            logger.info("still alive")
            await asyncio.sleep(3)

    asyncio.create_task(send_loop())
    asyncio.create_task(heartbeat())

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down service A")
    await app.state.connection.close()

@app.route("/")
async def index(request):
    return PlainTextResponse("Service A Running")
