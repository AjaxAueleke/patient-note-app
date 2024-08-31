import json
import logging

import boto3
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import Http404
from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework import viewsets, permissions
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView

from pulse_ai.therapist_session.api.pagination import StandardResultsSetPagination
from pulse_ai.therapist_session.models import TherapistSession
from .permissions import IsOwnerOrReadOnly
from .serializers import TherapistSessionSerializer
from .serializers import TranscriptionSerializer, SummarySerializer, ErrorSerializer

from sendgrid import SendGridAPIClient, Email
from sendgrid.helpers.mail import Mail, Content, Attachment
import base64
import os

logger = logging.getLogger(__name__)


class TherapistSessionFilter(filters.FilterSet):
    date = filters.DateFilter(field_name="created_at", lookup_expr='date', help_text="Filter sessions by specific date")
    status = filters.CharFilter(lookup_expr='iexact', help_text="Filter sessions by status")
    patient_name = filters.CharFilter(field_name="patient__name", lookup_expr='icontains', help_text="Filter sessions by patient name")
    session_name = filters.CharFilter(lookup_expr='icontains', help_text="Filter sessions by session name or description")
    patient_id = filters.NumberFilter(field_name="patient_id", lookup_expr='exact', help_text="Filter sessions by patient ID")  # Added patient_id filter
    favorite = filters.BooleanFilter(field_name="favorite",help_text="Filter sessions by favorite status")

    class Meta:
        model = TherapistSession
        fields = ['date', 'status', 'patient_name', 'session_name', 'patient_id', 'favorite']



class TherapistSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TherapistSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]       
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)   
    filterset_class = TherapistSessionFilter
    search_fields = ['session_name', 'description', 'patient__name']
    ordering_fields = ['created_at', 'session_name', 'description', 'patient__name', 'status', 'patient_id']  # Added patient_id for ordering
    ordering = ['-created_at']  # Default ordering
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # This ensures that users only see their own sessions
        return TherapistSession.objects.filter(therapist=self.request.user)

    def perform_create(self, serializer):
        try:
            session = serializer.save(therapist=self.request.user)
            data = {
                "action": "speech-to-text",
                "audio_url": session.session_audio.url,
                "session_id": session.id,
                "therapist_id": self.request.user.id,  # Include therapist ID
                "patient_id": session.patient_id,  # Include patient ID
            }
            print("QUEUE DATA: ")
            print(data)
            self._send_queue_message(data)
        except (ValidationError, IntegrityError) as e:
            logger.error(f"Database error during session creation: {e}")
            # Raise a DRF ValidationError which will be handled by DRF and turned into a 400 Bad Request
            raise DRFValidationError({"error": "Invalid data provided. Please check your inputs."})
        except Exception as e:
            logger.error(f"Unexpected error during session creation: {e}")
            print(e)
            raise APIException({"error": "An unexpected error occurred. Please try again later."})
    
    @action(detail=True, methods=['get'], url_path='toggle-favorite')
    def toggle_favorite(self, request, pk=None):
        try:
            session = self.get_object()
            session.favorite = not session.favorite
            session.save()

            return Response({
                'status': 'success',
                'message': 'Favorite status updated successfully.',
                'data': {
                    'therapist_id': session.therapist.id,
                    'session_id': session.id,
                    'favorite': session.favorite
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred.',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
    def _send_queue_message(self, data):
        queue_url = settings.SQS_URL

        sqs = boto3.client('sqs', aws_access_key_id=settings.FUNCTION_QUEUE_AWS_S3_AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.FUNCTION_QUEUE_AWS_S3_AWS_SECRET_ACCESS_KEY,
                           region_name=settings.AWS_REGION)
        # Send message
        response = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(data),
                                    MessageGroupId='therapist-session-queue')

        print(response)
        
class RegenerateTranscriptionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def create(self, request, session_id):
        try:
            session = TherapistSession.objects.filter(id=session_id, therapist=self.request.user).first()
            if not session:
                return Response({'success': False, 'message': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
            
            if session.transcription_regeneration_count >= settings.MAX_TRANSCRIPTION_REGENERATIONS:
                return Response({'success': False, 'message': 'Maximum number of transcription regenerations exceeded'},
                                status=status.HTTP_403_FORBIDDEN)


            transcription = session.transcriptions.last()
            if not transcription:
                return Response({'success': False, 'message': 'Transcription not found for this session'},
                                status=status.HTTP_404_NOT_FOUND)

            data = {
                "action": "regenerate-transcription",
                "audio_url": session.session_audio.url,
                "session_id": session.id,
                "therapist_id": self.request.user.id,  # Include therapist ID
                "patient_id": session.patient.id,  # Include patient ID
                "regenerate": True
            }
            print("QUEUE DATA: ")
            print(data)
            self._send_queue_message(data)

            return Response({'success': True, 'message': 'Transcription regeneration request sent'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Unexpected error during transcription regeneration: {e}")
            return Response({'success': False, 'message': 'An unexpected error occurred. Please try again later.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _send_queue_message(self, data):
        queue_url = settings.SQS_URL

        sqs = boto3.client('sqs', aws_access_key_id=settings.FUNCTION_QUEUE_AWS_S3_AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.FUNCTION_QUEUE_AWS_S3_AWS_SECRET_ACCESS_KEY,
                           region_name=settings.AWS_REGION)
        response = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(data),
                                    MessageGroupId='therapist-session-queue')

        print(response)



class RegenerateSummaryViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def create(self, request, session_id):
        try:
            session = TherapistSession.objects.filter(id=session_id, therapist=self.request.user).first()
            if not session:
                return Response({'success': False, 'message': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
            
            if session.summary_regeneration_count >= settings.MAX_SUMMARY_REGENERATIONS:
                return Response({'success': False, 'message': 'Maximum number of summary regenerations exceeded'},
                                status=status.HTTP_403_FORBIDDEN)

            transcription = session.transcriptions.last()
            if not transcription:
                return Response({'success': False, 'message': 'Transcription not found for this session'},
                                status=status.HTTP_404_NOT_FOUND)

            transcription_url = transcription.get_transcription_url()
            if not transcription_url:
                return Response({'success': False, 'message': 'Failed to fetch transcription URL'},
                                status=status.HTTP_404_NOT_FOUND)

            data = {
                "action": "regenerate-summary",
                "transcription_url": transcription_url,
                "session_id": session.id,
                "therapist_id": self.request.user.id,  # Include therapist ID
                "patient_id": session.patient.id,  # Include patient ID
                "regenerate": True
            }
            print("QUEUE DATA: ")
            print(data)
            self._send_queue_message(data)

            return Response({'success': True, 'message': 'Summary regeneration request sent'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Unexpected error during summary regeneration: {e}")
            return Response({'success': False, 'message': 'An unexpected error occurred. Please try again later.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _send_queue_message(self, data):
        queue_url = settings.SQS_URL

        sqs = boto3.client('sqs', aws_access_key_id=settings.FUNCTION_QUEUE_AWS_S3_AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.FUNCTION_QUEUE_AWS_S3_AWS_SECRET_ACCESS_KEY,
                           region_name=settings.AWS_REGION)
        response = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(data),
                                    MessageGroupId='therapist-session-queue')

        print(response)


# class SessionDataView(APIView):
#     def post(self, request, session_id):
#         api_key = request.headers.get('X-API-KEY')
#         if api_key != settings.THERAPIST_SESSION_POST_API_KEY:
#             return Response({'success': False, 'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

#         session = TherapistSession.objects.filter(id=session_id).first()
#         if not session:
#             return Response({'success': False, 'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

#         error = request.data.get('error', 'false').lower().strip(' ').strip() == 'true'

#         if error:
#             error_serializer = ErrorSerializer(
#                 data={'session': session_id, 'error_message': request.data.get('error_message', ''),
#                       'error_code': request.data.get('error_code', '')})
#             if error_serializer.is_valid():
#                 error_serializer.save()
#                 session.status = 'failed'
#                 session.save()
#                 return Response({'success': True, 'data': error_serializer.data}, status=status.HTTP_201_CREATED)
#             return Response({'success': False, 'errors': error_serializer.errors, 'message': 'Invalid data'},
#                             status=status.HTTP_400_BAD_REQUEST)
#         else:
#             transcription_data = {'session': session_id,
#                 'transcription_text_file': request.FILES.get('transcription_file')}
#             summary_data = {'session': session_id, 'summary_text_file': request.FILES.get('summary_file')}
#             transcription_serializer = TranscriptionSerializer(data=transcription_data)
#             summary_serializer = SummarySerializer(data=summary_data)

#             if transcription_serializer.is_valid() and summary_serializer.is_valid():
#                 transcription_serializer.save()
#                 summary_serializer.save()
#                 session.status = 'done'
#                 session.save()
#                 return Response({'success': True, 'message': 'Transcription and summary added',
#                                  'transcription': transcription_serializer.data, 'summary': summary_serializer.data},
#                                 status=status.HTTP_201_CREATED)
#             else:
#                 errors = {}
#                 if not transcription_serializer.is_valid():
#                     errors['transcription'] = transcription_serializer.errors
#                 if not summary_serializer.is_valid():
#                     errors['summary'] = summary_serializer.errors
#                 return Response({'success': False, 'errors': errors, 'message': 'Invalid data'},
#                                 status=status.HTTP_400_BAD_REQUEST)


# class SessionDataView(APIView):
#     def post(self, request, session_id):
#         api_key = request.headers.get('X-API-KEY')
#         if api_key != settings.THERAPIST_SESSION_POST_API_KEY:
#             return Response({'success': False, 'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

#         session = TherapistSession.objects.filter(id=session_id).first()
#         if not session:
#             return Response({'success': False, 'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

#         is_regeneration = request.data.get('is_regeneration', 'false').lower().strip() == 'true'
#         error = request.data.get('error', 'false').lower().strip() == 'true'

#         if error:
#             error_serializer = ErrorSerializer(
#                 data={'session': session_id, 'error_message': request.data.get('error_message', ''),
#                       'error_code': request.data.get('error_code', '')})
#             if error_serializer.is_valid():
#                 error_serializer.save()
#                 session.status = 'failed'
#                 session.save()
#                 return Response({'success': True, 'data': error_serializer.data}, status=status.HTTP_201_CREATED)
#             return Response({'success': False, 'errors': error_serializer.errors, 'message': 'Invalid data'},
#                             status=status.HTTP_400_BAD_REQUEST)
#         else:
#             transcription_data = {'session': session_id,
#                                    'transcription_text_file': request.FILES.get('transcription_file')}
#             summary_data = {'session': session_id, 'summary_text_file': request.FILES.get('summary_file')}

#             if is_regeneration:
#                 # Handle regeneration
#                 transcription = session.transcriptions.last()
#                 summary = session.summaries.last()

#                 if transcription and transcription_data['transcription_text_file']:
#                     transcription_serializer = TranscriptionSerializer(transcription, data=transcription_data, partial=True)
#                     if transcription_serializer.is_valid():
#                         transcription_serializer.save()
#                         session.transcription_regeneration_count += 1

#                 if summary and summary_data['summary_text_file']:
#                     summary_serializer = SummarySerializer(summary, data=summary_data, partial=True)
#                     if summary_serializer.is_valid():
#                         summary_serializer.save()
#                         session.summary_regeneration_count += 1

#                 session.status = 'done'
#                 session.save()

#                 return Response({'success': True, 'message': 'Transcription and/or summary updated after regeneration'},
#                                 status=status.HTTP_200_OK)

#             else:
#                 # Handle new transcription and summary
#                 transcription_serializer = TranscriptionSerializer(data=transcription_data)
#                 summary_serializer = SummarySerializer(data=summary_data)

#                 if transcription_serializer.is_valid() and summary_serializer.is_valid():
#                     transcription_serializer.save()
#                     summary_serializer.save()
#                     session.status = 'done'
#                     session.save()
#                     return Response({'success': True, 'message': 'Transcription and summary added',
#                                      'transcription': transcription_serializer.data, 'summary': summary_serializer.data},
#                                     status=status.HTTP_201_CREATED)
#                 else:
#                     errors = {}
#                     if not transcription_serializer.is_valid():
#                         errors['transcription'] = transcription_serializer.errors
#                     if not summary_serializer.is_valid():
#                         errors['summary'] = summary_serializer.errors
#                     return Response({'success': False, 'errors': errors, 'message': 'Invalid data'},
#                                     status=status.HTTP_400_BAD_REQUEST)
class SessionDataView(APIView):
    def post(self, request, session_id):
        api_key = request.headers.get('X-API-KEY')
        if api_key != settings.THERAPIST_SESSION_POST_API_KEY:
            return Response({'success': False, 'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

        session = TherapistSession.objects.filter(id=session_id).first()
        if not session:
            return Response({'success': False, 'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        is_regeneration = request.data.get('is_regeneration', 'false').lower().strip() == 'true'
        error = request.data.get('error', 'false').lower().strip() == 'true'

        if error:
            error_serializer = ErrorSerializer(
                data={'session': session_id, 'error_message': request.data.get('error_message', ''),
                      'error_code': request.data.get('error_code', '')})
            if error_serializer.is_valid():
                error_serializer.save()
                session.status = 'failed'
                session.save()
                return Response({'success': True, 'data': error_serializer.data}, status=status.HTTP_201_CREATED)
            return Response({'success': False, 'errors': error_serializer.errors, 'message': 'Invalid data'},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            transcription_data = {'session': session_id,
                                   'transcription_text_file': request.FILES.get('transcription_file')}
            summary_data = {'session': session_id, 'summary_text_file': request.FILES.get('summary_file')}

            if is_regeneration:
                # Handle regeneration by creating new transcription and summary records
                transcription_serializer = TranscriptionSerializer(data=transcription_data)
                summary_serializer = SummarySerializer(data=summary_data)

                if transcription_serializer.is_valid():
                    transcription_serializer.save()
                    session.transcription_regeneration_count += 1

                if summary_serializer.is_valid():
                    summary_serializer.save()
                    session.summary_regeneration_count += 1

                session.status = 'done'
                session.save()

                # Send email with attachments
                self.send_email_with_attachments(session, transcription_serializer.instance, summary_serializer.instance)

                return Response({'success': True, 'message': 'New transcription and/or summary created after regeneration'},
                                status=status.HTTP_200_OK)

            else:
                # Handle new transcription and summary (non-regeneration case)
                transcription_serializer = TranscriptionSerializer(data=transcription_data)
                summary_serializer = SummarySerializer(data=summary_data)

                if transcription_serializer.is_valid() and summary_serializer.is_valid():
                    transcription_serializer.save()
                    summary_serializer.save()
                    session.status = 'done'
                    session.save()

                    # Send email with attachments
                    self.send_email_with_attachments(session, transcription_serializer.instance, summary_serializer.instance)

                    return Response({'success': True, 'message': 'Transcription and summary added',
                                     'transcription': transcription_serializer.data, 'summary': summary_serializer.data},
                                    status=status.HTTP_201_CREATED)
                else:
                    errors = {}
                    if not transcription_serializer.is_valid():
                        errors['transcription'] = transcription_serializer.errors
                    if not summary_serializer.is_valid():
                        errors['summary'] = summary_serializer.errors
                    return Response({'success': False, 'errors': errors, 'message': 'Invalid data'},
                                    status=status.HTTP_400_BAD_REQUEST)

    def send_email_with_attachments(self, session, transcription, summary):
        try:
            # Get the therapist's email
            therapist_email = session.therapist.email

            # Prepare the email content
            subject = f"Session Files for {session.session_name}"
            message = f"Attached are the transcription and summary files for the session: {session.session_name}."
            from_email = Email("team@pulseai.au")
            to_email = Email(therapist_email)
            content = Content("text/plain", message)
            mail = Mail(from_email, to_email, subject, content)

            # Initialize S3 client
            s3_client = boto3.client('s3')

            # Add transcription file as attachment
            if transcription.transcription_text_file:
                transcription_key = transcription.transcription_text_file.name
                transcription_file_obj = s3_client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=transcription_key)
                transcription_data = transcription_file_obj['Body'].read()
                encoded_transcription = base64.b64encode(transcription_data).decode()
                transcription_attachment = Attachment()
                transcription_attachment.file_content = encoded_transcription
                transcription_attachment.file_type = "application/octet-stream"
                transcription_attachment.file_name = transcription_key.split('/')[-1]
                mail.add_attachment(transcription_attachment)

            # Add summary file as attachment
            if summary.summary_text_file:
                summary_key = summary.summary_text_file.name
                summary_file_obj = s3_client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=summary_key)
                summary_data = summary_file_obj['Body'].read()
                encoded_summary = base64.b64encode(summary_data).decode()
                summary_attachment = Attachment()
                summary_attachment.file_content = encoded_summary
                summary_attachment.file_type = "application/octet-stream"
                summary_attachment.file_name = summary_key.split('/')[-1]
                mail.add_attachment(summary_attachment)

            # Send the email
            sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            response = sg.send(mail)
            print(response.status_code)
            print(response.body)
            print(response.headers)

        except Exception as e:
            print(f"Failed to send email: {e}")