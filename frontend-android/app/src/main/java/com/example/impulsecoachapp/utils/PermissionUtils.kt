package com.example.impulsecoachapp.utils

import android.content.Context
import androidx.core.app.NotificationManagerCompat

// object 키워드를 사용해 싱글톤으로 만들면 어디서든 쉽게 접근 가능
object PermissionUtils {

    /**
     * 알림 접근 권한이 부여되었는지 확인하는 함수
     * @param context 함수를 호출하는 곳의 Context
     * @return 권한이 있으면 true, 없으면 false
     */
    fun isNotificationPermissionGranted(context: Context): Boolean {
        val myPackageName = context.packageName
        val enabledListeners = NotificationManagerCompat.getEnabledListenerPackages(context)
        return enabledListeners.contains(myPackageName)
    }
}