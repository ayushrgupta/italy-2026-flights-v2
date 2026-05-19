from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fast_flights import FlightQuery, Passengers, create_query, get_flights
import traceback
import os

app = FastAPI(title="Italy Flight Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# ── Serve index.html at root ───────────────────────────────────────────────
@app.get("/")
def root():
    return FileResponse("index.html")

# ── Health check ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}

# ── Flight search ──────────────────────────────────────────────────────────
@app.get("/flights")
def search_flights(
    from_airport: str = Query(..., description="Departure airport e.g. JFK"),
    to_airport:   str = Query(..., description="Arrival airport e.g. MXP"),
    date_out:     str = Query(..., description="Outbound date YYYY-MM-DD"),
    return_from:  str = Query(..., description="Return departure airport e.g. FLR"),
    date_ret:     str = Query(..., description="Return date YYYY-MM-DD"),
    adults:       int = Query(1,   description="Number of adults"),
):
    try:
        # Outbound: US city → Italian arrival airport
        out_query = create_query(
            flights=[FlightQuery(date=date_out, from_airport=from_airport, to_airport=to_airport)],
            seat="economy",
            trip="one-way",
            passengers=Passengers(adults=adults),
        )
        out_result = get_flights(out_query)

        # Return: Italian departure airport → US city
        ret_query = create_query(
            flights=[FlightQuery(date=date_ret, from_airport=return_from, to_airport=from_airport)],
            seat="economy",
            trip="one-way",
            passengers=Passengers(adults=adults),
        )
        ret_result = get_flights(ret_query)

        def serialize(result):
            if not result or not hasattr(result, 'flights'):
                return []
            return [
                {
                    "price":    f.price,
                    "name":     f.name,
                    "departure": f.departure,
                    "arrival":  f.arrival,
                    "duration": f.duration,
                    "stops":    f.stops,
                    "is_best":  getattr(f, 'is_best', False),
                    "delay":    getattr(f, 'delay', None),
                }
                for f in result.flights[:5]
            ]

        return JSONResponse({
            "outbound":      serialize(out_result),
            "return":        serialize(ret_result),
            "current_price": getattr(out_result, 'current_price', None),
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()}
        )
