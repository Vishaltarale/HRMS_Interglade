from rest_framework import serializers
from Shifts.models import Shift
from datetime import datetime

TIME_FORMAT = "%H:%M:%S"


class ShiftSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    shiftType = serializers.ChoiceField(
        choices=["Day", "Night", "Rotational", "Afternoon"]
    )
    fromTime = serializers.CharField(max_length=8)
    endTime = serializers.CharField(max_length=8)
    lateMarkTime = serializers.CharField(
        max_length=8, required=False, allow_blank=True, allow_null=True
    )

    # -------------------------
    # VALIDATION
    # -------------------------
    def validate_fromTime(self, value):
        self._validate_time(value)
        return value

    def validate_endTime(self, value):
        self._validate_time(value)
        return value

    def validate_lateMarkTime(self, value):
        if value:
            self._validate_time(value)
        return value

    def _validate_time(self, value):
        try:
            datetime.strptime(value, TIME_FORMAT)
        except ValueError:
            raise serializers.ValidationError(
                "Time must be in HH:MM:SS format"
            )

    # -------------------------
    # CREATE
    # -------------------------
    def create(self, validated_data):
        """
        Store RAW time strings only
        """
        return Shift.objects.create(**validated_data)

    # -------------------------
    # UPDATE
    # -------------------------
    def update(self, instance, validated_data):
        instance.shiftType = validated_data.get(
            "shiftType", instance.shiftType
        )
        instance.fromTime = validated_data.get(
            "fromTime", instance.fromTime
        )
        instance.endTime = validated_data.get(
            "endTime", instance.endTime
        )
        instance.lateMarkTime = validated_data.get(
            "lateMarkTime", instance.lateMarkTime
        )

        instance.save()
        return instance
