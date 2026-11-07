from django.http import JsonResponse
from django.shortcuts import render


def health(request):
    return JsonResponse({"status": "ok"})


def not_found(request, exception=None):
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "Not found."}, status=404)
    return render(request, "404.html", status=404)


def server_error(request):
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "A server error occurred."}, status=500)
    return render(request, "500.html", status=500)
