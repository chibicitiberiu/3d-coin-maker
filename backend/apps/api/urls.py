from django.urls import path

from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),

    # API endpoints as specified in the plan
    path('upload/', views.upload_image, name='upload_image'),
    path('process/', views.process_image, name='process_image'),
    path('generate/', views.generate_stl, name='generate_stl'),
    path('status/<str:generation_id>/', views.generation_status, name='generation_status'),
    path('download/<str:generation_id>/stl', views.download_stl, name='download_stl'),
    path('preview/<str:generation_id>', views.preview_image, name='preview_image'),
]
