from rest_framework import serializers


class ImageUploadSerializer(serializers.Serializer):
    """Serializer for image upload."""
    image = serializers.ImageField()

    def validate_image(self, value):
        """Validate uploaded image."""
        # Check file size
        if value.size > 52428800:  # 50MB
            raise serializers.ValidationError("Image file too large. Maximum size is 50MB.")

        # Check format
        allowed_formats = {'PNG', 'JPEG', 'GIF', 'BMP', 'TIFF'}
        if hasattr(value, 'image') and value.image.format not in allowed_formats:
            raise serializers.ValidationError(
                f"Unsupported image format. Allowed formats: {', '.join(allowed_formats)}"
            )

        return value


class ImageProcessingSerializer(serializers.Serializer):
    """Serializer for image processing parameters."""
    generation_id = serializers.UUIDField()
    filename = serializers.CharField(max_length=255)

    # Image processing parameters (matching frontend API)
    grayscale_method = serializers.ChoiceField(
        choices=['average', 'luminance', 'red', 'green', 'blue'],
        default='luminance'
    )
    brightness = serializers.IntegerField(min_value=-100, max_value=100, default=0)
    contrast = serializers.IntegerField(min_value=0, max_value=300, default=100)
    gamma = serializers.FloatField(min_value=0.1, max_value=5.0, default=1.0)
    invert = serializers.BooleanField(default=False)


class CoinParametersSerializer(serializers.Serializer):
    """Serializer for coin generation parameters."""
    generation_id = serializers.UUIDField()

    # Coin parameters
    shape = serializers.ChoiceField(
        choices=['circle', 'square', 'hexagon', 'octagon'],
        default='circle'
    )
    diameter = serializers.FloatField(min_value=0.01, default=30.0)  # No max limit, min 0.01mm
    thickness = serializers.FloatField(min_value=0.01, default=3.0)  # No max limit, min 0.01mm
    relief_depth = serializers.FloatField(min_value=0.01, default=1.0)  # No max limit, min 0.01mm

    # Heightmap positioning
    scale = serializers.FloatField(min_value=0.00001, default=100.0)  # No max limit, min 0.00001%
    offset_x = serializers.FloatField(default=0.0)  # No limits, any value allowed
    offset_y = serializers.FloatField(default=0.0)  # No limits, any value allowed
    rotation = serializers.FloatField(default=0.0)  # No limits, any value allowed

    def validate(self, attrs):
        """Validate coin parameters."""
        if attrs['relief_depth'] >= attrs['thickness']:
            raise serializers.ValidationError(
                "Relief depth must be less than coin thickness."
            )
        return attrs


class GenerationStatusSerializer(serializers.Serializer):
    """Serializer for generation status response."""
    generation_id = serializers.UUIDField()
    status = serializers.CharField()
    progress = serializers.IntegerField()
    step = serializers.CharField()
    error = serializers.CharField(required=False, allow_null=True)

    # File availability flags
    has_original = serializers.BooleanField()
    has_processed = serializers.BooleanField()
    has_heightmap = serializers.BooleanField()
    has_stl = serializers.BooleanField()

    # Cache busting timestamp for STL file
    stl_timestamp = serializers.IntegerField(required=False, allow_null=True)
