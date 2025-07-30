from rest_framework import serializers
from .models import *


class SubtitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtitle
        fields = '__all__'

class GlobalPDFSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalPDF
        fields = '__all__'

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalChatSession
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalMessage
        fields = '__all__'
