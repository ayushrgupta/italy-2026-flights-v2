from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fast_flights import FlightData, Passengers, Result, get_flights
import traceback

app = FastAPI(title="Italy Flight Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return FileResponse("index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

def serialize(result):
    if not result or not hasattr(result, 'flights'):
        return []
    out = []
    for f in result.flights[:5]:
        try:
            out.append({
                "price":     getattr(f, 'price',     None),
                "name":      getattr(f, 'name',      None),
                "departure": getattr(f, 'departure', None),
                "arrival":   getattr(f, 'arrival',   None),
                "duration":  getattr(f, 'duration',  None),
                "stops":     getattr(f, 'stops',     None),
                "is_best":   getattr(f, 'is_best',   False),
                "delay":     getattr(f, 'delay',     None),
            })
        except Exception:
            pass
    return out

@app.get("/flights")
def search_flights(
    from_airport: str = Query(...),
    to_airport:   str = Query(...),
    date_out:     str = Query(...),
    return_from:  str = Query(...),
    date_ret:     str = Query(...),
    adults:       int = Query(1),
):
    out_flights, ret_flights = [], []
    out_error, ret_error = None, None

    # Outbound leg
    try:
        out_result: Result = get_flights(
            flight_data=[FlightData(date=date_out, from_airport=from_airport, to_airport=to_airport)],
            trip="one-way", seat="economy",
            passengers=Passengers(adults=adults),
            fetch_mode="fallback",
        )
        out_flights = serialize(out_result)
    except Exception as e:
        out_error = str(e)

    # Return leg — run independently so one failure doesn't kill both
    try:
        ret_result: Result = get_flights(
            flight_data=[FlightData(date=date_ret, from_airport=return_from, to_airport=from_airport)],
            trip="one-way", seat="economy",
            passengers=Passengers(adults=adults),
            fetch_mode="fallback",
        )
        ret_flights = serialize(ret_result)
    except Exception as e:
        ret_error = str(e)

    # Return results even if one leg failed — frontend handles partial data
    return JSONResponse({
        "outbound":  out_flights,
        "return":    ret_flights,
        "out_error": out_error,
        "ret_error": ret_error,
        "current_price": None,
    })
