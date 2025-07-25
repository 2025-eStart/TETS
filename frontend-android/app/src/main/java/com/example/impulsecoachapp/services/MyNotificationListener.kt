package com.example.impulsecoachapp.services

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log

class MyNotificationListener : NotificationListenerService() {

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        super.onNotificationPosted(sbn)
        if (sbn == null) return

        val packageName = sbn.packageName
        val extras = sbn.notification.extras
        val title = extras.getString("android.title") ?: ""
        val text = extras.getString("android.text") ?: ""

        Log.d("NotificationListener", "Received: $packageName | $title | $text")

        // 1. 결제 관련 앱인지 필터링 (예시)
        if (packageName in listOf("com.kbcard.cain.sso", "com.kakaobank.android", "com.nh.smartcard")) {

            // 2. 결제 관련 키워드가 있는지 필터링
            if (title.contains("승인") || text.contains("결제") || text.contains("원")) {

                // 3. 정규표현식(Regex)으로 정보 추출 (가장 중요!)
                // 예시: "15,000원 승인 (주)스타벅스"
                val amount = extractAmount(text) // 금액 추출 함수
                val store = extractStore(text)  // 가맹점 추출 함수
                val date = sbn.postTime         // 알림 수신 시각 (Long 타입)

                if (amount != null && store != null) {
                    Log.i("PaymentParsed", "금액: $amount, 가맹점: $store, 시각: $date")
                    // 4. 추출한 정보를 서버로 전송 (아래 4단계에서 만들 함수 호출)
                    // sendTransactionToServer(userId, amount, store, date)
                }
            }
        }
    }

    // 여기에 정규식 기반의 정보 추출 함수들을 만듭니다.
    private fun extractAmount(text: String): Int? { /* ... */ return null }
    private fun extractStore(text: String): String? { /* ... */ return null }
}