import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    _initialized = False

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return

        try:
            # Path to the service account key
            # Assuming the file is in the backend root directory
            cred_path = os.path.join(settings.BASE_DIR, 'serviceAccountKey.json')
            
            if not os.path.exists(cred_path):
                logger.warning(f"Firebase Service Account Key not found at {cred_path}. Notifications will not work.")
                return

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            cls._initialized = True
            logger.info("Firebase Admin SDK initialized successfully.")
        except ValueError:
            # App already initialized
            cls._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")

    @staticmethod
    def send_multicast_notification(tokens, title, body, data=None):
        """
        Send a notification to multiple devices.
        """
        NotificationManager.initialize()
        
        if not NotificationManager._initialized:
            logger.warning("Firebase not initialized. Skipping notification.")
            return

        if not tokens:
            return

        # Filter out empty tokens
        valid_tokens = [t for t in tokens if t]
        
        if not valid_tokens:
            return

        # Android specific config to ensure high priority delivery in background
        android_config = messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                channel_id='self_manager_channel_v1',
                default_sound=True,
                priority='high' 
            )
        )

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=valid_tokens,
            android=android_config
        )

        try:
            # Try newer API
            response = messaging.send_multicast(message)
            
            # --- Success Path (if send_multicast works) ---
            logger.info(f'{response.success_count} messages were sent successfully')
            
            failed_tokens = []
            if response.failure_count > 0:
                responses = response.responses
                for idx, resp in enumerate(responses):
                    if not resp.success:
                        failed_tokens.append(valid_tokens[idx])
                        logger.error(f'Failure sending to {valid_tokens[idx]}: {resp.exception}')
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "failed_tokens": failed_tokens
            }

        except AttributeError:
             # Fallback for older SDK versions or strict environments
             # We must manually send to each token
             success_count = 0
             failure_count = 0
             failed_tokens_list = []
             
             for token in valid_tokens:
                 try:
                     msg = messaging.Message(
                        notification=messaging.Notification(title=title, body=body),
                        data=data or {},
                        token=token,
                        android=android_config
                     )
                     messaging.send(msg)
                     success_count += 1
                 except Exception as exc:
                     failure_count += 1
                     failed_tokens_list.append(token)
                     logger.error(f'Failure sending to {token}: {exc}')
            
             return {
                 "success_count": success_count,
                 "failure_count": failure_count,
                 "failed_tokens": failed_tokens_list
             }
        except Exception as e:
            logger.error(f"Error sending multicast notification: {str(e)}")
            return {
                "success_count": 0,
                "failure_count": len(valid_tokens),
                "error": str(e)
            }
