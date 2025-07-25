import asyncio
import threading
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.types import Lifespan
import grpc
from grpc import aio
from grpc_health.v1 import health_pb2, health_pb2_grpc

GRPC_PORT = 50051

# --------- GRPC SERVER IMPLEMENTATION ----------

class HealthServicer(health_pb2_grpc.HealthServicer):
    def __init__(self):
        super().__init__()
        self.set("", health_pb2.HealthCheckResponse.SERVING)

async def start_grpc_server():
    server = aio.server()
    health_servicer = HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    listen_addr = f"[::]:{GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    await server.start()
    print(f"gRPC server listening on {listen_addr}")
    await server.wait_for_termination()

def start_grpc_server_background():
    # Run the async gRPC server in its own event loop in a thread
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_grpc_server())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

# --------- GRPC HEALTH CHECK FROM HTTP ROUTE ----------

async def grpc_health_check():
    # To avoid event loop conflict, we run this client in a thread with its own loop
    def run_check():
        async def inner():
            async with aio.insecure_channel(f"localhost:{GRPC_PORT}") as channel:
                stub = health_pb2_grpc.HealthStub(channel)
                response = await stub.Check(health_pb2.HealthCheckRequest(service=""))
                return response.status
        return asyncio.run(inner())

    return await asyncio.to_thread(run_check)

# --------- STARLETTE ROUTE ----------

async def healthz(request):
    try:
        status = await grpc_health_check()
        status_str = health_pb2.HealthCheckResponse.ServingStatus.Name(status)
        return JSONResponse({"grpc_health": status_str})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# --------- STARLETTE APP ----------

routes = [
    Route("/healthz", healthz),
]

async def lifespan(app):
    start_grpc_server_background()
    await asyncio.sleep(0.5)  # give gRPC a moment to come up
    yield

app = Starlette(routes=routes, lifespan=lifespan)
