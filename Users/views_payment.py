import razorpay
import hmac
import hashlib
from decimal import Decimal
from decouple import config
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions

from Users.models import Wallet

# Razorpay client
client = razorpay.Client(auth=(
    config("RAZOR_KEY_ID"),
    config("RAZOR_KEY_SECRET")
))


# =====================================================
# STEP 1 — CREATE RAZORPAY ORDER
# =====================================================
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_razorpay_order(request):
    try:
        amount = request.data.get("amount")
        if not amount:
            return Response({"error": "Amount is required"}, status=400)

        # convert rupees → paise
        amount_paise = int(float(amount) * 100)

        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1
        })

        return Response({
            "order_id": order["id"],
            "amount": amount,
            "currency": "INR",
            "key": config("RAZOR_KEY_ID"),
        })

    except Exception as e:
        print("ORDER ERROR:", e)
        return Response({"error": "Order creation failed"}, status=500)



# =====================================================
# STEP 2 — VERIFY PAYMENT + UPDATE WALLET
# =====================================================
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])   # FIXED!
def razorpay_payment_success(request):

    try:
        user = request.user

        order_id = request.data.get("order_id")
        payment_id = request.data.get("payment_id")
        signature = request.data.get("signature")
        amount = request.data.get("amount")  # rupees

        if not all([order_id, payment_id, signature]):
            return Response({"error": "Missing payment details"}, status=400)

        # -------------------------------
        # VERIFY SIGNATURE
        # -------------------------------
        generated_signature = hmac.new(
            bytes(config("RAZOR_KEY_SECRET"), "utf-8"),
            msg=bytes(order_id + "|" + payment_id, "utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()

        if generated_signature != signature:
            return Response({"error": "Invalid payment signature"}, status=400)

        # -------------------------------
        # UPDATE WALLET (SAFE DECIMAL)
        # -------------------------------
        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.balance = wallet.balance + Decimal(amount)
        wallet.save()

        return Response({
            "success": True,
            "message": "Payment verified & wallet updated",
            "new_balance": wallet.balance
        })

    except Exception as e:
        print("VERIFY ERROR:", e)
        return Response({"error": "Payment verification failed"}, status=500)
# ============================= END OF FILE =============================