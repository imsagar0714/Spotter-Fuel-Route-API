from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from route_planner.serializers import RoutePlanRequestSerializer
from route_planner.services.exceptions import PlanningError
from route_planner.services.planner import RoutePlanService


class RoutePlanView(APIView):
    def post(self, request):
        serializer = RoutePlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = RoutePlanService().build(**serializer.validated_data)
        except PlanningError as error:
            return Response({"detail": str(error)}, status=error.status_code)
        return Response(payload, status=status.HTTP_200_OK)

