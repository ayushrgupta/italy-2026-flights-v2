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

@app.get("/flights")
def search_flights(
    from_airport: str = Query(...),
    to_airport:   str = Query(...),
    date_out:     str = Query(...),
    return_from:  str = Query(...),
    date_ret:     str = Query(...),
    adults:       int = Query(1),
):
    try:
        out_result: Result = get_flights(
            flight_data=[FlightData(date=date_out, from_airport=from_airport, to_airport=to_airport)],
            trip="one-way", seat="economy",
            passengers=Passengers(adults=adults),
            fetch_mode="fallback",
        )
        ret_result: Result = get_flights(
            flight_data=[FlightData(date=date_ret, from_airport=return_from, to_airport=from_airport)],
            trip="one-way", seat="economy",
            passengers=Passengers(adults=adults),
            fetch_mode="fallback",
        )

        def serialize(result):
            if not result or not hasattr(result, 'flights'):
                return []
            return [
                {
                    "price":     f.price,         # raw string e.g. "$379"
                    "name":      f.name,
                    "departure": f.departure,
                    "arrival":   f.arrival,
                    "duration":  f.duration,
                    "stops":     f.stops,
                    "is_best":   getattr(f, 'is_best', False),
                    "delay":     getattr(f, 'delay', None),
                }
                for f in result.flights[:5]
            ]

        out_flights = serialize(out_result)
        ret_flights = serialize(ret_result)

        return JSONResponse({
            "outbound":      out_flights,
            "return":        ret_flights,
            # Convenience: best combined price (cheapest outbound + cheapest return)
            "best_combined": {
                "outbound": out_flights[0] if out_flights else None,
                "return":   ret_flights[0] if ret_flights else None,
            },
            "current_price": getattr(out_result, 'current_price', None),
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()}
        )
