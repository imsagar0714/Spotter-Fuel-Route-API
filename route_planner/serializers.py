from rest_framework import serializers


class RoutePlanRequestSerializer(serializers.Serializer):
    start = serializers.CharField(max_length=255, trim_whitespace=True)
    finish = serializers.CharField(max_length=255, trim_whitespace=True)

    def validate(self, attributes):
        if attributes["start"].casefold() == attributes["finish"].casefold():
            raise serializers.ValidationError("Start and finish must be different locations.")
        return attributes

