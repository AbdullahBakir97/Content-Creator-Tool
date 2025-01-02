from rest_framework import serializers
from .models import Content, ContentType, ContentAsset
from apps.accounts.models import User, Profile

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'name', 'description', 'is_active', 'prompt_template']

class ContentAssetSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ContentAsset
        fields = ['id', 'file', 'file_url', 'asset_type', 'order', 'duration', 'metadata']
        
    def get_file_url(self, obj):
        return obj.file.url if obj.file else None

class ContentSerializer(serializers.ModelSerializer):
    assets = ContentAssetSerializer(many=True, read_only=True)
    creator_username = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    processing_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = [
            'id', 'creator', 'creator_username', 'content_type', 'title',
            'script', 'status', 'status_display', 'video_file', 'thumbnail',
            'scheduled_time', 'duration', 'processing_duration', 'assets',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['creator', 'status', 'processing_duration']
        
    def get_creator_username(self, obj):
        return obj.creator.username
        
    def get_status_display(self, obj):
        return obj.get_status_display()
        
    def get_processing_duration(self, obj):
        return obj.get_processing_duration()

class ContentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ['content_type', 'title', 'script', 'scheduled_time']
        
    def create(self, validated_data):
        user = self.context['request'].user
        return Content.objects.create(creator=user, **validated_data)

class ContentBatchCreateSerializer(serializers.Serializer):
    contents = ContentCreateSerializer(many=True)
    
    def create(self, validated_data):
        contents_data = validated_data.get('contents', [])
        user = self.context['request'].user
        created_contents = []
        
        for content_data in contents_data:
            content = Content.objects.create(creator=user, **content_data)
            created_contents.append(content)
            
        return created_contents
