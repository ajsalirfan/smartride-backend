import uuid
import logging
from django.conf import settings
from django.utils import timezone
from .models import Payment

logger = logging.getLogger(__name__)

class UPIPaymentGateway:
    """
    UPI Payment Gateway Integration (Mock Implementation)
    In production, integrate with real UPI providers like:
    - PhonePe
    - Paytm
    - Google Pay
    - BHIM UPI
    """
    
    @staticmethod
    def initiate_payment(amount, upi_id, user, ride=None):
        """
        Initiate UPI payment
        """
        try:
            # Generate unique transaction ID
            transaction_id = f"TXN{int(timezone.now().timestamp())}{uuid.uuid4().hex[:8].upper()}"
            
            # In production, this would call the actual UPI gateway API
            # For demo, we'll simulate the response
            
            payment_data = {
                'transaction_id': transaction_id,
                'amount': float(amount),
                'upi_id': upi_id,
                'status': 'pending',
                'payment_url': f"upi://pay?pa={upi_id}&pn=SmartRide&am={amount}&cu=INR&tn=SmartRide Payment",
                'qr_code_data': f"upi://pay?pa={upi_id}&pn=SmartRide&am={amount}&cu=INR&tn=SmartRide Payment"
            }
            
            # Create payment record
            payment = Payment.objects.create(
                user=user,
                ride=ride,
                amount=amount,
                payment_method='upi',
                status='pending',
                upi_id=upi_id,
                transaction_id=transaction_id,
                payment_gateway_response=payment_data
            )
            
            logger.info(f"UPI payment initiated: {transaction_id} for user {user.username}")
            
            return {
                'success': True,
                'payment_id': payment.id,
                'transaction_id': transaction_id,
                'payment_url': payment_data['payment_url'],
                'qr_code_data': payment_data['qr_code_data'],
                'amount': float(amount),
                'upi_id': upi_id
            }
            
        except Exception as e:
            logger.error(f"UPI payment initiation failed: {e}")
            return {
                'success': False,
                'error': 'Payment initiation failed'
            }
    
    @staticmethod
    def verify_payment(transaction_id):
        """
        Verify UPI payment status
        In production, this would poll the UPI gateway
        """
        try:
            # Mock verification - in real scenario, call UPI gateway API
            # Simulate successful payment for demo
            import random
            is_successful = random.choice([True, True, True, False])  # 75% success rate
            
            payment = Payment.objects.get(transaction_id=transaction_id)
            
            if is_successful:
                payment.status = 'completed'
                payment.payment_completed_at = timezone.now()
                payment.payment_gateway_response['verified_at'] = timezone.now().isoformat()
                payment.payment_gateway_response['gateway_status'] = 'SUCCESS'
                payment.save()
                
                # If this is a ride payment, update ride status
                if payment.ride:
                    payment.ride.payment_status = 'paid'
                    payment.ride.save()
                
                logger.info(f"UPI payment verified successfully: {transaction_id}")
                return {
                    'success': True,
                    'status': 'completed',
                    'message': 'Payment completed successfully'
                }
            else:
                payment.status = 'failed'
                payment.payment_gateway_response['gateway_status'] = 'FAILED'
                payment.save()
                
                logger.warning(f"UPI payment failed: {transaction_id}")
                return {
                    'success': False,
                    'status': 'failed',
                    'message': 'Payment failed or was cancelled'
                }
                
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: {transaction_id}")
            return {
                'success': False,
                'error': 'Payment not found'
            }
        except Exception as e:
            logger.error(f"Payment verification failed: {e}")
            return {
                'success': False,
                'error': 'Payment verification failed'
            }
    
    @staticmethod
    def process_refund(payment, refund_amount=None, reason="Admin refund"):
        """
        Process refund for UPI payment
        """
        try:
            refund_amount = refund_amount or payment.amount
            
            # In production, call UPI refund API
            payment.refund_amount = refund_amount
            payment.refund_reason = reason
            payment.refund_processed_at = timezone.now()
            payment.status = 'refunded'
            payment.save()
            
            logger.info(f"UPI refund processed: {payment.transaction_id} - ₹{refund_amount}")
            
            return {
                'success': True,
                'refund_amount': float(refund_amount),
                'transaction_id': payment.transaction_id,
                'refund_processed_at': payment.refund_processed_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"UPI refund failed: {e}")
            return {
                'success': False,
                'error': 'Refund processing failed'
            }


class WalletManager:
    """
    Wallet management utilities
    """
    
    @staticmethod
    def add_balance(user, amount, payment_method='upi'):
        """
        Add balance to user wallet
        """
        try:
            wallet = user.wallet
            wallet.balance += amount
            wallet.total_added += amount
            wallet.last_topup = timezone.now()
            wallet.save()
            
            # Record the payment
            Payment.objects.create(
                user=user,
                amount=amount,
                payment_method=payment_method,
                status='completed',
                transaction_id=f"TOPUP{int(timezone.now().timestamp())}",
                payment_completed_at=timezone.now()
            )
            
            logger.info(f"Wallet topped up: {user.username} - ₹{amount}")
            return True
            
        except Exception as e:
            logger.error(f"Wallet topup failed: {e}")
            return False
    
    @staticmethod
    def deduct_balance(user, amount, ride=None):
        """
        Deduct balance from user wallet for ride payment
        """
        try:
            wallet = user.wallet
            
            if wallet.balance < amount:
                return False, 'Insufficient balance'
            
            wallet.balance -= amount
            wallet.save()
            
            # Record the payment
            payment = Payment.objects.create(
                user=user,
                ride=ride,
                amount=amount,
                payment_method='wallet',
                status='completed',
                transaction_id=f"RIDE{int(timezone.now().timestamp())}",
                payment_completed_at=timezone.now()
            )
            
            if ride:
                ride.payment_status = 'paid'
                ride.save()
            
            logger.info(f"Wallet deduction: {user.username} - ₹{amount} for ride {ride.ride_id if ride else 'N/A'}")
            return True, 'Payment successful'
            
        except Exception as e:
            logger.error(f"Wallet deduction failed: {e}")
            return False, 'Payment failed'


class PaymentValidator:
    """
    Payment validation utilities
    """
    
    @staticmethod
    def validate_upi_id(upi_id):
        """
        Validate UPI ID format
        """
        import re
        # Basic UPI ID validation
        upi_pattern = r'^[a-zA-Z0-9.\-_]{2,49}@[a-zA-Z]{2,}$'
        return bool(re.match(upi_pattern, upi_id))
    
    @staticmethod
    def validate_amount(amount):
        """
        Validate payment amount
        """
        try:
            amount_float = float(amount)
            return amount_float >= 10.0  # Minimum ₹10
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def can_user_pay(user, amount):
        """
        Check if user can make payment
        """
        if not user.is_verified:
            return False, 'User not verified'
        
        if amount <= 0:
            return False, 'Invalid amount'
        
        return True, 'OK'