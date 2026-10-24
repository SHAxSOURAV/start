from fastapi import Request
from fastapi.responses import JSONResponse


class NotFoundHandler:
    @staticmethod
    async def handle(request: Request) -> JSONResponse:
        original_url = request.url.path
        if request.url.query:
            original_url = f"{original_url}?{request.url.query}"

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "Not Found",
                "errorMessages": [
                    {
                        "path": original_url,
                        "message": f"This {original_url} API Not Found",
                    }
                ],
            },
        )
