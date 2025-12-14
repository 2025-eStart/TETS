// data.local.DeviceIdManager
package com.example.impulsecoachapp.data.local

import android.content.Context
import android.content.SharedPreferences
import java.util.UUID
import javax.inject.Inject
import dagger.hilt.android.qualifiers.ApplicationContext

/**
 * 로그인 없이 사용자를 구분하기 위해
 * 기기에 고유한 ID(UUID)를 생성하고 저장하는 클래스
 */
class DeviceIdManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val prefs: SharedPreferences = context.getSharedPreferences("app_prefs", Context.MODE_PRIVATE)

    fun getDeviceId(): String {
        // 1. 저장된 ID가 있는지 확인
        val savedId = prefs.getString("device_id", null)

        if (savedId != null) {
            return savedId
        }

        // 2. 없으면 새로 생성 (UUID)
        val newId = UUID.randomUUID().toString()

        // 3. 저장
        prefs.edit().putString("device_id", newId).apply()

        return newId
    }
}